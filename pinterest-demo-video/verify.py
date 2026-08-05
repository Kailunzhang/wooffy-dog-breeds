"""Frame-check the demo animation: seek to key timestamps, screenshot each.

Usage: py verify.py
Outputs frames/frame-<t>.png next to this file; prints console errors if any.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "demo.html"
OUT = ROOT / "frames"
OUT.mkdir(exist_ok=True)

CHECK_TIMES = [1.0, 6.0, 25.0, 50.0, 72.0, 87.0]


def main() -> None:
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(HTML.as_uri(), wait_until="load", timeout=60000)
        page.wait_for_function("() => window.__ready === true", timeout=20000)
        for t in CHECK_TIMES:
            page.evaluate(f"window.__seek({t})")
            page.wait_for_timeout(250)
            page.screenshot(path=str(OUT / f"frame-{t:04.1f}.png"))
        ctx.close()
        browser.close()
    if errors:
        print("CONSOLE/PAGE ERRORS:")
        for e in errors:
            print(" ", e[:300])
    else:
        print("no console errors")
    print("frames written to", OUT)


if __name__ == "__main__":
    main()
