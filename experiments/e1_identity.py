"""E1: the endurance identity evaluated for each cell mode at equal die count.
Writes results/e1_identity.json."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hbfend import load_params, modes, life_days, residence_days, dwpd, lifetime_days  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def write_all(P, dram="1024000000000.0"):
    """Bytes per day that reach flash when every block leaving host DRAM is written once to unbounded
    flash (E6 'write-all unlimited' rows, Mooncake tool-and-agent constructed day, day 2)."""
    import csv
    out = {}
    for r in csv.DictReader(open(os.path.join(ROOT, "results", "e6_policies.csv"))):
        if r["policy"] == "write-all unlimited" and r["trace"] == "tool-and-agent" and r["dram_bytes"] == dram:
            out[r["model"]] = float(r["bytes_written_day2"])
    return out


def main():
    P = load_params()
    D = life_days(P)
    M = modes(P)
    S = P["stacks_per_node"]
    wa = write_all(P)
    slc_bytes = M["slc"].lifetime_bytes()
    rows = {}
    for k, m in M.items():
        r = {
            "label": m.label, "capacity_per_stack_bytes": m.capacity, "pe": m.pe,
            "residence_s_waf1": residence_days(m.pe, D) * 86400, "residence_s_waf2": residence_days(m.pe, D, 2.0) * 86400,
            "dwpd_waf1": dwpd(m.pe, D), "lifetime_bytes_per_stack": m.lifetime_bytes(),
            "slc_lifetime_bytes_ratio": slc_bytes / m.lifetime_bytes(),
            "node_budget_bytes_per_day": S * m.budget(D),
        }
        for model, w in wa.items():
            r[f"budget_share_{model}"] = S * m.budget(D) / w
            r[f"write_all_life_years_{model}"] = lifetime_days(S * m.capacity, m.pe, w) / P["year_days"]
        rows[k] = r
    out = {"life_days": D, "stacks": S, "write_all_bytes_per_day": wa, "modes": rows,
           "kv_ratio_llama_over_dsv3": wa["Llama-3.1-70B"] / wa["DeepSeek-V3"]}
    json.dump(out, open(os.path.join(ROOT, "results", "e1_identity.json"), "w"), indent=1)
    for k, r in rows.items():
        print(k, round(r["residence_s_waf1"] / 60, 1), "min", round(r["dwpd_waf1"], 2), "DWPD",
              round(r["slc_lifetime_bytes_ratio"], 2), "x", round(r["budget_share_Llama-3.1-70B"] * 100, 1), "%",
              round(r["write_all_life_years_Llama-3.1-70B"], 2), "y")


if __name__ == "__main__":
    main()
