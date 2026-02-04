import csv
import tempfile

from ibisworld_client.bulk import export_segments


class FakeClient:
    def __init__(self, response):
        self._response = response

    def get_segment_sections(self, code: str, sections, country: str = "US", use_cache: bool = True):
        return self._response


def test_export_creates_csv(tmp_path):
    # Arrange
    sample = {
        "Sections": [
            {
                "RequestedSection": "currentyearoverview",
                "StatusCode": 200,
                "Body": {"CurrentYearOverview": [{"SegmentSize": "All", "AverageRevenue": 200000}]}},
            {"RequestedSection": "keystatistics", "StatusCode": 200, "Body": {"KeyStatistics": []}},
        ]
    }
    client = FakeClient(sample)
    out = tmp_path / "out.csv"

    # Act
    rows = export_segments(client, ["32191", "42344"], sections=["keystatistics", "currentyearoverview"], out=str(out), use_cache=False)

    # Assert
    assert len(rows) == 2
    with open(out) as f:
        reader = csv.DictReader(f)
        lines = list(reader)
        assert len(lines) == 2
        assert lines[0]["Code"] == "32191"
