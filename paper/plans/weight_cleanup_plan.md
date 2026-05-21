# .pth 权重清理计划

## 原则
- 仿真管线需要 `best_model.pth` 和 `distill_best_model.pth` 来跑测试
- 训练中间断点 `checkpoint_epoch_*.pth` 仿真从不使用
- 已证明失败的实验分支可以不保留（必要时可重训）

## 保留清单（55 个）

### 主要基线（14 个）
```
branch_A/best_model.pth              branch_A/distill_best_model.pth
branch_B/best_model.pth              branch_B/distill_best_model.pth     branch_B/aug_best_model.pth
branch_Bplus/best_model.pth          branch_Bplus/distill_best_model.pth  branch_Bplus/aug_best_model.pth
branch_C/best_model.pth              branch_C/distill_best_model.pth
branch_D/best_model.pth              branch_D/distill_best_model.pth
branch_E/best_model.pth              branch_E/distill_best_model.pth
```

### E 消融变体（6 个）
```
branch_E/seq1_bcinit_distill_best_model.pth    branch_E/seq16_distill_best_model.pth
branch_E/seq4_distill_best_model.pth           branch_E/bornagain_Bplus2E_best_model.pth
branch_E/seq8_distill_best_model.pth           branch_E/bornagain_gamma2_best_model.pth
```
注：bornagain 虽然没用但只有 best_model，保留以备审稿人质疑。

### Teacher（1 个）
```
models/DroneMamba_model.pth
```

### 有状态分支（12 个）
```
branch_H/best_model.pth              branch_Hs/best_model.pth
branch_E_s/branch_E_s/best_model.pth
branch_Dst/best_model.pth            branch_Ds/branch_Ds/best_model.pth
```
注：E_s 和 Ds 的 checkpoint 可删，best_model 保留。

### G 系列对照（12 个）
```
branch_G/best_model.pth
branch_G_seed43/branch_G/best_model.pth
branch_G_seed44/branch_G/best_model.pth
branch_G_seed45/branch_G/best_model.pth
branch_G_lstm/best_model.pth
```
注：每个种子只保留 best_model.pth，4×2=8 个 checkpoint_epoch 全删。

### Essm 系列（3 个）
```
essm_bc_s42/branch_Essm/best_model.pth
essm_distill_a03/branch_Essm/distill_best_model.pth
essm_distill_s42/branch_Essm/distill_best_model.pth
```
注：essm_distill_bcinit 蒸馏失败变体，不保留。

### Fv5（1 个）
```
branch_Fv5/best_model.pth
```

### 多种子蒸馏（6 个）
```
branch_Bplus_distill_seed42/branch_Bplus/distill_best_model.pth
branch_E_distill_seed43/branch_E/distill_best_model.pth
branch_E_distill_seed44/branch_E/distill_best_model.pth
branch_E_distill_seed45/branch_E/distill_best_model.pth
```

## 删除清单（115 个）

### 训练中间断点（~90 个）
所有 `checkpoint_epoch_25/50/75/100.pth` 全部删除。
涉及：branch_A/B/C/D/E/E_s/F/Fv5/G/G_lstm/G_seed43/44/45/Dst/Ds/H + essm_bc/essm_distill/seq4_BC/seq8_BC

### 已废弃分支（~15 个）
```
branch_F/best_model.pth              （旧 F 分支，已被 Fv5 取代）
branch_F/bc_aug_best_model.pth       （同上）
seq16_distill_E/branch_E/best_model.pth  （重复，branch_E 已有）
seq1_bcinit_distill_E/branch_E/best_model.pth  （重复）
seq4_BC_E/branch_E/best_model.pth   （重复，seq4 消融不需要 best_model）
seq8_BC_E/branch_E/best_model.pth   （同上）
```

### 中间状态文件（~6 个）
```
seq16_distill_E/seq16_bc_init.pth    （中间文件）
seq4_distill_E/branch_E/best_model.pth  （重复）
seq8_distill_E/branch_E/best_model.pth  （重复）
mambafusion_bc_s42.pth              （废弃实验）
mambafusion_distill_s42.pth         （废弃实验）
essm_distill_bcinit/branch_Essm/best_model.pth  （失败实验）
```

### 损失权重消融中间文件（~6 个）
```
grid_E_a0.5_b0.5/branch_E/distill_best_model.pth  + checkpoint
grid_E_a0.5_b1.0/branch_E/distill_best_model.pth  + checkpoint
grid_E_a1.0_b0.5/branch_E/distill_best_model.pth  + checkpoint
grid_E_a1.0_b1.0/branch_E/distill_best_model.pth  + checkpoint
```
注：若需要保留 α=β=1.0 的结果，它和 branch_E/distill_best_model.pth 是同一个。

## 清理后仓库统计

| 指标 | 清理前 | 清理后 |
|------|--------|--------|
| .pth 文件 | 170 | ~55 |
| 仓库大小估算 | ~850MB | ~275MB |
| 仿真端可用性 | ✅ | ✅ |

## 提交策略

```bash
# 1. 从 git 跟踪中删除中间文件
git rm experiments/mamba_branches/optimized_training/*/checkpoint_epoch_*.pth
git rm experiments/mamba_branches/optimized_training/grid_E_*/*/checkpoint_epoch_*.pth
git rm experiments/mamba_branches/optimized_training/seq*_*/branch_*/checkpoint_epoch_*.pth
# ... 按需补充

# 2. 提交
git commit -m 'cleanup: remove 100+ checkpoint pth files (sim only needs best_model)'

# 3. 可选：用 git-filter-repo 从历史中彻底删除大文件
# （需要仿真端先推完所有本地修改，再协调时间窗口）
```
