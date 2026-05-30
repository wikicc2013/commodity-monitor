"""
黑色系大宗商品价格抓取脚本

设计原则:
1. 单文件、零环境依赖（除了 requirements.txt）
2. 幂等：今天重跑会覆盖今天的记录
3. 容错：单个品种失败不影响其他品种
4. 输出友好：最后打印摘要表
"""
import json
import sys
import logging
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional

import yaml
import pandas as pd
import types as _t
sys.modules.setdefault("jsonpath", _t.ModuleType("jsonpath"))  # jsonpath wheel fails to build; only used by NBS macro funcs we don't call
_py_mini_racer_stub = _t.ModuleType("py_mini_racer")
_py_mini_racer_stub.MiniRacer = type("MiniRacer", (), {})  # native build unavailable in cloud; only used by JS-eval funcs we don't call
sys.modules.setdefault("py_mini_racer", _py_mini_racer_stub)
import akshare as ak
from tenacity import retry, stop_after_attempt, wait_exponential


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
DATA_DIR = PROJECT_ROOT / "data"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("fetch")


def load_config() -> dict:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def is_trading_day(d: date) -> bool:
    try:
        cal = ak.tool_trade_date_hist_sina()
        trading_days = set(str(x)[:10] for x in cal["trade_date"])
        return d.isoformat() in trading_days
    except Exception:
        # 拿不到交易日历就当工作日处理
        return d.weekday() < 5


def safe_float(v) -> Optional[float]:
    try:
        if v is None or pd.isna(v):
            return None
        f = float(v)
        return f if f != 0 else None
    except (ValueError, TypeError):
        return None


def safe_int(v) -> Optional[int]:
    f = safe_float(v)
    return int(f) if f is not None else None


def load_month_file(code: str, year_month: str) -> list:
    path = DATA_DIR / code / f"{year_month}.json"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_month_file(code: str, year_month: str, records: list):
    path = DATA_DIR / code / f"{year_month}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)


def upsert_record(code: str, record: dict):
    """幂等写入：同一品种同一交易日的记录会被覆盖"""
    trade_date = record["trade_date"]
    year_month = trade_date[:7]
    records = load_month_file(code, year_month)
    records = [r for r in records if r.get("trade_date") != trade_date]
    records.append(record)
    records.sort(key=lambda r: r["trade_date"])
    save_month_file(code, year_month, records)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch_futures_daily(symbol_sina: str) -> Optional[dict]:
    """拿主力合约最新日K数据"""
    df = ak.futures_zh_daily_sina(symbol=symbol_sina)
    if df is None or df.empty:
        return None
    last = df.iloc[-1]
    return {
        "trade_date": str(last["date"])[:10],
        "open": safe_float(last.get("open")),
        "high": safe_float(last.get("high")),
        "low": safe_float(last.get("low")),
        "close": safe_float(last.get("close")),
        "volume": safe_int(last.get("volume")),
        "open_interest": safe_int(last.get("hold")),
        "settle": safe_float(last.get("settle")),
    }


@retry(stop=stop_after_attempt(2), wait=wait_exponential(min=2, max=8))
def fetch_spot_basis_all(target_date: str) -> dict:
    """拿当日所有商品的现货+基差"""
    df = ak.futures_spot_price_previous(target_date)
    if df is None or df.empty:
        return {}
    result = {}
    for _, r in df.iterrows():
        name = r.get("商品")
        spot = safe_float(r.get("现货价格"))
        futures = safe_float(r.get("主力合约价格"))
        basis = round(spot - futures, 2) if (spot and futures) else None
        result[name] = {"spot": spot, "futures": futures, "basis": basis}
    return result


def main():
    today = date.today()
    log.info(f"========== {today} 抓取开始 ==========")

    if not is_trading_day(today):
        log.info("非交易日，跳过")
        write_manifest_skip(today)
        return 0

    config = load_config()
    commodities = config["commodities"]

    today_yyyymmdd = today.strftime("%Y%m%d")
    try:
        spot_map = fetch_spot_basis_all(today_yyyymmdd)
        log.info(f"现货基差数据加载成功，含 {len(spot_map)} 个商品")
    except Exception as e:
        log.warning(f"现货基差数据拉取失败: {e}")
        spot_map = {}

    summary = []
    for c in commodities:
        code = c["code"]
        name = c["name_cn"]
        try:
            kline = fetch_futures_daily(c["symbol_sina"])
            if not kline:
                summary.append({"code": code, "name": name, "status": "no_data"})
                log.warning(f"[{name}] 无日K数据")
                continue

            spot_name = c.get("spot_name")
            if spot_name and spot_name in spot_map:
                kline.update({
                    "spot": spot_map[spot_name]["spot"],
                    "basis": spot_map[spot_name]["basis"],
                })

            kline["symbol_sina"] = c["symbol_sina"]
            kline["name_cn"] = name
            kline["exchange"] = c["exchange"]
            upsert_record(code, kline)

            change_pct = None
            year_month = kline["trade_date"][:7]
            month_records = load_month_file(code, year_month)
            if len(month_records) >= 2:
                prev = month_records[-2]
                if prev.get("close") and kline.get("close"):
                    change_pct = (kline["close"] - prev["close"]) / prev["close"] * 100

            summary.append({
                "code": code,
                "name": name,
                "status": "ok",
                "close": kline.get("close"),
                "change_pct": change_pct,
                "spot": kline.get("spot"),
                "basis": kline.get("basis"),
            })
            log.info(f"[{name}] OK close={kline.get('close')}")

        except Exception as e:
            summary.append({"code": code, "name": name, "status": "failed", "error": str(e)})
            log.exception(f"[{name}] 抓取异常")

    update_manifest(today, summary, config)
    print_summary(today, summary)
    return 0


def update_manifest(today: date, summary: list, config: dict):
    manifest = {
        "last_updated": today.isoformat(),
        "last_run_at": datetime.now().isoformat(timespec="seconds"),
        "commodities": [],
    }
    by_code = {s["code"]: s for s in summary}
    for c in config["commodities"]:
        s = by_code.get(c["code"], {})
        manifest["commodities"].append({
            "code": c["code"],
            "name_cn": c["name_cn"],
            "symbol_sina": c["symbol_sina"],
            "category": c["category"],
            "last_status": s.get("status", "unknown"),
            "last_close": s.get("close"),
            "last_change_pct": s.get("change_pct"),
        })
    DATA_DIR.mkdir(exist_ok=True)
    with open(DATA_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def write_manifest_skip(today: date):
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / "manifest.json"
    manifest = {}
    if path.exists():
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    manifest["last_check"] = today.isoformat()
    manifest["last_check_note"] = "非交易日"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def print_summary(today: date, summary: list):
    print()
    print(f"========== 执行摘要 {today} ==========")
    for s in summary:
        if s["status"] == "ok":
            pct = s.get("change_pct")
            pct_str = f"{pct:+.2f}%" if pct is not None else "—"
            spot_str = f"现货{s['spot']:.0f}" if s.get("spot") else ""
            basis_str = f"基差{s['basis']:+.0f}" if s.get("basis") is not None else ""
            print(f"  ✓ {s['name']:6s}  收盘 {s['close']:>8.0f}  {pct_str:>8s}  {spot_str} {basis_str}")
        elif s["status"] == "no_data":
            print(f"  ⚠ {s['name']:6s}  无数据")
        else:
            err = s.get("error", "未知")
            print(f"  ✗ {s['name']:6s}  失败: {err[:60]}")
    print("=" * 50)


if __name__ == "__main__":
    sys.exit(main())
