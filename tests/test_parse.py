from ibisworld_client.parse import parse_segment_datapoints


def sample_response():
    return {
        "Sections": [
            {
                "RequestedSection": "currentyearoverview",
                "StatusCode": 200,
                "Body": {
                    "CurrentYearOverview": [
                        {
                            "SegmentSize": "1-4",
                            "AverageRevenue": 100000.0,
                            "TotalRevenue": 400000,
                            "MarketShare": 0.1,
                            "MarketShareForecast": 0.11,
                            "MarketSharePrediction": "stable",
                        }
                    ]
                },
            },
            {
                "RequestedSection": "keystatistics",
                "StatusCode": 200,
                "Body": {
                    "KeyStatistics": [
                        {
                            "SegmentSize": "1-4",
                            "Statistics": [
                                {
                                    "Name": "Revenue",
                                    "Unit": "$",
                                    "Data": [{"Year": 2024, "Value": 100000}, {"Year": 2025, "Value": 110000}],
                                },
                                {"Name": "Employment", "Unit": "people", "Data": [{"Year": 2025, "Value": 3}]},
                                {"Name": "Wages", "Unit": "$", "Data": [{"Year": 2025, "Value": 50000}]},
                            ],
                        }
                    ]
                },
            },
        ]
    }


def test_parse_sample():
    resp = sample_response()
    rows = parse_segment_datapoints("32191", resp)
    assert len(rows) == 1
    r = rows[0]
    assert r["Code"] == "32191"
    assert r["SegmentSize"] == "1-4"
    assert r["Revenue"] == 110000
    assert r["Employment"] == 3
    assert r["Wages"] == 50000
    assert r["AverageRevenue"] == 100000.0
    assert r["Year"] == 2025
    assert "RevenuePerEmployee" in r
