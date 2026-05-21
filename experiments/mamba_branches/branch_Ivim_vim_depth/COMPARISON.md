# SSM Formulation Comparison Table

## Taxonomy

We identify three distinct SSM formulations used in this project:

### 1. Stateless SSM (seq_len=1)
The SSM state `h` is initialized to zero and updated for exactly 1 step per forward pass.
`h = ΔA · 0 + ΔB · x` → `h = ΔB · x`, `y = C · (ΔB · x) + D · x`
**Effect**: Degenerates to a gated linear projection — **no sequence mixing**.

### 2. Temporal Stateful SSM (seq_len=16)
Same SSM formulation but state IS propagated across sequential video frames.
`h_t = ΔA · h_{t-1} + ΔB · x_t`
**Problem** (Stuffed Mamba 2024): `T_forget ≈ 5.172 · d_state - 4.469`. For d_state=16, need ~78 frames for effective training. We only use seq_len=16, so state retention is too short to learn useful dynamics.

### 3. Spatial Token Mixing via ViM (bidirectional Mamba scan)
Patches the image → 54 patch tokens → bidirectional SSM scan across patch positions.
`h_pos = fwd_scan(patch_position)` + `bwd_scan(flipped_patch_position)`
**Effect**: True sequence token mixing (like self-attention), using Mamba as a spatial mixer.

## Results

| Formulation | Branch | Architecture | Params | Inputs | Best Val Loss | Simulation (60m, 5m/s) | Notes |
|-------------|--------|-------------|--------|--------|--------------|----------------------|-------|
| **Stateless** | E | DecisionMamba (CNN→CoarseSSM+FineSSM) | 2.19M | depth+vel+quat | **0.230** | 3 crashes (BC), **1 crash (Distill)** | Working baseline |
| **Stateful** | E_s | Same arch, state propagated seq_len=16 | 2.19M | depth+vel+quat | 0.262 | 4 crashes (BC) | Worse than stateless — seq_len too short |
| | H | Stateful SSM, d_state=16 | ~2.19M | depth+vel+quat | 0.253 | — | Similar to E_s |
| | Hs | Stateful SSM, d_state=4 | ~2.19M | depth+vel+quat | **0.246** | — | Smaller state actually helps |
| | Ds | STH-Mamba stateful, d_state=4 | ~2.60M | depth+vel+quat | **0.229** | — | Best stateful (matches stateless E) |
| | Dst | STH-Mamba stateful | ~2.60M | depth+vel+quat | 0.259 | 2 crashes (BC) | Worse than D with seq_len=16 |
| | ResE | Residual SSM | ~2.19M | depth+vel+quat | 0.263 | — | Closest to E_s |
| **ViM** | ViM-depth | Patch→6×Bidirectional Mamba→Pool | 4.14M | **depth only** | **0.482** (epoch 8) | — | Training in progress |

## Abandoned Branches (did not converge)

| Branch | Best Val Loss | Reason |
|--------|-------------|--------|
| CrossE (SSM+Cross-Attn) | 0.496 | Did not converge |
| LapE (Laplace Mixer) | 0.483 | Did not converge |
| ScanE (Spatial SSM scan) | 0.501 | Did not converge |

## Key Observations

1. **Stateful SSM does not help** for this task — the temporal horizon (seq_len=16) is too short relative to the required state retention (T_forget ≈ 78 for d_state=16).
2. **ViM is a fundamentally different operator** — it's a spatial token mixer, not a temporal state keeper. The val loss convergence is slower because it's learning 54-token patch interactions from scratch.
3. **ViM uses depth-only** input — it doesn't use velocity/quaternion. This is a deliberate architectural choice (image→action mapping), but it puts ViM at an information disadvantage vs E/D which get 7 extra state dimensions.
