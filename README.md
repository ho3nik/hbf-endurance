# hbf-endurance

Code and data pipeline for *Host DRAM First: What High Bandwidth Flash Adds to an LLM KV Cache*
(H. R. J. Nikzat, 2026).

`hbfend/` is a small calculator for the endurance identity of a flash region (write budget, residence time,
lifetime, drive writes per day), two bounds on how much reuse a wear-budgeted region can catch, and a host-DRAM
tier that sits between HBM and flash in the simulator.

## Reproduce

```bash
git clone https://github.com/ho3nik/shir-roar.git      # simulator, traces and WildChat gap statistics
git clone https://github.com/ho3nik/hbf-endurance.git   # this repository, next to shir-roar
python -m pip install -e shir-roar
cd hbf-endurance && PYTHONPATH=. ./run_all.sh
```

`run_all.sh` takes about 1.5 hours on 2 cores with 8 GB of memory; the policy simulations take almost all of it.
Run the simulation jobs one after another, not in parallel, or memory runs out. The script runs the tests, the
simulations, the analyses, the figures, the number macros, a check that every number typed in the manuscript is
an input, a generated macro or a quoted published value, and the LaTeX build.

| Script | Output | What it computes |
|---|---|---|
| `experiments/e6_policies.py main/extra/returns/review/relaxed` | `results/e6_policies.csv` | GPU-hours saved per day by each admission policy and cell type, with host DRAM in front of flash, on constructed two-day workloads (Table II, Fig. 4); also the unlimited-flash ceiling, seeds, late-return rates and TLC with relaxed retention |
| `experiments/e1_identity.py` | `results/e1_identity.json` | budget, residence, DWPD and write-all life per cell type (Table I) |
| `experiments/e2_gaps.py` | `results/e2_gaps.json` | time from HBM eviction to next reference in six public one-hour traces (Table IV) |
| `experiments/e2b_gaps_2h.py` | `results/e2b_gaps_2h.json` | the same on the four two-hour Qwen-Bailian traces, with a 90-minute window (Fig. 3) |
| `experiments/e3_reconcile.py` | `results/e3_reconcile.json` | write rates backed out from published lifetimes (Fig. 2) |
| `experiments/e4_regime.py` | `results/e4_regime.json` | cell-type regime map under ideal admission (not in the article) |
| `experiments/e5_tiers.py` | `results/e5_tiers.json` | time to bring one KV block back from each tier (Fig. 1) |
| `experiments/word_count.py` | printed | IEEE Micro word count (text, references, 250 words per figure or table) |

Every constant is in `inputs/params.json` with its source. Published lifetimes and their stated assumptions are
in `inputs/published_lifetimes.json`.

## Data

The simulator, its admission controllers and the traces live in `shir-roar`, which must sit next to this repository.
The Mooncake and Qwen-Bailian traces (Apache-2.0) and the WildChat-1M turn-gap statistics are read from the
`shir-roar` repository. No raw conversation text is used or stored.

## License

MIT (code). Trace licenses as above.
