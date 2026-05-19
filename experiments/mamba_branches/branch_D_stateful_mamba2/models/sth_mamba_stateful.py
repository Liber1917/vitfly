"""
Branch Dst: STH-Mamba + Stateful Mamba-2 with explicit state threading.

Architecture:
- CNN spatial encoder (from Branch D)
- Mamba-2 temporal head with state threading
- Output layer (3D velocity command)

Supports BOTH:
  4D input (B, C, H, W):  single-frame inference, state threaded via hidden_state param
  5D input (B, S, C, H, W): multi-frame rollout, state threaded internally over S

Training (seq_len=1):  caller manages hidden_state=None each step (stateless gradient)
Inference (seq_len>1): Mamba-2 state (dA * state + dB * x) is threaded across frames.

The Mamba2SSMBlock already implements:
    state = dA * state + dB * x
This wrapper makes state threading EXPLICIT across time steps.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import sys

# Reuse spatial encoder and Mamba-2 blocks from Branch D (no code duplication)
_D_MODELS = os.path.join(
    os.path.dirname(__file__),
    '../../branch_D_sth_mamba/models',
)
if _D_MODELS not in sys.path:
    sys.path.insert(0, _D_MODELS)

from sth_mamba_model import SpatialEncoder, Mamba2SSMBlock, Mamba2TemporalHead


class STHMambaStateful(nn.Module):
    """
    STH-Mamba + Stateful Mamba-2 with explicit state threading.

    Forward signature: (X, hidden_state=None) -> (output, hidden_state)

    Args:
        spatial_dim:       output dim of CNN spatial encoder
        temporal_d_state:  Mamba-2 state dimension
        temporal_hidden:   Mamba-2 inner / hidden dim
        temporal_layers:   number of stacked Mamba-2 blocks
        dropout:           dropout rate

    Input X list:
        X[0]: depth image  — (B, C, H, W) or (B, S, C, H, W)
        X[1]: velocity     — (B, 3)
        X[2]: quaternion   — (B, 4)  or None

    Returns:
        output:       (B, 3)  velocity command
        hidden_state: list of per-block state tensors, each (B, d_state)
    """

    def __init__(
        self,
        spatial_dim=256,
        temporal_d_state=16,
        temporal_hidden=256,
        temporal_layers=3,
        dropout=0.1,
    ):
        super().__init__()

        self.spatial_encoder = SpatialEncoder(output_dim=spatial_dim, dropout=dropout)
        self.state_proj = nn.Linear(7, 64)                       # velocity(3) + quat(4) → 64

        fusion_input = spatial_dim + 64
        self.temporal_head = Mamba2TemporalHead(
            fusion_input, temporal_d_state, temporal_hidden, temporal_layers, dropout,
        )

        self.fc_out = nn.Sequential(
            nn.Linear(temporal_hidden, 128),
            nn.GELU(),
            nn.Linear(128, 3),
        )

        # saved for introspection
        self.spatial_dim = spatial_dim
        self.temporal_d_state = temporal_d_state
        self.temporal_hidden = temporal_hidden
        self.temporal_layers = temporal_layers

    # ------------------------------------------------------------------
    def _encode_frame(self, img, vel, quat):
        """CNN spatial encoding + state vector fusion."""
        spatial_feat = self.spatial_encoder(img)                 # (B, spatial_dim)
        state_feat = self.state_proj(
            torch.cat((vel * 0.1, quat), dim=1)                  # (B, 7)
        )                                                        # (B, 64)
        return torch.cat((spatial_feat, state_feat), dim=1)     # (B, spatial_dim+64)

    # ------------------------------------------------------------------
    def forward(self, X, hidden_state=None):
        """
        Forward pass with 4D / 5D support.

        hidden_state:
          - None              → initialised to zeros inside Mamba2SSMBlock
          - list of tensors   → one state per temporal layer

        Returns (output, hidden_state)
        """
        # --- input refinement ---
        if X[2] is None:
            X[2] = torch.zeros((X[0].shape[0], 4), device=X[0].device)
            X[2][:, 0] = 1

        img, vel, quat = X[0], X[1], X[2]

        # --- convert 4D → 5D for uniform loop ---
        if img.dim() == 4:                                     # (B, C, H, W)
            is_4d = True
            img = img.unsqueeze(1)                             # (B, 1, C, H, W)
        else:
            is_4d = False

        B, S, C, H, W = img.shape

        # --- frame loop: thread Mamba-2 state across time ---
        for t in range(S):
            frame = img[:, t]                                  # (B, C, H, W)

            # Resize on-the-fly if needed
            if frame.shape[-2] != 60 or frame.shape[-1] != 90:
                frame = F.interpolate(frame, size=(60, 90), mode='bilinear')

            fusion_feat = self._encode_frame(frame, vel, quat)  # (B, fusion_input)
            temporal_out, hidden_state = self.temporal_head(
                fusion_feat, hidden_state,
            )

        # --- output projection ---
        out = self.fc_out(temporal_out)                        # (B, 3)

        return out, hidden_state

    # ------------------------------------------------------------------
    def get_parameter_count(self):
        return sum(p.numel() for p in self.parameters())

    def get_spatial_params(self):
        return sum(p.numel() for p in self.spatial_encoder.parameters())

    def get_temporal_params(self):
        return sum(p.numel() for p in self.temporal_head.parameters())


# =====================================================================
# Factory
# =====================================================================
def create_sth_mamba_stateful(config):
    """Create an STHMambaStateful from a config dict."""
    return STHMambaStateful(
        spatial_dim=config.get('spatial_dim', 256),
        temporal_d_state=config.get('temporal_d_state', 16),
        temporal_hidden=config.get('temporal_hidden', 256),
        temporal_layers=config.get('temporal_layers', 3),
        dropout=config.get('dropout', 0.1),
    )


# =====================================================================
# Self-test
# =====================================================================
if __name__ == '__main__':
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('=' * 55)
    print('STHMambaStateful — Self Test')
    print('=' * 55)
    print(f'device: {device}\n')

    config = {
        'spatial_dim': 256,
        'temporal_d_state': 16,
        'temporal_hidden': 256,
        'temporal_layers': 3,
        'dropout': 0.1,
    }

    model = create_sth_mamba_stateful(config).to(device)
    total = model.get_parameter_count()
    spatial_p = model.get_spatial_params()
    temporal_p = model.get_temporal_params()
    print(f'Spatial encoder params: {spatial_p:>8,}')
    print(f'Temporal head params:   {temporal_p:>8,}')
    print(f'Total params:           {total:>8,}  ({total/1e6:.2f}M)')
    print()

    # --- Test 4D input ---
    B, C, H, W = 2, 1, 60, 90
    x_4d = torch.randn(B, C, H, W, device=device)
    vel  = torch.randn(B, 3, device=device)
    quat = torch.randn(B, 4, device=device)

    with torch.no_grad():
        out_4d, hs_4d = model([x_4d, vel, quat])

    assert out_4d.shape == (B, 3), f'4D out shape mismatch: {out_4d.shape}'
    assert isinstance(hs_4d, list) and len(hs_4d) == config['temporal_layers']
    print(f'✓ 4D input ({B}, {C}, {H}, {W}) → out {list(out_4d.shape)}  '
          f'state {len(hs_4d)} blocks × {list(hs_4d[0].shape)}')

    # --- Test 5D input ---
    S = 5
    x_5d = torch.randn(B, S, C, H, W, device=device)

    with torch.no_grad():
        out_5d, hs_5d = model([x_5d, vel, quat])

    assert out_5d.shape == (B, 3), f'5D out shape mismatch: {out_5d.shape}'
    assert isinstance(hs_5d, list) and len(hs_5d) == config['temporal_layers']
    print(f'✓ 5D input ({B}, {S}, {C}, {H}, {W}) → out {list(out_5d.shape)}  '
          f'state {len(hs_5d)} blocks × {list(hs_5d[0].shape)}')

    # --- Statefulness check ---
    # Series of 4D calls with state threading should give same result as 5D with S=4
    x_4d_seq = torch.randn(B, C, H, W, device=device)
    hs = None
    for _ in range(4):
        out_seq, hs = model([x_4d_seq, vel, quat], hidden_state=hs)
    print(f'✓ 4 series calls → out {list(out_seq.shape)}  state kept alive')

    # --- Resize test (non-standard input size) ---
    x_small = torch.randn(B, 1, 30, 45, device=device)
    with torch.no_grad():
        out_resize, hs_resize = model([x_small, vel, quat])
    assert out_resize.shape == (B, 3)
    print(f'✓ Resize test (30×45 → 60×90) → out {list(out_resize.shape)}')

    print()
    print('All tests passed.')
