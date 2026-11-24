"""E4: which cell mode catches the most reuse at a five-year life, at equal die count.

Under ideal admission the share of reuse caught depends on the evicted bytes only through the
reusable write rate r = p * w (bytes per stack-day that will be referenced again), so the map's
x axis is r. The y axis is the median eviction-to-reuse gap, with log-normal gaps of shape sigma.
Each point is classed as: 0 SLC ahead by more than MARGIN, 1 within MARGIN, 2 pSLC or TLC ahead,
3 QLC ahead. The random-admission bound is reported at the measured points.
Writes results/e4_regime.json."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hbfend import load_params, modes, life_days, ideal_admission, random_admission, lognormal_cdf  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
MODES = ["slc", "pslc_low", "tlc", "qlc"]
MARGIN = 0.05


def evaluate(M, D, w_s, m_days, sigma, p, bound):
    G = lognormal_cdf(m_days, sigma)
    f = ideal_admission if bound == "ideal" else random_admission
    return {k: f(M[k].capacity, M[k].budget(D), w_s, p, G)["caught"] for k in MODES}


def main():
    P = load_params()
    D = life_days(P)
    M = modes(P)
    S = P["stacks_per_node"]
    e2 = json.load(open(os.path.join(ROOT, "results", "e2_gaps.json")))
    e1 = json.load(open(os.path.join(ROOT, "results", "e1_identity.json")))
    p_nom = e2["traces"]["Mooncake tool-and-agent"]["Llama-3.1-70B"]["share_reused_within_W"]

    r_grid = np.geomspace(0.01e12, 100e12, 61)          # reusable bytes/day/stack
    m_grid = np.geomspace(30 / 86400, 2.0, 61)          # days
    out = {"p_nominal": p_nom, "margin": MARGIN, "r_grid": r_grid.tolist(), "m_grid_days": m_grid.tolist(), "maps": {}}
    for sigma in (1.5, 2.3, 3.0):
        cls = np.zeros((len(m_grid), len(r_grid)), dtype=int)
        for i, m in enumerate(m_grid):
            for j, r in enumerate(r_grid):
                c = evaluate(M, D, r / p_nom, m, sigma, p_nom, "ideal")
                dense = max(MODES[1:], key=lambda k: c[k])
                if c["slc"] > (1 + MARGIN) * c[dense]:
                    cls[i, j] = 0
                elif c[dense] > (1 + MARGIN) * c["slc"]:
                    cls[i, j] = 3 if dense == "qlc" else 2
                else:
                    cls[i, j] = 1
        out["maps"][f"sigma{sigma}"] = {"class": cls.tolist(),
                                        "share": {str(k): float((cls == k).mean()) for k in range(4)}}
        print("sigma", sigma, {k: round(float((cls == k).mean()) * 100, 1) for k in range(4)}, flush=True)

    # Analytic boundary: a dense mode can admit all evicted bytes only when w_s <= its per-stack budget,
    # and it holds blocks longer than SLC only when gaps exceed SLC's capacity residence C_slc / w_s.
    out["tlc_budget_per_stack"] = M["tlc"].budget(D)
    out["qlc_budget_per_stack"] = M["qlc"].budget(D)
    out["slc_budget_per_stack"] = M["slc"].budget(D)

    # Measured operating points (Mooncake one-hour traces through the ROAR HBM pass).
    pts = []
    wa = e1["write_all_bytes_per_day"]
    for label, model in [("Mooncake tool-and-agent", "Llama-3.1-70B"), ("Mooncake tool-and-agent", "DeepSeek-V3")]:
        g = e2["traces"][label][model]
        w_s = wa[model] / S
        c_ideal = evaluate(M, D, w_s, g["median_gap_s"] / 86400, 2.3, g["share_reused_within_W"], "ideal")
        c_rand = evaluate(M, D, w_s, g["median_gap_s"] / 86400, 2.3, g["share_reused_within_W"], "random")
        pts.append({"trace": label, "model": model, "w_per_stack": w_s, "median_gap_s": g["median_gap_s"],
                    "reusable_per_stack": w_s * g["share_reused_within_W"],
                    "reusable_over_tlc_budget": w_s * g["share_reused_within_W"] / M["tlc"].budget(D),
                    "p": g["share_reused_within_W"],
                    "ideal_share": {k: v / g["share_reused_within_W"] for k, v in c_ideal.items()},
                    "random_share": {k: v / g["share_reused_within_W"] for k, v in c_rand.items()},
                    "w_over_tlc_budget": w_s / M["tlc"].budget(D)})
        print(model, "w/stack", round(w_s / 1e12, 1), "TB/d", {k: round(v, 3) for k, v in pts[-1]["ideal_share"].items()},
              {k: round(v, 3) for k, v in pts[-1]["random_share"].items()})
    out["points"] = pts
    json.dump(out, open(os.path.join(ROOT, "results", "e4_regime.json"), "w"))


if __name__ == "__main__":
    main()
