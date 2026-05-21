import torch, torch.nn as nn, torch.nn.functional as F
from decision_mamba_model import DecisionMambaNet

class EStatefulModel(nn.Module):
    def __init__(self, dim=256):
        super().__init__()
        self.base = DecisionMambaNet(embed_dim=dim)
    def forward(self, X, s=None):
        d, v, q = X
        if d.dim() == 5:
            B,S,C,H,W = d.shape
            vf = self.base.cnn_encoder(d.view(B*S, C, H, W)).view(B, S, -1)
            sf = self.base.state_proj(torch.cat((v.view(B*S,-1)*0.1,q.view(B*S,-1)),1).float()).view(B,S,-1)
            for t in range(S):
                cf, s = self.base.coarse_ssm(vf[:,t], s)
                ff, _ = self.base.fine_ssm(vf[:,t], None)
                o = self.base.fc_out(self.base.fusion(torch.cat([vf[:,t],sf[:,t],cf,ff],1)))
            return o, s
        return self._f(d, v, q, s)
    def _f(self, d, v, q, s):
        vf = self.base.cnn_encoder(d)
        sf = self.base.state_proj(torch.cat((v*0.1,q),1).float())
        cf, s = self.base.coarse_ssm(vf, s)
        ff, _ = self.base.fine_ssm(vf, None)
        return self.base.fc_out(self.base.fusion(torch.cat([vf,sf,cf,ff],1))), s

def create_e_stateful(c):
    return EStatefulModel(dim=c.get("embed_dim",256))

if __name__=="__main__":
    m=EStatefulModel(); p=sum(x.numel() for x in m.parameters())
    print(f"E_s: {p:,} ({p/1e6:.2f}M)")
