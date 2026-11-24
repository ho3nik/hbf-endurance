"""Check that every number typed directly in paper/main.tex is an input (inputs/*.json), a published
value quoted from a cited paper (inputs/published_lifetimes.json), or a structural constant; result
numbers must come through numbers.tex or the generated tables. Prints anything unclassified and
exits non-zero if there is any."""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
tex = open(os.path.join(ROOT, "paper", "main.tex")).read()
body = tex[tex.index("\\begin{document}"):]
body = re.sub(r"%.*", "", body)
body = re.sub(r"\\(cite|ref|label|eqref|includegraphics|tabinput|url|bibliography|bibliographystyle|graphicspath)\{[^}]*\}", "", body)
body = re.sub(r"\\begin\{tabular\}\{[^}]*\}", "", body)
body = re.sub(r"p\{[\d.]+cm\}", "", body)                # column widths
body = re.sub(r"ME \d{5}", "", body)                         # postal code in the byline
body = re.sub(r"\d+th percentile", "", body)                 # percentile names
body = re.sub(r"\\begin\{tikzpicture\}\[[^\]]*\]", "", body)     # figure layout options
body = re.sub(r"\\(hd|textwidth|columnwidth)", "", body)
body = re.sub(r"-?[\d.]+\s*(cm|pt|mm)\b", "", body)            # layout lengths (tikz, tabcolsep)
body = re.sub(r"length=[\d.]+mm", "", body)
body = re.sub(r"pos=[\d.]+", "", body)                         # tikz label positions
nums = re.findall(r"(?<![A-Za-z\\])\d[\d,]*(?:\.\d+)?", body)


def flatten(x, out):
    if isinstance(x, dict):
        for v in x.values():
            flatten(v, out)
    elif isinstance(x, list):
        for v in x:
            flatten(v, out)
    elif isinstance(x, (int, float)) and not isinstance(x, bool):
        out.add(float(x))
    elif isinstance(x, str):
        for t in re.findall(r"\d[\d,]*(?:\.\d+)?", x):
            out.add(float(t.replace(",", "")))
    return out


inputs = flatten(json.load(open(os.path.join(ROOT, "inputs", "params.json"))), set())
published = flatten(json.load(open(os.path.join(ROOT, "inputs", "published_lifetimes.json"))), set())
# Values quoted from cited sources in the text, each listed with its source.
QUOTED = {
    0.56: "Li et al.: TLC HBF lasts 0.56x the SSD pool [li2026hbfsucks]", 21.7: "Li et al. HBF budget, TB/day [li2026hbfsucks]",
    38.4: "Li et al. SSD-pool budget, TB/day [li2026hbfsucks]", 60000: "Swissbit/Electronic Design: pSLC 30,000-60,000 [swissbit2022pslc]",
    48: "48 one-hour replays make two days (structural)",
    0.4: "OCP grade range [TrendForce]", 3.0: "OCP grade range [TrendForce]", 1000: "Yu et al. read GB/s",
    327680: "Llama KV bytes/token (params)", 70272: "DeepSeek KV bytes/token (params)", 576: "MLA latent values [params source]",
    80: "Llama layers", 128: "KV head dim", 46: "FCR lifetime gain [cai2012fcr]", 3.24: "WARM [luo2015warm]",
    12.9: "WARM with refresh [luo2015warm]", 1000000: "FlashAccel cycles [wang2026flashaccel]", 1.02: "WAF [Baek, Lachesis]",
3.3: "Lachesis", 12.2: "Lachesis", 6.9: "HBFSim", 2.0: "HBFSim", 8.0: "Baek",
    20.0: "Baek", 1.21: "Yu", 14.82: "Yu", 6.0: "Peng (more than six years)", 50: "B200 utilization (params)",
    1024: "host DRAM GB (params)", 15: "WildChat 15 h threshold", 2012: "year of FCR", 2017: "year", 2026: "year",
    2.3: "lognormal shape used for the map (E4 setting)", 1.125: "gpu_flops in PFLOP/s (params)",
    141.2: "Llama flops_linear in GFLOP (params)", 0.3: "daily load curve low end (ROAR day builder default)",
    40: "JESD218 enterprise retention temperature [ibm2021jedec]", 2.7: "Luo et al. 2018 Sec. 6.3, refresh gain on 3D NAND [luo2018improving]", 55: "FlashAccel's 55 P/E cycles per day [wang2026flashaccel]", 74: "DeepSeek flops_linear in GFLOP (params)", 1.5: "E4 sigma sweep",
}
STRUCTURAL = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 20, 30, 32, 100, 512, 1000.0, 100000}
bad = []
for n in nums:
    v = float(n.replace(",", ""))
    if v in STRUCTURAL or v in QUOTED or v in inputs or v in published:
        continue
    bad.append(n)
print(f"{len(nums)} numbers typed in main.tex; {len(bad)} unclassified")
for b in sorted(set(bad), key=lambda s: float(s.replace(',', ''))):
    print("  UNCLASSIFIED:", b)
sys.exit(1 if bad else 0)
