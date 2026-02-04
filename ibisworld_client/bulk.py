"""Bulk export utilities for segment benchmarking reports."""
from __future__ import annotations

import csv
from typing import Iterable, List, Dict

from .parse import parse_segment_datapoints


def export_segments(client, codes: Iterable[str], sections: List[str], out: str = "segments.csv", use_cache: bool = True) -> List[Dict]:
    """Fetch multiple segment reports and write a CSV file.

    Returns the list of parsed rows for testing or further processing.
    """
    rows: List[Dict] = []
    for code in codes:
        data = client.get_segment_sections(code=code, sections=sections, country="US", use_cache=use_cache)
        parsed = parse_segment_datapoints(code, data)
        rows.extend(parsed)

    if not rows:
        # create empty file with minimal header
        with open(out, "w", newline="") as f:
            f.write("")
        return rows

    # define a stable header order of common fields
    common = ["Code", "SegmentSize", "Year", "Revenue", "Employment", "Wages", "Establishments", "AverageRevenue", "TotalRevenue", "MarketShare", "RevenuePerEmployee"]
    extras = sorted({k for r in rows for k in r.keys() if k not in common})
    headers = common + extras

    with open(out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in headers})

    return rows
