# Routine 执行手册

> 这份文件是给云端 Claude（Routine 跑的时候）看的。每次 Routine 启动时它都不记得上次的事，所以这份文件就是它的"操作系统"。

## 你的目标

抓取黑色系大宗商品当天价格 → 写进 data/ 目录 → commit push 回仓库。

## 步骤

```bash
# 1. 装依赖（云端环境会缓存，第二次跑很快）
pip install -r requirements.txt

# 2. 跑抓取
python scraper/fetch.py
```

## 抓取脚本做什么

`scraper/fetch.py` 读 `config.yaml`，对每个品种：
1. 拿当天的期货日 K 线（akshare `futures_zh_daily_sina`）
2. 拿当天的现货价 + 基差（akshare `futures_spot_price_previous`）
3. 把结果 **幂等** 写入 `data/{code}/{YYYY-MM}.json`（同日重跑会覆盖）
4. 更新 `data/manifest.json`（前端用它做索引）

## 异常处理原则

| 情况 | 怎么办 |
|---|---|
| akshare 403/超时 | 已有 retry，会自动重试 3 次 |
| 节假日 | 脚本会自己判断并退出，不会写空数据 |
| 某品种数据缺失 | 在 manifest 里标 `no_data`，不影响其他品种 |
| 全部失败 | 仍然 commit，commit message 写明失败原因 |

## Commit 规则

```bash
git config user.email "claude-routine@anthropic.com"
git config user.name "Claude Routine"
git add data/
git commit -m "data: $(date +%Y-%m-%d) 黑色系日更"
git push origin main
```

如果当天没有任何数据更新（比如节假日），**不要做空 commit**。

如果 git push 报 non-fast-forward（仓库有了新 commit），先：
```bash
git pull --rebase origin main
git push origin main
```

## 最后输出格式

执行完后，请用这个格式输出摘要给用户：

```
执行摘要 — 2026-05-12 16:03

✓ 螺纹钢 RB    3,612  (-0.45%)   现货 3,580  基差 -32
✓ 热轧卷板 HC  3,720  (-0.32%)   现货 3,690  基差 -30
✓ 铁矿石 I       742  (+1.23%)   现货  748  基差  +6
✓ 焦炭 J       1,580  (+0.82%)   ——
✗ 焦煤 JM      抓取失败：akshare 503 错误
✓ 硅铁 SF      6,420  (持平)    ——
✓ 锰硅 SM      6,180  (-1.05%)   ——

已 commit: abc1234  推送至 origin/main
```

## 不要做的事

- ❌ 修改 `scraper/fetch.py` 的核心逻辑（除非确认是 bug，并在 commit message 说明）
- ❌ 把抓不到数据的品种从 config.yaml 里删除
- ❌ 让单个品种的失败导致整个抓取退出
- ❌ 不 commit 直接结束（前端依赖最新的 manifest.json）
