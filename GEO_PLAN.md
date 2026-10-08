# Wooffy GEO 计划（Generative Engine Optimization）

**日期：** 2026-10-06
**目标：** 让 Wooffy 的内容被 AI 答案引擎（Google AI Overviews / AI Mode、ChatGPT Search、Perplexity、Copilot、Gemini）在回答狗狗品种、费用、美容、喂食问题时直接引用，并把这部分流量变成可衡量的渠道。
**周期：** 8 周（2026-10-06 → 2026-11-30），之后进入月度循环。

---

## 0. 现状盘点（基于仓库与线上主题实际检查）

| 项目 | 现状 | GEO 评价 |
|------|------|----------|
| 文章总量 | 855 篇，5 个 blog（dog-breeds 759 篇结构化 JSON；dog-nutrition / dog-health / dog-training / life-with-dogs 共 96 篇 `body_html`） | 规模是优势，深度是短板 |
| 结构化数据 | 线上主题 `Website v092026 (fixes 9-29)`：每篇文章一组 `@graph`（WebSite + BlogPosting + BreadcrumbList），Organization 单独输出并带 founder Person（Kailun Zhang / Mike）；`dateModified` 读 `custom.content_updated` metafield | 已达标，无需返工 |
| FAQPage schema | 759 篇品种文章由 `generate.py` 的 `build_faq()` 自动输出；96 篇 `body_html` 文章中约 90 篇已有 | 覆盖好 |
| Quick Answer（首段直接答案） | 96 篇 `body_html` 文章中 90 篇有；**759 篇品种文章中只有 1 篇**（portuguese-water-dog-grooming-guide） | **最大缺口** |
| 权威外链 / 引用来源 | 营养页有 Sources 区块；**759 篇品种文章中只有 30 篇**含 AKC / VCA / Merck 等来源 | 第二大缺口 |
| 可引用数据资产 | `costs-dataset.json` 已含 164 个品种的 `citable_stat`（一句带数字的可引用结论），但**没有任何脚本把它渲染到页面上** | 现成资产，零成本上线 |
| 小标题形式 | 主要是名词式（"Temperament"、"Care"），不是问句 | AI 引擎更容易匹配问句标题 |
| 关键数据展示 | 主指南的 stats 用 emoji 卡片 `div` 网格渲染 | `<table>` 比 div 网格更容易被抽取 |
| robots.txt | 线上主题没有 `templates/robots.txt.liquid`，走 Shopify 默认 → GPTBot、OAI-SearchBot、ClaudeBot、PerplexityBot、Google-Extended 均未被屏蔽 | 需在有外网的机器上确认一次线上实际内容 |
| llms.txt | 无 | 低优先级，但成本也低 |
| 作者实体 | Shopify 文章 author 已批量改为 Kailun Zhang；schema 指向 `/pages/about#mike` | 需确认 About 页真实存在且有完整介绍 |
| 度量 | 有 GA4 日报 + GSC 行动队列（`daily_digest.py`），**没有 AI 来源流量分段，也没有引用率追踪** | 先补基线 |
| 进行中的实验 | 164 篇费用页标题 A/B 测试（`seo-tests/cost-title-ab-2026-10`），读数窗口约 2026-10-29 | 费用页的标题/描述在读数前不能动 |

> 本次容器无法访问 thewooffy.com（出站代理拦截），所以线上 robots.txt、渲染后的页面、About 页需要在本机验证。见第 1 周清单。

---

## 1. GEO 的工作原理（指导所有改动的 6 条原则）

AI 答案引擎在生成回答时会检索网页、把页面切成段落、挑选最"像答案"的片段并给出引用。被选中的片段通常满足：

1. **前 40–80 词就是答案**，带具体数字、单位和范围（"$2,800–$5,400 first year"），不是铺垫。
2. **每个段落可独立成立**：一个小标题 + 一段话就能回答一个问题，不依赖上下文。
3. **问句标题**与用户真实提问同构（"How much does a Golden Retriever cost per year?"）。
4. **表格 / 列表**承载数据，比散文更容易被抽取和转述。
5. **可信来源**：页面引用 AKC、OFA、Merck 等权威，作者是可识别的真实实体，页面有可信的更新日期。
6. **可抓取**：文本在服务端 HTML 里（Shopify `body_html` 满足），AI 爬虫未被 robots 屏蔽。

Wooffy 的优势：原创数据（费用数据集、品种 stats）和真实第一人称经验（`mikes_take`）。这两者是竞品（AKC、PetMD、Rover）无法复制的，GEO 计划应围绕它们。

---

## 2. 工作流（Workstreams）

### W0 · 基线与度量（第 1 周，之后持续）

目的：先有尺子，再动内容。

1. **AI 来源流量分段**（GA4，已完成 2026-10-07）。`traffic_watch.py` 的日报原本已有 "AI 可见度" 区块；本次改为服务端按 `sessionSource` 正则过滤（小来源不再被 top-200 截掉）、分母改为 28 天全部会话、新增 "AI 引擎带来最多流量的页面"，来源表扩到 ChatGPT / Perplexity / Copilot / Gemini / Claude / Grok / Meta AI / Mistral / DeepSeek 等。新脚本 `scripts/geo_ai_referrals.py` 每天由 `daily-digest.yml` 在邮件之后运行，把 28 天 / 7 天总量、分引擎、落地页、日序列写进 `geo/ai-referrals.jsonl` 和 `geo/ai-referrals-latest.md` 并提交回仓库，这就是 KPI 的基线与趋势。Google AI Overviews / AI Mode 走 google.com referrer，无法分离，归在自然搜索里。
2. **引用率面板**（已完成 2026-10-08）。`geo/query_panel.json` 收录 60 条真实提问（费用 15、美容 10、适配性 15、喂食 10、榜单 10），每条带 `target` 指向应被引用的页面 slug。`scripts/geo_citation_audit.py` 用仓库已有的 `ANTHROPIC_API_KEY` 调 Claude + web search 工具逐条提问，记录引用的 URL、thewooffy.com 是否被引用、是否只是出现在搜索结果里没被引用、以及被引用的竞品域名。输出 `geo/citations/<日期>-claude.json`（可断点续跑）、`latest.md`、`history.jsonl`；`geo-citation-audit.yml` 每月 2 日自动跑并提交。引擎是插件式的，接 ChatGPT / Perplexity 只需加一个函数和对应 key。每次全量约 60 次搜索，几美元。Google AI Overviews 无 API，仍需每月人工抽 20 条记录。
3. **覆盖率审计**。`scripts/geo_audit.py`（已完成 2026-10-06）扫描 `breed-data/` 输出四个百分比：有 Quick Answer、有权威来源、小标题为问句、页面有可见更新日期，写 `geo_audit_report.md` 并在 `geo/audit-history.jsonl` 按日追加一行。每周跑一次作为进度指标；`--missing <signal> --type <type>` 列出待处理 slug。
4. **线上一次性验证清单**（在本机执行）：
   - `curl https://thewooffy.com/robots.txt`，确认无针对 GPTBot / OAI-SearchBot / ClaudeBot / PerplexityBot / Google-Extended / Applebot 的 Disallow。
   - 打开 `/pages/about`，确认页面存在、有 Kailun Zhang 的真实介绍，并且锚点 `#mike` 能对应到页面上的段落。
   - 随机 5 篇文章跑 Rich Results Test，确认仍是 1 Organization + 1 WebSite + 1 BlogPosting + 1 BreadcrumbList（+ FAQPage）。
   - 确认 `add_noindex_nutrition_blog.py` 只 noindex 了 blog 列表页，营养文章本身仍可索引。

**KPI：** AI 来源会话数/周（基线）、引用率（60 条中被引用条数）、覆盖率四项。

### W1 · 可抓取性与实体基础（第 1–2 周）

1. **robots.txt**：保持 Shopify 默认（不屏蔽 AI 爬虫）。只有当需要加规则时才新建 `templates/robots.txt.liquid`，并且永远不要屏蔽 OAI-SearchBot、PerplexityBot、Google-Extended 之外的 Googlebot。
2. **llms.txt**：Shopify 不能直接托管根目录文本文件。做法：`scripts/build_llms_txt.py` 从 `ARTICLES.md` 的数据生成 `llms.txt`（站点一句话介绍 + 按 blog 分组的文章标题与 URL + 数据集页链接），通过 Files API 上传得到 `cdn.shopify.com` 链接，再在 Shopify Admin 建 URL 重定向 `/llms.txt → 该链接`。各引擎对 llms.txt 的采用尚未证实，所以放在第 5 周，成本一小时。
3. **作者实体**：About 页补齐 Person 信息（姓名、Wooffy 创始人、养狗经历、社交账号 sameAs），在 About 页输出 Person JSON-LD，`@id` 与 `seo-schema.liquid` 里的 `author_id` 一致。文章页顶部应有可见的作者名并链接到 About 页。
4. **红线**：不编造资质。不出现 "vet-reviewed"、"DVM" 之类未经真实兽医审核的字样（与 2026-09 的修正保持一致）。

### W2 · 答案优先的内容层（第 2–6 周，最大杠杆）

把 759 篇品种文章改成"先给答案，再展开"。所有改动通过 `breed-data/*.json` + `generate.py` 完成，不手改 HTML。

**2.1 Quick Answer 区块**

- ✅ `generate.py` 新增 `build_quick_answer(breed)`（2026-10-08），读取 `meta.quick_answer`，渲染在 intro 的 H2 之后、正文之前，样式沿用 `seo_ai_overview_pwd.py` 里的 `.quick-answer` 盒子，标记 `<!-- WOOFFY_QUICK_ANSWER_v2 -->`；intro 里已有 v1 手写盒子的页面自动跳过，不会出现两个框。
- ✅ `scripts/geo_quick_answers.py --type main|costs [--apply]`（2026-10-08），按类型从已有结构化数据生成答案并写入 `meta.quick_answer`；grooming / checklist / roundup / comparison 四种类型待做：
  - **主指南（172 篇，已写入 JSON，待 `--update` 推送）**：由 `stats` + `costs-dataset.json` 合成，约 45–55 词。`right_for_you` 列表的句式不统一（"Have experience…" / "People who want…" / "You work full-time…"），拼进句子读不通，所以改用 `with_kids` 和 `beginners` 两个 stats 值映射成固定句子。模板："The {Breed} is a {size} {group} dog, weighing {weight} and living {lifespan}. Plan on {exercise} of exercise a day. Grooming is {grooming}; training is {training}. It is {good with kids / best with older children and supervision}. {first-time owner sentence}. Budget about ${year1} for the first year." 无需 API。
  - **费用页（164 篇，生成器已就绪，未写入）**：`costs-dataset.json[slug].citable_stat` 加一句年度持续费用。**2026-10-29 费用页标题 A/B 读数之后再 `--apply` 并推送**，test/control 两组同时推，保持实验平衡。
  - **美容页（约 160 篇）**：先用 `extract_costs_dataset.py` 的模式新建 `scripts/extract_grooming_dataset.py`，用 Claude API 抽取每篇的"刷毛频率 / 洗澡频率 / 专业美容周期 / 是否掉毛 / 工具"到 `grooming-dataset.json`（参考费用抽取成本约 $2–4），再合成答案。
  - **清单页（约 160 篇）**：一句话 + 前 5 件必备物品，从 `sections.care.html` 的首个 `<ul>` 抽取。
  - **榜单（61 篇）**："The best {topic} are {A}, {B}, {C}…" 从 `sections.care.html` 的品种卡片抽品种名。
  - **对比页（26 篇）**：一句话结论（"Choose X if…, Y if…"），从 `decision` 区块抽取，必要时人工补。
- 每批改动用 `echo YES | python3 scripts/generate.py <slugs> --update --touch-updated` 推送；`--touch-updated` 把 `custom.content_updated` 设为当天（这是实质内容更新），让 `dateModified` 真实变化。

**2.2 At-a-glance 数据表**（✅ 2026-10-08）

`build_stats_grid()` 已从 emoji 卡片 `div` 网格改为语义 `<table>`：`<caption>` "{Breed} at a glance"，每行两组 `<th scope="row">` 标签 + `<td>` 数值，手机上仍是四格宽；用 `border-spacing` 保留原来的卡片感。随下一次主指南 `--update` 一起上线。

**2.3 问句小标题**（✅ 2026-10-08，已写入 JSON，待推送）

`scripts/geo_question_headings.py` 按文章类型与 section key 把模板化小标题改成读者会问的问句，只用品种名拼句，不碰正文；旧标题存进 `sections.*.heading_prev`，`--revert --apply` 可整体回滚。已含 "?" 的标题和 `mikes_take` 不动。覆盖：
- main（172 篇 × 7 节）：intro "What is an Akita?"、appearance "What does an Akita look like?"、temperament "What is the temperament of an Akita?"、care "How much exercise and grooming does an Akita need?"、health "What health problems are common in the Akita?"、cost "How much does an Akita cost?"、finding "Where can you find an Akita puppy or rescue?"
- grooming：intro "What kind of coat does … have?"、care "How often should you groom …?"；special 的手写标题保留
- costs：intro "How much does … cost in the first year?"、care "What are the ongoing costs of …?"（16 篇无 care 的改 cost / health 两节）
- checklist：intro "What do you need before bringing home … puppy?"、care 按内容选 "What supplies does … puppy need?" 或 "What should the first week with … puppy look like?"
- roundup：只有标题以 best/most/easiest 等开头的 24 篇把品种列表那节改成 "What are the best large dog breeds?"，其余不动
共改 2,078 个标题、688 篇。`build_toc()` 同步改为：标题是问句时侧栏显示该节的短 `label`（Physical / Wellness / Budget…），避免侧栏被长问句撑满。审计：问句标题覆盖率 0.1% → 78.5%（roundup 9.8%、comparison 0%，这两类标题多为手写，暂不模板化）。

**2.4 每节首段即答案（BLUF）**

这是真正的改写，成本最高。只做 GSC 曝光前 100 的页面（从 `seo_report.py` 的数据取），用 `detemplatize_rewrite.py` 的 Claude 调用方式给每个 section 加一句开头结论，人工抽查 10%。其余页面依赖 Quick Answer 覆盖。

**2.5 权威引用**（✅ 2026-10-08，172 篇已写入 JSON，待推送）

`scripts/geo_breed_citations.py` 给 172 篇主指南的 `health` 区块末尾加 "Sources &amp; Further Reading"：品种的 AKC 页（APBT 用 UKC，9 个 doodle 用两个亲本品种的 AKC 页，mixed-breed 无品种页）、最多 3 条与该页健康正文实际提到的病症对应的 AKC 健康页（髋关节发育不良、PRA、胀气、甲减、髌骨脱位等 19 种）、以及 OFA CHIC 和 Merck 两条通用参考。沿用 `add_ymyl_citations.py` 的规则：dofollow、`rel=noopener`、哨兵注释幂等。因为云端容器访问不了外网，分两步：`geo-citation-verify.yml`（手动触发，已在 main 注册）在 GitHub runner 上跑 `--verify`，把 184 个候选 URL 的状态和最终 URL 写进 `geo/citation-urls.json` 并提交回分支（10-08 两轮后 184/184 通过，修正了 9 条病症页 URL 和 Saint Bernard 的 AKC slug）；`--apply` 只插入状态 200 且最终 URL 仍含预期关键词的链接（重定向到首页或搜索页的一律不算）；验证通过的来源少于 2 条的页面跳过。费用页引用 Rover / Synchrony 等费用调查，美容页引用 AKC 美容指南，待做。

**KPI：** 覆盖率四项每周上升；第 8 周目标：Quick Answer 100%、来源 ≥ 60%、问句标题 ≥ 80%。

### W3 · 可引用的数据资产（第 3–8 周）

AI 引擎最愿意引用的是"只有你有"的数据。Wooffy 已经有两份。

1. **Wooffy Dog Breed Cost Index 2026**（新页面，dog-breeds blog）：`scripts/build_cost_index_page.py` 从 `costs-dataset.json` 生成 164 个品种的表格（幼犬价、第一年总费用、年度持续费用、月食费、月保险），附方法说明（数据来自 164 篇费用指南的抽取与校验，日期），提供 CSV 下载（Files API），页面输出 `Dataset` JSON-LD。每个品种行链接回费用页，费用页的 Sources 反链到 Index。
2. **Breed Stats Table**：301 个品种的体型 / 体重 / 寿命 / 运动量 / 美容 / 训练难度一张表，来源 `stats`。可放在现有 `dog-breeds-a-z` 页或单独页面。同样输出 `Dataset` schema。
3. **费用计算器页**（`pages/cost-calculator-FINAL.html`）注明数据来源于 Cost Index，形成"数据集 → 工具 → 单篇指南"的互引闭环。
4. **对比页**的 side-by-side 表格已是好格式，补 2.1 的一句话结论即可。

**KPI：** Cost Index 页在引用率面板的"费用"组里出现的次数；该页的外链数（GSC 链接报告）。

### W4 · 实体与站外信号（第 4 周起，持续）

AI 引擎对一个域名的信任很大程度来自站外共现。按投入从低到高：

1. **一致性**：Organization 的 `sameAs` 已含 Pinterest / Instagram / YouTube；再补 LinkedIn 公司页和 Crunchbase（免费），确保各平台的简介都写 "Wooffy publishes dog breed guides and makes the Circla dog house"。
2. **Cost Index 的外宣**：这是最有传播性的素材。给 10–15 家宠物媒体 / 数据新闻作者发一封短邮件附 CSV；在 Pinterest 现有流程里做一组"X 品种第一年要花多少钱"的图钉指回 Index。
3. **Reddit / Quora**：在 r/dogs、r/puppy101 等版块回答费用、美容问题时引用具体数字和页面（Perplexity 和 ChatGPT 大量引用 Reddit）。只在真实有帮助时发，一周不超过 3 条，避免被判为自推。
4. **YouTube**：已有频道。把 Quick Answer 做成 60 秒短视频（"How much does a Golden Retriever cost?"），描述里放页面链接；Google AI Overviews 常引用视频。

### W5 · 技术渲染核对（第 2 周，一次性）

- 确认文章正文在服务端 HTML（`body_html`），不是 JS 注入 —— 已满足。
- FAQ 用 `<details>` 折叠，文本仍在 DOM 中，可抽取；不要改成 JS 懒加载。
- 页面不要有"Read more"截断、不要有需要点击才出现的正文。
- 确认每篇文章的 canonical 无查询参数，Shopify 默认满足。
- ✅ 文章顶部可见"Last updated {date}"（2026-10-08）：`generate.py <slugs> --update --touch-updated` 把 `meta.content_updated` 设为当天并写回 JSON，渲染成 intro 下的 `<time>` 行，同时作为 `custom.content_updated`（type `date`）metafield 推送，线上 `seo-schema.liquid` 正是读它做 `dateModified`。截至 10-08 线上没有任何文章设过这个 metafield，所以此前所有页面的 `dateModified` 都退回了发布日期；每次实质内容更新（含 Quick Answer 上线）都应带 `--touch-updated`。

---

## 3. 时间表

| 周 | 日期 | 交付物 |
|----|------|--------|
| 1 | 10-06 → 10-12 | ✅ GA4 AI 来源分段 + 每日落盘；✅ `geo_audit.py` 覆盖率基线；✅ `geo/query_panel.json` + `geo_citation_audit.py`（首跑待 Actions 手动触发）；线上验证清单完成 |
| 2 | 10-13 → 10-19 | ✅ `generate.py` 支持 `meta.quick_answer`；✅ `geo_quick_answers.py --type main` 写入 172 篇主指南（推送待本机执行）；✅ `build_stats_grid` 改表格；✅ `--touch-updated`；W5 其余核对 |
| 3 | 10-20 → 10-26 | ✅ `geo_question_headings.py` 已写入 688 篇；✅ `geo_breed_citations.py` 184 URL 全部验证、172 篇 Sources 已写入（随主指南一起推送） |
| 4 | 10-27 → 11-02 | 费用页 A/B 读数（10-29）；读数后 `--type costs` 用 `citable_stat` 推 164 篇；About 页 Person schema；LinkedIn / Crunchbase |
| 5 | 11-03 → 11-09 | Cost Index 页 + Dataset schema + CSV；llms.txt 上线；Cost Index 外宣邮件 |
| 6 | 11-10 → 11-16 | `extract_grooming_dataset.py` 抽取 → `--type grooming` 推美容页；`--type roundup` / `comparison` |
| 7 | 11-17 → 11-23 | 前 100 页 BLUF 改写；Breed Stats Table 页；YouTube 短视频前 10 条 |
| 8 | 11-24 → 11-30 | 第二次引用率审计；对比基线；写复盘，决定月度循环内容 |

---

## 4. 护栏

- **A/B 测试**：10-29 前不改 164 篇费用页的 `title_tag` / `meta_description`；正文改动 test / control 同步推。
- **发布节奏**：新文章仍遵守每天 30 篇；批量更新受 Shopify 速率限制（2 req/s），`generate.py --update` 顺序执行即可。
- **真实性**：Quick Answer 的数字只能来自页面已有内容或数据集，不新造数字；来源 URL 必须验证 200；不加任何未经真实审核的专业背书。
- **幂等**：所有注入脚本用哨兵注释，可重复运行；先 `--dry-run` 再 `--apply`。
- **回滚**：每批改动单独 commit，commit message 写明脚本与 slug 范围，出问题用上一版 JSON `--update` 即可回滚。

---

## 5. 需要新建的脚本一览

| 脚本 | 作用 | 依赖 |
|------|------|------|
| `scripts/geo_citation_audit.py`（已完成，Claude 引擎） | 60 条问题的月度引用率审计 | `ANTHROPIC_API_KEY`（已有）；ChatGPT / Perplexity 引擎待接 |
| `scripts/geo_audit.py` | 覆盖率四项统计 | 无 |
| `scripts/geo_quick_answers.py`（main / costs 已完成） | 按类型生成 `meta.quick_answer` | `costs-dataset.json`、`grooming-dataset.json` |
| `scripts/geo_question_headings.py`（已完成） | 小标题改问句 | 无 |
| `scripts/geo_breed_citations.py`（已完成） | 主指南 Sources 区块 | `geo-citation-verify.yml` 跑 `--verify` |
| `scripts/extract_grooming_dataset.py` | 美容数据抽取 | `ANTHROPIC_API_KEY`（已在 .env） |
| `scripts/build_cost_index_page.py` | Cost Index 页 + Dataset schema + CSV | `costs-dataset.json` |
| `scripts/build_llms_txt.py` | 生成并上传 llms.txt | Files API |
| `scripts/traffic_watch.py`（改，已完成） | AI 来源服务端过滤 + 落地页 | GA4 现有凭据 |
| `scripts/geo_ai_referrals.py`（已完成） | AI 转介日志，`daily-digest.yml` 每日提交 | GA4 现有凭据 |
| `scripts/generate.py`（改，已完成） | `build_quick_answer()`、`build_stats_grid()` 表格化、`--touch-updated` | 无 |

---

## 6. 成功标准（第 8 周复盘）

| 指标 | 基线（第 1 周测） | 第 8 周目标 |
|------|-------------------|-------------|
| 60 条问题引用率 | 待测 | 基线 ×2，且费用组 ≥ 40% |
| AI 来源会话 / 周 | 待测 | 基线 ×2 |
| Quick Answer 覆盖率 | 10.2%（87 / 855，`geo_audit.py` 2026-10-06） | 100% |
| 权威来源覆盖率 | 11.8%（101 / 855）→ 10-08 已达 31.0%（JSON） | ≥ 60% |
| 问句标题覆盖率 | 0.1%（全部小标题中 17.5% 是问句）→ 10-08 已达 78.5%（JSON） | ≥ 80% |
| 费用页 A/B | 进行中 | 读数后统一采用胜出模式 |
