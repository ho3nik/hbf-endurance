"""E2: time from HBM eviction to the block's next reference, measured on public one-hour traces.

For each trace and HBM size, run the ROAR simulator's LRU pass over HBM and, for every block
evicted in the first (trace length - W) seconds, find its next reference. W = 1800 s gives every
counted eviction the same 30-minute observation window, so the reuse share within W is not biased
by evictions near the end of the trace. Gaps longer than W are not observable in these traces.
Writes results/e2_gaps.json.
"""
import bisect
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hbfend import load_params, residence_days, life_days  # noqa: E402
from shirroar.trace import load_mooncake  # noqa: E402
from shirroar.hbm import hbm_pass, REF, EVICT  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA = os.path.join(ROOT, "..", "shir-roar", "data")
W = 1800.0

TRACES = {
    "Mooncake conversation": "conversation_trace.jsonl",
    "Mooncake tool-and-agent": "toolagent_trace.jsonl",
    "Qwen-Bailian chat (A)": "qwenA_h1.jsonl",
    "Qwen-Bailian API (B)": "qwenB_h1.jsonl",
    "Qwen-Bailian coder": "qwencoder_h1.jsonl",
    "Qwen-Bailian thinking": "qwenthinking_h1.jsonl",
}


def gaps_for(reqs, hbm_blocks):
    s = hbm_pass(reqs, hbm_blocks)
    t_end = reqs[-1].t
    refs = defaultdict(list)
    evicts = []
    for k, t, b in zip(s.kind, s.t, s.blk):
        if k == REF:
            refs[b].append(t)
        else:
            evicts.append((t, b))
    gaps, n_counted = [], 0
    for t, b in evicts:
        if t > t_end - W:
            continue
        n_counted += 1
        lst = refs[b]
        i = bisect.bisect_right(lst, t)
        if i < len(lst) and lst[i] - t <= W:
            gaps.append(lst[i] - t)
    return np.array(gaps), n_counted, len(evicts), t_end


def main():
    P = load_params()
    D = life_days(P)
    r_slc_s = residence_days(P["pe_cycles"]["slc"], D) * 86400
    out = {"window_s": W, "slc_residence_s": r_slc_s, "traces": {}}
    for label, fn in TRACES.items():
        reqs = load_mooncake(os.path.join(DATA, fn))
        models = ["Llama-3.1-70B", "DeepSeek-V3"] if label.startswith("Mooncake") else ["Llama-3.1-70B"]
        out["traces"][label] = {}
        for m in models:
            g, n, n_all, t_end = gaps_for(reqs, P["hbm_blocks"][m])
            blk = P["models"][m]["kv_bytes_per_token"] * P["block_tokens"]
            evict_rate = n_all * blk / t_end                      # bytes/s HBM evicts in this hour
            dram_res_s = P["host_dram_bytes_per_node"] / evict_rate  # FIFO residence of host DRAM at write-all
            q = np.quantile(g, [0.5, 0.9]) if len(g) else [float("nan")] * 2
            cdf_x = np.geomspace(1, W, 120)
            cdf_y = [float((g <= x).sum() / n) for x in cdf_x] if n else []
            out["traces"][label][m] = {
                "requests": len(reqs), "trace_s": t_end, "evictions": n_all, "evictions_counted": n,
                "reused_within_W": int(len(g)), "share_reused_within_W": float(len(g) / n) if n else None,
                "median_gap_s": float(q[0]), "p90_gap_s": float(q[1]),
                "share_reused_within_slc_residence": float((g <= r_slc_s).sum() / n) if n else None,
                "share_of_reuse_within_slc_residence": float((g <= r_slc_s).sum() / len(g)) if len(g) else None,
                "evict_bytes_per_s": evict_rate, "dram_residence_s": dram_res_s,
                "share_of_reuse_within_dram_residence": float((g <= dram_res_s).sum() / len(g)) if len(g) else None,
                "cdf_x_s": cdf_x.tolist(), "cdf_y": cdf_y,
            }
            print(label, m, {k: v for k, v in out["traces"][label][m].items() if not k.startswith("cdf")}, flush=True)
    with open(os.path.join(ROOT, "results", "e2_gaps.json"), "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
