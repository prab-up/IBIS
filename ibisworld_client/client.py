"""Simple IBISWorld client focused on Segment Benchmarking (US).

Features:
- Token or client-credentials support
- Rate limiting to respect IBISWorld limits
- Retries with exponential backoff
- Small file caching
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


class IBISWorldClient:
    BASE_URL = "https://api.ibisworld.com/v3"

    def __init__(
        self,
        token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token_url: Optional[str] = None,
        rate_limit_per_second: int = 8,
        cache_dir: str = "cache",
    ) -> None:
        self.token = token or os.getenv("IBISWORLD_TOKEN")
        self.client_id = client_id or os.getenv("IBISWORLD_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("IBISWORLD_CLIENT_SECRET")
        self.token_url = token_url or os.getenv("IBISWORLD_TOKEN_URL")
        self.rate_limit_per_second = rate_limit_per_second
        self._last_request_at = 0.0
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_token(self) -> str:
        if self.token:
            return self.token
        if self.client_id and self.client_secret and self.token_url:
            resp = requests.post(
                self.token_url,
                data={"grant_type": "client_credentials"},
                auth=(self.client_id, self.client_secret),
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            self.token = data.get("access_token")
            if not self.token:
                raise RuntimeError("Token endpoint did not return access_token")
            return self.token
        raise RuntimeError(
            "No IBISWorld token or client credentials found. Set IBISWORLD_TOKEN or provide client_id/client_secret/token_url"
        )

    def _headers(self) -> Dict[str, str]:
        token = self._ensure_token()
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def _throttle(self) -> None:
        min_interval = 1.0 / float(self.rate_limit_per_second)
        elapsed = time.time() - self._last_request_at
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_at = time.time()

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3), retry=retry_if_exception_type(requests.exceptions.RequestException))
    def _post(self, path: str, payload: Dict) -> Dict:
        self._throttle()
        url = f"{self.BASE_URL}{path}"
        resp = requests.post(url, headers=self._headers(), json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _cache_path(self, key: str) -> Path:
        safe = key.replace("/", "_").replace(" ", "_")
        return self.cache_dir / f"{safe}.json"

    def _save_cache(self, key: str, data: Dict) -> None:
        p = self._cache_path(key)
        p.write_text(json.dumps(data))

    def _load_cache(self, key: str) -> Optional[Dict]:
        p = self._cache_path(key)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except Exception:
                return None
        return None

    # Public methods
    def list_reports(self, country: str = "US", language: str = "English", use_cache: bool = True) -> List[Dict]:
        key = f"reportlist_{country}_{language}"
        if use_cache:
            cached = self._load_cache(key)
            if cached:
                return cached
        body = {"Country": country, "Language": language}
        data = self._post("/industry/v3/reportlist", body)
        self._save_cache(key, data)
        return data

    def get_segment_sections(self, code: str, sections: List[str], country: str = "US", language: str = "English", use_cache: bool = True) -> Dict:
        key = f"segment_{country}_{code}_{'_'.join(sections)}"
        if use_cache:
            cached = self._load_cache(key)
            if cached:
                return cached
        body = {"Country": country, "Code": str(code), "Language": language, "ReportSections": sections}
        data = self._post("/segmentbenchmarking/v3/sections", body)
        self._save_cache(key, data)
        return data

    def get_updated_reports(self, start_date: str, end_date: str, country: str = "US", language: str = "English") -> List[Dict]:
        body = {"StartDate": start_date, "EndDate": end_date, "Country": country, "Language": language}
        return self._post("/industry/v3/updatedreports", body)
