# Step 2：把项目推到 GitHub

完成本步骤大约需要 5 分钟。

## 操作

```bash
# 1. 解压项目到本地
unzip commodity-monitor.zip
cd commodity-monitor

# 2. 初始化 Git
git init
git branch -M main
git add .
git commit -m "init commodity monitor"

# 3. 关联远程仓库（把 YOUR_USERNAME 改成你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/commodity-monitor.git
git push -u origin main
```

## 如果 push 时报认证错误

GitHub 现在不再接受密码，必须用 Personal Access Token：

1. 打开 [github.com/settings/tokens](https://github.com/settings/tokens)
2. **Generate new token** → **Generate new token (classic)**
3. Note 填 `commodity-monitor`
4. Expiration 选 90 天或更长
5. 勾选 `repo` 这一整组权限
6. 生成后复制 token
7. 重新 push 时，用户名填你的 GitHub 用户名，密码处粘贴这个 token

或者用 SSH（更省事）：
```bash
git remote set-url origin git@github.com:YOUR_USERNAME/commodity-monitor.git
```
（需要先在 GitHub Settings → SSH keys 加入你的公钥）

---

## 本地先跑通一次（可选但强烈推荐）

在让 Routine 跑之前，先在本地验证抓取脚本能正常工作：

```bash
# 装依赖
pip install -r requirements.txt

# 跑一次
python scraper/fetch.py
```

期望看到类似输出：

```
========== 2026-05-12 抓取开始 ==========
2026-05-12 14:23:01 [INFO] 现货基差数据加载成功，含 ~30 个商品
2026-05-12 14:23:02 [INFO] [螺纹钢] OK close=3612.0
2026-05-12 14:23:03 [INFO] [热轧卷板] OK close=3720.0
...
========== 执行摘要 2026-05-12 ==========
  ✓ 螺纹钢    收盘     3612    -0.45%  现货3580 基差-32
  ✓ 热轧卷板  收盘     3720    -0.32%  现货3690 基差-30
  ...
```

然后检查 `data/` 目录有没有新文件：

```bash
ls data/
# 应该看到 manifest.json 和各品种子目录（RB, HC, I, J, JM, SF, SM）

cat data/manifest.json
# 应该看到 commodities 数组里有数据
```

如果都正常，**记得把生成的数据也 push 上去**：

```bash
git add data/
git commit -m "data: 首次本地抓取"
git push
```

这样云端 Routine 第一次跑的时候就有了基线，不会显得很空。

---

## 出问题怎么办

**akshare 安装慢**
- 用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`

**akshare 接口返回 403/超时**
- 大概率是网络问题，换个网络再试
- 也可能是 akshare 版本太老，升级：`pip install --upgrade akshare`

**没有任何数据被抓到**
- 看看 stderr 里的具体错误。如果是某个具体品种失败，问题不大；如果是全部失败，可能是 akshare 接口字段又变了，把报错完整贴给 Claude Code 让它修

---

## 进入下一步

[➡️ Step 3：创建 Claude Code Routine](03-create-routine.md)
