# Step 1：准备账号和仓库

完成本步骤大约需要 5 分钟。

## 你需要的三样东西

### 1. Claude Pro 账号（或更高）

打开 [claude.ai/settings/billing](https://claude.ai/settings/billing) 检查你的套餐：

- Free → **不行**，Routine 是付费功能
- Pro → 可以，每天 5 次 Routine
- Max → 可以，每天 15 次
- Team / Enterprise → 可以（但管理员可能关闭了 Routine 功能）

对这个项目，**Pro 完全够用**（每天只跑 1 次抓取）。

### 2. GitHub 账号

如果还没有，去 [github.com](https://github.com) 注册一个。

### 3. 本地装好 Git 和 Python

```bash
git --version    # 应该看到 git version 2.x
python3 --version  # 应该看到 Python 3.10+
```

如果没有：
- Mac：`brew install git python@3.11`
- Windows：装 [Git for Windows](https://git-scm.com/download/win) 和 [Python](https://www.python.org/downloads/)
- Ubuntu：`sudo apt install git python3 python3-pip`

> 注意：Python 只是用来本地**测试**抓取脚本能不能跑通。Routine 在云端跑的时候不需要你的本地 Python 环境。

---

## 创建一个空的 GitHub 仓库

1. 登录 GitHub，点右上角 **+** → **New repository**
2. 仓库名建议：`commodity-monitor`
3. 描述：随意，比如"黑色系大宗物资价格监控"
4. 可见性：
   - **Public**（推荐）：可以免费用 GitHub Pages
   - **Private** 也行，但 GitHub Pages 在 Pro 账号才能用于私有仓库
5. **不要**勾选 "Initialize this repository with a README"——我们要从本地推上去
6. 点 **Create repository**

记下仓库地址，形如：
```
https://github.com/你的用户名/commodity-monitor.git
```

下一步会用到。

---

## 进入下一步

[➡️ Step 2：把项目代码推到 GitHub](02-push-to-github.md)
