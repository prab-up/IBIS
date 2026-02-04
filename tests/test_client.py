import json
import os
from unittest.mock import patch

import responses

from ibisworld_client import IBISWorldClient


@responses.activate
def test_get_segment_sections_with_token(tmp_path, monkeypatch):
    # Arrange
    token = "fake-token"
    client = IBISWorldClient(token=token, cache_dir=str(tmp_path))

    expected = {"Sections": [{"RequestedSection": "keystatistics", "StatusCode": 200, "Body": {"Title": "Test"}}]}
    responses.add(responses.POST, "https://api.ibisworld.com/v3/segmentbenchmarking/v3/sections", json=expected, status=200)

    # Act
    result = client.get_segment_sections(code="32191", sections=["keystatistics"], country="US")

    # Assert
    assert "Sections" in result
    assert result["Sections"][0]["Body"]["Title"] == "Test"
