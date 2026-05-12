# Step 5：发布 GitHub Pages 看板

Routine 已经在抓数据并写进仓库了。现在让所有人能在浏览器看到这些数据。

完成本步骤大约需要 3 分钟。

---

## 修改前端配置

打开 `web/config.js`，把里面的 `YOUR_USERNAME` 改成你的 GitHub 用户名：

```javascript
window.DASHBOARD_CONFIG = {
  dataBaseUrl: "https://raw.githubusercontent.com/YOUR_USERNAME/commodity-monitor/main/data",
  cacheBust: true,
};
```

提交：

```bash
git add web/config.js
git commit -m "set dashboard data url"
git push
```

---

## 开启 GitHub Pages

1. 浏览器打开仓库 → **Settings** → 左侧 **Pages**
2. **Build and deployment** 部分：
   - **Source**: 选 `Deploy from a branch`
   - **Branch**: 选 `main`，文件夹选 `/ (root)` —— 嗯？我们的网页在 `web/` 里啊。

有两种处理方式：

### 方式 A（推荐）：把 web 目录里的文件放到根目录

最直接，对 Pages 最友好：

```bash
git mv web/index.html ./index.html
git mv web/config.js ./config.js
rm -rf web
git commit -m "move web files to root for github pages"
git push
```

然后在 Pages 设置里 Branch 选 `main` + `/ (root)`。

### 方式 B：用 docs 文件夹

GitHub Pages 支持从 `/docs` 目录发布：

```bash
mv web docs-site
git add -A
git commit -m "rename web to docs-site"
git push
```

不行——我们的 `docs/` 已经放分步教程了。所以方式 A 更省事，**推荐用方式 A**。

---

## 等 1-2 分钟

GitHub Pages 第一次发布需要构建时间。你可以在仓库的 **Actions** 标签页看到一个 "pages build and deployment" workflow 在跑。

跑完后，访问你的看板：

```
https://YOUR_USERNAME.github.io/commodity-monitor/
```

---

## 期望看到

打开后应该立刻看到：

- 顶部一行 7 个品种的实时价格卡片（红跌绿涨）
- 中间一个 K 线图 + 一个基差图
- 下面一个多品种归一化对比图

点击不同品种卡片，K 线图和基差图会切换。

> 如果看到"数据加载失败"，最常见原因是 `config.js` 里的 URL 错了。检查：
> - 用户名拼写
> - 仓库名
> - 分支名（默认是 main 不是 master）
> - 仓库是 Public 的（raw.githubusercontent.com 只能读 Public 仓库或带 token 的请求）

---

## 私有仓库的处理

如果你的仓库是 Private 的，`raw.githubusercontent.com` 拒绝匿名访问，前端会 404。两条路：

**A. 改成 Public**（最简单，推荐）

**B. 把数据复制到 Pages 一起发布**

修改 `config.js`：
```javascript
dataBaseUrl: "./data",  // 相对路径，从 Pages 站点的同源读
```

然后让 Routine 不仅 push 数据，还把数据复制一份到根目录的 `data/`，让 Pages 一起部署。这种方式数据会被静态化部署，刷新有几秒延迟，但能 work。

---

## 进入下一步

[➡️ Step 6：日常运维](06-operations.md)
