"""E2b: eviction-to-reuse gaps with a 90-minute look-ahead, on the full two-hour Qwen-Bailian files.

The converted files hold each two-hour trace as two one-hour halves with timestamps restarted at zero
and prefix-chained block names that are the same in both halves; h2 is shifted by its hour and
appended to h1. Evictions in the first (trace length - W) seconds are counted, each with the same
W = 5,400 s window, so SLC's 26-minute residence covers under a third of the window.
Writes results/e2b_gaps_2h.json."""
import bisect
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hbfend import load_params, residence_days, life_days  # noqa: E402
from shirroar.trace import load_mooncake, Request  # noqa: E402
from shirroar.hbm import hbm_pass, REF  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "..", "shir-roar", "data")
W = 5400.0
FILES = {"Qwen-Bailian chat (A)": "qwenA", "Qwen-Bailian API (B)": "qwenB",
         "Qwen-Bailian coder": "qwencoder", "Qwen-Bailian thinking": "qwenthinking"}


def two_hours(stem):
    h1 = load_mooncake(os.path.join(DATA, f"{stem}_h1.jsonl"))
    h2 = load_mooncake(os.path.join(DATA, f"{stem}_h2.jsonl"))
    return h1 + [Request(r.t + 3600.0, r.blocks, r.input_len, r.output_len, r.turn) for r in h2]


def main():
    P = load_params()
    D = life_days(P)
    r_slc = residence_days(P["pe_cycles"]["slc"], D) * 86400
    out = {"window_s": W, "slc_residence_s": r_slc, "traces": {}}
    for label, stem in FILES.items():
        reqs = two_hours(stem)
        s = hbm_pass(reqs, P["hbm_blocks"]["Llama-3.1-70B"])
        t_end = reqs[-1].t
        refs = defaultdict(list)
        ev = []
        for k, t, b in zip(s.kind, s.t, s.blk):
            (refs[b].append(t) if k == REF else ev.append((t, b)))
        gaps, n = [], 0
        for t, b in ev:
            if t > t_end - W:
                continue
            n += 1
            lst = refs[b]
            i = bisect.bisect_right(lst, t)
            if i < len(lst) and lst[i] - t <= W:
                gaps.append(lst[i] - t)
        g = np.array(gaps)
        x = np.geomspace(1, W, 150)
        out["traces"][label] = {
            "requests": len(reqs), "trace_s": t_end, "evictions_counted": n, "reused_within_W": int(len(g)),
            "share_reused_within_W": len(g) / n if n else None,
            "share_of_reuse_within_slc": float((g <= r_slc).mean()) if len(g) else None,
            "share_of_reuse_within_30min": float((g <= 1800).mean()) if len(g) else None,
            "share_of_reuse_after_slc": float((g > r_slc).mean()) if len(g) else None,
            "median_gap_s": float(np.median(g)) if len(g) else None,
            "cdf_x_s": x.tolist(), "cdf_y": [float((g <= xi).sum() / len(g)) for xi in x] if len(g) else []}
        d = out["traces"][label]
        print(label, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items() if not k.startswith("cdf")}, flush=True)
    json.dump(out, open(os.path.join(ROOT, "results", "e2b_gaps_2h.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
