"""E5: what one HBF hit is worth against the other places a missing KV block can come from,
and which reuse gaps each tier can hold at the write-all rate.
Writes results/e5_tiers.json."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hbfend import load_params, modes, life_days, residence_days  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def main():
    P = load_params()
    D = life_days(P)
    M = modes(P)
    S = P["stacks_per_node"]
    e1 = json.load(open(os.path.join(ROOT, "results", "e1_identity.json")))
    wa = e1["write_all_bytes_per_day"]
    out = {"models": {}}
    for name, spec in P["models"].items():
        blk = spec["kv_bytes_per_token"] * P["block_tokens"]
        t_rec0 = P["block_tokens"] * spec["flops_linear"] / P["gpu_flops"]
        t_hbf_1 = blk / P["stack_read_bytes_per_s"]
        t_hbf_4 = blk / (4 * P["stack_read_bytes_per_s"])
        t_pcie = blk / P["pcie_bytes_per_s"]
        t_ssd_1 = blk / P["ssd_bytes_per_s"]
        w = wa[name]
        tiers = {
            "recompute (depth 0)": {"fetch_s": t_rec0},
            "host DRAM over PCIe": {"fetch_s": t_pcie},
            "SSD, one drive": {"fetch_s": t_ssd_1},
            "SSD, striped (PCIe-bound)": {"fetch_s": max(t_pcie, blk / (32 * P["ssd_bytes_per_s"]))},
            "HBF, one stack": {"fetch_s": t_hbf_1},
            "HBF, four stacks": {"fetch_s": t_hbf_4},
        }
        ssd_res = {f"{k} DWPD": 86400.0 / k for k in P["ssd_dwpd_examples"]}
        ssd_share = {f"{k} DWPD": k * P["ssd_bytes_per_node"] / w for k in P["ssd_dwpd_examples"]}
        hbf = {k: {"wear_residence_s": residence_days(M[k].pe, D) * 86400,
                   "capacity_residence_s": S * M[k].capacity / w * 86400,
                   "budget_share": S * M[k].budget(D) / w} for k in ("slc", "tlc", "qlc")}
        out["models"][name] = {
            "block_bytes": blk, "write_all_bytes_per_day": w, "tiers": tiers,
            "ssd_wear_residence_s": ssd_res, "ssd_budget_share": ssd_share,
            "hbf": hbf,
            "value_vs_recompute_s": t_rec0 - t_hbf_4, "value_vs_dram_s": t_pcie - t_hbf_4,
            "recompute_over_dram_value": (t_rec0 - t_hbf_4) / (t_pcie - t_hbf_4),
        }
        print(name, {k: round(v["fetch_s"] * 1e3, 3) for k, v in tiers.items()}, "ms;",
              "value ratio", round(out["models"][name]["recompute_over_dram_value"], 1))
    json.dump(out, open(os.path.join(ROOT, "results", "e5_tiers.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
