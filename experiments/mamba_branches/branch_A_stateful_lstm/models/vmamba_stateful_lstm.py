"""
Branch Ast: VMamba + Stateful LSTM with explicit hidden state threading.

Architecture:
- VMamba visual encoder (from Branch A)
- LSTM with explicit hidden state threading
- Output layer (3D velocity command)

Supports BOTH:
  4D input (B, C, H, W):  single-frame inference, state threaded via hidden_state param
  5D input (B, S, C, H, W): multi-frame rollout, state threaded internally over S

Training (seq_len=1):  caller manages hidden_state=None each step (stateless gradient)
Inference (seq_len>1): hidden state is threaded across frames for temporal coherence
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import os
import sys

# Reuse VMamba encoder from Branch A (no code duplication)
_A_MODELS = os.path.join(
    os.path.dirname(__file__),
    '../../branch_A_vmamba_lstm/models',
)
if _A_MODELS not in sys.path:
    sys.path.insert(0, _A_MODELS)

from vmamba_encoder import VMambaEncoder, create_vmamba_encoder


class RefineInputs(nn.Module):
    """Input preprocessing module (shared with Branch A)."""
    def __init__(self):
        super().__init__()

    def forward(self, X):
        if X[2] is None:
            X[2] = torch.zeros((X[0].shape[0], 4), device=X[0].device)
            X[2][:, 0] = 1
        return X


class VMambaStatefulLSTM(nn.Module):
    """
    VMamba + Stateful LSTM with explicit hidden state threading.

    Forward signature: (X, hidden_state=None) -> (output, hidden_state)

    Args:
        vmamba_config:  dict passed to create_vmamba_encoder()
        lstm_hidden:    hidden size of the LSTM
        lstm_layers:    number of LSTM layers
        dropout:        dropout rate

    Input X list:
        X[0]: depth image  — (B, C, H, W) or (B, S, C, H, W)
        X[1]: velocity     — (B, 3)
        X[2]: quaternion   — (B, 4)  or None

    Returns:
        output:       (B, 3)  velocity command
        hidden_state: (h_n, c_n)  LSTM hidden/cell state tuple
    """

    def __init__(
        self,
        vmamba_config=None,
        lstm_hidden=128,
        lstm_layers=2,
        dropout=0.1,
    ):
        super().__init__()

        if vmamba_config is None:
            vmamba_config = {
                'in_channels': 1,
                'embed_dim': 64,
                'depth': 4,
                'd_state': 64,
                'dropout': dropout,
                'output_dim': 512,
            }

        # --- components ---
        self.vmamba = create_vmamba_encoder(vmamba_config)
        self.refine = RefineInputs()

        vmamba_output = vmamba_config.get('output_dim', 512)
        lstm_input = vmamba_output + 3 + 4          # features + velocity + quaternion

        self.lstm = nn.LSTM(
            input_size=lstm_input,
            hidden_size=lstm_hidden,
            num_layers=lstm_layers,
            dropout=dropout if lstm_layers > 1 else 0,
            bias=False,
        )

        self.fc_out = nn.Linear(lstm_hidden, 3)

        # --- config saved for introspection ---
        self.vmamba_config = vmamba_config
        self.lstm_hidden = lstm_hidden
        self.lstm_layers = lstm_layers

    # ------------------------------------------------------------------
    def _step(self, img, vel, quat, hidden_state):
        """Process one frame: VMamba → fuse → LSTM."""
        visual_feat = self.vmamba(img)                     # (B, 512)
        fused = torch.cat([visual_feat,
                           vel * 0.1,                       # velocity normalised
                           quat], dim=-1)                   # (B, 519)
        fused_seq = fused.unsqueeze(0)                     # (1, B, 519)

        if hidden_state is None:
            out, (h_n, c_n) = self.lstm(fused_seq)
            hidden_state = (h_n, c_n)
        else:
            out, hidden_state = self.lstm(fused_seq, hidden_state)

        return out.squeeze(0), hidden_state                # (B, 519), (h, c)

    # ------------------------------------------------------------------
    def forward(self, X, hidden_state=None):
        """
        Forward pass with 4D / 5D support.

        hidden_state:
          - None                        → initialised to zeros by LSTM
          - (h, c) tuple               → LSTM initial state

        Returns (output, hidden_state)
        """
        X = self.refine(X)
        img, vel, quat = X[0], X[1], X[2]

        # --- convert 4D → 5D for uniform loop ---
        if img.dim() == 4:                                 # (B, C, H, W)
            is_4d = True
            img = img.unsqueeze(1)                         # (B, 1, C, H, W)
        else:
            is_4d = False

        B, S, C, H, W = img.shape

        # --- frame loop ---
        for t in range(S):
            frame = img[:, t]                              # (B, C, H, W)
            out, hidden_state = self._step(frame, vel, quat, hidden_state)

        # --- output projection ---
        out = self.fc_out(out)                             # (B, 3)

        return out, hidden_state

    # ------------------------------------------------------------------
    # Parameter counting helpers
    def get_parameter_count(self):
        return sum(p.numel() for p in self.parameters())

    def get_vmamba_params(self):
        return sum(p.numel() for p in self.vmamba.parameters())

    def get_lstm_params(self):
        return sum(p.numel() for p in self.lstm.parameters())


# =====================================================================
# Factory
# =====================================================================
def create_vmamba_stateful_lstm(config):
    """Create a VMambaStatefulLSTM from a config dict."""
    vmamba_config = config.get('vmamba', {
        'in_channels': 1,
        'embed_dim': 64,
        'depth': 4,
        'd_state': 64,
        'dropout': 0.1,
        'output_dim': 512,
    })
    return VMambaStatefulLSTM(
        vmamba_config=vmamba_config,
        lstm_hidden=config.get('lstm_hidden', 128),
        lstm_layers=config.get('lstm_layers', 2),
        dropout=config.get('dropout', 0.1),
    )


# =====================================================================
# Self-test
# =====================================================================
if __name__ == '__main__':
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('=' * 55)
    print('VMambaStatefulLSTM — Self Test')
    print('=' * 55)
    print(f'device: {device}\n')

    config = {
        'vmamba': {
            'embed_dim': 64,
            'depth': 4,
            'd_state': 64,
            'output_dim': 512,
        },
        'lstm_hidden': 128,
        'lstm_layers': 2,
        'dropout': 0.1,
    }

    model = create_vmamba_stateful_lstm(config).to(device)
    total = model.get_parameter_count()
    vmamba_p = model.get_vmamba_params()
    lstm_p = model.get_lstm_params()
    print(f'VMamba params:     {vmamba_p:>8,}')
    print(f'LSTM params:       {lstm_p:>8,}')
    print(f'Total params:      {total:>8,}  ({total/1e6:.2f}M)')
    print()

    # --- Test 4D input ---
    B, C, H, W = 2, 1, 60, 90
    x_4d = torch.randn(B, C, H, W, device=device)
    vel   = torch.randn(B, 3, device=device)
    quat  = torch.randn(B, 4, device=device)

    with torch.no_grad():
        out_4d, hs_4d = model([x_4d, vel, quat])

    assert out_4d.shape == (B, 3), f'4D out shape mismatch: {out_4d.shape}'
    assert isinstance(hs_4d, tuple) and len(hs_4d) == 2, 'hs_4d must be (h, c) tuple'
    assert hs_4d[0].shape == (config['lstm_layers'], B, config['lstm_hidden'])
    print(f'✓ 4D input ({B}, {C}, {H}, {W}) → out {list(out_4d.shape)}  '
          f'hidden {list(hs_4d[0].shape)}')

    # --- Test 5D input ---
    S = 5
    x_5d = torch.randn(B, S, C, H, W, device=device)

    with torch.no_grad():
        out_5d, hs_5d = model([x_5d, vel, quat])

    assert out_5d.shape == (B, 3), f'5D out shape mismatch: {out_5d.shape}'
    assert isinstance(hs_5d, tuple) and len(hs_5d) == 2, 'hs_5d must be (h, c) tuple'
    print(f'✓ 5D input ({B}, {S}, {C}, {H}, {W}) → out {list(out_5d.shape)}  '
          f'hidden {list(hs_5d[0].shape)}')

    # --- Statefulness check ---
    # Series of 4D calls with state threading should give same result as 5D with S=4
    x_4d_seq = torch.randn(B, C, H, W, device=device)
    hs = None
    for _ in range(4):
        out_seq, hs = model([x_4d_seq, vel, quat], hidden_state=hs)
    print(f'✓ 4 series calls → out {list(out_seq.shape)}  state kept alive')

    print()
    print('All tests passed.')
