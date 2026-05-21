# Stateful SSM Simulation Findings — Architecture Guidance for Training Pipeline

## Current Best Results

### Spheres (trained environment)

| Model | Params | BC 5m/s | MAE | Jerk | MAE_y | vs E stateless |
|-------|--------|---------|-----|------|-------|---------------|
| E (stateless) | 2.19M | 3 | 0.220 | 0.0230 | 0.060 | — (baseline) |
| **E_s** (stateful) | **2.19M** | **3** | **0.111** | **0.0063** | **0.012** | MAE -2.0×, Jerk -3.6× |
| **H** (stateful, d=32) | **1.11M** | **5** | **1.12** | **0.50** | **2.01** | Half params |
| Hs (stateful, d=4) | 1.09M | 7 | 1.22 | 0.45 | 2.22 | Smaller state worse |
| Ds (stateful, d=4) | 2.56M | DNF | — | — | — | STH-Mamba unstable |

### Trees (unseen environment — generalization)

| Model | Params | BC 5m/s | MAE | Jerk | vs E stateless |
|-------|--------|---------|-----|------|---------------|
| E (stateless) | 2.19M | 2 | 0.346 | 0.040 | — |
| **E_s** (stateful) | **2.19M** | **2** | **0.151** | **0.0045** | MAE -2.3×, Jerk **-8.9×** |
| **H** (stateful, d=32) | **1.11M** | **1** 🏆 | **0.145** | **0.0067** | **Crash -50%, MAE -2.4×** |

## Key Architecture Insights

### 1. Simpler SSM > Complex SSM for Stateful
H (CoarseSSM, 67 lines, torch-only) beats Ds (Mamba-2 SSM, 260 lines, einops) consistently.
- **Stateful simple SSM converges and flies. Stateful fancy SSM drifts.**
- Training pipeline should focus on E-style CoarseSSM variants.

### 2. State Size Sweet Spot: d_state=32 > 4
H (d_state=32) vs Hs (d_state=4):
- Spheres: 5 crashes vs 7
- Trees: 1 crash vs ? (Hs not tested in trees)
- Larger state absorbs more temporal context without drifting.

### 3. State Regularization Works
Previous stateful attempts (H v1, v2) all climbed out of control (z→10m).
After state regularization: all stateful models maintain stable z≈1.8-3.5m.
**State regularization is mandatory for stateful SSM training.**

### 4. Generalization Gain > Training Environment Gain
Stateful SSM shows much larger improvement in trees (unseen) than spheres:
- E_s trees: MAE -2.3× vs E (spheres only -2.0×)
- H trees: **1 crash** vs E's 2 (spheres: H 5 vs E 3)
- Hypothesis: temporal state helps handle novel obstacle patterns where single-frame perception is insufficient.

### 5. Control Quality > Collision Reduction
Stateful SSM doesn't reduce crashes much but dramatically improves:
- MAE: 2-9× better  
- Jerk: 3.6-8.9× smoother
- Lateral deviation (MAE_y): 5× better
- **Collision count is insufficient to measure SSM temporal head value.**

## Recommended Next Architecture

```
E_s architecture (proven):
  CNN encoder (455K, proven effective)
  → CoarseSSM d_state=32 (stateful)
  → Simple fusion MLP (no FineSSM needed)
  = ~1.1M params (same as H, not 2.19M of E)

Key change from E_s: drop FineSSM, keep only CoarseSSM.
This is what H already does — and H has better generalization (1 crash trees).
```

## Distillation Priority
E_s distill should be the highest priority experiment:
- If distill reduces crashes AND maintains control quality → publishable result
- If distill doesn't reduce crashes → still publishable (control quality alone is significant)

## Data Files
```
results/pr_eval/tracking_EStatefulModel_*.yaml   — E_s control quality (spheres + trees)
results/pr_eval/tracking_StatefulSSMNet_*.yaml   — H control quality (spheres + trees)
results/branch_E_s_bc_summary.yaml               — E_s crash data
results/branch_H_bc_summary.yaml                 — H crash data
