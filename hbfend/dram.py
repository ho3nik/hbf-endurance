"""Put a host-DRAM buffer between HBM and flash in an HBM event stream.

The HBM pass (shirroar.hbm.hbm_pass) emits REF and EVICT events. This transform inserts an exclusive
FIFO buffer of `dram_blocks` blocks after HBM:
- an HBM eviction moves the block into DRAM; if DRAM is then over capacity, its oldest block leaves
  DRAM, and that departure becomes the EVICT event the flash policy sees;
- a reference that misses HBM but finds the block in DRAM is served from DRAM: it is marked as a
  hit (so the flash pass neither counts nor credits it) and the block leaves DRAM for HBM.
The parent flag of a DRAM departure is recomputed: true when the parent is in HBM or DRAM.
Returns the new stream and the number of references DRAM served.
"""
from __future__ import annotations

from array import array
from collections import OrderedDict

from shirroar.hbm import EVICT, REF, EventStream


def dram_pass(s: EventStream, dram_blocks: int):
    out = EventStream(hbm_capacity_blocks=s.hbm_capacity_blocks, n_requests=s.n_requests)
    out.kind, out.hbm_hit, out.parent_in_hbm, out.has_child = bytearray(), bytearray(), bytearray(), bytearray()
    out.t, out.blk, out.pos, out.req = array("d"), array("q"), array("i"), array("i")
    out.parent, out.position = s.parent, s.position
    dram: "OrderedDict[int, int]" = OrderedDict()    # block -> has_child flags at its HBM eviction
    in_hbm = set()
    served = 0
    parent = s.parent
    K, T, B, P, Q, H, PIN, HC = out.kind, out.t, out.blk, out.pos, out.req, out.hbm_hit, out.parent_in_hbm, out.has_child
    for k in range(len(s.kind)):
        b, t = s.blk[k], s.t[k]
        if s.kind[k] == REF:
            h = s.hbm_hit[k]
            if not h and b in dram:
                del dram[b]
                h = 1
                served += 1
            in_hbm.add(b)
            K.append(REF); T.append(t); B.append(b); P.append(s.pos[k]); Q.append(s.req[k]); H.append(h)
            PIN.append(1); HC.append(0)
        else:
            in_hbm.discard(b)
            dram[b] = s.has_child[k]
            while len(dram) > dram_blocks:
                e, hc = dram.popitem(last=False)
                p = parent.get(e)
                K.append(EVICT); T.append(t); B.append(e); P.append(s.position[e]); Q.append(-1); H.append(0)
                PIN.append(1 if (p is None or p in in_hbm or p in dram) else 0); HC.append(hc)
    return out, served
