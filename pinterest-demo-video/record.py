"""Record demo.html to wooffy-pinterest-publisher-demo.mp4 (1920x1080, 90s, H.264).

Python port of huashu-design's render-video.js protocol:
  1. warmup context (no recording) caches fonts/assets
  2. fresh context with record_video; inject window.__recording=true and
     CSS hiding .no-record chrome before navigation
  3. wait for window.__ready (paired with animation t=0), note the offset
  4. wait out the full duration, close context (flushes webm)
  5. ffmpeg: trim the pre-animation offset, encode H.264 yuv420p

Usage: py record.py
"""
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "demo.html"
OUT = ROOT / "wooffy-pinterest-publisher-demo.mp4"
TMP = ROOT / ".video-tmp"
DURATION = 90
W, H = 1920, 1080

HIDE_CHROME = """
() => {
  const style = document.createElement('style');
  style.textContent = '.no-record { display: none !important; }';
  const add = () => (document.head || document.documentElement).appendChild(style);
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', add, { once: true });
  } else { add(); }
}
"""


def main() -> None:
    TMP.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()

        print("warmup...")
        warm = browser.new_context(viewport={"width": W, "height": H})
        wp = warm.new_page()
        wp.goto(HTML.as_uri(), wait_until="load", timeout=60000)
        wp.wait_for_timeout(1500)
        warm.close()

        print("recording...")
        ctx = browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=1,
            record_video_dir=str(TMP),
            record_video_size={"width": W, "height": H},
        )
        ctx.add_init_script("window.__recording = true;")
        ctx.add_init_script(f"({HIDE_CHROME})()")

        t0 = time.time()
        page = ctx.new_page()
        page.goto(HTML.as_uri(), wait_until="load", timeout=60000)
        page.wait_for_function("() => window.__ready === true", timeout=20000)
        offset = time.time() - t0
        print(f"ready at {offset:.2f}s")
        page.wait_for_timeout(DURATION * 1000 + 300)
        page.close()
        ctx.close()
        browser.close()

    webms = sorted(TMP.glob("*.webm"), key=lambda f: f.stat().st_mtime)
    if not webms:
        raise SystemExit("no webm produced")
    webm = webms[-1]
    print(f"webm: {webm.stat().st_size / 1e6:.1f} MB, trim {offset + 0.05:.2f}s")

    subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", f"{offset + 0.05:.2f}",
            "-i", str(webm),
            "-t", str(DURATION),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18", "-preset", "medium",
            "-movflags", "+faststart",
            str(OUT),
        ],
        check=True,
        capture_output=True,
    )
    for f in TMP.glob("*"):
        f.unlink()
    TMP.rmdir()
    print(f"done: {OUT} ({OUT.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
