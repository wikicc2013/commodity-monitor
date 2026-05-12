# 飞书告警接入指南

让 Routine 在抓取完成后,把异动品种推送到飞书群。整套接入约 10 分钟。

---

## 第 1 步:在飞书群里建机器人

1. 打开飞书,进入你想接收告警的群(建议建一个 `大宗物资监控` 专用群)
2. 群设置 → **群机器人** → **添加机器人**
3. 选 **自定义机器人**
4. 机器人名字填 `大宗监控`(或随意)
5. 设置安全选项:
   - 勾选 **自定义关键词**
   - 关键词填 `大宗`(必须填这两个字,告警脚本里写死了)
   - 其他安全选项(签名校验/IP 白名单)**不要**勾——会增加复杂度
6. 点完成,**复制 Webhook 地址**保存好

Webhook 长这样:
```
https://open.feishu.cn/open-apis/bot/v2/hook/abcdef12-3456-7890-abcd-ef1234567890
```

---

## 第 2 步:本地测试 webhook 通不通

打开终端跑:

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"大宗物资测试消息"}}' \
  你的Webhook地址
```

成功应该返回:
```json
{"code":0,"msg":"ok"}
```

飞书群里会收到一条消息。**如果没收到或返回错误,常见原因:**
- 消息文本里没有"大宗"两个字 → 关键词没匹配,飞书拒收
- Webhook URL 拼错了 → 检查复制有没有漏字符
- 返回 `19024` 错误 → 关键词配置错了,回机器人设置重新填

---

## 第 3 步:本地试跑告警脚本

确保 `notify_feishu.py` 在 `scraper/` 目录下,然后:

```bash
# 设置 webhook(只在当前终端有效)
export FEISHU_WEBHOOK_URL="你的Webhook地址"

# 强制发送一条测试告警(不管今天有没有异动)
python scraper/notify_feishu.py --force
```

飞书群里应该出现一张红色/黄色头部的卡片,包含品种列表和"查看完整看板"按钮。

**如果没收到**,看终端的错误输出。常见问题:
- `缺少环境变量` → export 没执行成功
- `manifest.json 不存在` → 当前目录不对,要在项目根目录跑
- `飞书返回错误` → webhook URL 或关键词问题

---

## 第 4 步:把 Webhook URL 配进 Routine 环境

去 [claude.ai/code/routines](https://claude.ai/code/routines) → 点你的 Routine → 编辑

### 4a. 加环境变量

找到 **Environment** 区,点击当前环境的设置图标,在 **Environment variables** 添加:

| Name | Value |
|---|---|
| `FEISHU_WEBHOOK_URL` | 你的完整 webhook URL |

### 4b. 加网络白名单

同一个环境配置页面,**Allowed domains** 添加:

```
open.feishu.cn
*.feishu.cn
```

保存环境配置。

---

## 第 5 步:在 Routine 的 Prompt 里调用告警

编辑 Routine 的 Instructions,**在末尾追加**这一段:

```

【告警推送】
完成 git push 后,执行以下命令推送飞书告警:

  python scraper/notify_feishu.py

这个脚本会:
- 读取 data/manifest.json
- 找出涨跌幅 >= 3% 的品种,以及抓取失败的品种
- 如果有异动,推送飞书卡片;如果没有,什么也不做
- 失败不影响整体流程

最后在执行摘要中加一行:
- "飞书告警: 已推送 X 条" 或 "飞书告警: 今日无异动"
```

保存 Routine。

---

## 第 6 步:Run now 验证整条链路

回 Routine 详情页 → **Run now** → 等 2-3 分钟跑完

进 Session 查看 transcript,应该能看到:
- 抓取数据 OK
- git push OK
- `python scraper/notify_feishu.py` 被执行
- 输出 `[OK] 飞书告警已发送` 或 `[OK] 无品种触发告警`

如果今天确实有异动(单日涨跌 3% 以上),飞书群会收到告警卡片。

---

## 第 7 步(可选):平时如何手动测试

每次想验证飞书链路是否还活着,本地跑:

```bash
export FEISHU_WEBHOOK_URL="你的Webhook"
python scraper/notify_feishu.py --force
```

强制发一条卡片。看到了就说明链路 OK。

---

## 调整告警敏感度

默认涨跌幅阈值是 3%。想改的话:

**方法 1:改 Prompt 里的调用命令**

```bash
python scraper/notify_feishu.py --threshold 2.0   # 改成 2%
python scraper/notify_feishu.py --threshold 5.0   # 改成 5%(更不容易触发)
```

**方法 2:改脚本里的常量 DEFAULT_THRESHOLD**

打开 `scraper/notify_feishu.py`,找到 `DEFAULT_THRESHOLD = 3.0`,改成你想要的数字。

---

## 故障排查

### 飞书没收到告警

按这个顺序排查:

1. **本地能不能跑通?**
   ```bash
   export FEISHU_WEBHOOK_URL="..."
   python scraper/notify_feishu.py --force
   ```
   不通 → 检查 webhook URL、关键词、网络。通了 → 进入 2。

2. **Routine 的 Session 有没有执行这条命令?**
   进 Session 看 transcript,搜 `notify_feishu`。
   没执行 → Prompt 里那段告警指令没生效,检查格式。

3. **Routine 执行了但报错?**
   看具体报错:
   - `host_not_allowed: open.feishu.cn` → 网络白名单没配
   - `缺少环境变量` → FEISHU_WEBHOOK_URL 没配进环境
   - `HTTP 19024` → 关键词没匹配,卡片标题里没"大宗"二字

### 卡片样式想自定义

打开 `scraper/notify_feishu.py`,找到 `build_card()` 函数。里面的 `template`(颜色)、`elements`(卡片内容)都可以改。

飞书卡片 JSON 完整文档:
https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/feishu-cards/card-json-structure

### 想 @ 群里的某人

在 `build_card()` 的 `summary_text` 里插入:

```python
summary_text = f'<at user_id="all"></at> 关注本次异动\n' + summary_text
```

`user_id="all"` 是 @所有人。@具体某人需要从飞书后台拿那个人的 user_id。

---

## 进阶玩法

**1. 多群分发**

主管群只接 5% 以上巨变,操盘群接 3% 以上正常异动:

- 建两个机器人,得到两个 webhook
- 加两个环境变量 `FEISHU_WEBHOOK_MAJOR` 和 `FEISHU_WEBHOOK_MINOR`
- 脚本里根据 level 选不同 webhook 发

**2. 不同品种发不同群**

钢材群只收钢材品种,炉料群只收炉料品种——按 `category` 字段过滤。

**3. 早盘提醒**

新建 Routine 2,每天早上 8:30 跑,读 manifest.json 把昨日收盘价整理一下推给晨会群。
