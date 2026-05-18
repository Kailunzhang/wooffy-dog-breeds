"""Single daily digest = GA4 traffic report + GSC SEO action queue.

Reuses traffic_watch and seo_report (their analyze/build_report), so
the two reports stay independently testable but the user gets ONE
email. Each half is isolated: if one data source fails, the other
still ships (the merge trades failure-isolation for fewer emails, so
we re-add it here explicitly).

Env: same as the two reports combined
  GA4_PROPERTY_ID, GA4_OAUTH_CLIENT_ID/SECRET/REFRESH_TOKEN,
  GSC_SITE_URL (optional), ALERT_EMAIL_TO, GMAIL_USER,
  GMAIL_APP_PASSWORD
"""

import os
import smtplib
import sys
import traceback
from datetime import date
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import seo_report as seo  # noqa: E402
import traffic_watch as tw  # noqa: E402

BAR = "═" * 34


def _traffic():
    client, prop = tw._client_and_property()
    a = tw.analyze(tw.fetch(client, prop))
    _, body = tw.build_report(a)
    return a.get("verdict", "?"), body


def _seo():
    a = seo.analyze(seo.fetch(seo._access_token()))
    _, body = seo.build_report(a)
    n = sum(len(v) for v in a.get("actions", {}).values())
    return n, bool(a.get("alarm")), body


def main():
    today = date.today().strftime("%Y-%m-%d")
    verdict, traffic_body = "?", None
    seo_n, seo_alarm, seo_body = None, False, None

    try:
        verdict, traffic_body = _traffic()
    except Exception:
        traffic_body = "⚠️ 流量部分本次获取失败：\n" + traceback.format_exc()

    try:
        seo_n, seo_alarm, seo_body = _seo()
    except Exception:
        seo_body = "⚠️ SEO 部分本次获取失败：\n" + traceback.format_exc()

    n_txt = seo_n if seo_n is not None else "?"
    alarm_tag = "　|　\U0001F6A8 SEO 告警" if seo_alarm else ""
    head = (f"\U0001F436\U0001F4CA  Wooffy 每日晨报 · {today}\n{BAR}\n"
            f"流量判断：{verdict}　|　SEO 待办：{n_txt} 项{alarm_tag}\n"
            f"{BAR}\n\n")
    body = (head
            + (traffic_body or "")
            + f"\n\n{BAR}\n{BAR}\n\n"
            + (seo_body or ""))

    alarm = "\U0001F6A8 " if seo_alarm else ""
    subject = (f"\U0001F436 Wooffy 晨报 · {verdict} · "
               f"{alarm}SEO {n_txt} 项 · {today}")
    _send(subject, body)


def _send(subject, body):
    to = os.environ.get("ALERT_EMAIL_TO", "").strip()
    user = os.environ.get("GMAIL_USER", "").strip()
    pw = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not (to and user and pw):
        print("[no email creds - printing digest instead]\n")
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
    print(f"Sent daily digest to {to}")


if __name__ == "__main__":
    main()
