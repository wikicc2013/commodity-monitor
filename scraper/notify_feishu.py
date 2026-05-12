"""
飞书告警脚本(优化版)

读取 data/manifest.json,判断哪些品种需要告警,通过飞书自定义机器人 webhook 推送。

调用方式:
  python scraper/notify_feishu.py            # 正常模式,只在有异动时发送
  python scraper/notify_feishu.py --force    # 强制发送(用于测试链路)
  python scraper/notify_feishu.py --threshold 0.5  # 自定义涨跌阈值(默认 3.0%)
  python scraper/notify_feishu.py --debug    # 打印请求体,便于排查

环境变量:
  FEISHU_WEBHOOK_URL  必填,飞书自定义机器人 webhook 完整地址
  DASHBOARD_URL       可选,看板地址,默认 https://wikicc2013.github.io/commodity-monitor/

退出码:
  0 正常(发了告警或无需告警)
  1 配置错误(缺环境变量)
  2 网络错误或飞书拒收
"""
import argparse
import io
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path

# Windows 终端默认 GBK 无法输出 emoji，强制 stdout/stderr 用 UTF-8
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "manifest.json"

# 安全关键词:飞书机器人安全设置里也必须配同样的词
# 改这里时,飞书后台也要同步改
KEYWORD = "大宗"

DEFAULT_THRESHOLD = 3.0
DEFAULT_DASHBOARD_URL = "https://wikicc2013.github.io/commodity-monitor/"


def load_manifest():
    if not MANIFEST_PATH.exists():
        print(f"[ERROR] manifest.json 不存在: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        return json.load(f)


def classify_commodity(c, threshold):
    """
    判断单个品种状态,返回 (level, reason) 或 None
    level: 'major' / 'minor' / 'data_issue'
    """
    status = c.get("last_status", "unknown")
    pct = c.get("last_change_pct")

    if status != "ok":
        return ("data_issue", f"抓取状态: {status}")

    if pct is None:
        return None

    abs_pct = abs(pct)
    if abs_pct >= threshold * 2:
        return ("major", f"{'涨' if pct > 0 else '跌'} {abs_pct:.2f}%")
    elif abs_pct >= threshold:
        return ("minor", f"{'涨' if pct > 0 else '跌'} {abs_pct:.2f}%")
    return None


def build_card(alerts, manifest, dashboard_url):
    """
    构造飞书 interactive card
    alerts: [(commodity_dict, level, reason), ...]
    """
    has_major = any(a[1] == "major" for a in alerts)
    only_data_issue = (
        len(alerts) > 0
        and all(a[1] == "data_issue" for a in alerts)
    )

    if has_major:
        template = "red"
        title_emoji = "🔴"
    elif only_data_issue:
        template = "orange"
        title_emoji = "⚠️"
    else:
        template = "yellow"
        title_emoji = "📊"

    today = manifest.get("last_updated") or date.today().isoformat()

    lines = []
    for c, level, reason in alerts:
        name = c.get("name_cn", c.get("code", "?"))
        code = c.get("code", "")
        close = c.get("last_close")
        close_str = f"{close:.0f}" if isinstance(close, (int, float)) else "—"

        if level == "major":
            prefix = "🔴"
        elif level == "minor":
            prefix = "🟡"
        else:
            prefix = "⚠️"

        lines.append(f"{prefix} **{name}** ({code})  收盘 {close_str}  {reason}")

    summary_text = "\n".join(lines) if lines else "今日无异动品种"

    card = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"{title_emoji} {KEYWORD}物资异动告警 · {today}"
                },
                "template": template,
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": summary_text,
                    },
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"阈值: 涨跌 ≥ {DEFAULT_THRESHOLD}%  ·  数据来源: AKShare  ·  Routine 自动触发",
                        }
                    ],
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "查看完整看板"},
                            "url": dashboard_url,
                            "type": "primary",
                        }
                    ],
                },
            ],
        },
    }
    return card


def send_to_feishu(webhook_url, card, debug=False):
    """
    发送 POST 请求到飞书 webhook。
    关键点:
    - body 必须是 UTF-8 编码的 bytes(Python 处理中文 JSON 的标准做法)
    - ensure_ascii=False 让中文保持原样,而不是被转义成 \\uXXXX
    - Content-Type 必须明确声明 charset=utf-8
    """
    body_str = json.dumps(card, ensure_ascii=False)
    body_bytes = body_str.encode("utf-8")

    if debug:
        print("[DEBUG] 请求 body:")
        print(body_str)
        print(f"[DEBUG] body 字节数: {len(body_bytes)}")
        print(f"[DEBUG] webhook URL 前缀: {webhook_url[:60]}...")

    req = urllib.request.Request(
        webhook_url,
        data=body_bytes,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
            "User-Agent": "commodity-monitor-feishu-bot/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            if debug:
                print(f"[DEBUG] 飞书响应: {body}")
            result = json.loads(body)
            # 飞书有两种成功响应格式,都要兼容
            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print(f"[OK] 飞书告警已发送")
                return True
            else:
                print(f"[ERROR] 飞书拒收: {body}", file=sys.stderr)
                # 19024 = 关键词不匹配; 19021 = IP 不在白名单; 19015 = 签名错误
                code = result.get("code")
                if code == 19024:
                    print(f"[HINT] 错误 19024 表示卡片标题没有包含关键词 '{KEYWORD}',", file=sys.stderr)
                    print(f"       请检查飞书机器人安全设置里的关键词是否就是 '{KEYWORD}'", file=sys.stderr)
                return False
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print(f"[ERROR] HTTP {e.code}: {err_body}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[ERROR] 网络异常: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD,
                        help=f"涨跌告警阈值(百分比),默认 {DEFAULT_THRESHOLD}")
    parser.add_argument("--force", action="store_true",
                        help="强制发送告警(用于测试,即使没异动也发)")
    parser.add_argument("--debug", action="store_true",
                        help="打印请求 body 和响应,便于排查")
    args = parser.parse_args()

    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL", "").strip()
    if not webhook_url:
        print("[ERROR] 缺少环境变量 FEISHU_WEBHOOK_URL", file=sys.stderr)
        sys.exit(1)

    if not webhook_url.startswith("https://open.feishu.cn/open-apis/bot/"):
        print(f"[WARN] FEISHU_WEBHOOK_URL 看起来不像标准飞书 webhook 地址,继续尝试...", file=sys.stderr)

    dashboard_url = os.environ.get("DASHBOARD_URL", DEFAULT_DASHBOARD_URL).strip()

    manifest = load_manifest()
    commodities = manifest.get("commodities", [])

    if not commodities:
        print("[OK] manifest 中无品种,跳过告警")
        sys.exit(0)

    alerts = []
    for c in commodities:
        result = classify_commodity(c, args.threshold)
        if result:
            level, reason = result
            alerts.append((c, level, reason))

    if not alerts and not args.force:
        print(f"[OK] 无品种触发告警(阈值 {args.threshold}%),不发送飞书")
        sys.exit(0)

    if args.force and not alerts:
        # 测试模式:即使没异动也构造测试数据强制发送
        alerts = [(c, "minor", "测试模式") for c in commodities[:3]]
        print("[INFO] 测试模式: 强制构造告警")

    print(f"[INFO] 触发 {len(alerts)} 条告警,准备发送...")
    card = build_card(alerts, manifest, dashboard_url)

    ok = send_to_feishu(webhook_url, card, debug=args.debug)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
