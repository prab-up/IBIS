# IBISWorld Segment Benchmarking Importer 🔧

This project provides a small Python client and CLI to fetch IBISWorld Segment Benchmarking data (US). It is intended as a starting point—you must provide valid API credentials or a token to run it.

Quickstart

1. Copy `.env.example` to `.env` and set `IBISWORLD_TOKEN` or `IBISWORLD_CLIENT_ID`/`IBISWORLD_CLIENT_SECRET` and `IBISWORLD_TOKEN_URL`.
2. Install dependencies: `pip install -r requirements.txt`
3. Use the CLI:
   - List reports: `python cli.py list-reports`
   - Get segment sections: `python cli.py get-segment 32191 --sections keystatistics --sections keyratios`

Notes

- The client includes basic caching in `cache/` to avoid re-fetching data. Use `--refresh` in the CLI to bypass the cache.
- Rate limiting and retries are implemented to respect IBISWorld's published limits.
