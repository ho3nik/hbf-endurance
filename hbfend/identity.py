"""The endurance identity for a flash region, in the three forms the paper uses.

C   capacity in bytes
N   rated program/erase cycles
D   service life in days
WAF write amplification (flash bytes programmed per host byte written)
w   host write rate in bytes per day

Daily write budget          B = C*N / (D*WAF)                (Eq. 1)
Residence time at budget    R = C/B = D*WAF/N   (days)       (Eq. 2)
Lifetime at write rate w    L = C*N / (WAF*w)   (days)       (Eq. 3)
Drive writes per day        DWPD = B/C = 1/R                 (Eq. 4)
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def load_params(path: str | None = None) -> dict:
    path = path or os.path.join(ROOT, "inputs", "params.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k: (v["value"] if isinstance(v, dict) and "value" in v else v) for k, v in raw.items() if not k.startswith("_")}


def budget_bytes_per_day(C: float, N: float, D: float, waf: float = 1.0) -> float:
    return C * N / (D * waf)


def residence_days(N: float, D: float, waf: float = 1.0) -> float:
    return D * waf / N


def lifetime_days(C: float, N: float, w: float, waf: float = 1.0) -> float:
    return C * N / (waf * w)


def dwpd(N: float, D: float, waf: float = 1.0) -> float:
    return 1.0 / residence_days(N, D, waf)


def fifo_residence_days(C: float, admitted_bytes_per_day: float) -> float:
    """A FIFO (append-only) region written at a steady rate keeps each block for C / rate."""
    return C / admitted_bytes_per_day


@dataclass(frozen=True)
class Mode:
    """One stack run in one cell mode at equal die count."""
    key: str
    label: str
    capacity: float      # bytes per stack
    pe: float            # rated cycles

    def budget(self, D: float, waf: float = 1.0) -> float:
        return budget_bytes_per_day(self.capacity, self.pe, D, waf)

    def lifetime_bytes(self, waf: float = 1.0) -> float:
        return self.capacity * self.pe / waf


def modes(params: dict) -> dict:
    """Cell modes at equal die count: capacity scales with bits per cell from the SLC stack."""
    c0 = params["slc_stack_bytes"]
    bpc = params["bits_per_cell"]
    pe = params["pe_cycles"]
    return {
        "slc": Mode("slc", "SLC", c0 * bpc["slc"], pe["slc"]),
        "pslc_low": Mode("pslc_low", "pSLC (20K)", c0 * bpc["pslc"], pe["pslc_low"]),
        "pslc_high": Mode("pslc_high", "pSLC (30K)", c0 * bpc["pslc"], pe["pslc_high"]),
        "tlc": Mode("tlc", "TLC", c0 * bpc["tlc"], pe["tlc"]),
        "qlc": Mode("qlc", "QLC", c0 * bpc["qlc"], pe["qlc"]),
    }


def life_days(params: dict) -> float:
    return params["life_years"] * params["year_days"]
