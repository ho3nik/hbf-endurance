"""E3: back out each paper's implied host write rate from its reported lifetime and stated
assumptions (Eq. 3 solved for w), then recompute the lifetime under other assumptions at the
same die count and the same write rate. Writes results/e3_reconcile.json."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from hbfend import load_params, lifetime_days  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")

# (label, bits-per-cell multiplier relative to SLC, rated cycles key, WAF; None keeps the paper's own WAF)
SCENARIOS = [
    ("SLC, WAF 2", 1, "slc", 2.0),
    ("pSLC 20K, WAF 1", 1, "pslc_low", None),
    ("TLC 3K, WAF 1", 3, "tlc", None),
    ("QLC 1K, WAF 1", 4, "qlc", None),
    ("TLC 3K, WAF 2", 3, "tlc", 2.0),
]


def main():
    P = load_params()
    Y = P["year_days"]
    pub = json.load(open(os.path.join(ROOT, "inputs", "published_lifetimes.json")))["entries"]
    rows = []
    for e in pub:
        row = {k: e.get(k) for k in ("id", "paper", "url", "config", "cell", "pe", "waf", "capacity_bytes",
                                      "life_years", "life_years_range", "retention_modeled", "recompute")}
        if e["recompute"]:
            L = row["life_years"] * Y
            w = e["capacity_bytes"] * e["pe"] / (e["waf"] * L)
            row["implied_write_bytes_per_day"] = w
            row["implied_drive_writes_per_day"] = w / e["capacity_bytes"]
            row["scenarios"] = {}
            for label, mult, pe_key, waf in SCENARIOS:
                C = e["capacity_bytes"] * mult
                row["scenarios"][label] = lifetime_days(C, P["pe_cycles"][pe_key], w, waf if waf else e["waf"]) / Y
            tlc = row["scenarios"]["TLC 3K, WAF 1"]
            row["tlc_endurance_gain_needed_for_5y"] = P["life_years"] / tlc
        rows.append(row)
    rec = [r for r in rows if r["recompute"]]
    summary = {
        "n_published_points": len(rec),
        "reported_min_years": min(r["life_years"] for r in rec),
        "reported_max_years": max(r["life_years"] for r in rec),
        "n_reported_at_least_5y": sum(r["life_years"] >= P["life_years"] for r in rec),
        "tlc_max_years": max(r["scenarios"]["TLC 3K, WAF 1"] for r in rec),
        "tlc_min_years": min(r["scenarios"]["TLC 3K, WAF 1"] for r in rec),
        "n_tlc_at_least_5y": sum(r["scenarios"]["TLC 3K, WAF 1"] >= P["life_years"] for r in rec),
        "qlc_max_years": max(r["scenarios"]["QLC 1K, WAF 1"] for r in rec),
        "slc_waf2_n_at_least_5y": sum(r["scenarios"]["SLC, WAF 2"] >= P["life_years"] for r in rec),
        "tlc_gain_needed_min": min(r["tlc_endurance_gain_needed_for_5y"] for r in rec),
        "tlc_gain_needed_max": max(r["tlc_endurance_gain_needed_for_5y"] for r in rec),
        "implied_dwpd_min": min(r["implied_drive_writes_per_day"] for r in rec),
        "implied_dwpd_max": max(r["implied_drive_writes_per_day"] for r in rec),
        "tlc_factor": 3 * P["pe_cycles"]["tlc"] / P["pe_cycles"]["slc"],
        "qlc_factor": 4 * P["pe_cycles"]["qlc"] / P["pe_cycles"]["slc"],
        "n_papers": len({r["paper"] for r in rec}),
        # same die: a TLC-capable die run as pSLC (one bit) or TLC (three bits); TLC matches pSLC's lifetime
        # bytes when retention relaxation multiplies its cycles by N_pSLC / (3 * N_TLC)
        "same_die_breakeven": {str(n): n / (3 * P["pe_cycles"]["tlc"]) for n in
                               (P["pe_cycles"]["pslc_low"], P["pe_cycles"]["pslc_high"], P["pe_cycles"]["slc"])},
    }
    json.dump({"rows": rows, "summary": summary}, open(os.path.join(ROOT, "results", "e3_reconcile.json"), "w"), indent=1)
    for r in rec:
        print(r["id"], round(r["life_years"], 2), "y | w", round(r["implied_write_bytes_per_day"] / 1e12, 1), "TB/d |",
              {k: round(v, 2) for k, v in r["scenarios"].items()}, "| gain", round(r["tlc_endurance_gain_needed_for_5y"], 1))
    print(summary)


if __name__ == "__main__":
    main()
