import math

import numpy as np
import pytest

from hbfend import (budget_bytes_per_day, residence_days, lifetime_days, dwpd, load_params, modes,
                    life_days, random_admission, ideal_admission, lognormal_cdf)

P = load_params()
D = life_days(P)


def test_residence_does_not_depend_on_capacity():
    for C in (1e9, 512e9, 4e12):
        B = budget_bytes_per_day(C, 3000, D)
        assert math.isclose(C / B, residence_days(3000, D))


def test_dwpd_is_reciprocal_of_residence():
    for N in (1000, 3000, 20000, 100000):
        assert math.isclose(dwpd(N, D) * residence_days(N, D), 1.0)


def test_lifetime_at_budget_equals_service_life():
    C, N = 512e9, 100000
    assert math.isclose(lifetime_days(C, N, budget_bytes_per_day(C, N, D)), D)


def test_slc_residence_matches_roar_preprint():
    # ROAR preprint Table I: 26 min for SLC 100K over five years
    assert round(residence_days(100000, D) * 24 * 60) == 26


def test_equal_die_capacities():
    m = modes(P)
    assert m["tlc"].capacity == 3 * m["slc"].capacity
    assert m["qlc"].capacity == 4 * m["slc"].capacity


@pytest.mark.parametrize("median_days,sigma", [(1 / 1440, 1.5), (0.01, 2.3), (0.5, 3.0)])
def test_ideal_bound_dominates_random(median_days, sigma):
    G = lognormal_cdf(median_days, sigma)
    for C, B, w in [(4e12, 2e14, 5e14), (12e12, 2e13, 5e14), (4e12, 2e14, 2e13)]:
        r = random_admission(C, B, w, 0.4, G)
        i = ideal_admission(C, B, w, 0.4, G)
        assert i["caught"] >= r["caught"] - 1e-9
        assert i["caught"] <= min(1.0, B / w) + 1e-12
        assert i["caught"] <= 0.4 + 1e-12


def test_ideal_bound_grows_with_budget():
    G = lognormal_cdf(0.01, 2.3)
    vals = [ideal_admission(4e12, B, 5e14, 0.4, G)["caught"] for B in (1e13, 5e13, 1e14, 3e14)]
    assert all(b >= a - 1e-12 for a, b in zip(vals, vals[1:]))
