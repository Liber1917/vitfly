import torch, torch.nn as nn, torch.nn.functional as F
from decision_mamba_model import CNNEncoder, CoarseSSM

class LaplaceSSMNet(nn.Module):
    def __init__(self, embed_dim=256, downsample=2):
        super().__init__()
        self.cnn = CNNEncoder(output_dim=embed_dim)
        self.ssm = CoarseSSM(dim=embed_dim, d_state=32)
        self.dwconv = nn.Conv2d(embed_dim, embed_dim, 3, 1, 1, groups=embed_dim)
        self.fc = nn.Linear(embed_dim, 3)

    def forward(self, X):
        if X[2] is None:
            X[2] = torch.zeros((X[0].shape[0], 4), device=X[0].device); X[2][:, 0] = 1
        if X[0].shape[-2:] != (60, 90):
            X[0] = F.interpolate(X[0], (60, 90), mode='bilinear')
        h = self.cnn.conv1(X[0]); h = self.cnn.conv2(h)
        h = self.cnn.conv3(h); h = self.cnn.conv4(h)

        low = F.avg_pool2d(h, kernel_size=2)          # downsample → (B,256,2,3)
        low_up = F.interpolate(low, size=h.shape[2:], mode='bilinear')
        high = h - low_up                              # 高频残差 (TinyViM §3.2)

        low_vec = low.mean(dim=[2, 3])
        low_ssm, _ = self.ssm(low_vec, None)

        high_enhanced = self.dwconv(high)
        high_vec = high_enhanced.mean(dim=[2, 3])

        fused = low_ssm + high_vec                     # 逐元素加法 (TinyViM)
        return self.fc(fused), None

def create_laplace_ssm(config):
    return LaplaceSSMNet(embed_dim=config.get('embed_dim', 256))

if __name__ == '__main__':
    m = LaplaceSSMNet()
    print(f"LapE: {sum(x.numel() for x in m.parameters()):,} params")
