# Step 4：手动跑一次验证

不要等到明天 16:00 才看到底有没有跑通——现在就手动触发一次。

---

## 操作

1. 在 [claude.ai/code/routines](https://claude.ai/code/routines) 点开你刚创建的 Routine
2. 右上角点 **Run now**
3. 等 1-2 秒会出现一个 Session 链接，点进去看执行过程

---

## 验证清单

进入 Session 后，你应该按顺序看到 Claude 执行以下动作：

| 阶段 | 预期看到 |
|---|---|
| 启动 | "Cloning repository commodity-monitor..." |
| 准备 | "Reading ROUTINE_INSTRUCTIONS.md..." |
| 装依赖 | `pip install -r requirements.txt`（akshare、pandas 等被下载） |
| 抓数据 | `python scraper/fetch.py`，输出每个品种的进度日志 |
| 摘要 | 最后输出"执行摘要"表格，列出每个品种的最新价 |
| 提交 | `git add data/` → `git commit` → `git push origin main` |
| 结束 | "Session completed" |

如果你看到 Claude 自己写了一段总结回复你，类似：

> 已完成今日黑色系价格抓取。本次成功获取 7 个品种数据，已 commit 至 main 分支（commit hash: abc1234）。详情：
> - 螺纹钢 3,612（-0.45%）
> - 热轧卷板 3,720（-0.32%）
> - ……

那就**完全成功了**。

---

## 检查 GitHub 仓库

打开你的仓库页面：
```
https://github.com/YOUR_USERNAME/commodity-monitor
```

应该能看到：
- 有一条新的 commit，message 形如 `data: 2026-05-12 黑色系日更`
- `data/manifest.json` 已经被更新（last_updated 是今天）
- `data/RB/2026-05.json`、`data/HC/2026-05.json` 等文件出现了

点进任意一个月份文件，你会看到 JSON 数据，类似：

```json
[
  {
    "trade_date": "2026-05-12",
    "open": 3625,
    "high": 3640,
    "low": 3601,
    "close": 3612,
    "volume": 1234567,
    "open_interest": 2345678,
    "spot": 3580,
    "basis": -32,
    "symbol_sina": "RB0",
    "name_cn": "螺纹钢",
    "exchange": "shfe"
  }
]
```

---

## 出问题怎么办

### Session 显示绿色但实际啥也没干

绿色只代表 Session 没有基础设施错误，不代表任务成功。**一定要点进去看 transcript**。

### akshare 安装失败

看错误：
- `Could not find a version`：网络问题，多半是包管理器域名没在白名单。检查环境配置里勾了 "include default list of common package managers" 没。
- `Connection timeout`：偶发网络抖动，再 Run now 一次。

### akshare 接口报错 `403 host_not_allowed`

环境网络白名单漏了某个域名。看 transcript 里报错具体是哪个域名，把它加进 Allowed domains 后重新 Run now。

最常见的漏掉的：
- `quotes.sina.cn`
- `vip.stock.finance.sina.com.cn`
- 各种 akshare 内部用的数据接口域名

### git push 失败

- `Permission denied`：Routine 没拿到 push 权限。回 Step 3 检查"Allow unrestricted branch pushes"勾了没。
- `Updates were rejected`：仓库有了新 commit 但 Routine 没拉最新。在 Prompt 里加一句 "如果 push 失败，先 git pull --rebase 再 push"。

### 抓到的数据全是 null

akshare 接口字段可能变了。把 transcript 里的具体错误贴给 Claude Code，让它修 `scraper/fetch.py`：

```bash
# 本地
claude
> 阅读 scraper/fetch.py，根据下面这个错误修复字段名问题：
> [粘贴错误信息]
```

修完 push，下次 Routine 就自动用新代码了。

---

## 进入下一步

[➡️ Step 5：发布 GitHub Pages 看板](05-publish-pages.md)
