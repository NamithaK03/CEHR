"""Regenerate all data figures at their printed size (single IEEE column, 3.45 in wide).
Inputs: robustness_6seed_runs.csv, matched_fixed_target.csv, ablation_decomposition.csv.
Outputs: fig_paired_overlap.pdf, fig_seed_robustness.pdf, fig_duration_heatmap.pdf, fig_stage_ablation.pdf
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

p = Path(__file__).parent
W = 3.45  # printed width in inches (matches \columnwidth)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7.5, 'axes.labelsize': 7.5,
                     'xtick.labelsize': 7, 'ytick.labelsize': 7, 'legend.fontsize': 6.5,
                     'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6})

runs = pd.read_csv(p / 'robustness_6seed_runs.csv')

# 1. Paired scatter (36 runs)
fig, ax = plt.subplots(figsize=(W, 1.95))
colors = plt.cm.tab10(np.linspace(0, 1, 6))
for i, (v, g) in enumerate(runs.groupby('video', sort=True)):
    ax.scatter(g.fgs_overlap, g.refined_overlap, label=v, s=14, alpha=.9, color=colors[i],
               edgecolors='white', linewidths=.2)
mx = max(runs.fgs_overlap.max(), runs.refined_overlap.max()) * 1.04
ax.plot([0, mx], [0, mx], ls='--', lw=0.8, color='.35', label='Equal overlap')
ax.set_xlim(-mx * .025, mx); ax.set_ylim(-mx * .025, mx)
ax.set_xlabel('FGS overlap (px$^2$)'); ax.set_ylabel('CEHR overlap (px$^2$)')
ax.grid(alpha=.15, lw=.4)
ax.legend(ncol=4, loc='upper left', frameon=False, handletextpad=.3, columnspacing=.8)
fig.tight_layout(pad=.3)
fig.savefig(p / 'fig_paired_overlap.pdf', bbox_inches='tight'); plt.close(fig)

# 2. Per-video six-seed robustness (bars with min-max range)
g = runs.groupby('video', sort=True).agg(fgs=('fgs_overlap', 'first'), mean=('refined_overlap', 'mean'),
                                         lo=('refined_overlap', 'min'), hi=('refined_overlap', 'max'))
x = np.arange(len(g)); w = 0.38
fig, ax = plt.subplots(figsize=(W, 1.8))
ax.bar(x - w / 2, g.fgs, w, color='#9aa7b8', edgecolor='black', linewidth=0.3, label='FGS [20]')
ax.bar(x + w / 2, g['mean'], w, color='#2a5f9e', edgecolor='black', linewidth=0.3, label='CEHR seed mean')
ax.errorbar(x + w / 2, g['mean'], yerr=[g['mean'] - g.lo, g.hi - g['mean']], fmt='none',
            ecolor='black', capsize=1.8, lw=0.6)
ax.set_xticks(x, list(g.index)); ax.set_ylabel('False-overlap area (px$^2$)')
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{v:,.0f}'))
ax.legend(frameon=False, loc='upper left'); ax.grid(axis='y', alpha=.15, lw=.4)
fig.tight_layout(pad=.3)
fig.savefig(p / 'fig_seed_robustness.pdf', bbox_inches='tight'); plt.close(fig)

# 3. Fixed-target difference heatmap
b = pd.read_csv(p / 'matched_fixed_target.csv')
b['difference'] = b.fgs_repair_overlap - b.pceo_hierarchical_overlap
vids = sorted(b.video.unique()); fracs = [.25, .35, .5]
mat = np.array([[b.loc[(b.video == v) & np.isclose(b.fraction, f), 'difference'].iloc[0] for f in fracs] for v in vids])
fig, ax = plt.subplots(figsize=(W, 1.95))
im = ax.imshow(mat, cmap='Blues', aspect='auto', vmin=0)
ax.set_xticks(range(3), ['25%', '35%', '50%']); ax.set_yticks(range(6), vids)
ax.set_xlabel('Target duration / source temporal span'); ax.set_ylabel('Video')
for i in range(6):
    for j in range(3):
        val = mat[i, j]
        ax.text(j, i, f'{val / 1000:.1f}k', ha='center', va='center', fontsize=6.5,
                color='white' if val > mat.max() * .5 else '#222222')
cbar = fig.colorbar(im, ax=ax, fraction=.04, pad=.03)
cbar.set_label('FGS $-$ CEHR (px$^2$)', fontsize=7); cbar.ax.tick_params(labelsize=6.5)
fig.tight_layout(pad=.3)
fig.savefig(p / 'fig_duration_heatmap.pdf', bbox_inches='tight'); plt.close(fig)

# 4. Stage decomposition (12 development runs, pooled)
ab = pd.read_csv(p / 'ablation_decomposition.csv')
stages = ['Cube-derived\nplacement', 'Exact-length\ninitialization', 'Single-group\nrefinement']
vals = [ab.original_cube_pceo.sum(), ab.after_exact_initialization.sum(), ab.after_collision_refinement.sum()]
fig, ax = plt.subplots(figsize=(W, 1.55))
bars = ax.bar(range(3), [v / 1e6 for v in vals], 0.55, color=['#9aa7b8', '#5b84b1', '#2a5f9e'],
              edgecolor='black', linewidth=0.3)
for r, v in zip(bars, vals):
    ax.text(r.get_x() + r.get_width() / 2, v / 1e6 + 0.04, f'{v:,.0f}', ha='center', va='bottom', fontsize=6.5)
ax.set_xticks(range(3), stages); ax.set_ylabel('Pooled false-overlap area (million px$^2$)')
ax.set_ylim(0, max(vals) / 1e6 * 1.18); ax.grid(axis='y', alpha=.15, lw=.4)
fig.tight_layout(pad=.3)
fig.savefig(p / 'fig_stage_ablation.pdf', bbox_inches='tight'); plt.close(fig)
print('figures written; heatmap sum', mat.sum(), 'stage totals', vals)
