"""Pemutar ulang log sebagai aliran event (simulasi real-time)."""
import time
from typing import Iterator

import pandas as pd


def replay(events: pd.DataFrame, speedup: float = 0.0) -> Iterator[dict]:
    """Yield event satu per satu urut waktu.
    speedup=0  -> secepat mungkin (untuk benchmark/evaluasi)
    speedup=N  -> 1 detik nyata = N detik waktu log (untuk demo live)
    """
    prev = None
    for row in events.sort_values("ts").itertuples(index=False):
        if speedup and prev is not None:
            gap = (row.ts - prev).total_seconds() / speedup
            if gap > 0:
                time.sleep(min(gap, 2.0))
        prev = row.ts
        yield row._asdict()
