# 一键给 Claude Code 的指令

直接把这段话整段复制粘贴给你的本地 Claude Code,它会自动完成所有部署工作:

```
请把附件中的两个文件加入项目并完成部署:

1. notify_feishu.py 放到 scraper/ 目录(如果项目根目录有 scraper/ 就直接放进去)
2. docs-07-feishu-alerts.md 重命名为 07-feishu-alerts.md 放到 docs/ 目录

然后:
- 编辑 ROUTINE_INSTRUCTIONS.md,在末尾追加一节"飞书告警推送",说明:
  完成 git push 后调用 python scraper/notify_feishu.py
  失败不影响整体流程
  在执行摘要中报告飞书状态
- 编辑 CLAUDE.md,在"关键文件"表格里加一行:
  scraper/notify_feishu.py | 飞书告警脚本(从 manifest.json 读异动)
- 编辑 README.md,在"快速开始"表格末尾加一行:
  7. 配置飞书告警(可选) | docs/07-feishu-alerts.md
- commit 信息: "feat: 添加飞书告警推送"
- push 到 main

完成后告诉我我需要去 Routine 后台手动配置的 3 件事:
1. 环境变量名
2. 网络白名单域名
3. 给 Routine Prompt 追加的内容(直接给我可复制的文字)
```

它会:
1. 把 notify_feishu.py 放对位置
2. 把文档放进 docs/
3. 改 README/CLAUDE/ROUTINE_INSTRUCTIONS 三份说明
4. commit + push
5. 最后给你一份 Routine 后台需要手动配的清单

你按那份清单去 Routine 设置里改完,就全部跑通了。
