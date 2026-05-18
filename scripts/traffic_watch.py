"""Daily traffic watch for thewooffy.com.

Pulls GA4 analytics, judges the trend against a rolling baseline, attributes
spikes to specific article pages, and emails a plain-English verdict with
recommendations.

Required env:
  GA4_PROPERTY_ID      numeric GA4 property id (NOT the G-XXXX measurement id)
  GA4_SA_JSON          service-account key JSON (full string) with GA4 read access

Email env (optional - if absent the report is printed to stdout instead):
  ALERT_EMAIL_TO       recipient address
  GMAIL_USER           sending Gmail address
  GMAIL_APP_PASSWORD   Gmail app password for that address
"""

import json
import os
import smtplib
import statistics
import sys
from datetime import date
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        DateRange,
        Dimension,
        Metric,
        OrderBy,
        RunReportRequest,
    )
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials as UserCredentials
except ImportError:
    sys.exit(
        "Missing deps. Install with:\n"
        "  pip install google-analytics-data google-auth"
    )

# --- Tuning constants -------------------------------------------------------
DAILY_LOOKBACK_DAYS = 35          # history pulled for baseline + trend
BASELINE_DAYS = 28                # days (before yesterday) used as baseline
SPIKE_Z = 2.0                     # z-score above baseline => spike
SPIKE_PCT = 0.60                  # OR +60% vs baseline mean => spike
DROP_Z = -2.0                     # z-score below baseline => drop
DROP_PCT = -0.40                  # OR -40% vs baseline mean => drop
WOW_STRONG_UP = 0.25              # week-over-week thresholds
WOW_UP = 0.08
WOW_DOWN = -0.08
WOW_STRONG_DOWN = -0.25
TOP_PAGES_LIMIT = 15


GA4_SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def _credentials():
    """OAuth user (refresh token) takes priority; service account is fallback."""
    refresh = os.environ.get("GA4_OAUTH_REFRESH_TOKEN", "").strip()
    if refresh:
        cid = os.environ.get("GA4_OAUTH_CLIENT_ID", "").strip()
        csec = os.environ.get("GA4_OAUTH_CLIENT_SECRET", "").strip()
        if not (cid and csec):
            sys.exit("GA4_OAUTH_CLIENT_ID and GA4_OAUTH_CLIENT_SECRET are "
                     "required alongside GA4_OAUTH_REFRESH_TOKEN.")
        return UserCredentials(
            None,
            refresh_token=refresh,
            client_id=cid,
            client_secret=csec,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=GA4_SCOPES,
        )
    sa_json = os.environ.get("GA4_SA_JSON", "").strip()
    if sa_json:
        return service_account.Credentials.from_service_account_info(
            json.loads(sa_json), scopes=GA4_SCOPES)
    sys.exit("Provide GA4_OAUTH_REFRESH_TOKEN (+ CLIENT_ID/SECRET) "
             "or GA4_SA_JSON.")


def _client_and_property():
    prop = os.environ.get("GA4_PROPERTY_ID", "").strip()
    if not prop:
        sys.exit("GA4_PROPERTY_ID env var is required.")
    return BetaAnalyticsDataClient(credentials=_credentials()), prop


def _run(client, prop, dimensions, metrics, start, end, order_metric=None,
         limit=None):
    req = RunReportRequest(
        property=f"properties/{prop}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start, end_date=end)],
    )
    if order_metric:
        req.order_bys = [
            OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_metric),
                    desc=True)
        ]
    if limit:
        req.limit = limit
    resp = client.run_report(req)
    rows = []
    for r in resp.rows:
        rows.append(
            [d.value for d in r.dimension_values]
            + [m.value for m in r.metric_values]
        )
    return rows


def fetch(client, prop):
    daily = _run(
        client, prop, ["date"],
        ["sessions", "totalUsers", "screenPageViews", "engagementRate"],
        f"{DAILY_LOOKBACK_DAYS}daysAgo", "yesterday",
    )
    daily.sort(key=lambda x: x[0])  # GA4 'date' is YYYYMMDD, lexical == chrono
    series = [
        {
            "date": r[0],
            "sessions": int(r[1]),
            "users": int(r[2]),
            "views": int(r[3]),
            "engagement": float(r[4]),
        }
        for r in daily
    ]

    def channel(start, end):
        rows = _run(client, prop, ["sessionDefaultChannelGroup"],
                    ["sessions"], start, end, order_metric="sessions")
        return {r[0]: int(r[1]) for r in rows}

    channels_now = channel("7daysAgo", "yesterday")
    channels_prev = channel("14daysAgo", "8daysAgo")

    top_pages = _run(
        client, prop, ["pagePath"], ["sessions", "screenPageViews"],
        "7daysAgo", "yesterday", order_metric="sessions",
        limit=TOP_PAGES_LIMIT,
    )
    yest_landing = _run(
        client, prop, ["landingPagePlusQueryString"], ["sessions"],
        "yesterday", "yesterday", order_metric="sessions", limit=5,
    )
    return {
        "series": series,
        "channels_now": channels_now,
        "channels_prev": channels_prev,
        "top_pages": [(r[0], int(r[1]), int(r[2])) for r in top_pages],
        "yest_landing": [(r[0], int(r[1])) for r in yest_landing],
    }


def _pct(curr, base):
    if base == 0:
        return 0.0 if curr == 0 else 1.0
    return (curr - base) / base


def analyze(data):
    series = data["series"]
    if len(series) < 10:
        return {"verdict": "Not enough data yet", "lines": [],
                "recommendations": ["Let GA4 accumulate more days, then re-run."]}

    yesterday = series[-1]
    baseline = series[-(BASELINE_DAYS + 1):-1] or series[:-1]
    base_vals = [d["sessions"] for d in baseline]
    # Median + MAD: robust to publish-day spikes that skew a plain mean.
    base_median = statistics.median(base_vals)
    mad = statistics.median([abs(v - base_median) for v in base_vals])

    y = yesterday["sessions"]
    z = 0.6745 * (y - base_median) / mad if mad else 0.0
    vs_base = _pct(y, base_median)
    if z >= SPIKE_Z or vs_base >= SPIKE_PCT:
        day_state = "SPIKE"
    elif z <= DROP_Z or vs_base <= DROP_PCT:
        day_state = "DROP"
    else:
        day_state = "NORMAL"

    last7 = sum(d["sessions"] for d in series[-7:])
    prev7 = sum(d["sessions"] for d in series[-14:-7]) if len(series) >= 14 else 0
    wow = _pct(last7, prev7)
    if wow >= WOW_STRONG_UP:
        wow_state = "growing strongly"
    elif wow >= WOW_UP:
        wow_state = "growing"
    elif wow <= WOW_STRONG_DOWN:
        wow_state = "declining sharply"
    elif wow <= WOW_DOWN:
        wow_state = "declining"
    else:
        wow_state = "stable"

    org_now = data["channels_now"].get("Organic Search", 0)
    org_prev = data["channels_prev"].get("Organic Search", 0)
    org_growth = _pct(org_now, org_prev)
    total_now = sum(data["channels_now"].values()) or 1
    org_share = org_now / total_now

    if wow_state in ("growing strongly", "growing") and org_growth > 0.15:
        verdict = "Growing - SEO compounding"
    elif wow_state == "growing strongly":
        verdict = "Growing strongly"
    elif wow_state == "growing":
        verdict = "Growing"
    elif wow_state == "stable":
        verdict = "Stable"
    elif wow_state == "declining":
        verdict = "Slowing down"
    else:
        verdict = "Declining - needs attention"

    lines = [
        f"Yesterday ({yesterday['date']}): {y} sessions, "
        f"{yesterday['users']} users, {yesterday['views']} pageviews "
        f"(engagement {yesterday['engagement']*100:.0f}%).",
        f"Day vs 28-day baseline ({base_median:.0f} median): "
        f"{vs_base*100:+.0f}% (z={z:+.1f}) -> {day_state}.",
        f"Last 7 days: {last7} sessions vs previous 7 ({prev7}): "
        f"{wow*100:+.0f}% -> {wow_state}.",
        f"Organic search: {org_now} sessions last 7d "
        f"({org_share*100:.0f}% of traffic), {org_growth*100:+.0f}% WoW.",
    ]

    recs = []
    if day_state == "SPIKE" and data["yest_landing"]:
        top = data["yest_landing"][0]
        recs.append(
            f"Yesterday spiked. Top entry page was {top[0]} ({top[1]} "
            f"sessions) - produce/expand more content like it while it ranks."
        )
    if day_state == "DROP":
        recs.append(
            "Yesterday dropped well below baseline. Check the daily publish "
            "ran, the site is reachable, and recent articles are indexed "
            "(Google Search Console > Pages)."
        )
    recent_below = sum(
        1 for d in series[-3:] if d["sessions"] < base_median * 0.6
    )
    if recent_below >= 2 and day_state != "SPIKE":
        recs.append(
            "Traffic has been under baseline for multiple recent days - "
            "investigate publish cadence and indexing, not a one-off dip."
        )
    if org_growth >= 0.15:
        recs.append(
            "Organic search is compounding - keep the daily publish cadence; "
            "it is the growth engine."
        )
    elif org_share < 0.30:
        recs.append(
            "Organic search is still a minority of traffic - focus on "
            "internal linking and Search Console coverage so articles rank."
        )
    if wow_state in ("growing strongly", "growing"):
        recs.append(
            "Week-over-week growth is healthy - maintain current cadence; "
            "do not change what is working."
        )
    if not recs:
        recs.append("Traffic is stable. No action needed; keep publishing.")

    return {
        "verdict": verdict,
        "lines": lines,
        "recommendations": recs,
        "top_pages": data["top_pages"][:8],
        "channels": data["channels_now"],
    }


def build_report(a):
    today = date.today().strftime("%Y-%m-%d")
    pages = "\n".join(
        f"  {i+1}. {p[0]}  -  {p[1]} sessions"
        for i, p in enumerate(a.get("top_pages", []))
    )
    chans = ", ".join(
        f"{k}: {v}" for k, v in sorted(
            a.get("channels", {}).items(), key=lambda x: -x[1]
        )
    )
    recs = "\n".join(f"  - {r}" for r in a["recommendations"])
    summary = "\n".join(f"  {l}" for l in a["lines"])
    text = (
        f"WOOFFY TRAFFIC WATCH - {today}\n"
        f"{'=' * 50}\n\n"
        f"VERDICT: {a['verdict']}\n\n"
        f"SUMMARY\n{summary}\n\n"
        f"TRAFFIC SOURCES (last 7d)\n  {chans}\n\n"
        f"TOP PAGES (last 7d)\n{pages}\n\n"
        f"RECOMMENDATIONS\n{recs}\n"
    )
    subject = f"[Wooffy] {a['verdict']} - traffic {today}"
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
    print(f"Sent report to {to}")


def main():
    client, prop = _client_and_property()
    data = fetch(client, prop)
    analysis = analyze(data)
    subject, body = build_report(analysis)
    send_email(subject, body)


if __name__ == "__main__":
    main()
