# Pinterest Standard Access 申请材料（复制粘贴用）

申请入口：https://developers.pinterest.com/ → My apps → 选中你的 app → 「Request standard access」（有的界面叫 Upgrade / Trial access banner 里的链接）

审核通常 1–5 个工作日。申请时需要填的内容如下，直接复制：

## App / Use case description (English)

```
We operate thewooffy.com, a dog breed education blog (650+ in-depth breed guides)
built on Shopify. This app publishes our own original blog content as Pins to our
own Pinterest business account (@thewooffy) on a scheduled cadence.

Use case: automated content publishing for our own account only.
- Create Pins linking back to our own articles on thewooffy.com
- Organize Pins into our own boards (breed guides, grooming, costs, health)
- Read basic Pin/board data to avoid duplicates and track what has been posted

We do not access any third-party user data, do not act on behalf of other users,
and do not offer this app to anyone else. Single-account, first-party automation.

Scopes needed: boards:read, boards:write, pins:read, pins:write, user_accounts:read
```

## 常见追加问题

- **How many users will use this app?** → `1 (our own business account only)`
- **Will you store user data?** → `Only our own account's pin/board IDs, stored locally for deduplication.`
- **Demo / screencast** → 如果要求演示，说明是 server-side script（无 UI），附上 GitHub repo 或脚本说明即可。

## 批准之后

1. 无需改代码——`scripts/pinterest_api.py` 直接可用。
2. 跑：`py scripts/pinterest_api.py publish --batch=5`
3. 之后可加 GitHub Actions cron 每天自动发 5 个（参考 publish.yml 的模式）。

## 当前状态（2026-07-11）

- 40 个 pin 文案全部就绪（`scripts/pinterest_pin_copy.py` PIN_CONFIGS）
- 8 个目标 board 已在正式账号创建，ID 存于 `pinterest-boards.json`（已验证真实存在）
- OAuth 凭证有效（.env），token 刷新逻辑已测通（GET /boards 返回 200）
- 唯一阻塞：app 为 Trial access，POST /pins 返回 403 code 29
- 已发布：0 / 40
