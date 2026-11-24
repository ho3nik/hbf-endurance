"""Write every result number the paper prints into paper/numbers.tex (macros) and paper/tab_*.tex
(table bodies). The manuscript types no result number by hand."""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..")
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "paper")
MACROS = {}


def load(n):
    return json.load(open(os.path.join(RES, n)))


def fmt(x, nd=1):
    s = f"{x:,.{nd}f}"
    return s.replace(",", "{,}")


def m(name, value):
    assert name.isalpha(), name
    MACROS[name] = value


def main():
    e1, e2, e3, e4, e5 = (load(f) for f in ("e1_identity.json", "e2_gaps.json", "e3_reconcile.json",
                                             "e4_regime.json", "e5_tiers.json"))
    P = json.load(open(os.path.join(ROOT, "inputs", "params.json")))
    md = e1["modes"]
    L, DS = "Llama-3.1-70B", "DeepSeek-V3"
    # E1 identity
    m("LifeDays", fmt(e1["life_days"], 0))
    m("ResSLCmin", fmt(md["slc"]["residence_s_waf1"] / 60, 0))
    m("ResPSLCh", fmt(md["pslc_low"]["residence_s_waf1"] / 3600, 1))
    m("ResPSLCHighh", fmt(md["pslc_high"]["residence_s_waf1"] / 3600, 1))
    m("ResTLCh", fmt(md["tlc"]["residence_s_waf1"] / 3600, 1))
    m("ResQLCh", fmt(md["qlc"]["residence_s_waf1"] / 3600, 1))
    m("DwpdSLC", fmt(md["slc"]["dwpd_waf1"], 0))
    m("DwpdTLC", fmt(md["tlc"]["dwpd_waf1"], 1))
    m("DwpdQLC", fmt(md["qlc"]["dwpd_waf1"], 2))
    m("RatioTLC", fmt(md["tlc"]["slc_lifetime_bytes_ratio"], 1))
    m("RatioQLC", fmt(md["qlc"]["slc_lifetime_bytes_ratio"], 0))
    m("RatioPSLC", fmt(md["pslc_low"]["slc_lifetime_bytes_ratio"], 0))
    m("WriteAllLlamaTB", fmt(e1["write_all_bytes_per_day"][L] / 1e12, 0))
    m("WriteAllDSTB", fmt(e1["write_all_bytes_per_day"][DS] / 1e12, 0))
    m("KVRatio", fmt(P["models"]["value"][L]["kv_bytes_per_token"] / P["models"]["value"][DS]["kv_bytes_per_token"], 2))
    m("ShareSLCLlama", fmt(md["slc"][f"budget_share_{L}"] * 100, 1))
    m("ShareTLCLlama", fmt(md["tlc"][f"budget_share_{L}"] * 100, 1))
    m("ShareQLCLlama", fmt(md["qlc"][f"budget_share_{L}"] * 100, 1))
    m("LifeSLCLlama", fmt(md["slc"][f"write_all_life_years_{L}"], 2))
    m("LifeTLCLlama", fmt(md["tlc"][f"write_all_life_years_{L}"], 2))
    m("BudgetSLCNodeTB", fmt(md["slc"]["node_budget_bytes_per_day"] / 1e12, 0))
    m("BudgetTLCNodeTB", fmt(md["tlc"]["node_budget_bytes_per_day"] / 1e12, 1))
    rows = []
    for k in ("slc", "pslc_low", "pslc_high", "tlc", "qlc"):
        r = md[k]
        res = r["residence_s_waf1"]
        res_s = f"{fmt(res / 60, 0)} min" if res < 3600 else f"{fmt(res / 3600, 1)} h"
        rows.append(f"{r['label']} & {fmt(r['capacity_per_stack_bytes'] / 1e9, 0)} & {fmt(r['pe'], 0)} & {res_s} & "
                    f"{fmt(r['dwpd_waf1'], 2 if r['dwpd_waf1'] < 1 else 1)} & {fmt(r['lifetime_bytes_per_stack'] / 1e15, 1)} & "
                    f"{fmt(r['slc_lifetime_bytes_ratio'], 1)} & {fmt(r[f'budget_share_{L}'] * 100, 1)} & "
                    f"{fmt(r[f'write_all_life_years_{L}'], 2)} \\\\")
    open(os.path.join(OUT, "tab_identity.tex"), "w").write("\n".join(rows) + "\n")
    rows = []
    for k in ("slc", "pslc_low", "pslc_high", "tlc", "qlc"):
        r = md[k]
        res = r["residence_s_waf1"]
        res_s = f"{fmt(res / 60, 0)} min" if res < 3600 else f"{fmt(res / 3600, 1)} h"
        rows.append(f"{r['label']} & {fmt(r['capacity_per_stack_bytes'] / 1e9, 0)} & {fmt(r['pe'], 0)} & {res_s} & "
                    f"{fmt(r['dwpd_waf1'], 2 if r['dwpd_waf1'] < 1 else 1)} & {fmt(r[f'write_all_life_years_{L}'], 2)} \\\\")
    open(os.path.join(OUT, "tab_identity_micro.tex"), "w").write("\n".join(rows) + "\n")

    # E3 reconciliation
    s = e3["summary"]
    m("RecN", str(s["n_published_points"]))
    m("RecPapers", str(s["n_papers"]))
    sd = s["same_die_breakeven"]
    m("SameDieMin", fmt(min(sd.values()), 1))
    m("SameDieMax", fmt(sorted(sd.values())[1], 1))
    m("SameDieHundred", fmt(max(sd.values()), 1))
    m("RecMin", fmt(s["reported_min_years"], 2))
    m("RecMax", fmt(s["reported_max_years"], 0))
    m("RecFiveY", str(s["n_reported_at_least_5y"]))
    m("RecWafTwoFiveY", str(s["slc_waf2_n_at_least_5y"]))
    m("RecTLCFiveY", str(s["n_tlc_at_least_5y"]))
    m("RecTLCMax", fmt(s["tlc_max_years"], 1))
    m("RecQLCMax", fmt(s["qlc_max_years"], 1))
    m("RecGainMin", fmt(s["tlc_gain_needed_min"], 1))
    m("RecGainMax", fmt(s["tlc_gain_needed_max"], 0))
    m("RecDwpdMin", fmt(s["implied_dwpd_min"], 0))
    m("RecDwpdMax", fmt(s["implied_dwpd_max"], 0))
    m("TLCFactor", fmt(s["tlc_factor"], 2))
    m("QLCFactor", fmt(s["qlc_factor"], 2))
    names = {"yu_h3_fcfs": "Yu et al. \\cite{yu2026hbf}, 8+8 stacks, FCFS",
             "yu_h3_aware": "Yu et al., 8+8 stacks, cache-aware",
             "yu_shared_fcfs": "Yu et al., 4+4 stacks, FCFS", "yu_shared_aware": "Yu et al., 4+4 stacks, cache-aware",
             "baek_all48": "Baek et al. \\cite{baek2026hotcold}, all KV, 48 sessions",
             "baek_all128": "Baek et al., all KV, 128 sessions",
             "baek_evict48": "Baek et al., write on evict, 48 sessions",
             "peng_lru1": "Peng et al. \\cite{peng2026gr}, LRU$^{\\dagger}$",
             "yu_h3_aware_nobuf": "Yu et al., 8+8 stacks, cache-aware, no buffer",
             "yu_shared_aware_nobuf": "Yu et al., 4+4 stacks, cache-aware, no buffer",
             "peng_lruk10": "Peng et al., LRU-K, K=10"}
    rows = []
    for r in e3["rows"]:
        if not r["recompute"]:
            continue
        sc = r["scenarios"]
        rows.append(f"{names[r['id']]} & {fmt(r['life_years'], 2)} & {fmt(r['implied_drive_writes_per_day'], 0)} & "
                    f"{fmt(sc['SLC, WAF 2'], 2)} & {fmt(sc['pSLC 20K, WAF 1'], 2)} & {fmt(sc['TLC 3K, WAF 1'], 2)} & "
                    f"{fmt(sc['QLC 1K, WAF 1'], 2)} & {fmt(r['tlc_endurance_gain_needed_for_5y'], 1)} \\\\")
    open(os.path.join(OUT, "tab_reconcile.tex"), "w").write("\n".join(rows) + "\n")
    yu = {r["id"]: r for r in e3["rows"]}
    m("YuAwareTLC", fmt(yu["yu_h3_aware"]["scenarios"]["TLC 3K, WAF 1"], 2))
    m("BaekEvictTLC", fmt(yu["baek_evict48"]["scenarios"]["TLC 3K, WAF 1"], 2))

    # E2 gaps (Mooncake hours, 30-minute window) and E2b (two-hour Qwen-Bailian, 90-minute window)
    e2b = load("e2b_gaps_2h.json")
    tr = e2["traces"]
    qb = e2b["traces"]
    m("GapWindowMin", fmt(e2["window_s"] / 60, 0))
    m("QwWindowMin", fmt(e2b["window_s"] / 60, 0))
    m("QwSlcMin", fmt(min(d["share_of_reuse_within_slc"] for d in qb.values()) * 100, 0))
    m("QwSlcMax", fmt(max(d["share_of_reuse_within_slc"] for d in qb.values()) * 100, 0))
    m("QwAfterMin", fmt(min(d["share_of_reuse_after_slc"] for d in qb.values()) * 100, 0))
    m("QwAfterMax", fmt(max(d["share_of_reuse_after_slc"] for d in qb.values()) * 100, 0))
    m("QwReuseMin", fmt(min(d["share_reused_within_W"] for d in qb.values()) * 100, 1))
    m("QwReuseMax", fmt(max(d["share_reused_within_W"] for d in qb.values()) * 100, 0))
    m("QwMedMin", fmt(min(d["median_gap_s"] for d in qb.values()) / 60, 1))
    m("QwMedMax", fmt(max(d["median_gap_s"] for d in qb.values()) / 60, 1))
    allshares = [d["share_reused_within_W"] for d in qb.values()] + [tr[t][mm]["share_reused_within_W"] for t in tr for mm in tr[t]]
    m("MoReuseMin", fmt(min(allshares) * 100, 0))
    m("MoReuseMax", fmt(max(allshares) * 100, 0))
    ds = [tr[t]["DeepSeek-V3"]["share_reused_within_W"] for t in tr if "DeepSeek-V3" in tr[t]]
    m("MoReuseDSMin", fmt(min(ds) * 100, 1))
    m("MoReuseDSMax", fmt(max(ds) * 100, 1))
    rows = []
    for t, d in qb.items():
        rows.append(f"{t.replace(' (A)', ' A').replace(' (B)', ' B')} & {fmt(e2b['window_s'] / 60, 0)} & {fmt(d['share_reused_within_W'] * 100, 1)} & "
                    f"{fmt(d['median_gap_s'] / 60, 1)} & {fmt(d['share_of_reuse_within_slc'] * 100, 0)} \\\\")
    for t in ("Mooncake conversation", "Mooncake tool-and-agent"):
        for mm, d in tr[t].items():
            lab = "\\quad same, DeepSeek-V3" if mm == "DeepSeek-V3" else t
            rows.append(f"{lab} & {fmt(e2['window_s'] / 60, 0)} & {fmt(d['share_reused_within_W'] * 100, 1)} & "
                        f"{fmt(d['median_gap_s'] / 60, 1)} & {fmt(d['share_of_reuse_within_slc_residence'] * 100, 0)} \\\\")
    open(os.path.join(OUT, "tab_gaps.tex"), "w").write("\n".join(rows) + "\n")
    wc = json.load(open(os.path.join(ROOT, "..", "shir-roar", "results", "wildchat_gaps.json")))
    m("WcFollowUps", fmt(wc["follow_up_gaps"], 0))
    m("WcMedianS", fmt(wc["median_gap_s"], 0))
    m("WcOverOneH", fmt(wc["share_of_follow_ups_over_1h"] * 100, 1))
    m("WcOverFifteenH", fmt(wc["share_of_follow_ups_over_15h"] * 100, 2))
    m("WcOverDay", fmt(wc["share_of_follow_ups_over_24h"] * 100, 2))
    tl = P["tracelab"]["value"]
    m("TlMeanMin", fmt(tl["mean_user_gap_s"] / 60, 1))
    m("TlMedianMin", fmt(tl["median_user_gap_s"] / 60, 1))

    # E5 tiers
    t5 = e5["models"][L]
    ti = t5["tiers"]
    m("TRecMs", fmt(ti["recompute (depth 0)"]["fetch_s"] * 1e3, 0))
    m("TDramMs", fmt(ti["host DRAM over PCIe"]["fetch_s"] * 1e3, 1))
    m("ValueDramMs", fmt(t5["value_vs_dram_s"] * 1e3, 1))
    m("TSsdMs", fmt(ti["SSD, one drive"]["fetch_s"] * 1e3, 0))
    m("THbfUs", fmt(ti["HBF, four stacks"]["fetch_s"] * 1e6, 0))
    m("THbfOneUs", fmt(ti["HBF, one stack"]["fetch_s"] * 1e6, 0))
    m("ValueRatio", fmt(t5["recompute_over_dram_value"], 0))
    m("ValueRatioDS", fmt(e5["models"][DS]["recompute_over_dram_value"], 0))
    m("SsdShareOne", fmt(t5["ssd_budget_share"]["1 DWPD"] * 100, 1))
    m("SsdShareThree", fmt(t5["ssd_budget_share"]["3 DWPD"] * 100, 1))
    m("SsdResThreeH", fmt(t5["ssd_wear_residence_s"]["3 DWPD"] / 3600, 0))
    m("BlockMiB", fmt(t5["block_bytes"] / 2**20, 0))
    rows = []
    for k, v in ti.items():
        f = v["fetch_s"]
        fs = f"{fmt(f * 1e3, 1)} ms" if f >= 1e-3 else f"{fmt(f * 1e6, 0)} $\\mu$s"
        fd = e5["models"][DS]["tiers"][k]["fetch_s"]
        fds = f"{fmt(fd * 1e3, 1)} ms" if fd >= 1e-3 else f"{fmt(fd * 1e6, 0)} $\\mu$s"
        rows.append(f"{k} & {fs} & {fds} \\\\")
    open(os.path.join(OUT, "tab_tiers.tex"), "w").write("\n".join(rows) + "\n")

    # E4 regime
    pts = {p["model"]: p for p in e4["points"]}
    m("RegimeP", fmt(e4["p_nominal"] * 100, 0))
    m("TLCBudgetStack", fmt(e4["tlc_budget_per_stack"] / 1e12, 1))
    m("QLCBudgetStack", fmt(e4["qlc_budget_per_stack"] / 1e12, 1))
    m("SLCBudgetStack", fmt(e4["slc_budget_per_stack"] / 1e12, 0))
    m("LlamaReusableStack", fmt(pts[L]["reusable_per_stack"] / 1e12, 1))
    m("LlamaOverTLC", fmt(pts[L]["reusable_over_tlc_budget"], 1))
    m("DSReusableStack", fmt(pts[DS]["reusable_per_stack"] / 1e12, 2))
    m("DSOverTLC", fmt(pts[DS]["reusable_over_tlc_budget"], 2))
    m("LlamaIdealSLC", fmt(pts[L]["ideal_share"]["slc"] * 100, 0))
    m("LlamaIdealTLC", fmt(pts[L]["ideal_share"]["tlc"] * 100, 0))
    m("LlamaRandSLC", fmt(pts[L]["random_share"]["slc"] * 100, 0))
    m("LlamaRandTLC", fmt(pts[L]["random_share"]["tlc"] * 100, 1))
    m("DSIdealSLC", fmt(pts[DS]["ideal_share"]["slc"] * 100, 0))
    m("DSIdealTLC", fmt(pts[DS]["ideal_share"]["tlc"] * 100, 0))
    m("DSRandSLC", fmt(pts[DS]["random_share"]["slc"] * 100, 0))
    m("DSRandTLC", fmt(pts[DS]["random_share"]["tlc"] * 100, 0))
    m("RegimeMargin", fmt(e4["margin"] * 100, 0))
    sh = {s: e4["maps"][f"sigma{s}"]["share"] for s in ("1.5", "2.3", "3.0")}
    m("SlcAheadMin", fmt(min(v["0"] for v in sh.values()) * 100, 0))
    m("SlcAheadMax", fmt(max(v["0"] for v in sh.values()) * 100, 0))
    m("QlcAheadMin", fmt(min(v["3"] for v in sh.values()) * 100, 0))
    m("QlcAheadMax", fmt(max(v["3"] for v in sh.values()) * 100, 0))

    import math
    import numpy as np
    from scipy.stats import norm
    m("PSLCBudgetStack", fmt(e1["modes"]["pslc_low"]["node_budget_bytes_per_day"] / e1["stacks"] / 1e12, 1))
    m("SigmaFit", fmt(math.log(wc["p99_gap_s"] / wc["median_gap_s"]) / norm.ppf(0.99), 2))
    tail = np.array(wc["gaps_over_1h_s"], dtype=float)
    m("WcOverTLC", fmt((tail > md["tlc"]["residence_s_waf1"]).sum() / wc["follow_up_gaps"] * 100, 2))
    m("DwpdRatioMin", fmt(s["implied_dwpd_min"] / md["slc"]["dwpd_waf1"], 1))
    m("DwpdRatioMax", fmt(s["implied_dwpd_max"] / md["slc"]["dwpd_waf1"], 1))
    m("SLCOverTLCDwpd", fmt(md["slc"]["dwpd_waf1"] / md["tlc"]["dwpd_waf1"], 0))
    cut8 = yu["yu_h3_fcfs"]["implied_write_bytes_per_day"] / yu["yu_h3_aware"]["implied_write_bytes_per_day"]
    cut4 = yu["yu_shared_fcfs"]["implied_write_bytes_per_day"] / yu["yu_shared_aware"]["implied_write_bytes_per_day"]
    m("YuCutMin", fmt(min(cut8, cut4), 0))
    m("YuCutMax", fmt(max(cut8, cut4), 0))

    import csv
    rows6 = list(csv.DictReader(open(os.path.join(RES, "e6_policies.csv"))))
    TB1 = "1024000000000.0"

    def g(trace, model, dram, waf, mode, pol):
        for r in rows6:
            if (r["trace"], r["model"], r["dram_bytes"], r["waf"], r["mode"], r["policy"]) == (trace, model, dram, waf, mode, pol):
                return float(r["saved_flash_gpu_s_day2"]) / 3600.0
        raise KeyError((trace, model, dram, waf, mode, pol))
    TA, L1, DS = "tool-and-agent", "Llama-3.1-70B", "DeepSeek-V3"

    def row(trace, model, dram, waf, mode, pol):
        for r in rows6:
            if (r["trace"], r["model"], r["dram_bytes"], r["waf"], r["mode"], r["policy"]) == (trace, model, dram, waf, mode, pol):
                return r
        raise KeyError((trace, model, dram, waf, mode, pol))
    node_h = P["stacks_per_node"]["value"] * 24
    m("SimNodeGPUh", fmt(node_h, 0))
    roar = {k: g(TA, L1, TB1, "1.0", k, "ROAR") for k in ("slc", "pslc_low", "tlc", "qlc", "ssd")}
    orac = {k: g(TA, L1, TB1, "1.0", k, "oracle") for k in roar}
    akk = {k: g(TA, L1, TB1, "1.0", k, "adaptive k") for k in roar}
    m("SimRoarSLC", fmt(roar["slc"], 1)); m("SimRoarTLC", fmt(roar["tlc"], 1)); m("SimRoarSSD", fmt(roar["ssd"], 1))
    m("SimRoarSLCpct", fmt(roar["slc"] / node_h * 100, 1)); m("SimRoarTLCpct", fmt(roar["tlc"] / node_h * 100, 1))
    m("SimSlcOverTlc", fmt(roar["slc"] / roar["tlc"], 1))
    ratios = [orac[k] / roar[k] for k in roar]
    m("SimOracleOverRoarMin", fmt(min(ratios), 1)); m("SimOracleOverRoarMax", fmt(max(ratios), 1))
    lead = [(roar[k] / akk[k] - 1) * 100 for k in ("slc", "pslc_low", "tlc", "qlc")]
    m("SimRoarOverAkMin", fmt(min(lead), 0)); m("SimRoarOverAkMax", fmt(max(lead), 0))
    m("SimWaSLC", fmt(g(TA, L1, TB1, "1.0", "slc", "write-all within budget"), 1))
    m("SimWaTLC", fmt(g(TA, L1, TB1, "1.0", "tlc", "write-all within budget"), 1))
    m("SimAkTLC", fmt(akk["tlc"], 1))
    m("SimTlcPolicySpread", fmt(roar["tlc"] / g(TA, L1, TB1, "1.0", "tlc", "write-all within budget"), 0))
    m("SimConvRoarSLC", fmt(g("conversation", L1, TB1, "1.0", "slc", "ROAR"), 1))
    m("SimConvRoarTLC", fmt(g("conversation", L1, TB1, "1.0", "tlc", "ROAR"), 1))
    m("SimNoDramRoarSLC", fmt(g(TA, L1, "0.0", "1.0", "slc", "ROAR"), 1))
    m("SimNoDramRoarTLC", fmt(g(TA, L1, "0.0", "1.0", "tlc", "ROAR"), 1))
    m("SimDramTwoRoarSLC", fmt(g(TA, L1, "2048000000000.0", "1.0", "slc", "ROAR"), 1))
    m("SimDramFourRoarSLC", fmt(g(TA, L1, "4096000000000.0", "1.0", "slc", "ROAR"), 1))
    m("SimDramTwoRoarTLC", fmt(g(TA, L1, "2048000000000.0", "1.0", "tlc", "ROAR"), 1))
    m("SimDramFourRoarTLC", fmt(g(TA, L1, "4096000000000.0", "1.0", "tlc", "ROAR"), 1))
    m("SimWafTwoRoarSLC", fmt(g(TA, L1, TB1, "2.0", "slc", "ROAR"), 1))
    m("SimWafTwoRoarTLC", fmt(g(TA, L1, TB1, "2.0", "tlc", "ROAR"), 1))
    m("WcReturnPct", fmt(wc["return_after_1h_per_turn"] * 100, 1))
    dsr = {k: g(TA, DS, TB1, "1.0", k, "ROAR") for k in ("slc", "pslc_low", "tlc", "qlc", "ssd")}
    dso = {k: g(TA, DS, TB1, "1.0", k, "oracle") for k in dsr}
    m("SimDsRoarSLC", fmt(dsr["slc"], 2)); m("SimDsRoarTLC", fmt(dsr["tlc"], 2)); m("SimDsRoarSSD", fmt(dsr["ssd"], 2))
    m("SimDsSecondSLC", fmt(g(TA, DS, TB1, "1.0", "slc", "admit on 2nd reference"), 2))
    m("SimDsOracleOverRoarMax", fmt(max(dso[k] / dsr[k] for k in dsr), 1))
    wu = row(TA, DS, TB1, "1.0", "slc", "write-all unlimited")
    m("SimDsWaShare", fmt(float(wu["written_over_budget"]) * 100, 0))
    rr = row(TA, DS, TB1, "1.0", "slc", "ROAR")
    m("SimDsSlcResMin", fmt(P["stacks_per_node"]["value"] * P["slc_stack_bytes"]["value"] / float(rr["bytes_written_day2"]) * 1440, 0))
    m("SimOracleWrittenMax", fmt(max(float(row(TA, L1, TB1, "1.0", k, "oracle")["written_over_budget"]) for k in roar) * 100, 0))
    online = [float(r["written_over_budget"]) for r in rows6 if r["policy"] not in ("oracle", "write-all unlimited")]
    m("SimMaxOver", fmt((max(online) - 1) * 100, 0))
    pol_rows = [("write-all within budget", "Write within budget"), ("admit on 2nd reference", "Admit on second reference"),
                ("adaptive k", "Adaptive $k$"), ("ROAR", "ROAR"), ("oracle", "Oracle (offline)")]
    lines = []
    for key, lab in pol_rows:
        cells = []
        for model in ("Llama-3.1-70B", "DeepSeek-V3"):
            for mode in ("slc", "pslc_low", "tlc", "qlc", "ssd"):
                try:
                    cells.append(fmt(g(TA, model, TB1, "1.0", mode, key), 2 if model == "DeepSeek-V3" else 1))
                except KeyError:
                    cells.append("--")
        lines.append(lab + " & " + " & ".join(cells) + " \\\\")
    open(os.path.join(OUT, "tab_sim.tex"), "w").write("\n".join(lines) + "\n")

    # sensitivity table: ROAR on SLC and TLC under other settings (Llama-3.1-70B, tool-and-agent)
    sens = [("Main setting: 1~TB host DRAM, WAF 1, measured returns", TA, TB1, "1.0"),
            ("No host DRAM", TA, "0.0", "1.0"),
            ("2~TB host DRAM", TA, "2048000000000.0", "1.0"),
            ("4~TB host DRAM", TA, "4096000000000.0", "1.0"),
            ("WAF 2", TA, TB1, "2.0"),
            ("No returns after an hour", TA + "@x0", TB1, "1.0"),
            ("Four times the measured returns", TA + "@x4", TB1, "1.0")]
    lines = []
    for lab, tr_, dr, wf in sens:
        a, b = g(tr_, L1, dr, wf, "slc", "ROAR"), g(tr_, L1, dr, wf, "tlc", "ROAR")
        lines.append(f"{lab} & {fmt(a, 1)} & {fmt(b, 1)} & {fmt(a / b, 1)} \\\\")
    open(os.path.join(OUT, "tab_sens.tex"), "w").write("\n".join(lines) + "\n")
    for key, tr_ in (("XZero", TA + "@x0"), ("XFour", TA + "@x4")):
        a, b = g(tr_, L1, TB1, "1.0", "slc", "ROAR"), g(tr_, L1, TB1, "1.0", "tlc", "ROAR")
        m(f"SimRet{key}SLC", fmt(a, 1)); m(f"SimRet{key}TLC", fmt(b, 1)); m(f"SimRet{key}Ratio", fmt(a / b, 1))
    m("SimWafTwoDropSLC", fmt((1 - g(TA, L1, TB1, "2.0", "slc", "ROAR") / roar["slc"]) * 100, 0))
    m("SimWafTwoDropTLC", fmt((1 - g(TA, L1, TB1, "2.0", "tlc", "ROAR") / roar["tlc"]) * 100, 0))

    # ---- Micro version: ceiling, DRAM shares, reusable rate, seeds, relaxed retention, Table II (micro) ----
    def rw(tr_, model, dr, wf, mode, pol):
        return row(tr_, model, dr, wf, mode, pol)
    T2, T4, Z = "2048000000000.0", "4096000000000.0", "0.0"
    hbm = lambda tr_, dr, model=L1: float(rw(tr_, model, dr, "1.0", "slc", "ROAR" if model == L1 else "adaptive k")["saved_hbm_gpu_s_day2"]) / 3600
    ceil0 = g(TA, L1, Z, "1.0", "slc", "write-all unlimited")
    m("SimCeilZero", fmt(ceil0, 1)); m("SimCeilOne", fmt(g(TA, L1, TB1, "1.0", "slc", "write-all unlimited"), 1))
    m("SimCeilTwo", fmt(g(TA, L1, T2, "1.0", "slc", "write-all unlimited"), 1))
    m("SimCeilFour", fmt(g(TA, L1, T4, "1.0", "slc", "write-all unlimited"), 1))
    m("SimCeilFourPct", fmt(g(TA, L1, T4, "1.0", "slc", "write-all unlimited") / node_h * 100, 1))
    m("SimCeilDS", fmt(g(TA, DS, TB1, "1.0", "slc", "write-all unlimited"), 2))
    h0 = hbm(TA, Z)
    for key, dr in (("One", TB1), ("Two", T2), ("Four", T4)):
        m(f"SimDramShare{key}", fmt((hbm(TA, dr) - h0) / ceil0 * 100, 0))
    m("SimNoDramSlcShare", fmt(g(TA, L1, Z, "1.0", "slc", "ROAR") / ceil0 * 100, 0))
    c1 = g(TA, L1, TB1, "1.0", "slc", "write-all unlimited")
    m("SimRoarSlcCeilPct", fmt(roar["slc"] / c1 * 100, 0)); m("SimRoarTlcCeilPct", fmt(roar["tlc"] / c1 * 100, 0))
    m("SimRoarSsdCeilPct", fmt(roar["ssd"] / c1 * 100, 0)); m("SimOracleSlcCeilPct", fmt(orac["slc"] / c1 * 100, 0))
    m("SimOracleSLC", fmt(orac["slc"], 1)); m("SimOracleSSD", fmt(orac["ssd"], 1))
    m("SimDramFourAkSLC", fmt(g(TA, L1, T4, "1.0", "slc", "adaptive k"), 1))
    m("SimDramFourAkTLC", fmt(g(TA, L1, T4, "1.0", "tlc", "adaptive k"), 1))
    bbL = 512 * P["models"]["value"]["Llama-3.1-70B"]["kv_bytes_per_token"]
    for key, mode in (("SLC", "slc"), ("TLC", "tlc")):
        r_ = rw(TA, L1, TB1, "1.0", mode, "ROAR")
        m(f"SimHitsPerBlock{key}", fmt(float(r_["flash_hits"]) / (float(r_["bytes_written_day2"]) / bbL), 2))
    reuL = float(rw(TA, L1, TB1, "1.0", "slc", "oracle")["bytes_written_day2"]) / 1e12
    reuD = float(rw(TA, DS, TB1, "1.0", "slc", "oracle")["bytes_written_day2"]) / 1e12
    tlc_node = md["tlc"]["node_budget_bytes_per_day"] / 1e12
    slc_node = md["slc"]["node_budget_bytes_per_day"] / 1e12
    m("SimReusableL", fmt(reuL, 0)); m("SimReusableDS", fmt(reuD, 1))
    m("SimReusableLOverTLC", fmt(reuL / tlc_node, 1)); m("SimReusableLOverSLC", fmt(reuL / slc_node, 2))
    m("SimReusableDSOverTLC", fmt(reuD / tlc_node, 2))
    m("SimPslcOverTlcPct", fmt((roar["pslc_low"] / roar["tlc"] - 1) * 100, 0))
    m("SimPslcOverTlcAkPct", fmt((akk["pslc_low"] / akk["tlc"] - 1) * 100, 0))
    m("SimWriteBwRatio", fmt(8e9 / (md["slc"]["node_budget_bytes_per_day"] / P["stacks_per_node"]["value"] / 86400), 0))
    m("SimReusableLOverSLCPct", fmt(reuL / slc_node * 100, 0)); m("SimReusableDSOverTLCPct", fmt(reuD / tlc_node * 100, 0))
    drops = {}
    for mode in ("slc", "tlc"):
        d = [(1 - g(TA, L1, TB1, "2.0", mode, p_) / g(TA, L1, TB1, "1.0", mode, p_)) * 100 for p_ in ("ROAR", "adaptive k")]
        drops[mode] = f"{fmt(min(d), 0)}--{fmt(max(d), 0)}"
    m("SimWafTwoDropRangeSLC", drops["slc"]); m("SimWafTwoDropRangeTLC", drops["tlc"])
    tt = t5["tiers"]
    m("SimSsdHitValuePct", fmt((tt["recompute (depth 0)"]["fetch_s"] - tt["SSD, striped (PCIe-bound)"]["fetch_s"])
                              / (tt["recompute (depth 0)"]["fetch_s"] - tt["HBF, four stacks"]["fetch_s"]) * 100, 0))
    m("DramBiasPct", fmt(tt["host DRAM over PCIe"]["fetch_s"] / tt["recompute (depth 0)"]["fetch_s"] * 100, 0))
    m("SimEnduranceGBs", fmt(md["slc"]["node_budget_bytes_per_day"] / P["stacks_per_node"]["value"] / 86400 / 1e9, 2))
    for key, dr in (("One", TB1), ("Four", T4)):
        refs = float(rw(TA, L1, dr, "1.0", "slc", "ROAR")["dram_served_refs_2days"])
        gbs = refs * bbL / (2 * 86400) / 1e9
        m(f"SimDramGBs{key}", fmt(gbs, 1)); m(f"SimDramLinkPct{key}", fmt(gbs / 63 * 100, 0))
    dsr_ = e2["traces"]["Mooncake tool-and-agent"]
    m("DramResLs", fmt(dsr_["Llama-3.1-70B"]["dram_residence_s"], 0)); m("DramResDSmin", fmt(dsr_["DeepSeek-V3"]["dram_residence_s"] / 60, 0))
    m("DramShareL", fmt(dsr_["Llama-3.1-70B"]["share_of_reuse_within_dram_residence"] * 100, 0))
    m("DramShareDS", fmt(dsr_["DeepSeek-V3"]["share_of_reuse_within_dram_residence"] * 100, 0))
    ro = [float(r["written_over_budget"]) for r in rows6 if r["policy"] == "ROAR"]
    ak = [float(r["written_over_budget"]) for r in rows6 if r["policy"] == "adaptive k"]
    m("SimRoarOverMax", fmt((max(ro) - 1) * 100, 0)); m("SimAkOverMax", fmt((max(ak) - 1) * 100, 0))
    shown = [float(r["written_over_budget"]) for r in rows6 if r["policy"] == "ROAR" and r["waf"] == "1.0"
             and r["trace"] == TA and r["mode"] in ("slc", "pslc_low", "tlc", "ssd")]
    m("SimRoarOverShown", fmt((max(shown) - 1) * 100, 0))
    m("SimDsAkTLC", fmt(g(TA, DS, TB1, "1.0", "tlc", "adaptive k"), 2)); m("SimDsAkSSD", fmt(g(TA, DS, TB1, "1.0", "ssd", "adaptive k"), 2))
    dso_all = [g(TA, DS, TB1, "1.0", k, "oracle") for k in ("slc", "pslc_low", "tlc", "ssd")]
    m("SimDsOracleMin", fmt(min(dso_all), 2)); m("SimDsOracleMax", fmt(max(dso_all), 2))
    m("SimDramFourRoarOverPct", fmt((float(rw(TA, L1, T4, "1.0", "slc", "ROAR")["written_over_budget"]) - 1) * 100, 0))
    m("SimDsWrittenPct", fmt(float(rw(TA, DS, TB1, "1.0", "slc", "ROAR")["written_over_budget"]) * 100, 0))
    m("SimDsSsdOverPct", fmt((float(rw(TA, DS, TB1, "1.0", "ssd", "ROAR")["written_over_budget"]) - 1) * 100, 0))
    # late returns at 16x
    try:
        a16, b16 = g(TA + "@x16", L1, TB1, "1.0", "slc", "adaptive k"), g(TA + "@x16", L1, TB1, "1.0", "tlc", "adaptive k")
        m("SimRetXSixteenSLC", fmt(a16, 1)); m("SimRetXSixteenTLC", fmt(b16, 1)); m("SimRetXSixteenRatio", fmt(a16 / b16, 1))
    except KeyError:
        pass
    # late returns x4 with no and 4 TB DRAM
    try:
        c4 = g(TA + "@x4", L1, Z, "1.0", "slc", "write-all unlimited")
        h04 = float(rw(TA + "@x4", L1, Z, "1.0", "slc", "ROAR")["saved_hbm_gpu_s_day2"]) / 3600
        h44 = float(rw(TA + "@x4", L1, T4, "1.0", "slc", "ROAR")["saved_hbm_gpu_s_day2"]) / 3600
        m("SimXFourDramShareFour", fmt((h44 - h04) / c4 * 100, 0))
        m("SimXFourFourSLC", fmt(g(TA + "@x4", L1, T4, "1.0", "slc", "adaptive k"), 1))
        m("SimXFourFourTLC", fmt(g(TA + "@x4", L1, T4, "1.0", "tlc", "adaptive k"), 1))
        m("SimXFourCeilFour", fmt(g(TA + "@x4", L1, T4, "1.0", "slc", "write-all unlimited"), 1))
    except KeyError:
        pass
    # seeds
    try:
        spread, ratios = [], []
        for mode in ("slc", "pslc_low", "tlc"):
            for pol in ("ROAR", "adaptive k"):
                v = [g(TA + sfx, L1, TB1, "1.0", mode, pol) for sfx in ("", "@s1", "@s2")]
                spread.append((max(v) - min(v)) / (sum(v) / 3) * 100)
        for sfx in ("", "@s1", "@s2"):
            ratios.append(g(TA + sfx, L1, TB1, "1.0", "slc", "ROAR") / g(TA + sfx, L1, TB1, "1.0", "tlc", "ROAR"))
        m("SimSeedSpreadMax", fmt(max(spread), 0)); m("SimSeedRatioMin", fmt(min(ratios), 1)); m("SimSeedRatioMax", fmt(max(ratios), 1))
        rng = lambda a, b, d: fmt(a, d) if fmt(a, d) == fmt(b, d) else f"{fmt(a, d)}--{fmt(b, d)}"
        m("SimSeedRatioRange", rng(min(ratios), max(ratios), 1))
        diffs = []
        for sfx in ("", "@s1", "@s2"):
            bs = max(g(TA + sfx, DS, TB1, "1.0", "slc", p_) for p_ in ("admit on 2nd reference", "adaptive k", "ROAR"))
            bt = max(g(TA + sfx, DS, TB1, "1.0", "tlc", p_) for p_ in ("admit on 2nd reference", "adaptive k", "ROAR"))
            bsd = max(g(TA + sfx, DS, TB1, "1.0", "ssd", p_) for p_ in ("adaptive k", "ROAR"))
            diffs.append((bs, bt, bsd))
        m("SimSeedDsSlcMin", fmt(min(d[0] for d in diffs), 2)); m("SimSeedDsSlcMax", fmt(max(d[0] for d in diffs), 2))
        m("SimSeedDsTlcMin", fmt(min(d[1] for d in diffs), 2)); m("SimSeedDsTlcMax", fmt(max(d[1] for d in diffs), 2))
        m("SimSeedDsSsdMin", fmt(min(d[2] for d in diffs), 2))
        m("SimSeedDsSlcRange", rng(min(d[0] for d in diffs), max(d[0] for d in diffs), 2))
        aks = [g(TA + sfx, DS, TB1, "1.0", "ssd", "adaptive k") for sfx in ("", "@s1", "@s2")]
        m("SimSeedDsSsdAkRange", rng(min(aks), max(aks), 2))
        m("SimSeedDsTlcRange", rng(min(d[1] for d in diffs), max(d[1] for d in diffs), 2))
    except KeyError:
        pass
    # relaxed retention
    try:
        m("SimRelaxTlcL", fmt(g(TA, L1, TB1, "1.0", "tlc_relaxed", "ROAR"), 1))
        m("SimPslcHighL", fmt(g(TA, L1, TB1, "1.0", "pslc_high", "ROAR"), 1))
        m("SimRelaxTlcDS", fmt(g(TA, DS, TB1, "1.0", "tlc_relaxed", "ROAR"), 2))
    except KeyError:
        pass
    m("YuPlainCutMin", fmt(min(4.77 / 1.21, 1.06 / 0.75), 1)); m("YuPlainCutMax", fmt(max(4.77 / 1.21, 1.06 / 0.75), 1))
    # Table II for the Micro version: no QLC, ceiling row, over-budget marks, best online value in bold
    cols = [(L1, k) for k in ("slc", "pslc_low", "tlc", "ssd")] + [(DS, k) for k in ("slc", "pslc_low", "tlc", "ssd")]
    pols = [("write-all within budget", "Write within budget"), ("admit on 2nd reference", "Admit on second reference"),
            ("adaptive k", "Adaptive $k$"), ("ROAR", "ROAR"), ("oracle", "Oracle (offline)")]
    best = {}
    for c in cols:
        vals = []
        for key, _ in pols[:4]:
            try:
                if float(rw(TA, c[0], TB1, "1.0", c[1], key)["written_over_budget"]) <= 1.05:
                    vals.append(g(TA, c[0], TB1, "1.0", c[1], key))
            except KeyError:
                pass
        best[c] = max(vals)
    lines = []
    for key, lab in pols:
        cells = []
        for c in cols:
            try:
                r_ = rw(TA, c[0], TB1, "1.0", c[1], key)
            except KeyError:
                cells.append("--"); continue
            v = float(r_["saved_flash_gpu_s_day2"]) / 3600
            t = fmt(v, 2 if c[0] == DS else 1)
            if key != "oracle" and abs(v - best[c]) < 1e-9:
                t = "\\textbf{" + t + "}"
            if key != "oracle" and float(r_["written_over_budget"]) > 1.05:
                t += "$^{*}$"
            cells.append(t)
        lines.append(lab + " & " + " & ".join(cells) + " \\\\")
    lines.append("\\midrule")
    lines.append("Unlimited flash (ceiling) & \\multicolumn{4}{c}{" + fmt(c1, 1) + "} & \\multicolumn{4}{c}{"
                 + fmt(g(TA, DS, TB1, "1.0", "slc", "write-all unlimited"), 2) + "} \\\\")
    open(os.path.join(OUT, "tab_sim_micro.tex"), "w").write("\n".join(lines) + "\n")

    with open(os.path.join(OUT, "numbers.tex"), "w") as f:
        f.write("% Generated by experiments/make_numbers.py from results/*.json. Do not edit.\n")
        for k, v in MACROS.items():
            f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
    print(len(MACROS), "macros")


if __name__ == "__main__":
    main()
