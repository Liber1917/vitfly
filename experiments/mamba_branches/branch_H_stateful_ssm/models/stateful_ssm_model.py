"""
Branch H: Stateful SSM Temporal Head for Visual Obstacle Avoidance

Key design: SSW's CoarseSSM maintains hidden state across consecutive frames,
making it a TRUE temporal head (not just a feature processor applied to single frames).

Architecture:
  Frame t0: CNN encodes depth → CoarseSSM(state=None) → (out0, h1)
  Frame t1: CNN encodes depth → CoarseSSM(state=h1)   → (out1, h2)
  ...
  Frame tN: CNN encodes depth → CoarseSSM(state=hN)   → (outN, h_{N+1})
  Only last frame output (outN) goes to fusion → velocity command

Based on: DecisionMamba's CNNEncoder + CoarseSSM (branch E)
           Guo & Dao. Mamba: Linear-Time Sequence Modeling (arXiv:2312.00752)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class RefineInputs(nn.Module):
    """Input preprocessing: resize depth to 60x90, fill missing quaternion."""
    def __init__(self):
        super().__init__()

    def forward(self, depth, vel, quat):
        if quat is None:
            quat = torch.zeros((depth.shape[0], 4), device=depth.device)
            quat[:, 0] = 1
        if depth.shape[-2] != 60 or depth.shape[-1] != 90:
            depth = F.interpolate(depth, size=(60, 90), mode='bilinear')
        return depth, vel, quat


class CNNEncoder(nn.Module):
    """Lightweight CNN visual encoder (~455K params). Same as Branch E."""
    def __init__(self, in_channels=1, output_dim=256):
        super().__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels, 32, 3, stride=2, padding=1),
            nn.BatchNorm2d(32), nn.GELU())
        self.conv2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.BatchNorm2d(64), nn.GELU())
        self.conv3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, stride=2, padding=1),
            nn.BatchNorm2d(128), nn.GELU())
        self.conv4 = nn.Sequential(
            nn.Conv2d(128, 256, 3, stride=2, padding=1),
            nn.BatchNorm2d(256), nn.GELU())
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Linear(256, output_dim)

    def forward(self, x):
        x = self.conv1(x)  # (B,32,30,45)
        x = self.conv2(x)  # (B,64,15,23)
        x = self.conv3(x)  # (B,128,8,12)
        x = self.conv4(x)  # (B,256,4,6)
        x = self.pool(x)   # (B,256,1,1)
        return self.fc(x.flatten(1))


class CoarseSSM(nn.Module):
    """
    Stateful Mamba SSM block. Maintains hidden state across forward calls.
    
    Forward(x, state) → (y, new_state)
    If state is None, initializes to zeros.
    If state is provided, continues from previous state.
    
    d_state=32 gives ~300K params. Same implementation as Branch E.
    """
    def __init__(self, dim, d_state=32):
        super().__init__()
        self.dim = dim
        self.d_state = d_state

        self.in_proj = nn.Linear(dim, dim * 2)
        self.x_proj = nn.Linear(dim, d_state * 2, bias=False)
        self.dt_proj = nn.Linear(dim, dim, bias=True)
        self.A_log = nn.Parameter(torch.randn(d_state))
        self.D = nn.Parameter(torch.ones(dim) * 0.1)
        self.out_proj = nn.Linear(dim, dim)
        self.norm = nn.LayerNorm(dim)

    def forward(self, x, state=None):
        B = x.shape[0]
        x_norm = self.norm(x)
        xz = self.in_proj(x_norm)
        x_inner, z = xz.chunk(2, dim=-1)

        BC = self.x_proj(x_inner)
        B_state, C_state = BC.chunk(2, dim=-1)

        dt = F.softplus(self.dt_proj(x_inner))
        A = -torch.exp(self.A_log)

        dt_mean = dt.mean(dim=-1, keepdim=True)
        dA = torch.exp(dt_mean * A.unsqueeze(0))
        dB = dt_mean * B_state

        if state is None:
            state = torch.zeros(B, self.d_state, device=x.device)
        state = dA * state + dB * x_inner[:, :self.d_state]

        y = (C_state * state).sum(dim=-1, keepdim=True)
        y = y.expand(-1, self.dim)
        y = y + self.D * x_inner
        y = y * torch.sigmoid(z)
        y = self.out_proj(y)
        return y, state


class StatefulSSMNet(nn.Module):
    """
    Stateful SSM architecture for end-to-end quadrotor obstacle avoidance.
    
    Processes seq_len consecutive depth frames with SSM hidden state
    carried forward between frames — true temporal reasoning.
    
    Parameters: ~1.0M (CNN 455K + CoarseSSM 300K + fusion 250K)
    """
    def __init__(self, embed_dim=256, d_state=32, dropout=0.1):
        super().__init__()
        self.embed_dim = embed_dim

        self.refine = RefineInputs()
        self.cnn_encoder = CNNEncoder(in_channels=1, output_dim=embed_dim)
        self.state_proj = nn.Linear(7, embed_dim)  # vel(3) + quat(4)
        self.coarse_ssm = CoarseSSM(embed_dim, d_state)

        fusion_dim = embed_dim * 3  # vision + state_meta + ssm
        self.fusion = nn.Sequential(
            nn.Linear(fusion_dim, 384),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(384, 192),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.fc_out = nn.Linear(192, 3)

    def forward(self, X, ssm_state=None):
        """
        Args:
            X: tuple of (depth, vel, quat)
               depth: (B, seq_len, 1, 60, 90) when seq_len > 1
                      (B, 1, 60, 90) when seq_len == 1
               vel:   (B, seq_len, 3) or (B, 3)
               quat:  (B, seq_len, 4) or (B, 4)
            ssm_state: (B, d_state) or None

        Returns:
            velocity: (B, 3)
            new_state: (B, d_state)
        """
        depth = X[0]
        vel = X[1]
        quat = X[2]

        # Determine sequence length from depth tensor
        if depth.dim() == 5:  # (B, seq_len, C, H, W)
            B, seq_len, C, H, W = depth.shape
        else:  # (B, C, H, W)
            B = depth.shape[0]
            seq_len = 1
            depth = depth.unsqueeze(1)   # → (B, 1, C, H, W)
        if vel.dim() == 2:
            vel = vel.unsqueeze(1)        # → (B, 1, 3)
        if quat.dim() == 2:
            quat = quat.unsqueeze(1)      # → (B, 1, 4)

        # Process each frame sequentially with state passing
        for t in range(seq_len):
            d_t, vel_t, quat_t = self.refine(depth[:, t], vel[:, t], quat[:, t])
            vis_feat = self.cnn_encoder(d_t)
            ssm_feat, ssm_state = self.coarse_ssm(vis_feat, ssm_state)

        # Only last frame's features go to fusion
        state_feat = self.state_proj(torch.cat((vel[:, -1] * 0.1, quat[:, -1]), dim=1))
        fusion_in = torch.cat((vis_feat, state_feat, ssm_feat), dim=1)
        x = self.fusion(fusion_in)
        return self.fc_out(x), ssm_state

    def get_parameter_count(self):
        return sum(p.numel() for p in self.parameters())


def create_stateful_ssm_model(config=None):
    if config is None:
        config = {}
    return StatefulSSMNet(
        embed_dim=config.get('embed_dim', 256),
        d_state=config.get('d_state', 32),
        dropout=config.get('dropout', 0.1),
    )


if __name__ == '__main__':
    model = StatefulSSMNet()
    params = model.get_parameter_count()
    print(f"StatefulSSM total params: {params:,} ({params/1e6:.2f}M)")

    # Test T=1 (stateless)
    print("\n--- T=1 ---")
    X1 = [torch.randn(2, 1, 60, 90), torch.randn(2, 3), torch.randn(2, 4)]
    with torch.no_grad():
        v1, s1 = model(X1)
    print(f"  Input depth: {X1[0].shape}, Output: {v1.shape}, State: {s1.shape}")

    # Test T=4 (stateful — real temporal processing)
    print("\n--- T=4 ---")
    X4 = [torch.randn(2, 4, 1, 60, 90), torch.randn(2, 4, 3), torch.randn(2, 4, 4)]
    with torch.no_grad():
        v4, s4 = model(X4)
    print(f"  Input depth: {X4[0].shape}, Output: {v4.shape}, State: {s4.shape}")

    # Verify state is different from zeros (proving state was used)
    print(f"\n  State mean: {s4.mean():.4f}, State std: {s4.std():.4f}")
    print(f"  Output mean: {v4.mean():.4f}, Output std: {v4.std():.4f}")

    # T=1 vs T=4 should produce different outputs (temporal context matters)
    with torch.no_grad():
        # T=1 uses only last frame
        v1_last, _ = model([X4[0][:, -1:], X4[1][:, -1:], X4[2][:, -1:]])
        v4_full, _ = model(X4)
    diff = (v1_last - v4_full).abs().mean()
    print(f"\n  T=1(last only) vs T=4(full) output diff: {diff:.6f}")
    print(f"  {'Temporal context matters!' if diff > 0.001 else 'WARNING: no temporal effect'}")
