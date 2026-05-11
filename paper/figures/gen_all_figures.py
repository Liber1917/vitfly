#!/usr/bin/env python3
"""Generate radar chart, scatter plot, and heatmap for thesis figures."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from math import pi
import os

OUTDIR = os.path.dirname(os.path.abspath(__file__))

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.labelsize": 10, "legend.fontsize": 8, "legend.frameon": False,
    "figure.dpi": 300, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False,
})

# ── Color palette (Okabe-Ito colorblind-safe) ──
C_OURS = "#E76F51"     # coral — our method
C_TEACHER = "#264653"  # dark teal
C_BP = "#2A9D8F"       # teal
C_C = "#E9C46A"        # gold
C_A = "#8C8C8C"        # gray
C_G_BASIC = "#B0BEC5"  # light gray
C_G_LSTM = "#78909C"   # blue-gray
C_OTHER = "#B0BEC5"

# Use short English tags for matplotlib (Chinese glyphs missing on Linux)
MODEL_TAGS = {
    'E.dist': 'E.dist', 'B+.dist': 'B+.dist', 'Teacher': 'Teacher',
    'C': 'C', 'A': 'A', 'G_basic': 'G_basic', 'G_lstm': 'G_lstm',
}
MODEL_COLORS = {
    'E.dist': C_OURS, 'B+.dist': C_BP, 'Teacher': C_TEACHER,
    'C': C_C, 'A': C_A, 'G_basic': C_G_BASIC, 'G_lstm': C_G_LSTM,
}

# ═══════════════════════════════════════════════════════════════
# FIGURE 1: RADAR CHART
# ═══════════════════════════════════════════════════════════════
def make_radar():
    models = ['E.dist', 'B+.dist', 'Teacher', 'C', 'A', 'G_basic', 'G_lstm']
    # Raw data (lower=better for all)
    raw = {
        'Crashes':   [1, 1, 2, 3, 3, 4, 4],
        'MAE':       [0.220, 0.286, 0.346, 0.357, 0.532, 1.255, 1.271],
        'Jerk':      [0.023, 0.056, 0.040, 0.057, 0.104, 0.560, 0.266],
        'Latency_ms':[7.1, 9.8, 9.0, 8.5, 24.3, 0.74, 1.00],
        'MAE_y':     [0.060, 0.111, 0.307, 0.160, 0.227, 2.041, 1.983],
    }
    labels = list(raw.keys())
    n_metrics = len(labels)
    angles = [n / n_metrics * 2 * pi for n in range(n_metrics)]
    angles += angles[:1]

    # Normalize: best=1 (outer), worst=0 (center)
    norm = {}
    for metric in labels:
        vals = raw[metric]
        vmin, vmax = min(vals), max(vals)
        if vmax == vmin:
            norm[metric] = [1.0] * len(vals)
        else:
            norm[metric] = [(vmax - v) / (vmax - vmin) for v in vals]

    fig, ax = plt.subplots(figsize=(5.5, 5.5), subplot_kw=dict(polar=True))

    for i, model in enumerate(models):
        color = MODEL_COLORS.get(model, C_OTHER)
        values = [norm[l][i] for l in labels]
        values += values[:1]
        ax.plot(angles, values, 'o-', linewidth=1.5, label=model,
                color=color, markersize=4)
        ax.fill(angles, values, alpha=0.05, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1.15)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['0.25', '0.5', '0.75', 'Best'], fontsize=7)
    ax.set_title('Multi-Metric Model Comparison\n(all metrics: lower is better)', pad=20, fontsize=11)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.1), fontsize=7.5)

    fig.savefig(os.path.join(OUTDIR, 'fig_radar.pdf'))
    fig.savefig(os.path.join(OUTDIR, 'fig_radar.png'), dpi=300)
    plt.close(fig)
    print("✓ Radar chart saved")

# ═══════════════════════════════════════════════════════════════
# FIGURE 2: MULTI-METRIC SCATTER (PARETO FRONTIER)
# ═══════════════════════════════════════════════════════════════
def make_pareto():
    models = ['E.dist', 'B+.dist', 'B.dist', 'D.BC', 'D.dist', 'A.BC',
              'A.dist', 'C.BC', 'C.dist', 'B+.BC', 'E.BC', 'G_basic', 'G_lstm']
    data = {
        'E.dist':   (1, 7.1, 2.19),
        'B+.dist':  (1, 9.8, 2.55),
        'B.dist':   (2, 10.2, 2.61),
        'D.BC':     (2, 11.5, 2.60),
        'D.dist':   (2, 11.5, 2.60),
        'A.BC':     (3, 24.3, 0.97),
        'A.dist':   (3, 24.3, 0.97),
        'C.BC':     (3, 8.5, 2.41),
        'C.dist':   (3, 8.5, 2.41),
        'B+.BC':    (3, 9.8, 2.55),
        'E.BC':     (3, 7.1, 2.19),
        'G_basic':  (4, 0.74, 0.49),
        'G_lstm':   (4, 1.0, 0.80),
    }
    t_crash, t_lat, t_param = 2, 9.0, 3.56

    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    # Mark regions
    ax.axhspan(-0.5, 0.5, xmin=0, xmax=0.15, alpha=0.06, color='green')
    ax.annotate('Ideal', xy=(2, 0.5), fontsize=8, color='green', alpha=0.6)

    # Plot all models
    for name, (crashes, lat, params) in data.items():
        is_best = '.dist' in name and crashes <= 1
        color = C_OURS if is_best else \
                C_G_BASIC if 'G_' in name else C_OTHER
        size = 40 + params * 30
        edge_c = 'black' if is_best else 'none'
        lw = 1.0 if is_best else 0.3
        ax.scatter(lat, crashes, s=size, c=color, marker='o',
                   edgecolors=edge_c, linewidth=lw, alpha=0.8, zorder=5)

        # Label
        offset_x, offset_y = 0.3, 0.15
        if name == 'G_basic':
            offset_y = -0.4
        elif name == 'G_lstm':
            offset_y = 0.4
        elif name == 'A BC':
            offset_x = -1.0

        ax.annotate(name, (lat, crashes), (lat + offset_x, crashes + offset_y),
                    fontsize=6.5, ha='left', va='bottom', alpha=0.8)

    # Teacher
    ax.scatter(t_lat, t_crash, s=200, c=C_TEACHER, marker='s',
               edgecolors='black', linewidth=1.0, zorder=6, alpha=0.9,
               label='Teacher ViT+LSTM')
    ax.annotate('Teacher', (t_lat, t_crash), (t_lat + 0.2, t_crash + 0.25),
                fontsize=7, ha='left', va='bottom', fontweight='bold')

    # Pareto frontier (best models only)
    frontier_pts = [(0.74, 4), (7.1, 1), (9.8, 1)]  # G_basic, E_distill, B+_distill
    frontier_pts.sort()
    xs, ys = zip(*frontier_pts)
    ax.plot(xs, ys, '--', color='#2A9D8F', linewidth=1.2, alpha=0.5, zorder=1)
    ax.annotate('Pareto frontier', (2, 3), fontsize=7.5, color='#2A9D8F',
                fontstyle='italic', alpha=0.6)

    ax.set_xlabel('Inference Latency (ms)')
    ax.set_ylabel('Collisions (60m course)')
    ax.set_title('Performance Pareto Frontier: Latency vs Collisions\n(marker size ~ parameters)', fontsize=11)

    ax.set_xlim(-1, 28)
    ax.set_ylim(0, 5.5)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(1))

    # Legend proxies
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor=C_OURS,
               markersize=8, label='Best distill (1 crash)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=C_OTHER,
               markersize=8, label='Other models'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor=C_TEACHER,
               markersize=8, label='Teacher'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=C_G_BASIC,
               markersize=8, label='G baselines'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=7)

    fig.savefig(os.path.join(OUTDIR, 'fig_pareto.pdf'))
    fig.savefig(os.path.join(OUTDIR, 'fig_pareto.png'), dpi=300)
    plt.close(fig)
    print("✓ Pareto scatter saved")


# ═══════════════════════════════════════════════════════════════
# FIGURE 3: HEATMAP — Model × Condition Ablation Effects
# ═══════════════════════════════════════════════════════════════
def make_heatmap():
    import matplotlib.colors as mcolors

    # Data: (rows x cols) collision counts
    models = ['B+.dist', 'B.dist', 'C.dist', 'D.dist', 'E.dist']
    conditions = ['Sphere\nno aug', 'Sphere\n+aug', 'Trees\nno aug', 'Trees\n+aug']

    data = np.array([
        [3, 1, 0, 0],   # B+
        [np.nan, 3, np.nan, 0],  # B (DNF = NaN)
        [3, 5, 0, 2],   # C
        [2, 5, 0, 1],   # D
        [3, 4, 1, 2],   # E
    ])

    # Improvement: augmentation effect (with_aug - without_aug)
    # negative = improvement, positive = degradation
    delta = data[:, 1] - data[:, 0]  # sphere with_aug - without_aug
    delta_trees = data[:, 3] - data[:, 2]  # trees

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.8),
                             gridspec_kw={'width_ratios': [2.2, 1.2, 1.2]})

    # ─── Panel A: Main heatmap ───
    ax = axes[0]
    norm = mcolors.Normalize(vmin=0, vmax=5)
    cmap = plt.cm.YlOrRd.copy()
    cmap.set_bad('lightgray')

    # Mask NaN
    mask = np.isnan(data)
    im = ax.imshow(data, cmap=cmap, norm=norm, aspect='auto')

    # Annotate cells
    for i in range(len(models)):
        for j in range(len(conditions)):
            val = data[i, j]
            if np.isnan(val):
                text = 'DNF'
                color = '#999'
            else:
                text = f'{int(val)}'
                color = 'white' if val > 2.5 else 'black'
            ax.text(j, i, text, ha='center', va='center', fontsize=11,
                    fontweight='bold', color=color)

    ax.set_xticks(range(len(conditions)))
    ax.set_xticklabels(conditions, fontsize=7.5)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels(models, fontsize=8)
    ax.set_title('Collisions by Model & Condition', fontsize=9)

    cbar = fig.colorbar(im, ax=ax, shrink=0.7, aspect=15)
    cbar.ax.tick_params(labelsize=7)

    # ─── Panel B: Sphere delta ───
    ax = axes[1]
    colors_delta = ['#D55E00' if d > 0 else '#009E73' for d in delta]
    colors_delta = ['lightgray' if np.isnan(d) else c for d, c in zip(delta, colors_delta)]
    bars = ax.barh(range(len(models)), delta, color=colors_delta, height=0.5,
                   edgecolor='white', linewidth=0.5)
    ax.axvline(0, color='black', linewidth=0.5)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([''] * len(models))
    ax.set_xticks([-3, 0, 3])
    ax.set_xlabel('Δ collisions', fontsize=7)
    ax.set_title('Sphere\nAug effect', fontsize=8)
    ax.tick_params(labelsize=7)

    for i, d in enumerate(delta):
        if not np.isnan(d):
            label = f'{int(d):+d}'
            ax.text(d + (0.2 if d >= 0 else -0.6), i, label,
                    va='center', fontsize=8, fontweight='bold',
                    color='#D55E00' if d > 0 else '#009E73')

    # ─── Panel C: Trees delta ───
    ax = axes[2]
    colors_delta_t = []
    for d in delta_trees:
        if np.isnan(d):
            colors_delta_t.append('lightgray')
        elif d > 0:
            colors_delta_t.append('#D55E00')
        elif d < 0:
            colors_delta_t.append('#009E73')
        else:
            colors_delta_t.append('#999')
    bars = ax.barh(range(len(models)), delta_trees, color=colors_delta_t, height=0.5,
                   edgecolor='white', linewidth=0.5)
    ax.axvline(0, color='black', linewidth=0.5)
    ax.set_yticks(range(len(models)))
    ax.set_yticklabels([''] * len(models))
    ax.set_xticks([-3, 0, 3])
    ax.set_xlabel('D collisions', fontsize=7)
    ax.set_title('Trees\nAug effect', fontsize=8)
    ax.tick_params(labelsize=7)

    for i, d in enumerate(delta_trees):
        if not np.isnan(d):
            label = f'{int(d):+d}'
            ax.text(d + (0.2 if d >= 0 else -0.6), i, label,
                    va='center', fontsize=8, fontweight='bold',
                    color='#D55E00' if d > 0 else '#009E73')

    fig.suptitle('Data Augmentation: Architecture-Dependent Effect on Collisions',
                 fontsize=11, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUTDIR, 'fig_ablation_heatmap.pdf'))
    fig.savefig(os.path.join(OUTDIR, 'fig_ablation_heatmap.png'), dpi=300)
    plt.close(fig)
    print("✓ Ablation heatmap saved")


# ═══════════════════════════════════════════════════════════════
# RUN ALL
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    make_radar()
    make_pareto()
    make_heatmap()
    print("\nAll figures generated in", OUTDIR)
