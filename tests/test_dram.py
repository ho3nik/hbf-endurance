import os

from shirroar import hbm_pass, load_mooncake
from shirroar.hbm import EVICT, REF
from hbfend.dram import dram_pass

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "shir-roar", "data", "qwenthinking_h1.jsonl")


def stream():
    return hbm_pass(load_mooncake(DATA), 2000)


def test_zero_dram_is_identity():
    s = stream()
    o, served = dram_pass(s, 0)
    assert served == 0
    assert list(o.kind) == list(s.kind) and list(o.blk) == list(s.blk) and list(o.hbm_hit) == list(s.hbm_hit)


def test_large_dram_serves_reuse_and_holds_evictions():
    s = stream()
    o, served = dram_pass(s, 10**9)
    assert sum(1 for k in o.kind if k == EVICT) == 0            # nothing leaves an unbounded DRAM
    misses_in = sum(1 for k, h in zip(s.kind, s.hbm_hit) if k == REF and not h)
    misses_out = sum(1 for k, h in zip(o.kind, o.hbm_hit) if k == REF and not h)
    assert misses_in - misses_out == served > 0
    assert sum(1 for k in o.kind if k == REF) == sum(1 for k in s.kind if k == REF)
