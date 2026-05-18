"""Daily SEO action queue for thewooffy.com (Google Search Console).

Turns GSC search data into a short, ranked list of concrete actions:
striking-distance keywords, title/CTR quick wins, ranking-drop triage,
rising queries, new-content visibility, and a site-wide collapse alarm
(the only reliable programmatic proxy for a penalty/deindexation, since
Google exposes no Manual Actions API).

Required env:
  GA4_OAUTH_CLIENT_ID / GA4_OAUTH_CLIENT_SECRET / GA4_OAUTH_REFRESH_TOKEN
      OAuth creds (token must include webmasters.readonly scope)
  GSC_SITE_URL   GSC property, default sc-domain:thewooffy.com

Email env (optional - prints to stdout if absent):
  ALERT_EMAIL_TO / GMAIL_USER / GMAIL_APP_PASSWORD
"""

import json
import os
import smtplib
import statistics
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SITE = (os.environ.get("GSC_SITE_URL") or "sc-domain:thewooffy.com").strip()
SITEMAP = "https://www.thewooffy.com/sitemap.xml"

# GSC data lags ~2 days; end the analysis window there.
DATA_LAG_DAYS = 2
RECENT_DAYS = 7
CONTEXT_DAYS = 28
NEW_CONTENT_DAYS = 14

# Expected organic CTR by integer SERP position (rough 2024 benchmarks).
CTR_BY_POS = {1: .27, 2: .15, 3: .10, 4: .07, 5: .05,
              6: .04, 7: .03, 8: .025, 9: .021, 10: .018}

STRIKE_MIN_IMPR = 30        # 28d impressions to qualify as opportunity
STRIKE_POS_LO, STRIKE_POS_HI = 4.0, 15.0
CTR_WIN_MIN_IMPR = 80
CTR_WIN_MAX_POS = 10.5
DROP_MIN_CLICKS = 5         # prior-window clicks to bother triaging
DROP_RATIO = 0.6            # recent <= 60% of prior => drop
RISE_MIN_CLICKS = 5
RISE_RATIO = 1.6
COLLAPSE_RATIO = 0.5        # last-3-day mean < 50% of trailing median => alarm
MAX_ROWS = {"strike": 7, "ctr": 5, "drop": 7, "rise": 5, "new": 10}


def _access_token():
    cid = os.environ.get("GA4_OAUTH_CLIENT_ID", "").strip()
    csec = os.environ.get("GA4_OAUTH_CLIENT_SECRET", "").strip()
    rt = os.environ.get("GA4_OAUTH_REFRESH_TOKEN", "").strip()
    if not (cid and csec and rt):
        sys.exit("GA4_OAUTH_CLIENT_ID/SECRET/REFRESH_TOKEN are required.")
    body = urllib.parse.urlencode({
        "client_id": cid, "client_secret": csec,
        "refresh_token": rt, "grant_type": "refresh_token",
    }).encode()
    resp = json.loads(urllib.request.urlopen(
        "https://oauth2.googleapis.com/token", body).read())
    return resp["access_token"]


def _gsc(token, body):
    site = urllib.parse.quote(SITE, safe="")
    url = (f"https://searchconsole.googleapis.com/webmasters/v3/"
           f"sites/{site}/searchAnalytics/query")
    req = urllib.request.Request(url, json.dumps(body).encode(),
                                 method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    return json.loads(urllib.request.urlopen(req).read()).get("rows", [])


def _q(token, start, end, dims, limit=1000):
    return _gsc(token, {
        "startDate": start.isoformat(), "endDate": end.isoformat(),
        "dimensions": dims, "rowLimit": limit, "type": "web",
        "dataState": "all",
    })


def _exp_ctr(pos):
    return CTR_BY_POS.get(int(round(pos)), 0.012 if pos > 10 else 0.05)


def fetch(token):
    end = date.today() - timedelta(days=DATA_LAG_DAYS)
    r_start = end - timedelta(days=RECENT_DAYS - 1)
    p_end = r_start - timedelta(days=1)
    p_start = p_end - timedelta(days=RECENT_DAYS - 1)
    ctx_start = end - timedelta(days=CONTEXT_DAYS - 1)
    nc_start = end - timedelta(days=NEW_CONTENT_DAYS - 1)

    def tot(s, e):
        rows = _q(token, s, e, [], 1)
        return rows[0] if rows else {"clicks": 0, "impressions": 0,
                                     "ctr": 0, "position": 0}
    return {
        "win": {"recent": (r_start, end), "prior": (p_start, p_end),
                "ctx": (ctx_start, end)},
        "tot_recent": tot(r_start, end),
        "tot_prior": tot(p_start, p_end),
        "tot_ctx": tot(ctx_start, end),
        "daily": _q(token, end - timedelta(days=29), end, ["date"], 100),
        "pq_ctx": _q(token, ctx_start, end, ["query", "page"], 5000),
        "page_recent": _q(token, r_start, end, ["page"], 2000),
        "page_prior": _q(token, p_start, p_end, ["page"], 2000),
        "q_recent": _q(token, r_start, end, ["query"], 2000),
        "q_prior": _q(token, p_start, p_end, ["query"], 2000),
        "page_14": _q(token, nc_start, end, ["page"], 5000),
    }


def _short(url, n=60):
    p = url.replace("https://www.thewooffy.com", "").replace(
        "https://thewooffy.com", "")
    return p if len(p) <= n else p[:n - 1] + "…"


def analyze(d):
    actions = {}

    # 1. Striking distance: pos 4-15, enough impressions, low CTR.
    strike = []
    for r in d["pq_ctx"]:
        pos, impr = r["position"], r["impressions"]
        if STRIKE_POS_LO <= pos <= STRIKE_POS_HI and impr >= STRIKE_MIN_IMPR:
            gain = impr * max(0.0, _exp_ctr(3) - r["ctr"])
            strike.append((gain, r))
    strike.sort(key=lambda x: -x[0])
    actions["strike"] = [
        f"「{r['keys'][0]}」位列第 {r['position']:.1f}（{r['impressions']} 曝光，"
        f"CTR {r['ctr']*100:.1f}%）→ 优化 {_short(r['keys'][1])} 的标题/正文"
        f"针对该词，冲进前 3 约 +{g/CONTEXT_DAYS*30:.0f} 点击/月"
        for g, r in strike[:MAX_ROWS["strike"]]
    ]

    # 2. CTR quick wins: page-1 ranking but CTR far below positional norm.
    seen, ctr_win = set(), []
    for r in sorted(d["pq_ctx"], key=lambda x: -x["impressions"]):
        pos = r["position"]
        if (pos <= CTR_WIN_MAX_POS and r["impressions"] >= CTR_WIN_MIN_IMPR
                and r["ctr"] < 0.5 * _exp_ctr(pos)):
            key = r["keys"][1]
            if key in seen:
                continue
            seen.add(key)
            ctr_win.append(r)
    actions["ctr"] = [
        f"{_short(r['keys'][1])} 在「{r['keys'][0]}」排第 {r['position']:.1f}，"
        f"但 CTR 仅 {r['ctr']*100:.1f}%（同位置应 ~{_exp_ctr(r['position'])*100:.0f}%）"
        f"→ 重写 title/meta description，最快见效"
        for r in ctr_win[:MAX_ROWS["ctr"]]
    ]

    # 3. Ranking-drop triage (page level, recent vs prior).
    pr = {x["keys"][0]: x for x in d["page_recent"]}
    pp = {x["keys"][0]: x for x in d["page_prior"]}
    drops = []
    for url, prev in pp.items():
        if prev["clicks"] < DROP_MIN_CLICKS:
            continue
        now = pr.get(url, {"clicks": 0, "position": 99})
        if now["clicks"] <= prev["clicks"] * DROP_RATIO:
            drops.append((prev["clicks"] - now["clicks"], url, prev, now))
    drops.sort(key=lambda x: -x[0])
    actions["drop"] = [
        f"{_short(u)}：点击 {pv['clicks']}→{nw['clicks']}（"
        f"排名 {pv['position']:.1f}→{nw.get('position',99):.1f}）"
        f"→ 排查算法更新/内容变动/自相残杀"
        for _, u, pv, nw in drops[:MAX_ROWS["drop"]]
    ]

    # 4. Rising queries (lean in).
    qr = {x["keys"][0]: x for x in d["q_recent"]}
    qp = {x["keys"][0]: x["clicks"] for x in d["q_prior"]}
    rise = []
    for q, now in qr.items():
        if now["clicks"] < RISE_MIN_CLICKS:
            continue
        before = qp.get(q, 0)
        if before == 0 or now["clicks"] >= before * RISE_RATIO:
            rise.append((now["clicks"] - before, q, now, before))
    rise.sort(key=lambda x: -x[0])
    actions["rise"] = [
        f"「{q}」点击 {bf}→{nw['clicks']}（第 {nw['position']:.1f} 名）"
        f"→ 加深这块内容，趁势扩量"
        for _, q, nw, bf in rise[:MAX_ROWS["rise"]]
    ]

    # 5. New content with no search visibility yet.
    visible = {x["keys"][0] for x in d["page_14"]}
    new_urls = _recent_sitemap_urls()
    actions["new"] = [
        f"{_short(u)} → 近期发布/更新但 14 天内 0 搜索曝光，"
        f"检查是否被收录、是否薄内容"
        for u in [u for u in new_urls if u not in visible][:MAX_ROWS["new"]]
    ]

    # 6. Site-wide collapse alarm (penalty/deindex/algo proxy).
    daily = sorted(d["daily"], key=lambda x: x["keys"][0])
    alarm = None
    if len(daily) >= 14:
        clicks = [x["clicks"] for x in daily]
        last3 = statistics.mean(clicks[-3:])
        base = statistics.median(clicks[:-3])
        if base > 0 and last3 < base * COLLAPSE_RATIO:
            alarm = (f"全站点击近 3 天均值 {last3:.0f} vs 基线 {base:.0f}"
                     f"（跌 {(1-last3/base)*100:.0f}%）。可能是人工处罚/去索引/"
                     f"核心更新——立即手动检查 Search Console › "
                     f"安全和手动操作 / 网页收录 / 移除项。")

    tr, tp, tc = d["tot_recent"], d["tot_prior"], d["tot_ctx"]
    wow = ((tr["clicks"] - tp["clicks"]) / tp["clicks"] * 100
           if tp["clicks"] else 0.0)
    summary = [
        f"近 28 天：{tc['clicks']} 点击 · {tc['impressions']} 曝光 · "
        f"平均排名 {tc['position']:.1f} · CTR {tc['ctr']*100:.1f}%",
        f"近 7 天 vs 前 7 天点击：{tp['clicks']} → {tr['clicks']}"
        f"（{wow:+.0f}%）· 当前平均排名 {tr['position']:.1f}",
    ]
    return {"alarm": alarm, "summary": summary, "actions": actions,
            "win": d["win"]}


def _recent_sitemap_urls():
    cut = (datetime.now(timezone.utc).replace(tzinfo=None)
           - timedelta(days=NEW_CONTENT_DAYS))
    out = []
    try:
        root = _xml(SITEMAP)
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        children = [e.text for e in root.iter(ns + "loc")]
        maps = [c for c in children if "sitemap" in c and (
            "blog" in c or "post" in c)] or children
        for sm in maps[:8]:
            try:
                r = _xml(sm)
            except Exception:
                continue
            for url in r.iter(ns + "url"):
                loc = url.findtext(ns + "loc")
                lm = url.findtext(ns + "lastmod")
                if not loc or "/blogs/" not in loc:
                    continue
                if lm and _parse_dt(lm) and _parse_dt(lm) >= cut:
                    out.append(loc)
    except Exception:
        pass
    return out[:40]


def _xml(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return ET.fromstring(urllib.request.urlopen(req, timeout=20).read())


def _parse_dt(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(
            tzinfo=None)
    except Exception:
        return None


def _section(icon, title, items, empty):
    body = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(items)) \
        if items else f"  {empty}"
    return f"{icon}  {title}\n\n{body}"


def build_report(a):
    today = date.today().strftime("%Y-%m-%d")
    bar = "─" * 34
    parts = [f"\U0001F50E  Wooffy SEO 行动队列 · {today}", bar]
    if a["alarm"]:
        parts += ["", f"\U0001F6A8  紧急告警\n\n  {a['alarm']}", bar]
    parts += [
        "",
        "\U0001F4CA  概览\n\n" + "\n".join(f"  • {s}" for s in a["summary"]),
        bar, "",
        _section("\U0001F3AF", "临门一脚关键词（最高 ROI）",
                 a["actions"]["strike"], "（暂无符合条件的机会词）"),
        bar, "",
        _section("✍️", "标题速赢（CTR 偏低）",
                 a["actions"]["ctr"], "（页面 CTR 均正常）"),
        bar, "",
        _section("\U0001F4C9", "排名下跌待排查",
                 a["actions"]["drop"], "（无显著下跌）"),
        bar, "",
        _section("\U0001F680", "上升中（趁势扩量）",
                 a["actions"]["rise"], "（暂无明显上升词）"),
        bar, "",
        _section("\U0001F195", "新发布未获搜索曝光",
                 a["actions"]["new"], "（近期发布均已获得曝光）"),
        bar,
        "\U0001F916  本邮件由 Wooffy SEO Watch 每日自动生成 · "
        "数据源 Google Search Console（滞后约 2 天）",
    ]
    text = "\n".join(parts) + "\n"
    flag = "\U0001F6A8 " if a["alarm"] else ""
    n = sum(len(v) for v in a["actions"].values())
    subject = f"\U0001F50E {flag}Wooffy SEO 行动队列 · {n} 项待办 · {today}"
    return subject, text


def send_email(subject, body):
    to = os.environ.get("ALERT_EMAIL_TO", "").strip()
    user = os.environ.get("GMAIL_USER", "").strip()
    pw = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not (to and user and pw):
        print("[no email creds - printing report instead]\n")
        print(body)
        return
    msg = MIMEMultipart()
    msg["From"] = user
    msg["To"] = to
    msg["Subject"] = Header(subject, "utf-8")
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, pw)
        s.sendmail(user, [to], msg.as_string())
    print(f"Sent SEO report to {to}")


def main():
    token = _access_token()
    subject, body = build_report(analyze(fetch(token)))
    send_email(subject, body)


if __name__ == "__main__":
    main()
