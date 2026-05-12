# Step 6：日常运维

项目已经在自动运行了。这份文档讲：怎么知道它有没有出问题、怎么改、怎么扩展。

---

## 怎么知道今天抓没抓成功

**方式 1：看仓库 commits**

每天 16:00-16:10 应该会看到一条新 commit。如果某天没有 commit，多半是出问题了。

**方式 2：看 Routines 控制台**

[claude.ai/code/routines](https://claude.ai/code/routines) → 点开 Routine → 看 "Past runs" 列表。
- 绿点 = Session 跑完了（不代表任务成功）
- 红点 = Session 报错

点进任意一个 Run 看 transcript 确认。

**方式 3：看看板**

打开 GitHub Pages 看板，"最近更新"字段就是 manifest.json 里的 `last_updated`。如果不是今天，说明今天没更新成功。

---

## 加新品种

编辑 `config.yaml`，加一个条目：

```yaml
- code: AU                    # 主力代号
  symbol_sina: AU0            # 新浪连续合约代码
  name_cn: 沪金
  spot_name: 黄金              # 生意社的命名
  exchange: shfe
  category: 贵金属
```

提交：

```bash
git add config.yaml
git commit -m "add gold"
git push
```

下一次 Routine 跑就会带上这个新品种。

> 想知道某个品种在 akshare 里叫什么代码？[查 akshare 的合约代号表](https://akshare.akfamily.xyz/data/futures/futures.html#id7)。

---

## 加价格告警

修改 Routine 的 Prompt（不是 fetch.py 的代码——告警逻辑由 Claude 在 Routine 里自己判断更灵活）：

1. 在 [claude.ai/code/routines](https://claude.ai/code/routines) 点编辑 Routine
2. 在 Prompt 最后加几段：

```
抓取完成后，请检查 data/manifest.json：
- 如果有任何品种当日跌幅超过 3%，调用 Slack connector 在 #alerts 频道发消息
- 消息格式：「[品种名] 跌幅 X%，当前价 Y，请注意」
```

3. 在 **Connectors** 里勾上 Slack（如果没连过先去 Settings → Connectors 连接）
4. 保存

下一次 Routine 跑完会自动判断并通知。

---

## 加更多数据维度

比如想加"钢厂高炉开工率"：

1. 用 Claude Code 帮你在 `scraper/fetch.py` 里加一个新函数：
   ```bash
   claude
   > 阅读 CLAUDE.md 和 scraper/fetch.py。
   > 帮我新增一个函数 fetch_blast_furnace_rate()，
   > 使用 akshare 的 ak.futures_inventory_em() 或类似接口拿钢厂高炉开工率，
   > 写入 data/inventory/{YYYY-MM}.json
   ```

2. 让 Claude 顺手在前端 `web/index.html`（或根目录 `index.html`）加一个图表展示

3. push 完事

---

## 改抓取频率

**想从每天改成每小时（盘中行情）**

注意：盘中行情用 Routine 跑成本会显著上升（Pro 每天 5 次额度可能不够）。建议：
- 日终归档继续用 Routine
- 盘中实时用本地脚本 + cron（重新加上之前的 APScheduler 方案）

**改 cron 表达式**

在 CLI 用 `/schedule update` 命令，或者在 web UI 编辑 trigger。注意最小间隔是 1 小时。

---

## 改前端样式

`web/index.html`（或根目录 `index.html`）是单文件，包含全部 HTML/CSS/JS。

直接用 Claude Code 改：

```bash
claude
> 阅读 index.html，把暗色主题改成浅色主题，按钮风格用 Tailwind 那种
```

改完 push，GitHub Pages 1 分钟内重新部署。

---

## 数据归档

`data/{品种}/{YYYY-MM}.json` 是按月分文件的，所以单个文件不会无限长大。

按月一个 30 行的 JSON 文件，单个品种一年大约 12 个文件，7 个品种总共一年 84 个文件——对 Git 来说完全没压力。

可以放心跑几年。

---

## 删掉重建

如果想重置：

```bash
rm -rf data/
git rm -r data/
mkdir data
echo '{}' > data/manifest.json
git add data/
git commit -m "reset data"
git push
```

下次 Routine 跑会重新建立。

---

## 完了

你现在拥有了一套全自动的大宗物资监控系统：

- 你电脑可以关机
- 你出差度假，数据照样更新
- 你想给同事看，发 GitHub Pages 链接就行
- 你想加品种、加告警、改图表，都是改文本文件 push

有任何具体问题，把现象贴给 Claude Code，它知道整个项目结构（因为我们写了 CLAUDE.md）。
