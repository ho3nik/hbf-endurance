"""E6: admission policies from the HBF literature in one simulator, at equal writable bytes per cell mode.

Workload (constructed): two synthetic days built from one public Mooncake hour by the ROAR simulator's
day builder, plus cross-hour returns: each request is re-issued with the probability that a WildChat
turn is followed by another turn more than an hour later, after a gap drawn from those measured gaps
(shirroar.trace.build_days_reinject). Day 1 warms the caches; day 2 is measured.
Hierarchy: HBM (about 1 TB, LRU) -> host DRAM (FIFO; 0, 1, 2 or 4 TB) -> HBF (8 stacks, FIFO log) or an SSD pool.
Each cell mode gets its five-year write budget (C*N/D, WAF 1) and its capacity at equal die count.
Policies, all held to the same budget:
  write-all within budget   write every evicted block while the period's wear quota lasts
  admit on 2nd reference    the same quota, but only blocks referenced at least twice (LRU-K, K=2)
  adaptive k                admit-on-k with k raised or lowered to track the wear schedule
  ROAR                      admit when the estimated recomputation saving exceeds a wear price
  oracle                    offline: the blocks with the largest future savings, up to one day's budget
  write-all unlimited       every evicted block written once to unbounded flash: defines the write-all rate
Writes results/e6_policies.csv (one row per run; reruns skip rows already present).
Usage: python e6_policies.py JOB   where JOB selects a subset (see JOBS)."""
import csv
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "..", "shir-roar", "experiments"))

from common import (PeriodQuota, Region, new_estimator, oracle_select, roar, OracleSet)  # noqa: E402
from e6_adaptive_k import GRID  # noqa: E402
from e10_load_aware import AK  # noqa: E402
from shirroar import LLAMA31_70B, DEEPSEEK_V3, AdaptiveK, Simulator, build_days_reinject, hbm_pass, load_mooncake  # noqa: E402
from hbfend import load_params, modes, life_days  # noqa: E402
from hbfend.identity import Mode  # noqa: E402
from hbfend.dram import dram_pass  # noqa: E402

DAY = 86400.0
T = 2 * DAY
OUT = os.path.join(ROOT, "results", "e6_policies.csv")
DATA = os.path.join(ROOT, "..", "shir-roar", "data")
MODELS = {"Llama-3.1-70B": LLAMA31_70B, "DeepSeek-V3": DEEPSEEK_V3}
TRACES = {"tool-and-agent": "toolagent_trace.jsonl", "conversation": "conversation_trace.jsonl"}
POLICIES = ["write-all within budget", "admit on 2nd reference", "adaptive k", "ROAR", "oracle"]
MODES = ["slc", "pslc_low", "tlc", "qlc"]
TB = 1024e9
# (trace, model, host DRAM bytes, WAF, modes, policies)
JOBS = {
    "main": [("tool-and-agent", "Llama-3.1-70B", TB, 1.0, MODES + ["ssd"], POLICIES + ["write-all unlimited"]),
             ("tool-and-agent", "DeepSeek-V3", TB, 1.0, MODES + ["ssd"], POLICIES + ["write-all unlimited"]),
             ("conversation", "Llama-3.1-70B", TB, 1.0, MODES, ["adaptive k", "ROAR", "oracle", "write-all unlimited"])],
    "extra": [("tool-and-agent", "Llama-3.1-70B", 0.0, 1.0, ["slc", "tlc"], ["ROAR", "oracle", "write-all unlimited"]),
              ("tool-and-agent", "Llama-3.1-70B", 2 * TB, 1.0, ["slc", "pslc_low", "tlc"], ["adaptive k", "ROAR"]),
              ("tool-and-agent", "Llama-3.1-70B", 4 * TB, 1.0, ["slc", "pslc_low", "tlc"], ["adaptive k", "ROAR"]),
              ("tool-and-agent", "Llama-3.1-70B", TB, 2.0, ["slc", "pslc_low", "tlc"], ["adaptive k", "ROAR"])],
    # runs requested by the cold review: unlimited-flash ceiling at more DRAM sizes, late returns with no/large DRAM,
    # two more seed pairs for the key cells, and a high late-return rate
    "review": [("tool-and-agent", "Llama-3.1-70B", 2 * TB, 1.0, ["slc"], ["write-all unlimited"]),
               ("tool-and-agent", "Llama-3.1-70B", 4 * TB, 1.0, ["slc"], ["write-all unlimited"]),
               ("tool-and-agent@x4", "Llama-3.1-70B", 0.0, 1.0, ["slc", "tlc"], ["ROAR", "write-all unlimited"]),
               ("tool-and-agent@x4", "Llama-3.1-70B", 4 * TB, 1.0, ["slc", "tlc"], ["adaptive k", "ROAR", "write-all unlimited"]),
               ("tool-and-agent@s1", "Llama-3.1-70B", TB, 1.0, ["slc", "pslc_low", "tlc"], ["adaptive k", "ROAR", "oracle", "write-all unlimited"]),
               ("tool-and-agent@s2", "Llama-3.1-70B", TB, 1.0, ["slc", "pslc_low", "tlc"], ["adaptive k", "ROAR", "oracle", "write-all unlimited"]),
               ("tool-and-agent@s1", "DeepSeek-V3", TB, 1.0, ["slc", "tlc", "ssd"], ["admit on 2nd reference", "adaptive k", "ROAR"]),
               ("tool-and-agent@s2", "DeepSeek-V3", TB, 1.0, ["slc", "tlc", "ssd"], ["admit on 2nd reference", "adaptive k", "ROAR"]),
               ("tool-and-agent@x16", "Llama-3.1-70B", TB, 1.0, ["slc", "tlc"], ["adaptive k", "ROAR"])],
    # same-die comparison with relaxed retention: pSLC at 30K cycles and TLC at 2.7x cycles
    "relaxed": [("tool-and-agent", "Llama-3.1-70B", TB, 1.0, ["pslc_high", "tlc_relaxed"], ["adaptive k", "ROAR"]),
                ("tool-and-agent", "DeepSeek-V3", TB, 1.0, ["pslc_high", "tlc_relaxed"], ["adaptive k", "ROAR"])],
    # return-rate sweep: "@x<m>" multiplies the WildChat long-gap return probability by m (x0: no cross-hour returns)
    "returns": [("tool-and-agent@x0", "Llama-3.1-70B", TB, 1.0, ["slc", "tlc"], ["adaptive k", "ROAR", "oracle"]),
                ("tool-and-agent@x4", "Llama-3.1-70B", TB, 1.0, ["slc", "tlc"], ["adaptive k", "ROAR", "oracle"])],
}


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def done_keys():
    if not os.path.exists(OUT):
        return set()
    return {(r["trace"], r["model"], r["dram_bytes"], r["waf"], r["mode"], r["policy"]) for r in csv.DictReader(open(OUT))}


def append(row):
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)


def main(job):
    P = load_params()
    D = life_days(P)
    M = modes(P)
    # TLC with the 2.7-fold cycle gain Luo et al. estimate for refresh on 3D NAND (same capacity as TLC)
    M["tlc_relaxed"] = Mode("tlc_relaxed", "TLC, 2.7x cycles", M["tlc"].capacity, 2.7 * M["tlc"].pe)
    S = P["stacks_per_node"]
    wc = json.load(open(os.path.join(ROOT, P["wildchat_file"])))
    have = done_keys()
    for trace, mname, dram_bytes, waf, mode_list, pol_list in JOBS[job]:
        todo = [(m, p) for m in mode_list for p in pol_list
                if (trace, mname, str(dram_bytes), str(waf), m, p) not in have
                and not (m == "ssd" and p in ("write-all within budget", "admit on 2nd reference"))
                and not (p == "write-all unlimited" and m != mode_list[0])]
        if not todo:
            continue
        model = MODELS[mname]
        bb = model.block_bytes()
        hbm_blocks = P["hbm_blocks"][mname]
        # trace name grammar: <trace>[@x<m>][@s<k>]; x multiplies the late-return rate, s picks seed pair (2k, 2k+1)
        parts = trace.split("@")
        tname, mult, sk = parts[0], 1.0, 0
        for tok in parts[1:]:
            if tok.startswith("x"):
                mult = float(tok[1:])
            elif tok.startswith("s"):
                sk = int(tok[1:])
        base = load_mooncake(os.path.join(DATA, TRACES[tname]))
        reqs = build_days_reinject(base, seeds=(2 * sk, 2 * sk + 1), frac=min(1.0, mult * wc["return_after_1h_per_turn"]),
                                   gaps=wc["gaps_over_1h_s"])
        s = hbm_pass(reqs, hbm_blocks)
        del reqs
        evict_day2 = sum(1 for k, t in zip(s.kind, s.t) if k == 1 and t >= DAY) * bb   # every HBM eviction on day 2
        served = 0
        if dram_bytes > 0:
            s, served = dram_pass(s, int(dram_bytes // bb))
        log(trace, mname, "dram", dram_bytes, "waf", waf, "events", len(s.kind), "dram-served refs", served)
        for mk, pname in todo:
            read_bw = 4 * P["stack_read_bytes_per_s"]                  # a block striped over four stacks
            if mk == "ssd":
                sp = P["ssd_pool"]
                cap_bytes, budget_day, read_bw = sp["bytes"], sp["dwpd"] * sp["bytes"] / waf, sp["read_bytes_per_s"]
                label = "SSD pool"
            else:
                mode = M[mk]
                cap_bytes, budget_day, label = S * mode.capacity, S * mode.budget(D, waf), mode.label
            budget = budget_day * (T / DAY)                              # bytes over the two simulated days
            cap = int(cap_bytes // bb)
            est = None
            if pname == "write-all unlimited":
                from shirroar import WriteAll
                reg, pol = [Region("unlimited", bb, 1e30, T, None)], WriteAll()
            else:
                reg = [Region(label, bb, budget, T, cap)]
                if pname == "write-all within budget":
                    pol = PeriodQuota(60.0, 1)
                elif pname == "admit on 2nd reference":
                    pol = PeriodQuota(60.0, 2)
                elif pname == "adaptive k":
                    pol = AdaptiveK(**GRID[AK])
                elif pname == "ROAR":
                    pol, est = roar(), new_estimator()
                else:
                    pol = OracleSet(oracle_select(s, model, int(budget / 2 / bb), by="value"))
            t0 = time.time()
            res = Simulator(s, model, reg, pol, tick_s=10.0, t_start=0.0, t_end=T, warmup_s=DAY, estimator=est,
                            read_bw=read_bw).run()
            row = {"trace": trace, "model": mname, "dram_bytes": str(dram_bytes), "waf": str(waf), "mode": mk,
                   "policy": pname, "saved_flash_gpu_s_day2": res.saved_flash_s, "saved_hbm_gpu_s_day2": res.saved_hbm_s,
                   "flash_hits": res.flash_hits, "misses": res.misses, "refs": res.refs,
                   "bytes_written_day2": res.bytes_written[0], "budget_day": budget_day,
                   "written_over_budget": res.bytes_written[0] / budget_day,
                   "blocks_discarded": reg[0].blocks_discarded, "capacity_blocks": cap if pname != "write-all unlimited" else -1,
                   "dram_served_refs_2days": served, "hbm_evict_bytes_day2": evict_day2,
                   "seconds": round(time.time() - t0, 1)}
            append(row)
            log(mk, pname, "saved GPU-h/day", round(res.saved_flash_s / 3600, 2), "written/budget",
                round(row["written_over_budget"], 3), f"{row['seconds']}s")
        del s


if __name__ == "__main__":
    main(sys.argv[1])
