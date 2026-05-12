# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Black-series commodity futures price monitor. Claude Code Routine runs daily in the cloud, scrapes prices via akshare, commits JSON data to `data/`, and a static ECharts dashboard reads from raw.githubusercontent.com.

## Commands

```bash
pip install -r requirements.txt    # install deps
python scraper/fetch.py            # run scraper (fetches today's data)
cd web && python -m http.server 8000  # preview dashboard locally
```

No test suite, no linter, no build step.

## Architecture

**Data flow**: `config.yaml` → `scraper/fetch.py` → `data/{code}/{YYYY-MM}.json` + `data/manifest.json` → `web/index.html` (ECharts reads JSON via fetch)

**Two execution contexts**:
- **Local** (you): reads this CLAUDE.md. Make code changes, test locally.
- **Cloud Routine** (automated): reads `ROUTINE_INSTRUCTIONS.md`. Runs `fetch.py`, commits data, pushes. Stateless — no memory between runs.

**Scraper** (`scraper/fetch.py`): Single-file script. Reads `config.yaml` for commodity list. Uses `akshare` to call `futures_zh_daily_sina` (daily K-line) and `futures_spot_price_previous` (spot + basis). `upsert_record()` does idempotent write per trade-date — re-running overwrites today's record, never duplicates. `update_manifest()` rewrites `manifest.json` from scratch each run (frontend entry point).

**Frontend** (`web/`): Static HTML + ECharts 5. `config.js` sets `dataBaseUrl` (local `../data` or GitHub raw URL). Loads `manifest.json` first, then fetches monthly JSON files on demand. Charts: candlestick K-line with MA5/MA20 + volume, spot/basis overlay, and normalized multi-commodity comparison.

**Config** (`config.yaml`): Each commodity has `code`, `symbol_sina` (Sina continuous contract like `RB0`), `name_cn`, `spot_name` (null = no spot data available), `exchange`, `category`.

## Design Constraints (do not change)

1. Data lives in Git — no external database.
2. One JSON file per commodity per month — keeps diffs readable.
3. `fetch.py` stays single-file — Routine debugging reads one file.
4. Frontend is pure static — no backend API, deployed via GitHub Pages.
5. Alert logic belongs in the Routine prompt, not in Python code.

## Common Modifications

**Add a commodity**: edit `config.yaml` to add a new entry with `code`, `symbol_sina`, `name_cn`, `spot_name`, `exchange`, `category`. Verify `fetch.py` handles it (no code changes needed — it iterates the config list).

**Fix akshare errors**: edit `scraper/fetch.py`. Preserve the `@retry` decorator and per-commodity try/except isolation.

**Add a chart**: edit `web/index.html`. Use ECharts 5. Data is loaded via `loadCommodityHistory(code, months)` which returns an array of `{trade_date, open, high, low, close, volume, spot, basis}` records.

**Change data source URL**: edit `web/config.js` → `dataBaseUrl`.
