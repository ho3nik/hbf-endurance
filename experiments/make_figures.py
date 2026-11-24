"""Draw the paper's figures from the result files only. Writes figures/*.pdf."""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "figures")
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID, TIE = "#0b0b0b", "#52514e", "#e6e5e1", "#d9d8d4"

plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "legend.frameon": False, "pdf.fonttype": 42, "font.family": "DejaVu Sans"})


def load(name):
    return json.load(open(os.path.join(RES, name)))


def fig_gaps():
    e2, e1 = load("e2b_gaps_2h.json"), load("e1_identity.json")
    wc = json.load(open(os.path.join(ROOT, "..", "shir-roar", "results", "wildchat_gaps.json")))
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.5))
    series = [("Qwen-Bailian chat (A)", "chat (A)", BLUE), ("Qwen-Bailian API (B)", "API (B)", ORANGE),
              ("Qwen-Bailian coder", "coder", AQUA), ("Qwen-Bailian thinking", "thinking", YELLOW)]
    for key, lab, col in series:
        d = e2["traces"][key]
        a.plot(np.array(d["cdf_x_s"]) / 60.0, d["cdf_y"], color=col, lw=1.6, label=lab)
    slc = e2["slc_residence_s"] / 60.0
    a.axvline(slc, color=INK2, lw=0.8, ls="--")
    a.text(slc * 1.08, 0.08, f"SLC residence\n{slc:.0f} min", ha="left", va="bottom", fontsize=6.5, color=INK2)
    W = e2["window_s"] / 60.0
    a.set_xscale("log"); a.set_xlim(0.1, W); a.set_ylim(0, 1.02)
    a.set_xlabel("time from HBM eviction to next reference (min)")
    a.set_ylabel(f"share of reuse within {W:.0f} min")
    a.grid(color=GRID, lw=0.5); a.legend(loc="upper left", fontsize=6.5, title="Qwen-Bailian", title_fontsize=6.5)
    a.set_title("(a) two-hour traces, Llama-3.1-70B", fontsize=8, loc="left")

    tail = np.sort(np.array(wc["gaps_over_1h_s"], dtype=float)) / 3600.0
    n = wc["follow_up_gaps"]
    x = np.geomspace(1.0, tail.max(), 200)
    ccdf = [(tail > xi).sum() / n for xi in x]
    b.plot(x, ccdf, color=BLUE, lw=1.6)
    for key, txt in [("pslc_low", "pSLC"), ("tlc", "TLC"), ("qlc", "QLC")]:
        r = e1["modes"][key]["residence_s_waf1"] / 3600.0
        b.axvline(r, color=INK2, lw=0.8, ls="--")
        b.text(r * 1.08, 0.03, f"{txt}\n{r:.1f} h", fontsize=7, color=INK2, va="top")
    b.set_xscale("log"); b.set_yscale("log"); b.set_xlim(1, tail.max())
    b.set_xlabel("gap between turns (h)"); b.set_ylabel("share of follow-ups beyond gap")
    b.grid(color=GRID, lw=0.5)
    b.set_title("(b) WildChat follow-ups after one hour", fontsize=8, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_gaps.pdf"))
    plt.close(fig)


SHORT = {"yu_h3_fcfs": "Yu et al., 8+8, FCFS", "yu_h3_aware": "Yu et al., 8+8 stacks, cache-aware",
         "yu_shared_fcfs": "Yu et al., 4+4, FCFS", "yu_shared_aware": "Yu et al., 4+4 stacks, cache-aware",
         "baek_all48": "Baek et al., all KV, 48 sessions", "baek_all128": "Baek et al., all KV, 128 sessions",
         "baek_evict48": "Baek et al., write on evict, 48 sessions", "peng_lru1": "Peng et al., LRU"}


def fig_reconcile():
    e3 = load("e3_reconcile.json")
    rows = [r for r in e3["rows"] if r["recompute"]]
    rows.sort(key=lambda r: r["life_years"])
    fig, ax = plt.subplots(figsize=(3.5, 3.0))
    for i, r in enumerate(rows):
        tl = r["scenarios"]["TLC 3K, WAF 1"]
        ax.plot([tl, r["life_years"]], [i, i], color=GRID, lw=2.0, zorder=1)
        ax.scatter([r["life_years"]], [i], s=22, color=BLUE, zorder=3, edgecolor="white", lw=0.8,
                   label="as reported (SLC)" if i == 0 else None)
        ax.scatter([tl], [i], s=22, color=ORANGE, zorder=3, edgecolor="white", lw=0.8,
                   label="TLC, same dies" if i == 0 else None)
    ax.axvline(5, color=INK2, lw=0.8, ls="--")
    ax.set_ylim(-0.6, len(rows) + 0.3)
    ax.text(5 * 1.08, len(rows) + 0.2, "5-year life", fontsize=6.5, color=INK2, va="top", ha="left")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([LABEL.get(r["id"], r["id"]) for r in rows], fontsize=6.5)
    ax.set_xscale("log"); ax.set_xlabel("HBF lifetime (years)")
    ax.grid(axis="x", color=GRID, lw=0.5); h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=6.5, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(os.path.join(FIG, "fig_reconcile.pdf"))
    plt.close(fig)


def fig_sens():
    """ROAR's savings with SLC and TLC under each setting (Llama-3.1-70B, constructed tool-and-agent day)."""
    import csv
    rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "e6_policies.csv"))))

    def g(trace, dram, waf, mode):
        for r in rows:
            if (r["trace"], r["model"], r["dram_bytes"], r["waf"], r["mode"], r["policy"]) == \
                    (trace, "Llama-3.1-70B", dram, waf, mode, "ROAR"):
                return float(r["saved_flash_gpu_s_day2"]) / 3600.0
        raise KeyError((trace, dram, waf, mode))
    TA, TB = "tool-and-agent", "1024000000000.0"
    settings = [("no host DRAM", TA, "0.0", "1.0"), ("1 TB host DRAM (main)", TA, TB, "1.0"),
                ("2 TB host DRAM", TA, "2048000000000.0", "1.0"), ("4 TB host DRAM", TA, "4096000000000.0", "1.0"),
                ("write amplification 2", TA, TB, "2.0"), ("no late returns", TA + "@x0", TB, "1.0"),
                ("4\u00d7 late returns", TA + "@x4", TB, "1.0")]
    fig, ax = plt.subplots(figsize=(3.45, 2.75))
    h = 0.36
    ys = np.arange(len(settings))[::-1]
    for (lab, tr, dr, wf), y in zip(settings, ys):
        for mode, col, off in (("slc", BLUE, h / 2 + 0.02), ("tlc", ORANGE, -h / 2 - 0.02)):
            v = g(tr, dr, wf, mode)
            ax.barh(y + off, v, height=h, color=col, edgecolor="white", linewidth=0.6)
            ax.text(v + 0.15, y + off, f"{v:.1f}", va="center", ha="left", fontsize=6.5, color=INK2)
    ax.set_yticks(ys); ax.set_yticklabels([s[0] for s in settings], fontsize=7)
    ax.axhline(ys[3] - 0.5, color=GRID, lw=0.8)
    ax.set_xlim(0, 12.2)
    ax.set_xlabel("GPU-hours saved per day")
    ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="SLC"), Patch(color=ORANGE, label="TLC")], loc="lower right",
              fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_sens.pdf"))
    plt.close(fig)


LABEL = {"yu_h3_fcfs": "Yu et al., 8+8, FCFS",
         "yu_h3_aware_nobuf": "Yu et al., 8+8, cache-aware",
         "yu_h3_aware": "Yu et al., 8+8, cache-aware + buffer",
         "yu_shared_fcfs": "Yu et al., 4+4, FCFS",
         "yu_shared_aware_nobuf": "Yu et al., 4+4, cache-aware",
         "yu_shared_aware": "Yu et al., 4+4, cache-aware + buffer",
         "baek_all48": "Baek et al., all KV, 48 sessions",
         "baek_all128": "Baek et al., all KV, 128 sessions",
         "baek_evict48": "Baek et al., write on evict, 48 sessions",
         "peng_lru1": "Peng et al., LRU",
         "peng_lruk10": "Peng et al., LRU-K (K=10)"}


def fig_demand():
    """Drive writes per day each published workload asks for, against what each cell type sustains for five years."""
    e3, e1 = load("e3_reconcile.json"), load("e1_identity.json")
    pub = {e["id"]: e for e in json.load(open(os.path.join(ROOT, "inputs", "published_lifetimes.json")))["entries"]}
    rows = sorted([r for r in e3["rows"] if r["recompute"]], key=lambda r: r["implied_drive_writes_per_day"])
    fig, ax = plt.subplots(figsize=(3.45, 2.9))
    ys = np.arange(len(rows))
    for y, r in zip(ys, rows):
        lb = pub[r["id"]].get("lower_bound", False)
        ax.plot(r["implied_drive_writes_per_day"], y, marker="<" if lb else "o", ms=5, color=BLUE, zorder=3)
    ax.set_yticks(ys); ax.set_yticklabels([LABEL.get(r["id"], r["id"]) for r in rows], fontsize=6.5)
    md = e1["modes"]
    for i, (k, lab) in enumerate((("slc", "SLC"), ("pslc_low", "pSLC 20K"), ("tlc", "TLC"), ("qlc", "QLC"))):
        x = md[k]["dwpd_waf1"]
        ax.axvline(x, color=INK2, lw=0.7, ls="--", zorder=1)
        ax.text(x, len(rows) - 0.35 + (0.75 if i % 2 else 0.0), lab, fontsize=6.5, color=INK2, ha="center", va="bottom",
                bbox=dict(facecolor="white", edgecolor="none", pad=0.6))
    ax.set_xscale("log"); ax.set_xlim(0.15, 700); ax.set_ylim(-0.6, len(rows) + 1.2)
    ax.set_xlabel("drive writes per day")
    ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_demand.pdf"))
    plt.close(fig)


def fig_gaps_micro():
    """Single-column version of Fig. gaps (a): two-hour Qwen-Bailian traces."""
    e2 = load("e2b_gaps_2h.json")
    fig, a = plt.subplots(figsize=(3.45, 2.3))
    series = [("Qwen-Bailian chat (A)", "chat A", BLUE), ("Qwen-Bailian API (B)", "API B", ORANGE),
              ("Qwen-Bailian coder", "coder", AQUA), ("Qwen-Bailian thinking", "thinking", YELLOW)]
    for key, lab, col in series:
        d = e2["traces"][key]
        a.plot(np.array(d["cdf_x_s"]) / 60.0, d["cdf_y"], color=col, lw=1.6, label=lab)
    slc = e2["slc_residence_s"] / 60.0
    a.axvline(slc, color=INK2, lw=0.8, ls="--")
    a.text(slc * 0.92, 0.04, f"SLC residence, {slc:.0f} min", ha="right", va="bottom", fontsize=6.5, color=INK2)
    W = e2["window_s"] / 60.0
    a.set_xscale("log"); a.set_xlim(0.1, W); a.set_ylim(0, 1.02)
    a.set_xlabel("time from HBM eviction to next reference (min)")
    a.set_ylabel(f"cumulative share of\nreuse within {W:.0f} min")
    a.grid(color=GRID, lw=0.5); a.legend(loc="upper left", fontsize=6.5, frameon=False)
    for sp in ("top", "right"):
        a.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_gaps_micro.pdf"))
    plt.close(fig)


def fig_value():
    """GPU-hours per day saved beyond HBM, split into host DRAM and flash, for each DRAM size."""
    import csv
    rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "e6_policies.csv"))))

    def r(dram, mode, pol):
        for x in rows:
            if (x["trace"], x["model"], x["dram_bytes"], x["waf"], x["mode"], x["policy"]) == \
                    ("tool-and-agent", "Llama-3.1-70B", dram, "1.0", mode, pol):
                return x
        raise KeyError((dram, mode, pol))
    base = float(r("0.0", "slc", "ROAR")["saved_hbm_gpu_s_day2"]) / 3600
    ceil = float(r("0.0", "slc", "write-all unlimited")["saved_flash_gpu_s_day2"]) / 3600
    sizes = [("0.0", "no DRAM"), ("1024000000000.0", "1 TB DRAM"), ("2048000000000.0", "2 TB DRAM"),
             ("4096000000000.0", "4 TB DRAM")]
    fig, ax = plt.subplots(figsize=(3.45, 2.7))
    h, y0, ticks, labs = 0.36, 0, [], []
    for i, (dr, lab) in enumerate(sizes):
        y = len(sizes) - 1 - i
        dpart = float(r(dr, "slc", "ROAR")["saved_hbm_gpu_s_day2"]) / 3600 - base
        for mode, col, off in (("slc", BLUE, h / 2 + 0.02), ("tlc", ORANGE, -h / 2 - 0.02)):
            f = float(r(dr, mode, "ROAR")["saved_flash_gpu_s_day2"]) / 3600
            ax.barh(y + off, dpart, height=h, color=TIE, edgecolor="white", linewidth=0.6)
            ax.barh(y + off, f, left=dpart, height=h, color=col, edgecolor="white", linewidth=0.6)
            ax.text(dpart + f + 0.25, y + off, f"{dpart + f:.1f}", va="center", ha="left", fontsize=6.5, color=INK2)
        ticks.append(y); labs.append(lab)
    ax.axvline(ceil, color=INK, lw=0.9, ls="--")
    ax.text(ceil - 0.2, len(sizes) - 0.45, f"any cache below\nHBM: {ceil:.1f}", ha="right", va="top", fontsize=6.5, color=INK)
    ax.set_yticks(ticks); ax.set_yticklabels(labs, fontsize=7)
    ax.set_xlim(0, 22.5); ax.set_ylim(-0.6, len(sizes) - 0.1)
    ax.set_xlabel("GPU-hours per day saved below HBM")
    ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=TIE, label="host DRAM"), Patch(color=BLUE, label="SLC flash"),
                       Patch(color=ORANGE, label="TLC flash")], loc="upper center", bbox_to_anchor=(0.45, -0.22),
              ncol=3, fontsize=6.5, frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_value.pdf"))
    plt.close(fig)


def fig_regime():
    e4 = load("e4_regime.json")
    cls = np.array(e4["maps"]["sigma2.3"]["class"])
    r = np.array(e4["r_grid"]) / 1e12
    m = np.array(e4["m_grid_days"]) * 86400 / 60.0
    fig, ax = plt.subplots(figsize=(3.5, 2.7))
    cmap = ListedColormap([BLUE, TIE, ORANGE, AQUA])
    ax.pcolormesh(r, m, cls, cmap=cmap, vmin=-0.5, vmax=3.5, shading="nearest", rasterized=True)
    e1 = load("e1_identity.json")
    budgets = [(e1["modes"]["pslc_low"]["node_budget_bytes_per_day"] / e1["stacks"], "pSLC budget"),
               (e4["tlc_budget_per_stack"], "TLC budget"), (e4["qlc_budget_per_stack"], "QLC budget")]
    for xb, txt in budgets:
        x = xb / 1e12
        ax.axvline(x, color=INK, lw=0.8, ls="--")
        ax.text(x * 0.94, 0.62, txt, rotation=90, fontsize=6, color=INK, va="bottom", ha="right")
    for p, lab in []:
        ax.scatter([p["reusable_per_stack"] / 1e12], [p["median_gap_s"] / 60], s=26, color="white",
                   edgecolor=INK, lw=1.0, zorder=4)
        deep = lab.startswith("Deep")
        ax.text(p["reusable_per_stack"] / 1e12 * (0.8 if deep else 1.25), p["median_gap_s"] / 60 * (1.0 if deep else 0.72),
                lab, fontsize=6.5, color=INK if deep else "white", va="center" if deep else "top",
                ha="right" if deep else "center", zorder=4)
    ax.text(40, 30, "SLC\nahead", fontsize=7, color="white", ha="center", va="center")
    ax.text(0.05, 3.0, "within 5%", fontsize=7, color=INK, ha="center")
    ax.text(0.12, 800, "QLC ahead", fontsize=7, color="white", ha="center", va="center")
    ax.text(1.75, 150, "pSLC or TLC", fontsize=6.5, color="white", ha="center", va="center", rotation=90)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("reusable KV written per stack (TB/day)")
    ax.set_ylabel("median eviction-to-reuse gap (min)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_regime.pdf"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(FIG, exist_ok=True)
    fig_gaps(); fig_reconcile(); fig_regime(); fig_sens(); fig_demand(); fig_gaps_micro(); fig_value()
    print("figures written")
