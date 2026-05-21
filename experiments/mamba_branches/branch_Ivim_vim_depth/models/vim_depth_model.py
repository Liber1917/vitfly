"""ViM-depth: depth image → patch (6×6=36) → bidirectional Mamba scan → velocity.
This is the ORIGINAL ViM [Zhu et al. 2024] usage — NOT our previous SSM(1-step)."""
import torch, torch.nn as nn, torch.nn.functional as F

class ViMDepth(nn.Module):
    def __init__(self, dim=256, d_state=16, n_layers=6, patch_size=10):
        super().__init__()
        n_patches = (60 // patch_size) * (90 // patch_size)  # 6×9=54 patches
        self.patch_embed = nn.Linear(patch_size * patch_size, dim)
        self.pos_embed = nn.Parameter(torch.randn(1, n_patches, dim) * 0.02)
        self.state_proj = nn.Linear(7, dim)  # vel(3) + quat(4), matches E/D/H
        self.layers = nn.ModuleList([SSMLayer(dim, d_state) for _ in range(n_layers)])
        self.norm = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, 3)
        self.ps = patch_size

    def forward(self, X, *_):
        d = X[0]
        B, C, H, W = d.shape
        ps = self.ps
        patches = d.unfold(2, ps, ps).unfold(3, ps, ps)
        patches = patches.permute(0, 2, 3, 1, 4, 5).contiguous()
        patches = patches.view(B, -1, ps * ps)  # (B, N, 100)
        # State conditioning (same scaling as E/D/H: vel*0.1 + quat)
        state_feat = self.state_proj(torch.cat((X[1] * 0.1, X[2]), dim=1))
        x = self.patch_embed(patches) + self.pos_embed + state_feat.unsqueeze(1)
        for layer in self.layers:
            x = layer(x)
        x = self.norm(x).mean(dim=1)  # global average pooling
        return self.head(x), None

class SSMLayer(nn.Module):
    def __init__(self, dim=256, ds=16):
        super().__init__(); self.ds = ds
        self.norm = nn.LayerNorm(dim)
        self.fwd = SSM(dim, ds)
        self.bwd = SSM(dim, ds)
        self.mlp = nn.Sequential(nn.Linear(dim, dim*4), nn.GELU(), nn.Linear(dim*4, dim))
    def forward(self, x):
        r = x
        x = self.norm(x)
        x_fwd, _ = self.fwd(x)
        x_bwd, _ = self.bwd(x.flip(1))
        x = x_fwd + x_bwd.flip(1)
        return r + self.mlp(x)

class SSM(nn.Module):
    def __init__(self, dim=256, ds=16):
        super().__init__(); self.ds = ds
        self.xp = nn.Linear(dim, ds*2, bias=False)
        self.dt = nn.Linear(dim, dim, bias=True)
        self.Al = nn.Parameter(torch.randn(ds))
        self.D = nn.Parameter(torch.ones(dim))
        self.Cp = nn.Linear(dim, ds, bias=False)
    def forward(self, x, s=None):
        """Vectorized prefix-scan SSM. Uses FP64 for cumulative scan for
        numerical stability, all other ops in FP32."""
        B, L, D = x.shape
        xi = self.xp(x)                        # (B, L, 2*ds) FP32
        dt = torch.sigmoid(self.dt(x).mean(-1))# (B, L) FP32
        dA = torch.exp(dt.unsqueeze(-1) * (-torch.exp(self.Al)))  # (B,L,ds) FP32
        dB = dt.unsqueeze(-1) * xi[:,:,:self.ds]                 # (B,L,ds) FP32

        # Vectorized prefix scan in FP64 for numerical stability.
        #   s_t = sum_{i=0}^{t} (prod_{j=i+1}^{t} dA_j) * dB_i * x_i
        dA_f64 = dA.double()
        dB_f64 = dB.double()
        x_f64 = x.double()
        xi_f64 = xi.double()
        D_f64 = self.D.double()

        log_dA = torch.log(dA_f64.clamp(min=1e-10))  # (B,L,ds)
        cumlog = torch.cumsum(log_dA, dim=1)          # cumprod in log-space
        P_t = torch.exp(cumlog)                       # cumulative product
        P_t_inv = torch.exp(-cumlog)                  # inverse cumulative product
        # weighted = cumsum(P_i^{-1} * dB_i * x_i)
        weighted = torch.cumsum(P_t_inv * dB_f64 * x_f64[:,:,:self.ds], dim=1)
        s = P_t * weighted                            # all states (B,L,ds)

        # Output: y_t = C_t @ s_t + D * x_t
        y = (xi_f64[:,:,self.ds:] * s).sum(-1, keepdim=True) + D_f64 * x_f64
        return y.float(), s[:, -1, :].float()  # return last state for stateful use

def create_vim_depth(c):
    return ViMDepth(dim=c.get('dim', 256))

if __name__ == '__main__':
    m = ViMDepth(); p = sum(x.numel() for x in m.parameters())
    print(f"ViM-depth: {p:,} ({p/1e6:.2f}M)")
    X = [torch.randn(2, 1, 60, 90), torch.randn(2, 3), torch.randn(2, 4)]
    o, _ = m(X)
    print(f"Output: {o.shape}")
