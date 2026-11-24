"""Two bounds on how much reuse a wear-budgeted FIFO flash region can catch.

Setting. HBM evicts w bytes per day ("write-all"). A fraction p of evicted blocks is
referenced again; the time from eviction to that next reference (the reuse gap) has CDF G.
A region of capacity C admits a fraction a of evicted bytes, so it is written at a*w bytes
per day and keeps each block for R = C/(a*w) days. Wear allows at most a*w <= B.

Random admission writes each evicted block with probability a, blind to its future:
    caught(a) = a * p * G(C/(a*w)),  0 < a <= min(1, B/w); the best a is used.
Ideal admission writes only blocks whose gap is at most the residence they will get:
    caught = max a such that a <= min(1, B/w) and a <= p * G(C/(a*w)).
Both count each evicted block's next reference once. "Share caught" divides by p.
"""
from __future__ import annotations

import math
from typing import Callable

import numpy as np


def lognormal_cdf(median_days: float, sigma: float) -> Callable[[np.ndarray], np.ndarray]:
    from scipy.stats import norm
    mu = math.log(median_days)

    def G(x):
        x = np.asarray(x, dtype=float)
        out = np.zeros_like(x)
        pos = x > 0
        out[pos] = norm.cdf((np.log(x[pos]) - mu) / sigma)
        return out
    return G


def empirical_cdf(gaps_days: np.ndarray) -> Callable[[np.ndarray], np.ndarray]:
    g = np.sort(np.asarray(gaps_days, dtype=float))

    def G(x):
        return np.searchsorted(g, np.asarray(x, dtype=float), side="right") / len(g)
    return G


def a_max(B: float, w: float) -> float:
    return min(1.0, B / w)


def random_admission(C: float, B: float, w: float, p: float, G, grid: int = 400) -> dict:
    hi = a_max(B, w)
    a = np.geomspace(hi * 1e-4, hi, grid)
    caught = a * p * G(C / (a * w))
    i = int(np.argmax(caught))
    return {"a": float(a[i]), "caught": float(caught[i]), "share": float(caught[i] / p),
            "residence_days": float(C / (a[i] * w))}


def ideal_admission(C: float, B: float, w: float, p: float, G, iters: int = 80) -> dict:
    hi = a_max(B, w)
    f = lambda a: a - min(hi, p * float(G(np.array([C / (a * w)]))[0]))
    if f(hi) <= 0:          # the budget binds: every admitted byte can be a hit
        a = hi
    else:                   # bisect on the fixed point a = p*G(C/(a*w)); f is increasing in a
        lo_a, hi_a = 1e-12, hi
        for _ in range(iters):
            mid = math.sqrt(lo_a * hi_a)
            if f(mid) <= 0:
                lo_a = mid
            else:
                hi_a = mid
        a = lo_a
    return {"a": float(a), "caught": float(a), "share": float(a / p), "residence_days": float(C / (a * w))}
