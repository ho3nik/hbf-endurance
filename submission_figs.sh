#!/usr/bin/env bash
# Exports each figure as a separate file for submission: vector PDF and a 600-dpi PNG, named nikzat-figN.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p submission/figures
cp figures/fig_demand.pdf submission/figures/nikzat-fig2.pdf
cp figures/fig_gaps_micro.pdf submission/figures/nikzat-fig3.pdf
cp figures/fig_value.pdf submission/figures/nikzat-fig4.pdf
(cd submission/figures && for f in nikzat-fig2 nikzat-fig3 nikzat-fig4; do pdftoppm -r 600 -png -singlefile $f.pdf $f; done)
