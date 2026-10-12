# 已作废（2026-10-12）

> 同日改策略：Reddit 只做每日选题源，不做发帖阵地。现行方案见 `reddit-trend-daily.md`。下文保留作参考（板块规则核实结果仍有效）。

# Wooffy Reddit 计划（2026-10-12）

> 结论先行：Reddit 对 Wooffy **不是一个"发链接引流"的渠道**，所有主流狗板块都明文禁止推自己的博客；它能做的是三件更小但更稳的事——选题情报、在 Google 排名的 Reddit 帖子里留下 Wooffy 的数据、每月一篇原创数据帖。预期流量是"每月几十次点击"量级，不是 Pinterest 那种可以批量的渠道。下面的方案按这个预期来定节奏。

## ✅ 需要你拍板的 4 件事

| 决策 | 我的建议 | 为什么 |
|---|---|---|
| 用谁的账号 | **你本人一个真人账号**（如果已有旧账号就用旧的，账龄是资产），不建新品牌号 | Reddit 规则第 5 条禁止多账号/伪装；r/dogs 对品牌马甲"公开羞辱"；真人账号 + 公开披露"我做 thewooffy.com"是唯一走得通的路 |
| 谁来发 | **我起草，你手动发**，不接任何自动发帖工具 | Reddit 垃圾政策明文把"生成式 AI 工具协助扩散"列为违规；手动发是和机器人的唯一区别 |
| 前 4 周做什么 | 只评论，不提 Wooffy，不放链接 | 账龄和社区内评论历史是所有板块 AutoMod 的隐藏门槛；没历史的账号第一条就被静默删 |
| 数据帖之前 | 先过一遍"数据可辩护"闸门（见 §5） | Pinterest 那轮已经抓到成本数字错误（Cavalier、Toller、狗粮 143%）；Reddit 上贴数据会被逐条质疑 |

---

## 0. 现状（已核实）

| 项 | 情况 |
|---|---|
| Wooffy 有没有 Reddit 账号 | 项目和记忆里都没有记录，默认没有 |
| 之前用过 Reddit 做什么 | 只做过选题研究：`scripts/generate_reddit_trend_batch_2.py`（狗粮预算/智能项圈/Doodle 伦理 3 篇）、湾区本地指南的"车主怎么说"块 |
| 最适合带上 Reddit 的内容 | GSC 近 90 天前 20 页里 7 篇是成本页、7 篇是榜单；价格意图占可见点击 1/3（`analytics/step0-2026-10-03/summary.md`） |
| 本环境能不能直接读 Reddit | **不能**：curl、WebFetch、内置浏览器对 reddit.com 全部 403/拦截；板块规则是从 Reddit 帮助中心和第三方镜像（threadfox 2026-10-05 读取、redlib）核的，标注见 §2 |

---

## 1. Reddit 官方规则（2026 年 10 月，来自 Reddit 帮助中心）

- **推广本身不算垃圾**，垃圾的定义是"重复的或未经请求的动作（无论自动还是手动）"。
- 官方对站长的唯一要求："如果你的贡献主要是指向自己业务的链接，请**注意发帖频率**，或者考虑自助广告平台。" 没有写死比例。
- 给版主的指引里提到 **10% 规则**：社区内发帖+评论历史里自我推广不超过 10%。这是各板块自己决定是否采用的，但事实上是大家的默认标尺。
- **AI 内容**：允许，但"冒充人写的"属于违规，要求"打标签或以其他方式说明由 AI 生成/修改"。各板块可以进一步全禁。r/OpenDogTraining 2026-08 已在提案"Rule 7：用自己的话，禁 AI slop"；r/DogAdvice 版主 2026-08 发公告在追机器人账号。
- **明确禁止**：多账号、投票操纵、短链接、同一内容跨板块重复发、无人值守的推广机器人。
- 处罚层级：单帖删除（常见、静默）→ 板块封禁（永久，Reddit 不受理申诉）→ 全站影子封禁 → **域名封禁**（thewooffy.com 的任何链接在全站自动删除，连普通用户推荐也删，可持续数年）。最后这条是我们真正要防的。

## 2. 目标板块地图

"核实"= 看到了规则原文；"待核实"= 只有二手描述，你发第一条前自己在 App 里点开 Rules 看 30 秒。

| 板块 | 成员 | 自推规则 | 对 Wooffy 的用法 | 核实状态 |
|---|---|---|---|---|
| r/dogs | 270 万 | **禁止**自推内容、营销调查、网店推广、社媒引流；"同一网站/博主重复分享低质内容"被点名禁止；只发链接的帖子删。例外是 **[OC] 标签**：需账龄+karma（未公开）、正文必须含全文或完整摘要、每发一条 OC 之前要有 10 条与自己内容无关的真诚评论、每月最多 3 条、评论区禁止自推、用小号推自己内容永久封+公开点名 | 唯一值得争取的"数据帖"位置（§4 玩法 C）；平时当主要评论阵地 | 已核实（redlib 镜像 wiki/rules + wiki/flairs；threadfox 2026-09-26） |
| r/DogAdvice | 53 万 | **明文禁止**"链接你的业务、网站、博客、产品、服务、社媒"；只有"无利益关系的人出于帮助目的"分享才欢迎；调查需版主批准；禁止推荐生食/自制粮 | 只评论、永不提站；版主在主动抓 AI 账号，评论必须是你自己的话 | 已核实（threadfox 2026-10-05 全文 15 条） |
| r/puppy101 | 38 万 | "No Photo Posts, No Spam, No Promos"；强调零惩罚训练 | 幼犬清单/第一年准备类问题的评论阵地；不提站 | 已核实规则标题，全文待你看 |
| r/Goldendoodles | 13 万 | 禁止营销/卖产品/卖狗；**禁止求 breeder 帖**；版主可删低质帖 | 成本问题评论（Goldendoodle 是全站第一流量页）；不提站、不放链接 | 已核实（threadfox 2026-10-05 全 6 条） |
| r/Bernedoodles | 约 3–5 万 | 未见明文规则；2026-07 有用户公开请求版主置顶"基础教育/FAQ/辟谣"，版主回复倾向开 wiki | **机会**：如果 wiki 开放，可以贡献一段"第一年花费怎么算"，署名不带链接 | 待核实 |
| r/CavaPoo | 未知 | 未见明文规则；帖子里反复出现"breeder 不做健康测试"焦虑 | 成本+健康测试话题评论 | 待核实 |
| r/dogbreed | 未知 | 以"这是什么品种"识别帖为主 | 价值低，不作为阵地 | 待核实 |
| 犬种专板（r/goldenretrievers、r/germanshepherds、r/corgi、r/labrador、r/Dachshund、r/AustralianShepherd、r/frenchbulldogs） | 10–50 万各 | 普遍"以图和故事为主，推广会被踩"；具体规则各不相同 | 每周只在 2–3 个里评论；不做首发阵地 | 待核实 |
| r/OpenDogTraining | 未知 | 提案中的"禁 AI slop"规则 | 不进 | 已核实提案帖 |

**明确不碰**：任何"求 breeder"帖（多板块禁止，且 Wooffy 不该背书 breeder）、任何医疗帖（YMYL，r/DogAdvice 要求 NSFW 标记且版主要求"视为可疑"）、任何需要钱/众筹的帖。

## 3. Wooffy 的两个先天风险，方案怎么绕

1. **全站内容是 AI 生成的**（图带 C2PA 标记，文稿 AI 写后去模板化）。Reddit 要求 AI 内容打标签，狗板块正在猎 AI 账号。→ 规则：**Reddit 上的每一个字都由你自己写**，我只给数据表、要点和结构，不给可以直接粘贴的整段英文。草稿里凡是整句英文都标"改写后再发"。
2. **Wooffy 同时是一家店**（狗屋、托特包）。r/dogs 明文禁"网店推广"。→ 规则：Reddit 上 Wooffy 只以"犬种指南/成本数据站"身份出现，**永远不提商品**，个人简介里也不放店铺链接。

## 4. 三个玩法（按风险从低到高）

### 玩法 A：听（零风险，收益最高，立刻开始）
每周花 20 分钟在 r/dogs、r/puppy101、r/DogAdvice 和 2 个 doodle 板块里按"cost / how much / worth it / regret / first year"搜，把真实问题和抱怨记到 `reddit/listening-log.md`。用途：
- 新选题（和之前 `generate_reddit_trend_batch_2.py` 一样的来源）
- 给成本页补"车主实际说的数字"段落（只转述、不引用、不点名用户，和湾区指南一样的做法）
- 判断哪些犬种的成本争议最大，那就是数据帖的素材

### 玩法 B：答（低风险，4 周之后才开始）
在"How much did you pay / first year cost / is X worth it"这类帖子里，**用你自己的话**给出区间，附一句披露："I run a breed-cost site (thewooffy) so I've compiled a lot of these numbers — happy to be corrected."
- 允许放链接的板块（目前没有一个核实允许）：不放
- 不允许的板块：只给数字和拆分，不放链接；想看的人会点你的个人主页，主页简介里放站点
- 比例：**每 10 条评论最多 1 条提到 Wooffy**，其余 9 条是纯帮忙（训练、美容、选犬种）
- 每条回答要说清"数字来自哪里"（见 §5），并且主动说一句数据的局限（地区差异、breeder 差异）
- 评论要在帖子发出的 1 小时内（大板块只有前排评论有人看），所以这件事只能你顺手做，不能攒

### 玩法 C：原创数据帖（中风险，第 6–8 周才做第一条）
在 r/dogs 用 [OC] 标签发一篇"我整理了 164 个犬种第一年花费的区间，表在正文"：
- 全文和表格放在帖子正文里（r/dogs 硬性要求），**不放链接**，只在最后一句披露来源站
- 发之前满足 r/dogs 的 OC 条件：已有 ≥10 条与自己内容无关的真诚评论
- 每月最多 1 条（规则上限 3 条，我们只用 1 条，留余量）
- 候选题目（都来自 Wooffy 自有数据，`costs-dataset.json`，164 犬种）：
  1. 第一年花费按体型分组：玩具犬平均约 $4,100 → 巨型犬约 $7,150，中间差的主要是保险和狗粮，不是买狗钱
  2. 最贵的不是买狗钱：年均持续支出前 8 全是巨型犬（Mastiff、Irish Wolfhound、Great Dane…）约 $3,500–4,050/年
  3. Doodle 的"美容税"：Goldendoodle/Bernedoodle 等每年专业美容 $600–1,200，是同体型短毛犬的 3–5 倍
  4. 保险月费最高的 8 个犬种（Irish Wolfhound、French Bulldog、Mastiff…），法斗是唯一进榜的小型犬
- 发后 48 小时内你必须回每一条评论（规则要求 OC 作者参与讨论）；有人指出数字错，当场认并承诺改站上文章

**不做的**：Reddit 广告（自助广告是 Reddit 官方给站长的替代路线，但目前联盟月收入约 $120，广告跑不平；等月收入过 $500 再评估）；跨板块同一内容重复发；任何形式的投票互助。

## 5. 数据可辩护闸门（玩法 B/C 的前置条件）

Reddit 上贴数字会被问"你的数据哪来的"。现状是 `costs-dataset.json` 的 `citable_stat` 由 AI 从我们自己的文章提取，文章本身没有写方法论（我 grep 了 goldendoodle 成本页，没有 source/methodology 字样）。在发任何数字之前要补：

- [ ] 一句话方法论（例如"区间取自 2025–26 年美国 breeder 公开报价、AKC 费用指南和主流宠物保险公司公开报价，按 2026 年 X 月整理"）——**这句话必须是真的**，如果文章的数字来源说不清，就先不发那个犬种
- [ ] 抽查 10 个将要引用的犬种，对照文章正文核一遍区间（Pinterest 那轮抓到过 3 处错）
- [ ] 把方法论那句话同步写进成本页模板（这同时也是 SEO/E-E-A-T 该做的）
- [ ] 对 `missing`/`est` 字段非空的犬种（如 Labrador 的 ongoing、German Shepherd 的 spay）不引用那一项

## 6. 节奏与里程碑

| 周 | 做什么 | 不做什么 |
|---|---|---|
| 第 1–4 周 | 账号准备（见 `reddit-week1-kit.md`）；每周 5–10 条纯帮忙评论，分布在 4–5 个板块；玩法 A 每周一次 | 不提 Wooffy、不放链接、不发主帖 |
| 第 5–6 周 | 开始玩法 B，每周 ≤1 条带披露的评论；完成 §5 闸门 | 不发 OC |
| 第 7–8 周 | 第一条 r/dogs [OC] 数据帖（题目 1） | 不跨板块转发 |
| 第 9–12 周 | 每月 1 条 OC；玩法 B 维持 ≤10%；60 天复盘 | — |

**熔断规则**（和 Pinterest 一样硬）：
- 任何一条评论被删 → 该板块停 7 天，查原因
- 收到版主警告 → 该板块永久只看不写
- 30 天内 2 次删除（不同板块）→ 所有提及 Wooffy 的行为停 30 天，只做玩法 A
- 发现任何"影子封禁"迹象（登出后看不到自己的帖）→ 全停，告诉我

## 7. 怎么衡量（60 天后看）

| 指标 | 怎么取 | 及格线 |
|---|---|---|
| Reddit 引荐会话 | GA4 → 流量获取 → 来源 reddit.com | 60 天 ≥ 100（这是小渠道，不要期待更多） |
| 被删/警告次数 | 你的发帖记录（kit 里有表） | 0 次版主警告 |
| 账号 karma | 个人主页 | 评论 karma ≥ 200（说明评论被认可） |
| "有 Wooffy 数据的帖子数" | 发帖记录 | ≥ 5 条在 Google 搜"<breed> cost reddit"能出现的帖子里 |
| 选题产出 | listening-log | ≥ 5 个新选题或 ≥ 10 段"车主怎么说" |

如果 60 天后引荐会话 < 30 且 karma < 100，就把 Reddit 收缩成只做玩法 A，不再投时间。

## 8. 和其他渠道的关系

- Pinterest 仍是唯一能批量的渠道，Reddit 不替代它
- 玩法 A 的产出直接喂给去模板化/新文章 pipeline
- §5 的方法论一句话同时解决成本页的 E-E-A-T 空白，这是 Reddit 之外也值得做的

## 来源

- Reddit 帮助中心 Spam 政策：https://support.reddithelp.com/hc/en-us/articles/360043504051-Spam
- Reddit 帮助中心 给版主的"如何防垃圾"（10% 规则出处）：https://support.reddithelp.com/hc/en-us/articles/28012014962580-How-do-I-keep-spam-out-of-my-community
- Reddit Rules（第 2 条真实参与、第 5 条身份真实）：https://redditinc.com/policies/reddit-rules
- r/dogs 规则与 [OC] 条件（redlib 镜像）：https://redlib.vanillax.me/r/dogs/wiki/rules 、https://redlib.vanillax.me/r/dogs/wiki/flairs
- r/dogs 规则摘录（threadfox，2026-09-26 读取）：https://threadfox.vip/rules/dogs
- r/DogAdvice 全部 15 条规则（threadfox，2026-10-05 读取）：https://threadfox.vip/rules/DogAdvice
- r/Goldendoodles 全部 6 条规则（threadfox，2026-10-05 读取）：https://threadfox.vip/rules/Goldendoodles
- r/puppy101 规则摘要：https://huntcomments.com/r/puppy101/rules
- r/DogAdvice 版主关于机器人账号的公告（2026-08-05）：https://www.reddit.com/r/DogAdvice/comments/1vfvfs2/meta_following_up_on_reports_of_bots/
- r/OpenDogTraining "禁 AI slop" 规则提案（2026-08-26）：https://www.reddit.com/r/OpenDogTraining/comments/1vyywz1/new_rule_7_proposal/
- r/Bernedoodles 用户请求置顶教育帖（2026-07-13）：https://www.reddit.com/r/Bernedoodles/comments/1uvhq4w/ask_mods_mods_can_we_have_some_basic_education/
- 9:1 规则的来龙去脉（第三方，但逐条引用了官方原文）：https://parsestream.com/guides/reddit-self-promotion-rules
