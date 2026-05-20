"""GateE: SSM低频门控 × CNN高频空间特征 — 通道级融合, 无注意力瓶颈.
MobileMamba MRFFI (CVPR 2025) 启发: SSM做全局门控, CNN保留高频空间结构."""
import torch, torch.nn as nn, torch.nn.functional as F
from decision_mamba_model import CNNEncoder, CoarseSSM

class GateSSMNet(nn.Module):
    def __init__(self, embed_dim=256, gate_dim=128):
        super().__init__()
        self.cnn = CNNEncoder(output_dim=embed_dim)
        self.ssm = CoarseSSM(dim=embed_dim, d_state=32)
        self.spatial_proj = nn.Conv2d(embed_dim, gate_dim, 1)
        self.gate_proj = nn.Linear(embed_dim, gate_dim)
        self.fc_out = nn.Linear(gate_dim, 3)

    def forward(self, X):
        if X[2] is None:
            X[2] = torch.zeros((X[0].shape[0], 4), device=X[0].device); X[2][:, 0] = 1
        if X[0].shape[-2:] != (60, 90):
            X[0] = F.interpolate(X[0], (60, 90), mode='bilinear')
        h = self.cnn.conv1(X[0]); h = self.cnn.conv2(h)
        h = self.cnn.conv3(h); h = self.cnn.conv4(h)
        spatial = self.spatial_proj(h)
        pooled = h.mean(dim=[2, 3])
        ssm_out, _ = self.ssm(pooled, None)
        gate = torch.sigmoid(self.gate_proj(ssm_out)).unsqueeze(-1).unsqueeze(-1)
        fused = (spatial * gate).sum(dim=[2, 3])
        return self.fc_out(fused), None

def create_gate_ssm(config):
    return GateSSMNet(embed_dim=config.get('embed_dim', 256))

def create_cross_ssm(config):
    return create_gate_ssm(config)
