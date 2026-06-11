# Mamba/SSM for End-to-End Quadrotor Visual Obstacle Avoidance

This repository is a fork of [ViT-Fly](https://github.com/anish-bhattacharya/vitfly) (Bhattacharya et al., ICRA 2025) that systematically explores **Mamba / State Space Model (SSM) architectures** as drop-in replacements for the Vision Transformer encoder and LSTM temporal head in end-to-end quadrotor obstacle avoidance.

**Key contributions:**
- 6 Mamba/SSM student architectures systematically compared under unified training and evaluation protocols
- Cross-architecture knowledge distillation from ViT+LSTM teacher to Mamba students, with identified boundary conditions (encoder spatial structure determines distillation success)
- Stateful vs. stateless SSM temporal head comparison, revealing control quality improvements but collision metric limitations
- Lightweight CoarseSSM architecture (1.11M params) with stateful temporal modeling

## Branches Overview

| Branch | Encoder | Temporal Head | Params | Key Feature |
|--------|---------|---------------|--------|-------------|
| A | SS2D (VMamba) | LSTM | 0.97M | 2D selective scan, stateful |
| B | MambaVision | SSM | 2.55M | Hybrid CNN-Mamba encoder |
| **B+** | **MambaVision** | **Mamba-3** | **2.32M** | **Best generalization** |
| C | CNN | Mamba-3 | 2.10M | Full conv + SSM |
| D | CNN | STH-Mamba | 2.84M | Mamba-2 based temporal |
| Ds | CNN | STH-Mamba (stateful) | 2.56M | Stateful STH-Mamba |
| **E** | **CNN (light)** | **SSM (DecisionMamba)** | **2.19M** | **Best BC+distill balance** |
| **E_s** | **CNN (light)** | **SSM (stateful)** | **2.19M** | **Stateful variant of E** |
| Fv5 | CNN (wide) | SSM | 5.28M | Parameter allocation test |
| **G_basic** | **CNN** | **MLP** | **0.49M** | **No temporal head baseline** |
| G_lstm | CNN | LSTM | 0.77M | LSTM baseline |
| **H** | **CNN** | **CoarseSSM (stateful)** | **1.11M** | **Lightweight stateful** |
| Teacher | MixTransformer | 3-layer LSTM | 3.56M | ViT-LSTM teacher |

## Key Experimental Results (Sphere Environment, 5m/s)

| Model | Training | Collisions | MAE | Jerk | Params | Latency |
|-------|----------|-----------|-----|------|--------|---------|
| Teacher (ViT+LSTM) | — | 2 | — | — | 3.56M | 9.0ms |
| **E** | BC | 3 | 0.220 | 0.023 | 2.19M | 7.1ms |
| **E** | **Distill** | **1** | 0.087 | 0.008 | 2.19M | 7.1ms |
| **E_s** | **BC** | **3** | **0.111** | **0.0063** | 2.19M | — |
| **H** | **BC (trees)** | **1** 🏆 | **0.145** | **0.0067** | **1.11M** | — |
| B+ | BC | 3 | — | — | 2.32M | — |
| **B+** | **Distill** | **1** | — | — | 2.32M | — |
| G_basic | BC | 3.7±1.2 | 1.269 | 0.567 | **0.49M** | **0.74ms** |
| D | BC | 2 | — | — | 2.84M | — |
| D | Distill | 5 | — | — | 2.84M | — |

**Key findings:**
- BC + distillation achieves best collision performance (E: 3→1, B+: 3→1)
- Stateful SSM (E_s) improves control quality 2-5× over stateless (MAE: 0.111 vs 0.220)
- Stateful distillation **fails** — teacher-student state modeling incompatibility causes 7.3× MAE degradation
- SSM temporal heads provide marginal collision benefit over simple MLP (G_basic achieves comparable collisions)
- Encoder quality dominates obstacle avoidance performance; temporal head choice is secondary

## Installation

```bash
cd ~/catkin_ws/src
git clone git@github.com:Liber1917/vitfly.git
cd vitfly
pip install -r requirements.txt
```

## Dataset Setup

Download `data.zip` (2.5GB, 580 trajectories) from [Datashare](https://upenn.app.box.com/v/ViT-quad-datashare) (pw: vitfly2025):

```bash
mkdir -p training/datasets/data_full training/logs
unzip <path/to/data.zip> -d training/datasets/data_full
```

## Training

```bash
cd training
# Train all Mamba branches
python train_mamba_optimized.py --data_dir <path>/data_full

# Distillation training
python train_mamba_optimized.py --branches E --distill --teacher <teacher_checkpoint>
```

## Simulation Testing

Test models in the Flightmare simulator:

```bash
# Quick test
bash test_mamba_branch.bash E DecisionMamba

# Full competition evaluation
bash launch_evaluation.bash 1 vision
```

See the **[Simulation Runbook](.claude/skills/vitfly/SKILL.md)** for detailed WSL2 setup, network configuration, and troubleshooting.

## Thesis

This repository supports the bachelor's thesis:

> **"基于神经网络的四旋翼飞行器端到端视觉避障"** (End-to-End Visual Obstacle Avoidance for Quadrotors Based on Neural Networks)
> Xing Jinwen, Northeastern University, 2026

The full thesis document is available in `paper/`.

## Repository Structure

```
vitfly/
├── training/                    # Training scripts & configs
│   ├── train_mamba_optimized.py # Main training entry point
│   └── dataloading.py           # Dataset loading
├── experiments/mamba_branches/  # Mamba branch implementations
│   ├── branch_A_vmamba_lstm/    # SS2D + LSTM
│   ├── branch_B_mambavision_ssm/ # MambaVision + SSM
│   ├── branch_Bplus_mambavision_mamba3/ # MambaVision + Mamba-3
│   ├── branch_C_cnn_mamba3/     # CNN + Mamba-3
│   ├── branch_D_sth_mamba/      # STH-Mamba
│   ├── branch_E_decisionmamba/  # DecisionMamba
│   ├── branch_E_stateful/       # Stateful DecisionMamba
│   ├── branch_H/                # CoarseSSM (stateful)
│   └── branch_G_cnn_baseline/   # CNN baselines (MLP, LSTM)
├── envtest/                     # Simulation test harness
├── models/                      # Pretrained weights
├── results/                     # Evaluation logs
└── paper/                       # Thesis documents & figures
```

## Citation

If you use this work, please cite both the original ViT-Fly paper and this repository:

```bibtex
@inproceedings{bhattacharya2025vision,
  title={Vision transformers for end-to-end vision-based quadrotor obstacle avoidance},
  author={Bhattacharya, Anish and Rao, Nishanth and Parikh, Dhruv and Kunapuli, Pratik and Wu, Yuwei and Tao, Yuezhan and Matni, Nikolai and Kumar, Vijay},
  booktitle={2025 IEEE International Conference on Robotics and Automation (ICRA)},
  year={2025}
}
```

## Acknowledgements

Original simulation code and the Flightmare/DodgeDrone integration are from the [ICRA 2022 DodgeDrone Competition](https://github.com/uzh-rpg/agile_flight). The baseline ViT-Fly framework is from Bhattacharya et al. (GRASP Lab, University of Pennsylvania).

---

## WSL2 Environment Setup Guide

This fork adds full **WSL2 (Windows Subsystem for Linux 2)** support for running the Flightmare simulation. The original codebase targets native Ubuntu 20.04; running it under WSL2 requires several workarounds documented below.

### Prerequisites

- Windows 10/11 with WSL2 enabled
- Ubuntu 20.04 installed in WSL2
- NVIDIA GPU with latest Windows drivers
- WSLg enabled (comes with modern WSL2, provides display via XWayland)

### Step 1: Enable WSL2 Mirrored Networking

Create or edit `%USERPROFILE%\.wslconfig` on the Windows side:

```ini
[wsl2]
networkingMode=mirrored
dnsTunneling=true
firewall=true
autoProxy=true
```

Then restart WSL from PowerShell: `wsl --shutdown`, and reopen your WSL terminal.

### Step 2: Fix Loopback Routing (Critical)

WSL2 mirrored mode routes `127.0.0.1` traffic through a virtual `loopback0` interface instead of the standard `lo` interface, breaking NetMQ's internal Signaler (TCP loopback pipe). **The simulation will not work without this fix.**

The `launch_evaluation.bash` script automatically applies the fix on every run. To apply it manually:

```bash
ip route get 127.0.0.1
# If output shows "dev loopback0":
ip route del 127.0.0.1 via 169.254.73.152 dev loopback0 proto kernel src 127.0.0.1 onlink table 127
ip route flush cache
# Verify (should show "dev lo"):
ip route get 127.0.0.1
```

### Step 3: Install ROS Noetic

```bash
sudo apt install -y ros-noetic-desktop-full
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
```

### Step 4: Python Environment (Miniconda)

```bash
conda create -n ros_py38 python=3.8 -y
conda activate ros_py38
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install numpy pandas pyyaml opencv-python scipy
```

### Step 5: Fix cv_bridge Library Conflict

Preload the system library to resolve ROS conda conflicts:

```bash
export LD_PRELOAD=/lib/x86_64-linux-gnu/libffi.so.7
```

This is already included in `launch_evaluation.bash`.

### Step 6: OpenGL Configuration

```bash
export MESA_GL_VERSION_OVERRIDE=4.5
export MESA_GLSL_VERSION_OVERRIDE=450
```

Do **NOT** install `libnvidia-gl-*` packages in WSL2 — they conflict with XWayland and cause Unity crashes.

### Step 7: Run the Simulation

```bash
# Apply IP alias (once per session):
ip addr add 192.168.233.250/32 dev lo
# Launch:
bash launch_evaluation.bash 1 vision
```

Expected output:
1. Unity window appears (via WSLg)
2. `[UnityBridge] Flightmare Unity is connected.`
3. `[Pilot] Z-position smaller than takeoff height, taking off!`
4. `[RUN_COMPETITION] Model loaded`
5. `[RUN_COMPETITION] compute_command_vision_based took ~0.008 seconds`

### Troubleshooting

**Unity window doesn't appear**: Verify `echo $DISPLAY` returns `:0`. If not, `export DISPLAY=:0`.

**`[UnityBridge] Unity Connection time out!`**: The loopback route fix is not applied. Run `ip route get 127.0.0.1` — must show "dev lo".

**Segfault from visionsim_node**: Unity ZMQ connection failed. Fix the loopback route first.

**ROS fails to bind**: The IP alias `192.168.233.250` has been lost. Re-apply:
```bash
ip addr add 192.168.233.250/32 dev lo
```

**ZMQ ports stuck after crash**: No Linux tool can clear them. Run in Windows PowerShell:
```powershell
wsl --shutdown
```
Then reopen WSL2 and re-apply the loopback alias.
