"""Pull the data needed to analyse the Amazon affiliate programme.

GA4 (via traffic_watch's client):
  - outbound clicks to amazon.com / amzn.to by page, link URL and link text
  - daily click series, device / country / channel splits
  - page views, sessions, engaged sessions per /blogs/ page (all countries and US only)
  - a sanity table of event names, so an empty click table is explainable
GSC (via seo_report's token helper):
  - clicks / impressions / CTR / position per page for the window and the
    equal-length prior window
  - page x query rows

Everything is written as JSON under analytics/amazon-affiliate-<end>/ plus a
short summary.md. Dates are ISO (YYYY-MM-DD). Default window: 2026-09-29
(affiliate launch) to yesterday.

Env: same as traffic_watch.py / seo_report.py (GA4_PROPERTY_ID + OAuth trio).

Usage:
    python3 scripts/amazon_affiliate_pull.py [--start 2026-09-29] [--end 2026-10-29]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import seo_report as sr  # noqa: E402
import traffic_watch as tw  # noqa: E402
from google.analytics.data_v1beta.types import (  # noqa: E402
    Filter, FilterExpression, FilterExpressionList)

AMAZON_RE = r"amazon\.com|amzn\.to"
GSC_LAG_DAYS = 2


def _str_filter(field: str, value: str, match: str) -> FilterExpression:
    mt = getattr(Filter.StringFilter.MatchType, match)
    return FilterExpression(filter=Filter(
        field_name=field,
        string_filter=Filter.StringFilter(match_type=mt, value=value, case_sensitive=False)))


def amazon_click_filter() -> FilterExpression:
    return FilterExpression(and_group=FilterExpressionList(expressions=[
        _str_filter("eventName", "click", "EXACT"),
        _str_filter("linkUrl", AMAZON_RE, "PARTIAL_REGEXP"),
    ]))


def ga4_pull(start: str, end: str) -> dict:
    client, prop = tw._client_and_property()
    clicks = amazon_click_filter()
    blogs = _str_filter("pagePath", "/blogs/", "BEGINS_WITH")
    us_blogs = FilterExpression(and_group=FilterExpressionList(expressions=[
        blogs, _str_filter("country", "United States", "EXACT")]))
    page_metrics = ["screenPageViews", "sessions", "engagedSessions",
                    "userEngagementDuration", "activeUsers"]

    def run(dims, mets, flt=None, limit=20000, order=None):
        try:
            return tw._run(client, prop, dims, mets, start, end,
                           order_metric=order, limit=limit, dim_filter=flt)
        except Exception as exc:  # keep the pull going; record the failure
            return [["__error__", str(exc)[:300]]]

    return {
        "window": {"start": start, "end": end},
        "event_names": run(["eventName"], ["eventCount"], limit=50, order="eventCount"),
        "clicks_page_link_text": run(["pagePath", "linkUrl", "linkText"], ["eventCount"],
                                     clicks, order="eventCount"),
        "clicks_by_link": run(["linkUrl"], ["eventCount"], clicks, order="eventCount"),
        "clicks_daily": run(["date"], ["eventCount"], clicks),
        "clicks_by_device": run(["deviceCategory"], ["eventCount"], clicks),
        "clicks_by_country": run(["country"], ["eventCount"], clicks, limit=25, order="eventCount"),
        "clicks_by_channel": run(["sessionDefaultChannelGroup"], ["eventCount"], clicks,
                                 limit=25, order="eventCount"),
        "pages": run(["pagePath"], page_metrics, blogs, order="screenPageViews"),
        "pages_us": run(["pagePath"], page_metrics, us_blogs, order="screenPageViews"),
        "pages_daily_total": run(["date"], ["screenPageViews", "sessions", "engagedSessions"], blogs),
    }


def gsc_pull(start: date, end: date) -> dict:
    token = sr._access_token()
    end = min(end, date.today() - timedelta(days=GSC_LAG_DAYS))
    days = (end - start).days + 1
    p_end = start - timedelta(days=1)
    p_start = p_end - timedelta(days=days - 1)
    return {
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "prior_window": {"start": p_start.isoformat(), "end": p_end.isoformat()},
        "pages": sr._q(token, start, end, ["page"], 5000),
        "pages_prior": sr._q(token, p_start, p_end, ["page"], 5000),
        "page_query": sr._q(token, start, end, ["page", "query"], 25000),
        "daily": sr._q(token, start, end, ["date"], 400),
    }


def write(out_dir: Path, name: str, data) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=1)
    (out_dir / name).write_text(text, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2026-09-29")
    ap.add_argument("--end", default=(date.today() - timedelta(days=1)).isoformat())
    args = ap.parse_args(argv)
    out_dir = ROOT / "analytics" / f"amazon-affiliate-{args.end}"

    ga4 = ga4_pull(args.start, args.end)
    for key, rows in ga4.items():
        if key != "window":
            write(out_dir, f"ga4_{key}.json", {"window": ga4["window"], "rows": rows})
    gsc = gsc_pull(date.fromisoformat(args.start), date.fromisoformat(args.end))
    for key in ("pages", "pages_prior", "page_query", "daily"):
        write(out_dir, f"gsc_{key}.json", {"window": gsc["window"], "prior_window": gsc["prior_window"],
                                          "rows": gsc[key]})

    links = [r for r in ga4["clicks_by_link"] if r[0] != "__error__"]
    total_clicks = sum(int(r[-1]) for r in links)
    lines = [
        f"# Amazon affiliate data pull {args.start} to {args.end}",
        "",
        f"- GA4 outbound Amazon clicks: {total_clicks} across {len(links)} link URLs "
        f"and {len({r[0] for r in ga4['clicks_page_link_text']})} pages",
        f"- GA4 event names seen (top): {', '.join(r[0] + '=' + r[-1] for r in ga4['event_names'][:12])}",
        f"- GA4 blog pages with views: {len(ga4['pages'])}",
        f"- GSC window {gsc['window']['start']} to {gsc['window']['end']}: {len(gsc['pages'])} pages, "
        f"{len(gsc['page_query'])} page x query rows",
    ]
    write(out_dir, "summary.md", "\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
