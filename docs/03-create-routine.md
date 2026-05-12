# Step 3：创建 Claude Code Routine

这是整个项目的核心。完成本步骤大约需要 10 分钟。

---

## 打开 Routines 控制台

浏览器访问：[claude.ai/code/routines](https://claude.ai/code/routines)

如果你是第一次用，可能会先看到引导页。按提示完成"Connect to GitHub"——这一步会让 Claude Code 拿到访问你 GitHub 仓库的权限。

完成后点 **New routine**，进入创建表单。

---

## 表单字段填写

### Name（名字）

```
黑色系价格日更
```

### Prompt（提示词）—— 关键

把下面这段完整复制粘贴进 Prompt 输入框：

```
你的任务是抓取今日黑色系大宗物资价格数据，并 commit 推回仓库。

详细操作步骤请阅读仓库根目录的 ROUTINE_INSTRUCTIONS.md，严格按里面的流程执行。

简要流程：
1. 安装 requirements.txt 中的依赖
2. 运行 python scraper/fetch.py（这会更新 data/ 目录下的 JSON 文件）
3. 用 git 把 data/ 的变更 commit 并 push 到 main 分支
4. 输出一份简短的执行摘要（哪些品种成功、各自最新价、是否有异常）

遇到 akshare 接口报错时：
- 单个品种失败不要影响其他品种
- 网络抖动可重试 2-3 次
- 如果所有品种都失败，把错误信息写进 commit message 但仍然要 push

不要修改 fetch.py 的核心逻辑（除非你确认是 bug 并在 commit message 里说明）。
```

### Repository（仓库）

从下拉选择你刚才推上去的 `commodity-monitor` 仓库。

### Environment（环境）—— 必须改

默认环境的网络白名单不包括 akshare 用的数据源，必须改：

1. 点环境选择器旁边的设置图标
2. 选 **Custom** 环境（或者编辑 Default）
3. **Network access** 改为 **Custom**
4. **Allowed domains** 添加以下域名（一行一个）：
   ```
   *.sinajs.cn
   hq.sinajs.cn
   *.sina.com.cn
   finance.sina.com.cn
   stock2.finance.sina.com.cn
   *.100ppi.com
   www.100ppi.com
   *.qhwang.com.cn
   stock.qhwang.com.cn
   *.akshare.xyz
   ```
5. 勾上 **Also include default list of common package managers**（这样 pip 还能正常工作）
6. 保存

> 提示：如果之后跑起来某个域名被拦截了，Session 日志里会显示 `403 host_not_allowed: xxx.com`，回来把那个域名加进白名单就行。

### Trigger（触发器）

选 **Schedule** → **Daily**，时间设置为 **16:00**（你的本地时区，工作日下午4点黑色系收盘后）。

> 如果想精确控制（比如只在周一到周五），先这样设置，保存后再用 CLI 命令 `/schedule update` 改成自定义 cron 表达式 `0 16 * * 1-5`。

### Connectors（连接器）

这个项目用不到（不发邮件、不通知 Slack），把默认勾选的连接器全部**取消**，减少安全暴露面。

### Permissions（权限）

勾选 **Allow unrestricted branch pushes**。

> 为什么：默认 Routine 只能推到 `claude/*` 前缀的分支，需要你手动 merge。我们想让它直接推 main，前端才能马上读到。

---

## 点 Create

创建完成会回到 Routines 列表，能看到你这个 Routine 显示 "Daily at 16:00" 和下一次运行时间。

---

## 出问题怎么办

**找不到 Routines 入口**
- 确认账号是 Pro/Max/Team/Enterprise
- 如果是 Team/Enterprise 但访问被拒：让管理员去 [claude.ai/admin-settings/claude-code](https://claude.ai/admin-settings/claude-code) 启用 Routines

**Repository 下拉没有我的仓库**
- 在 CLI 跑 `/web-setup`，或者在 Routines 页面找 "Connect more repositories"
- 如果是私有仓库，GitHub App 安装时需要授权给那个仓库

**Network access 找不到 Custom 选项**
- 你可能在编辑 Default 环境而没有新建自己的——Default 改不了，需要先点 "Create new environment"

---

## 进入下一步

[➡️ Step 4：手动跑一次验证](04-verify-routine.md)
