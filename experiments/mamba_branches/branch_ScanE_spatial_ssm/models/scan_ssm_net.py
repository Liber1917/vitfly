import torch, torch.nn as nn, torch.nn.functional as F
from decision_mamba_model import CNNEncoder, CoarseSSM

class ScanSSMNet(nn.Module):
    def __init__(self, embed_dim=256, d_state=32):
        super().__init__()
        self.cnn = CNNEncoder(output_dim=embed_dim)
        self.ssm = CoarseSSM(dim=embed_dim, d_state=d_state)
        self.fusion = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 2), nn.GELU(),
            nn.Linear(embed_dim * 2, embed_dim), nn.GELU(),
        )
        self.fc_out = nn.Linear(embed_dim, 3)

    def forward(self, X):
        if X[2] is None:
            X[2] = torch.zeros((X[0].shape[0], 4), device=X[0].device); X[2][:, 0] = 1
        if X[0].shape[-2:] != (60, 90):
            X[0] = F.interpolate(X[0], (60, 90), mode='bilinear')
        h = self.cnn.conv1(X[0]); h = self.cnn.conv2(h)
        h = self.cnn.conv3(h); h = self.cnn.conv4(h)
        B = h.shape[0]
        tokens = h.flatten(2).permute(0, 2, 1).reshape(B * 24, 256)
        scanned, _ = self.ssm(tokens, None)
        feat = scanned.view(B, 24, 256).mean(dim=1)
        feat = self.fusion(feat)
        return self.fc_out(feat), None

def create_scan_ssm(config):
    return ScanSSMNet(embed_dim=config.get('embed_dim', 256))

if __name__ == '__main__':
    m = ScanSSMNet()
    print(f"ScanE: {sum(x.numel() for x in m.parameters()):,} params")
