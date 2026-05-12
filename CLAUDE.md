# 项目上下文（本地 Claude Code 用）

> 这份文件是你在本地用 Claude Code 改这个项目时给它看的。Routine 在云端运行时看的是 `ROUTINE_INSTRUCTIONS.md`，别混。

## 项目目标

通过 Claude Code Routine 每天云端抓取黑色系大宗商品价格，把数据 commit 进 GitHub 仓库的 data/ 目录，前端 ECharts 看板从 raw.githubusercontent.com 直接读取。

## 关键文件

| 文件 | 角色 |
|---|---|
| `scraper/fetch.py` | 单文件抓取脚本，是 Routine 调用的核心 |
| `config.yaml` | 监控品种列表 |
| `data/manifest.json` | 全局索引（前端入口） |
| `data/{code}/{YYYY-MM}.json` | 每品种每月一个文件 |
| `web/index.html` 或根目录 `index.html` | ECharts 看板 |
| `ROUTINE_INSTRUCTIONS.md` | 云端 Routine 跑时的指南 |
| `docs/01..06-*.md` | 用户分步教程 |

## 设计决策（不要改）

1. **数据存进 Git 本身**：Routine 是无状态云会话，不能假设外部数据库。Git 历史 = 时序记录 = 免费云存储。
2. **按品种/月份分片 JSON**：单文件不超过 30 行（一个月交易日），diff 友好。
3. **幂等写入**：今天重跑覆盖今天的记录，不重复 append。
4. **单文件 fetch.py**：不做 OOP 拆分。Routine 调试看 1 个文件比看 5 个文件快。
5. **前端纯静态**：不需要后端 API，部署到 GitHub Pages 就完事。
6. **告警逻辑写在 Routine Prompt 里**：不要塞进 fetch.py。Prompt 改起来比代码改起来灵活。

## 本地开发流程

```bash
# 装依赖
pip install -r requirements.txt

# 试跑
python scraper/fetch.py

# 本地预览前端
cd web && python -m http.server 8000
# 或者根目录有 index.html 时
python -m http.server 8000
```

## 常见任务的 prompt 模板

**加新品种**
> 阅读 config.yaml 和 scraper/fetch.py。
> 帮我加上 [品种名]，新浪连续合约代码是 [代号]，交易所是 [shfe/dce/czce]。
> 验证 fetch 函数能正确处理它。

**修 akshare 接口报错**
> 阅读 scraper/fetch.py，根据下面这个错误修复：
> [粘贴报错]
> 注意保持 retry 装饰器和异常处理逻辑不变。

**给前端加图表**
> 阅读 web/index.html。
> 帮我新增一个图表展示"基差走势 vs 价格走势"的散点图，
> 看是否存在均值回归现象。用 ECharts 5。

**优化数据存储**
> 阅读 data/ 目录的文件结构和 fetch.py 的 upsert_record 函数。
> 帮我增加一个 archive 功能：超过 2 年的月文件自动 gzip 压缩。
> 但要保证 manifest.json 能继续被前端正常读取。

## 不要做的事

- ❌ 引入数据库（违背"数据 = Git"的核心设计）
- ❌ 把 fetch.py 拆成多个文件（Routine 调试体验变差）
- ❌ 在 fetch.py 里写复杂日志框架（print 就够，Routine 会捕获 stdout）
- ❌ 给数据文件加压缩或二进制格式（破坏 git diff）
- ❌ 把 API key 硬编码（这个项目不需要 key）
