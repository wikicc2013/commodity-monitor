"""
飞书告警推送脚本

用法:
  python scraper/notify_feishu.py          # 正常模式：只推送有异动时才发
  python scraper/notify_feishu.py --force  # 强制模式：有异动即推，同普通模式

逻辑：
- 读 data/manifest.json
- 涨跌幅 >= 3% 或抓取失败的品种视为"异动"
- 有异动 → 通过 FEISHU_WEBHOOK_URL 推卡片消息
- 无异动 → 静默退出（不打扰群）
- 失败时打印错误但不抛异常（飞书是次要功能）
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.json"
THRESHOLD_PCT = 3.0


def load_manifest() -> dict:
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def classify(manifest: dict) -> tuple[list, list]:
    """返回 (大幅波动列表, 失败列表)"""
    big_movers = []
    failures = []
    for c in manifest.get("commodities", []):
        status = c.get("last_status", "unknown")
        if status in ("failed", "no_data"):
            failures.append(c)
        elif status == "ok":
            pct = c.get("last_change_pct")
            if pct is not None and abs(pct) >= THRESHOLD_PCT:
                big_movers.append(c)
    return big_movers, failures


def fmt_pct(pct) -> str:
    if pct is None:
        return "—"
    return f"{pct:+.2f}%"


def build_card(date_str: str, big_movers: list, failures: list) -> dict:
    lines = []
    if big_movers:
        lines.append("**📊 大幅波动品种**")
        for c in big_movers:
            pct = fmt_pct(c.get("last_change_pct"))
            close = c.get("last_close")
            close_str = f"{close:.0f}" if close else "—"
            lines.append(f"• {c['name_cn']} ({c['code']})  收盘 {close_str}  {pct}")
    if failures:
        lines.append("**⚠️ 抓取失败品种**")
        for c in failures:
            lines.append(f"• {c['name_cn']} ({c['code']})  状态: {c.get('last_status')}")

    content = "\n".join(lines)
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"黑色系商品告警 {date_str}"},
                "template": "red" if failures else "orange",
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": content}}
            ],
        },
    }


def send_webhook(url: str, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode())
        if result.get("code", 0) != 0 or result.get("StatusCode", 0) not in (0, 200):
            raise RuntimeError(f"飞书返回错误: {result}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="强制模式（与默认行为相同，保留接口兼容性）")
    args = parser.parse_args()

    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL", "")

    try:
        manifest = load_manifest()
    except Exception as e:
        print(f"飞书告警: 发送失败，原因 读取 manifest 失败: {e}", file=sys.stderr)
        return

    date_str = manifest.get("last_updated", "未知日期")
    big_movers, failures = classify(manifest)

    if not big_movers and not failures:
        print("飞书告警: 今日无异动")
        return

    total = len(big_movers) + len(failures)

    if not webhook_url:
        print(f"飞书告警: 发送失败，原因 FEISHU_WEBHOOK_URL 未配置（有 {total} 条待推送）")
        return

    try:
        card = build_card(date_str, big_movers, failures)
        send_webhook(webhook_url, card)
        print(f"飞书告警: 已推送 {total} 条")
    except Exception as e:
        print(f"飞书告警: 发送失败，原因 {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
