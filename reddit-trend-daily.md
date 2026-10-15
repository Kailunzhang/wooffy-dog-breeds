# Wooffy 每日热点文章（Reddit 选题 → 自动写作 → 自动发布）

> 2026-10-12 起的策略：Reddit 不再当发帖阵地（`reddit-plan.md` 已作废），改为**每日选题源**。每天早上 6:30（太平洋时间）GitHub Actions 读 7 个狗板块当天最热的帖子，让 Claude 选 1 个站上还没有的常青话题，写一篇 1,500–2,200 词的指南，配图，发布到博客，然后给你发一封邮件。

## 每天发生什么

| 步骤 | 做什么 | 失败时 |
|---|---|---|
| 1 抓取 | 读 r/dogs、r/puppy101、r/DogAdvice、r/Dogtraining、r/OpenDogTraining、r/reactivedogs、r/DogFood 的公开 Atom feed（`/top/.rss?t=day`）。Reddit 对匿名请求限 **1 次/分钟**，所以每个板块间隔 65 秒，整步约 7 分钟 | 单个板块失败不影响其他；全部失败则邮件说"无选题" |
| 2 预筛 | 纯 Python：只留有正文的文字帖，去掉 megathread、安乐死/去世、走失/捡到、送养、众筹、调查、卖东西，去掉之前看过的帖子 | 没有候选 → 邮件"无选题"，不写文章 |
| 3 选题 | Claude 看候选标题+摘要、站上全部 slug、最近 60 天已发的热点题，提 3 个常青指南题（slug、角度、簇、是否 YMYL、来源帖 id）；取第一个 slug 不重复的 | 都重复 → "无选题" |
| 4 写作 | Claude 按站内 hub 式结构（intro / care / special + 6–7 FAQ）写 JSON；内链只能从真实 slug 里选，由 `wooffy_links` 渲染 | — |
| 5 校验 | 字数 1,300–2,600、三段齐全、FAQ ≥5、**不含电话号码**、不提 Reddit/论坛/用户名、不含剂量语言、内链 slug 必须存在 | 不过 → 自动改写一轮 |
| 6 审核 | 健康/营养/中毒类（YMYL）自动加一轮"兽医+训犬师"审稿：pass / fix / block | fix → 改写一轮；**block → 存为 published:false 草稿，不上线** |
| 7 配图 | fal.ai nano-banana-pro 生成 3:2 封面 → 上传 Shopify Files CDN | 没 FAL_KEY 或失败 → 用占位图，邮件标"需替换" |
| 8 发布 | 写 `breed-data/<slug>.json`，`generate.py <slug> --publish`；按簇选博客：营养→dog-nutrition，健康→dog-health，训练→dog-training，生活/用品/领养→life-with-dogs，犬种→dog-breeds；对应 secret 没配就退回 dog-breeds | 失败 → 邮件标 publish-failed，Actions 退出码 1 |
| 9 记录 | `reddit-trends-state.json` 记已选题和看过的帖子 id，连同新 JSON 提交回 main | — |
| 10 邮件 | 主题 `[Wooffy 热点] <日期> <状态>`，正文：选题、来源帖链接、审核意见、配图状态、发布 URL、怎么删 | 没配邮件 secret 就只打日志 |

成本：每篇约 3 次 Claude 调用（选题小、写作大、YMYL 审核中）+ 1 张 fal 图，估计 **$0.30–0.60/天**。

## 上线前你要做的 3 件事

1. **加 secret `FAL_KEY`**（否则每篇都是占位图）。值在你本机 `~/.claude.json` 的 `mcpServers.fal-ai.env.FAL_KEY`：
   ```bash
   gh secret set FAL_KEY --repo Kailunzhang/wooffy-dog-breeds
   ```
2. **（可选）加各博客 id**，不加就全发到 dog-breeds 博客。值在本地 `.env`：
   ```bash
   gh secret set SHOPIFY_LIFE_WITH_DOGS_BLOG_ID --repo Kailunzhang/wooffy-dog-breeds
   ```
   同样方式加 `SHOPIFY_DOG_HEALTH_BLOG_ID`、`SHOPIFY_DOG_TRAINING_BLOG_ID`。
3. **先手动跑一次 dry-run** 看效果再让定时跑：Actions → "Wooffy Reddit Trend Article" → Run workflow → dry_run = true。

## 怎么停、怎么删

- **暂停整条线**：Actions 页面 → 该 workflow → "Disable workflow"；或注释掉 yml 里的 `schedule:` 块。
- **删一篇**：Shopify 后台 → Blog posts → 搜 slug → Delete。再删掉 `breed-data/<slug>.json`（或把 `published` 改 false 并 `--update`），否则下次有人 `--all` 会重新发。
- **换板块/频率**：`scripts/reddit_trends/feeds.py` 的 `DEFAULT_SUBREDDITS`；cron 在 yml 里。
- **指定题目**：Run workflow 时填 topic，或本地 `python scripts/reddit_trends/run.py --topic "..." --cluster training`。

## 事故记录

- **2026-10-13/14 同题发了两篇**（`how-to-crate-train-a-puppy-and-stop-crying`、`how-to-crate-train-a-puppy-step-by-step`）。原因：`generate.py --publish` 发布后自动重写 ARTICLES.md/.xlsx，提交步骤的 `git pull --rebase` 因工作区有未暂存改动而退出 128，状态文件和文章 JSON 没进仓库，第二天不知道昨天选过什么。修复（10-14）：提交步骤连 ARTICLES.md/.xlsx 一起提交并用 `--autostash`；选题前额外向 Shopify 查最近 30 天已发文章的 handle 做去重，不再只信仓库状态。两篇文章的 JSON 不在仓库里，需从 Shopify 回填或删一篇。
- **Amazon 链接**：`scripts/inject_amazon_links.py` 只处理美容/清单/成本页、榜单页和目录里点名的 10 个 extra 页，而且是手动批量脚本，没有任何 workflow 调它；热点文章（size_category "Guide"、slug 无后缀）不在它的范围内。另外目录里按 2026-09-29 的决定没有狗笼，所以 crate 文章最相关的品类本来就不存在。要给热点文章挂链接需要两步：目录加一个 "guide" 页型（按 anchors 匹配通用品类：围栏、门栏、填食玩具、训练零食、嗅闻垫、尿垫、酶清洁剂等），再在 run.py 发布前调用注入器。

## 已知限制（诚实版）

- **GitHub Actions 的 IP 可能被 Reddit 拦**。我在你家网络验证了 RSS 能拿到（1 次/分钟），但云端 IP 没验证。第一次 dry-run 的邮件/日志会直接告诉你哪些板块失败；如果 7 个全失败，备选是注册一个 Reddit 应用走 OAuth（需要 Reddit 账号），我再接。
- **Reddit 数据只当信号**。文章不引用、不转述具体帖子，只用标题判断"大家在问什么"，避开 Reddit 数据条款和抄袭风险。
- **一天一篇，不是越多越好**。站上已有 875 篇，GSC 曝光高点击低（CTR 0.52%）；热点篇的价值在"抓到站上没有的常青问题"，不在数量。60 天后看这些篇的 GSC 点击再决定是否加到 2 篇/天。
- **AI 写作的老问题仍在**：事实靠模型，没有人工核。校验只能拦电话号码、剂量、Reddit 提及这类硬规则。YMYL 题有二审，但二审也是模型。邮件里有来源帖和草稿路径，建议前两周每天花 2 分钟扫一眼。
- 每篇文章 JSON 多一个 `source` 字段（来源帖 id、簇、角度），`generate.py` 不读它，只是留档。

## 文件

| 文件 | 作用 |
|---|---|
| `scripts/reddit_trends/feeds.py` | 抓取+解析 Atom，限速/429 重试 |
| `scripts/reddit_trends/selector.py` | 预筛、选题 prompt、解析 |
| `scripts/reddit_trends/writer.py` | 写作/审核/改写 prompt，硬规则校验，拼装 breed-data JSON |
| `scripts/reddit_trends/hero.py` | fal.ai 配图 + CDN 上传，占位图回退 |
| `scripts/reddit_trends/run.py` | 编排、状态、发布、邮件；`--dry-run --no-hero --topic --review` |
| `scripts/reddit_trends/tests/` | 26 个 pytest：`uv run --python 3.12 --with requests --with pytest python -m pytest scripts/reddit_trends` |
| `.github/workflows/reddit-trend-daily.yml` | 每天 13:30 UTC（内容见下方附录） |
| `reddit-trends-state.json` | 已选题 + 看过的帖子 id（由 workflow 提交） |

## 附录：workflow 文件内容

保存为 `.github/workflows/reddit-trend-daily.yml`：

```yaml
name: Wooffy Reddit Trend Article

# Daily: read top posts of the dog subreddits (public Atom feeds, ~1 req/min,
# so the fetch step takes ~7 min), let Claude pick ONE evergreen topic the
# site lacks, write it, hero via fal.ai, publish via scripts/generate.py,
# email a summary. Design + kill switch: reddit-trend-daily.md
# Runs 13:30 UTC (06:30 PT), before the 16:00 UTC breed publisher.

on:
  schedule:
    - cron: '30 13 * * *'
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'true = write the draft JSON only, do not publish'
        required: false
        default: 'false'
      topic:
        description: 'Optional topic override (skips Reddit)'
        required: false
        default: ''

permissions:
  contents: write

concurrency:
  group: reddit-trend-article
  cancel-in-progress: false

jobs:
  trend-article:
    runs-on: ubuntu-latest
    timeout-minutes: 40
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests

      - name: Create .env
        run: |
          printf 'SHOPIFY_STORE=%s\nSHOPIFY_TOKEN=%s\nSHOPIFY_BLOG_ID=%s\nSHOPIFY_DOG_NUTRITION_BLOG_ID=%s\nSHOPIFY_LIFE_WITH_DOGS_BLOG_ID=%s\nSHOPIFY_DOG_HEALTH_BLOG_ID=%s\nSHOPIFY_DOG_TRAINING_BLOG_ID=%s\nANTHROPIC_API_KEY=%s\n' \
            "${{ secrets.SHOPIFY_STORE }}" \
            "${{ secrets.SHOPIFY_TOKEN }}" \
            "${{ secrets.SHOPIFY_BLOG_ID }}" \
            "${{ secrets.SHOPIFY_DOG_NUTRITION_BLOG_ID }}" \
            "${{ secrets.SHOPIFY_LIFE_WITH_DOGS_BLOG_ID }}" \
            "${{ secrets.SHOPIFY_DOG_HEALTH_BLOG_ID }}" \
            "${{ secrets.SHOPIFY_DOG_TRAINING_BLOG_ID }}" \
            "${{ secrets.ANTHROPIC_API_KEY }}" > .env

      - name: Run pipeline
        env:
          FAL_KEY: ${{ secrets.FAL_KEY }}
          GMAIL_USER: ${{ secrets.GMAIL_USER }}
          GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
          ALERT_EMAIL_TO: ${{ secrets.ALERT_EMAIL_TO }}
          DRY_RUN: ${{ github.event.inputs.dry_run }}
          TOPIC: ${{ github.event.inputs.topic }}
        run: |
          ARGS=()
          if [ "$DRY_RUN" = "true" ]; then ARGS+=(--dry-run); fi
          if [ -n "$TOPIC" ]; then ARGS+=(--topic "$TOPIC"); fi
          python3 scripts/reddit_trends/run.py "${ARGS[@]}"

      - name: Commit article JSON and state
        if: always()
        run: |
          git config user.name "wooffy-bot"
          git config user.email "wooffy-bot@users.noreply.github.com"
          # generate.py --publish regenerates ARTICLES.md/.xlsx; commit them too,
          # otherwise the dirty tree makes `git pull --rebase` exit 128 and the
          # state file is lost (which is how the same topic got published twice
          # on 2026-10-13 and 2026-10-14).
          git add reddit-trends-state.json breed-data/*.json ARTICLES.md ARTICLES.xlsx || true
          if git diff --cached --quiet; then
            echo "Nothing to commit"
          else
            git commit -m "chore: daily reddit-trend article $(date -u +%F) [skip ci]"
            git pull --rebase --autostash origin main
            git push origin HEAD:main
          fi
```
