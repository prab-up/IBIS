"""Helpers to parse Segment Benchmarking responses into flat datapoints."""
from typing import Dict, List, Optional


def _latest_value(stat: Dict, preferred_year: Optional[int] = None):
    """Return the (year, value) pair for the latest available data or preferred_year if present."""
    data = stat.get("Data", [])
    if not data:
        return None, None
    # find by preferred_year first
    if preferred_year is not None:
        for d in data:
            if d.get("Year") == preferred_year:
                return d.get("Year"), d.get("Value")
    # otherwise pick max Year
    d = max(data, key=lambda x: x.get("Year", 0))
    return d.get("Year"), d.get("Value")


def parse_segment_datapoints(code: str, response: Dict) -> List[Dict]:
    """Parse the API response for a segment benchmarking report and return flat rows.

    Each row corresponds to a SegmentSize (e.g., "1-4", "5-9", "All").
    Fields include Revenue, Employment, Wages, Establishments, AverageRevenue, TotalRevenue,
    MarketShare, RevenuePerEmployee (computed if missing), Year, and `Code`.
    """
    sections = {}
    for s in response.get("Sections", []):
        key = (s.get("RequestedSection") or "").lower()
        sections[key] = s.get("Body") or {}

    # helpers
    cyo = sections.get("currentyearoverview", {})
    keystats = sections.get("keystatistics", {})
    keyratios = sections.get("keyratios", {})

    # Map segment -> current year overview data
    cyo_map = {}
    for entry in cyo.get("CurrentYearOverview", []) if isinstance(cyo, dict) else []:
        seg = entry.get("SegmentSize")
        if seg:
            cyo_map[seg] = entry

    rows: List[Dict] = []

    # Iterate key statistics per segment
    for seg_entry in keystats.get("KeyStatistics", []) if isinstance(keystats, dict) else []:
        seg = seg_entry.get("SegmentSize")
        if not seg:
            continue
        stats = seg_entry.get("Statistics", [])
        row = {"Code": str(code), "SegmentSize": seg}
        # collect Revenue, Employment, Wages, Establishments
        latest_year = None
        for stat in stats:
            name = (stat.get("Name") or "").lower()
            year, value = _latest_value(stat)
            if year:
                latest_year = max(latest_year or 0, year)
            # normalize names
            if "revenue" in name:
                row["Revenue"] = value
            elif "employment" in name:
                row["Employment"] = value
            elif "wages" in name:
                row["Wages"] = value
            elif "establish" in name:
                row["Establishments"] = value
            else:
                # store other stats by name
                row[name.replace(" ", "_")] = value

        row["Year"] = latest_year

        # add current year overview values if present
        c = cyo_map.get(seg)
        if c:
            row["AverageRevenue"] = c.get("AverageRevenue")
            row["TotalRevenue"] = c.get("TotalRevenue")
            row["MarketShare"] = c.get("MarketShare")
            row["MarketShareForecast"] = c.get("MarketShareForecast")
            row["MarketSharePrediction"] = c.get("MarketSharePrediction")

        # ratios
        # try to find revenue per employee from keyratios
        for stat in keyratios.get("KeyRatios", []) if isinstance(keyratios, dict) else []:
            if stat.get("SegmentSize") != seg:
                continue
            for sname in stat.get("Statistics", []):
                if (sname.get("Name") or "").lower().replace(" ", "_") == "revenue_per_employee":
                    # get latest
                    y, v = _latest_value(sname)
                    row["RevenuePerEmployee"] = v
                elif (sname.get("Name") or "").lower().replace(" ", "_") == "wages_as_a_share_of_revenue":
                    y, v = _latest_value(sname)
                    row["WagesShareOfRevenue"] = v

        # compute revenue per employee if missing and both revenue & employment present
        if "RevenuePerEmployee" not in row and row.get("Revenue") and row.get("Employment"):
            try:
                row["RevenuePerEmployee"] = float(row["Revenue"]) / float(row["Employment"]) if float(row["Employment"]) != 0 else None
            except Exception:
                row["RevenuePerEmployee"] = None

        rows.append(row)

    # If KeyStatistics missing but CurrentYearOverview present, convert those to rows
    if not rows:
        for seg, c in cyo_map.items():
            r = {"Code": str(code), "SegmentSize": seg}
            r["AverageRevenue"] = c.get("AverageRevenue")
            r["TotalRevenue"] = c.get("TotalRevenue")
            r["MarketShare"] = c.get("MarketShare")
            # no year info
            r["Year"] = None
            rows.append(r)

    return rows
