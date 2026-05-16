#!/usr/bin/env python3
"""Generate all thesis figures — grayscale, school-template compliant."""

import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np, os

OUTPUT = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(f'{OUTPUT}/arch', exist_ok=True)

# ─── Grayscale template style ───
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'SimSun'],
    'font.size': 10, 'axes.titlesize': 12, 'axes.labelsize': 10,
    'xtick.labelsize': 9, 'ytick.labelsize': 9, 'legend.fontsize': 8,
    'figure.dpi': 300, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.alpha': 0.2, 'grid.linestyle': '-',
})
GRAYS = ['0.15', '0.40', '0.55', '0.70', '0.85', '0.92']
HATCHES = ['///', '\\\\', 'xx', '..', '++', '||']
FIG_W = (6.75, 3.2)

# ====================================================================
# FIGURE 3: Inference Latency
# ====================================================================
def fig3_latency():
    models = ['A','B','B+','C','D','E','Teacher','G_basic','G_lstm']
    lat = [24.3,10.2,9.8,8.5,11.5,7.1,9.0,0.74,1.00]
    par = [0.97,2.61,2.55,2.41,2.60,2.19,3.56,0.49,0.80]

    fig,(ax1,ax2) = plt.subplots(1,2,figsize=FIG_W)

    # Bar chart — grayscale+hatch
    x = np.arange(len(models))
    bars = ax1.bar(x, lat, color='white', edgecolor='black', linewidth=0.8)
    for i,b in enumerate(bars):
        b.set_hatch(HATCHES[i%len(HATCHES)])
    ax1.set_xticks(x); ax1.set_xticklabels(models, fontsize=7, rotation=30, ha='right')
    ax1.set_ylabel('Inference Latency (ms)')
    ax1.axhline(y=16.7, color='black', linestyle='--', linewidth=0.6, label='60Hz limit')
    ax1.legend(fontsize=7)

    # Scatter — marker shapes, no labels, use shared legend
    markers = ['o','s','^','D','v','p','*','h','<']
    scatters = []
    for i,m in enumerate(models):
        sz = 60 if m=='E' else 35
        s = ax2.scatter(par[i], lat[i], s=sz, c='white', edgecolors='black',
                       linewidths=0.8, marker=markers[i], zorder=5)
        scatters.append(s)
    ax2.set_xlabel('Parameters (M)'); ax2.set_ylabel('Inference Latency (ms)')
    ax2.set_xlim(0,4.2)
    ax2.legend(scatters, models, loc='upper left', fontsize=6.5, ncol=2,
               framealpha=0.85, markerscale=0.7)

    plt.tight_layout(); plt.savefig(f'{OUTPUT}/figure3.pdf'); plt.close()
    print('figure3.pdf done')

# ====================================================================
# FIGURE 2: Environment comparison
# ====================================================================
def fig2_envs():
    mods = ['Teacher','B+ Distill','E Distill','G_basic','G_lstm']
    s5 = [2,1,1,2.8,4]; s7 = [5,3,1,6,6]
    t5 = [0,0,1,2,4]; t7 = [0,1,2,3,6]

    fig,(ax1,ax2) = plt.subplots(1,2,figsize=FIG_W,sharey=True)
    x = np.arange(len(mods)); w = 0.3

    for ax,tit,d5,d7 in [(ax1,'Sphere',s5,s7),(ax2,'Trees',t5,t7)]:
        b5 = ax.bar(x-w/2, d5, w, color='white', edgecolor='black', linewidth=0.8, hatch='///', label='5m/s')
        b7 = ax.bar(x+w/2, d7, w, color='0.6', edgecolor='black', linewidth=0.8, hatch='\\\\', label='7m/s')
        ax.set_title(tit, fontsize=10)
        ax.set_xticks(x); ax.set_xticklabels(mods, fontsize=7, rotation=15)
        ax.set_ylabel('Crashes'); ax.legend(fontsize=7)

    plt.tight_layout(); plt.savefig(f'{OUTPUT}/figure2.pdf'); plt.close()
    print('figure2.pdf done')

# ====================================================================
# FIGURE 1: Distillation framework + main results
# ====================================================================
def fig1_overview():
    mods = ['A','B','B+','C','D','E']
    bc = [3,0,3,3,2,3]; dis = [3,2,1,3,2,1]
    x = np.arange(len(mods)); w = 0.3

    fig,(ax1,ax2) = plt.subplots(1,2,figsize=FIG_W,
                                 gridspec_kw={'width_ratios':[1,1.3]})
    ax1.axis('off')
    ax1.set_xlim(0, 1.0); ax1.set_ylim(0, 1.0)

    # Teacher box (top)
    ax1.add_patch(mpatches.FancyBboxPatch((0.15,0.80), 0.7, 0.10, boxstyle='round,pad=0.02',
                  fc='0.85', ec='black', lw=0.8))
    ax1.text(0.5, 0.85, 'Teacher: ViT + LSTM (3.56M)', ha='center', va='center',
            fontsize=8, fontweight='bold')

    # Three loss channels (middle row)
    loss_names = [r'$L_{feat}$', r'$L_{distill}$', r'$L_{GT}$']
    loss_desc = ['Feature\nAlignment', 'Output\nDistillation', 'Ground Truth\nSupervision']
    loss_colors = ['0.75', '0.65', '0.55']
    loss_xs = [0.15, 0.38, 0.61]
    for i in range(3):
        lx = loss_xs[i]; ly = 0.57
        ax1.add_patch(mpatches.FancyBboxPatch((lx,ly), 0.20, 0.16, boxstyle='round,pad=0.02',
                      fc=loss_colors[i], ec='black', lw=0.6))
        ax1.text(lx+0.10, ly+0.12, loss_names[i], ha='center', va='center',
                fontsize=8, fontweight='bold')
        ax1.text(lx+0.10, ly+0.04, loss_desc[i], ha='center', va='center',
                fontsize=5.5, color='black')
        # Down arrow from teacher to each loss
        ax1.annotate('', xy=(lx+0.10, ly+0.16), xytext=(lx+0.10, 0.79),
                    arrowprops=dict(arrowstyle='->', lw=0.5, color='0.4'))

    # Student box (bottom)
    ax1.add_patch(mpatches.FancyBboxPatch((0.05,0.22), 0.9, 0.28, boxstyle='round,pad=0.02',
                  fc='0.3', ec='black', lw=0.8))
    ax1.text(0.5, 0.46, 'Mamba Students', ha='center', va='center',
            fontsize=8, fontweight='bold', color='white')
    # 6 branch labels inside student box
    branches = ['A: VMamba+LSTM', 'B: MambaVision+SSM', 'B+: MambaVision+Mamba3',
                'C: CNN+Mamba3', 'D: STH-Mamba', 'E: DecisionMamba']
    for i,b in enumerate(branches):
        col = i % 2; row = i // 2
        ax1.text(0.15 + col*0.42, 0.39 - row*0.075, b, fontsize=5.5, color='white',
                ha='center', va='center')

    # Arrows from each loss to student
    for i in range(3):
        lx = loss_xs[i]
        ax1.annotate('', xy=(lx+0.10, 0.50), xytext=(lx+0.10, 0.555),
                    arrowprops=dict(arrowstyle='->', lw=0.5, color='0.4'))

    ax1.set_title('(A) Cross-Architecture Distillation Framework', fontsize=9)

    # Right panel: Bar chart
    b1 = ax2.bar(x-w/2, bc, w, color='white', edgecolor='black', linewidth=0.8, hatch='///', label='BC')
    b2 = ax2.bar(x+w/2, dis, w, color='0.5', edgecolor='black', linewidth=0.8, hatch='\\\\', label='Distill')
    ax2.axhline(y=2, color='black', linestyle=':', linewidth=0.7, label='Teacher')
    ax2.set_xticks(x); ax2.set_xticklabels(mods)
    ax2.set_ylabel('Crashes (60m @5m/s)'); ax2.set_title('(B) Main Results', fontsize=9)
    ax2.legend(fontsize=7)
    ax2.text(1-w/2,0.2,'DNF',ha='center',fontsize=6,color='red')

    plt.tight_layout(); plt.savefig(f'{OUTPUT}/figure1.pdf'); plt.close()
    print('figure1.pdf done')

# ====================================================================
# Architecture diagrams — grayscale drawio-compatible style
# ====================================================================
ARCHS = {
 'A':[['Conv3×3\n32ch','Conv3×3\n64ch','Conv3×3\n128ch','Conv3×3\n256ch\n+SS2D×4'],'0.7','LSTM\nh=128×3','0.85'],
 'B':[['Stem7×7\ns4','DWConv+\nMLP×2','DWConv+\nMLP×2','DWConv+\nMLP×2'],'0.75','SSM\nd=16×2','0.85'],
 'B+':[['Stem7×7\ns4','DWConv+\nMLP×2','DWConv+\nMLP×2','DWConv+\nMLP×2'],'0.75','Mamba-3\nd=32','0.85'],
 'C':[['Conv3×3\n32ch,s2','Conv3×3\n64ch,s2','Conv3×3\n128ch,s2','Conv3×3\n256ch\nGAP'],'0.8','Mamba-3\nd=32','0.85'],
 'D':[['Conv3×3\n32ch','Conv3×3\n64ch','Conv3×3\n128ch','ST-Mamba\nscan'],'0.75','Mamba-2\nSSD d=128','0.85'],
 'E':[['Conv3×3\n32ch,s2','Conv3×3\n64ch,s2','Conv3×3\n128ch,s2','Conv3×3\n256ch\nAP'],'0.7','SSM\nd=16×2','0.85'],
}

def draw_arch(branch):
    layers, ec, tname, tc = ARCHS[branch]
    fig,ax = plt.subplots(1,1,figsize=(5,2.8)); ax.axis('off')

    # Input
    ax.add_patch(mpatches.FancyBboxPatch((0.02,0.3),0.1,0.4,boxstyle='round',fc='0.9',ec='black'))
    ax.text(0.07,0.5,'Depth\n60×90',ha='center',va='center',fontsize=5.5)

    # Encoder stack
    x0, y0, bw, bh = 0.16, 0.12, 0.2, 0.14
    for i,ly in enumerate(layers):
        y = y0 + (3-i)*bh
        fc = f'{0.3+i*0.12}'
        ax.add_patch(mpatches.FancyBboxPatch((x0,y),bw,bh-0.01,boxstyle='round',fc=fc,ec='black'))
        lines = ly.split('\n')
        for li,l in enumerate(lines):
            sz = 5 if len(lines)>1 else 5.5
            ax.text(x0+bw/2, y+bh/2-0.02+(len(lines)-1)*0.025-li*0.05, l,
                   ha='center', va='center', fontsize=sz, color='white')

    # Concat
    ax.add_patch(mpatches.FancyBboxPatch((0.42,0.33),0.08,0.34,boxstyle='round',fc='0.88',ec='black'))
    ax.text(0.46,0.5,'Cat\n+vel\n+quat',ha='center',va='center',fontsize=4.5)

    # Temporal
    x1 = 0.55
    for i in range(2):
        ax.add_patch(mpatches.FancyBboxPatch((x1,0.25+i*0.2),0.18,0.18,boxstyle='round',fc='0.85',ec='black'))
    ax.text(x1+0.09,0.5,tname,ha='center',va='center',fontsize=5.5,fontweight='bold')

    # Output
    ax.add_patch(mpatches.FancyBboxPatch((0.78,0.33),0.18,0.34,boxstyle='round',fc='0.9',ec='black'))
    ax.text(0.87,0.5,'Velocity\n(vx,vy,vz)',ha='center',va='center',fontsize=5)

    # Arrows
    for a,b in [(0.12,0.16),(0.36,0.42),(0.50,0.55),(0.73,0.78)]:
        ax.annotate('',xy=(b,0.5),xytext=(a,0.5),arrowprops=dict(arrowstyle='->',color='black',lw=0.8))
    ax.set_xlim(0,1); ax.set_ylim(0,1)
    ax.set_title(f'Branch {branch}',fontsize=10,fontweight='bold')

    plt.tight_layout(); plt.savefig(f'{OUTPUT}/arch/arch_branch_{branch}.pdf'); plt.close()
    print(f'arch_branch_{branch}.pdf done')

# ====================================================================
# Main
# ====================================================================
if __name__ == '__main__':
    fig3_latency()
    fig2_envs()
    fig1_overview()
    for b in ['A','B','B+','C','D','E']: draw_arch(b)
    print('\nAll figures generated in grayscale!')
