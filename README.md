# 黑色系大宗物资价格监控系统

一个零本地资源、零部署成本的大宗物资监控看板。

- 数据采集：Claude Code Routine 在云端每天自动跑（你电脑可以关机）
- 数据存储：直接 commit 进 GitHub 仓库的 `data/` 目录
- 数据展示：纯静态 HTML + ECharts，挂 GitHub Pages

监控品种：螺纹钢、热轧卷板、铁矿石、焦炭、焦煤、硅铁、锰硅

---

## 三句话搞懂工作原理

1. Claude Code Routine 每天下午 16:00（北京时间）在 Anthropic 云端启动一个会话
2. 这个会话克隆你的 GitHub 仓库，运行 `scraper/fetch.py` 抓数据，把结果写进 `data/` 目录，commit 后推回 GitHub
3. 任何人打开 GitHub Pages 上的网页，浏览器直接从 GitHub 拉数据，用 ECharts 画图

**没有服务器，没有数据库，没有定时任务管理工具。**

---

## 快速开始

按文档顺序看，从前到后做一遍就完事：

| 步骤 | 文档 |
|---|---|
| 1. 准备账号和仓库 | [docs/01-prerequisites.md](docs/01-prerequisites.md) |
| 2. 推代码到 GitHub | [docs/02-push-to-github.md](docs/02-push-to-github.md) |
| 3. 创建 Claude Code Routine | [docs/03-create-routine.md](docs/03-create-routine.md) |
| 4. 验证抓取成功 | [docs/04-verify-routine.md](docs/04-verify-routine.md) |
| 5. 开启 GitHub Pages | [docs/05-publish-pages.md](docs/05-publish-pages.md) |
| 6. 日常运维 | [docs/06-operations.md](docs/06-operations.md) |

每一步都有截图位置说明、命令、和"出问题怎么办"。

---

## 目录结构

```
commodity-monitor/
├── README.md                       入口文档（本文件）
├── ROUTINE_INSTRUCTIONS.md         给云端 Claude 的执行手册（核心）
├── CLAUDE.md                       本地 Claude Code 开发时的项目上下文
├── requirements.txt                Python 依赖
├── config.yaml                     监控品种配置
├── .gitignore
├── scraper/
│   ├── __init__.py
│   └── fetch.py                    单文件抓取脚本
├── data/
│   ├── manifest.json               全局索引（前端从这里开始读）
│   └── {品种}/{年-月}.json          每个品种每月一个文件
├── web/
│   ├── index.html                  ECharts 看板
│   └── config.js                   前端配置（数据源 URL）
└── docs/                           分步教程
    ├── 01-prerequisites.md
    ├── 02-push-to-github.md
    ├── 03-create-routine.md
    ├── 04-verify-routine.md
    ├── 05-publish-pages.md
    └── 06-operations.md
```

---

## 成本说明

| 项 | 成本 |
|---|---|
| GitHub 公开仓库 + GitHub Pages | 免费 |
| 数据源（akshare 调用的新浪/生意社等公开接口） | 免费 |
| Claude Pro 套餐 | 已付费的话，每天 1 次 Routine 占用约 20% 额度 |
| 本地电脑 | 完全不需要保持开机 |

**唯一前提：Claude Pro 及以上账号**（Routine 是 Pro/Max/Team/Enterprise 才有的功能）。
