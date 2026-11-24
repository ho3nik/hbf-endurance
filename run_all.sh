#!/usr/bin/env bash
# Regenerates every result, figure, number macro and the PDF. About 1.5 hours on 2 cores, 8 GB of memory
# (the policy simulations dominate; run the two e6 jobs one after the other, not in parallel).
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pytest -q tests
python3 experiments/e6_policies.py main
python3 experiments/e6_policies.py extra
python3 experiments/e6_policies.py returns
python3 experiments/e6_policies.py review
python3 experiments/e6_policies.py relaxed
python3 experiments/e1_identity.py
python3 experiments/e2_gaps.py
python3 experiments/e2b_gaps_2h.py
python3 experiments/e3_reconcile.py
python3 experiments/e4_regime.py
python3 experiments/e5_tiers.py
python3 experiments/make_figures.py
python3 experiments/make_numbers.py
python3 experiments/check_numbers.py
(cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > build.log)
python3 experiments/word_count.py
./submission_figs.sh
echo "done: paper/main.pdf"
