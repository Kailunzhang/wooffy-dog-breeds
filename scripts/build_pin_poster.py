"""Parse pinterest-sprint-1.md into a local manual-posting dashboard.

Output:
  - pinterest-assets/sprint1/*.png   (downloaded unique hero images)
  - pinterest-manual-poster.html     (self-contained workbench)

The dashboard shows one card per pin: local image preview, board,
one-click copy buttons for title / description / destination link,
and a checkbox whose state persists in localStorage.
"""
from __future__ import annotations

import hashlib
import html
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "pinterest-sprint-1.md"
IMG_DIR = ROOT / "pinterest-assets" / "sprint1"
OUT = ROOT / "pinterest-manual-poster.html"

IMG_DIR.mkdir(parents=True, exist_ok=True)


def parse_pins(text: str) -> list[dict]:
    blocks = re.split(r"(?m)^## Pin (\d+) of 40 - (.+)$", text)
    pins = []
    for i in range(1, len(blocks), 3):
        num = int(blocks[i])
        heading = blocks[i + 1].strip()
        body = blocks[i + 2]
        pins.append({
            "num": num,
            "heading": heading,
            "board": _grab(r"\*\*Board\*\*:\s*`([^`]+)`", body),
            "image": _grab_code_after(body, r"Image source"),
            "link": _grab_code_after(body, r"Destination link"),
            "title": _grab_section(body, "Title"),
            "description": _grab_section(body, "Description"),
        })
    return pins


def _grab(pattern: str, text: str) -> str:
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


def _grab_code_after(body: str, label: str) -> str:
    m = re.search(label + r".*?```\s*\n(.*?)\n\s*```", body, re.S)
    return m.group(1).strip() if m else ""


def _grab_section(body: str, name: str) -> str:
    m = re.search(r"### " + name + r"\b.*?```\s*\n(.*?)\n```", body, re.S)
    return m.group(1).strip() if m else ""


def local_image(url: str) -> str:
    if not url:
        return ""
    fname = re.sub(r"\?.*$", "", url).rsplit("/", 1)[-1]
    stem, ext = (fname.rsplit(".", 1) + ["png"])[:2]
    h = hashlib.md5(url.encode()).hexdigest()[:6]
    fname = f"{stem}-{h}.{ext}"
    dest = IMG_DIR / fname
    if not dest.exists():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                dest.write_bytes(r.read())
            print(f"  downloaded {fname} ({dest.stat().st_size // 1024} KB)")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {url}: {e}", file=sys.stderr)
            return ""
    return f"pinterest-assets/sprint1/{fname}"


def build_html(pins: list[dict]) -> str:
    cards = []
    for p in pins:
        img_rel = local_image(p["image"])
        variant = "A" if p["heading"].endswith("variant A)") else ("B" if p["heading"].endswith("variant B)") else "")
        title_name = re.sub(r"\s*\(variant [AB]\)$", "", p["heading"])
        cards.append(f"""
      <article class="card" data-pin="{p['num']}">
        <div class="imgwrap">
          <img loading="lazy" src="{html.escape(img_rel)}" alt="pin {p['num']}">
          <span class="variant">{variant}</span>
        </div>
        <div class="body">
          <div class="cardhead">
            <span class="num">PIN {p['num']:02d}/40</span>
            <label class="done"><input type="checkbox" data-pin="{p['num']}"> posted</label>
          </div>
          <h2>{html.escape(title_name)}</h2>
          <div class="board">BOARD &rarr; {html.escape(p['board'])}</div>
          <div class="field">
            <div class="flabel">TITLE <span class="cc">{len(p['title'])}/100</span></div>
            <pre class="val" data-copy>{html.escape(p['title'])}</pre>
            <button class="copy">copy title</button>
          </div>
          <div class="field">
            <div class="flabel">DESCRIPTION <span class="cc">{len(p['description'])}/500</span></div>
            <pre class="val" data-copy>{html.escape(p['description'])}</pre>
            <button class="copy">copy description</button>
          </div>
          <div class="field">
            <div class="flabel">DESTINATION LINK</div>
            <pre class="val link" data-copy>{html.escape(p['link'])}</pre>
            <button class="copy">copy link</button>
          </div>
        </div>
      </article>""")

    boards = sorted({p["board"] for p in pins})
    board_opts = "".join(f'<option value="{html.escape(b)}">{html.escape(b)}</option>' for b in boards)

    return f"""<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wooffy Pinterest &mdash; Manual Poster</title>
<style>
:root {{ --bg:#0f0f0f; --card:#181818; --line:#2a2a2a; --fg:#f5f5f5; --mut:#8a8a8a; --acc:#ff5a1f; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font-family:-apple-system,Helvetica,Arial,sans-serif; }}
header {{ position:sticky; top:0; z-index:10; background:#0f0f0fee; backdrop-filter:blur(8px);
  border-bottom:2px solid var(--acc); padding:14px 20px; display:flex; gap:16px; align-items:center; flex-wrap:wrap; }}
header h1 {{ font-size:15px; letter-spacing:.06em; text-transform:uppercase; margin:0; font-weight:800; }}
.stat {{ font:600 12px/1 ui-monospace,Menlo,monospace; color:var(--mut); }}
.stat b {{ color:var(--acc); font-size:15px; }}
.bar {{ flex:1; height:8px; background:var(--line); min-width:120px; overflow:hidden; }}
.bar > i {{ display:block; height:100%; background:var(--acc); width:0; transition:width .2s; }}
select, .ghost {{ background:var(--card); color:var(--fg); border:1px solid var(--line);
  padding:7px 10px; font:600 12px/1 ui-monospace,monospace; text-transform:uppercase; letter-spacing:.04em; }}
main {{ padding:20px; display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:16px; max-width:1600px; margin:0 auto; }}
.card {{ background:var(--card); border:1px solid var(--line); display:flex; flex-direction:column; }}
.card.hide {{ display:none; }}
.card.is-done {{ opacity:.4; }}
.imgwrap {{ position:relative; aspect-ratio:1/1; overflow:hidden; background:#000; border-bottom:1px solid var(--line); }}
.imgwrap img {{ width:100%; height:100%; object-fit:cover; }}
.variant {{ position:absolute; top:8px; left:8px; background:var(--acc); color:#000;
  font:800 11px/1 ui-monospace,monospace; padding:4px 7px; }}
.body {{ padding:14px; display:flex; flex-direction:column; gap:12px; }}
.cardhead {{ display:flex; justify-content:space-between; align-items:center; }}
.num {{ font:700 11px/1 ui-monospace,monospace; color:var(--mut); letter-spacing:.08em; }}
.done {{ font:700 11px/1 ui-monospace,monospace; text-transform:uppercase; color:var(--mut);
  display:flex; gap:6px; align-items:center; cursor:pointer; }}
.card h2 {{ font-size:15px; line-height:1.3; margin:0; font-weight:700; }}
.board {{ font:700 11px/1 ui-monospace,monospace; color:var(--acc); letter-spacing:.03em; }}
.field {{ display:flex; flex-direction:column; gap:6px; }}
.flabel {{ font:700 10px/1 ui-monospace,monospace; color:var(--mut); letter-spacing:.1em; display:flex; justify-content:space-between; }}
.cc {{ color:#5a5a5a; }}
.val {{ margin:0; padding:9px 10px; background:#0f0f0f; border:1px solid var(--line); white-space:pre-wrap;
  font:400 12.5px/1.5 -apple-system,Helvetica,sans-serif; max-height:150px; overflow:auto; }}
.val.link {{ font-family:ui-monospace,monospace; font-size:11px; color:#9ecbff; word-break:break-all; }}
.copy {{ align-self:flex-start; background:transparent; color:var(--fg); border:1px solid var(--acc);
  padding:6px 12px; font:700 11px/1 ui-monospace,monospace; text-transform:uppercase; letter-spacing:.05em; cursor:pointer; }}
.copy:hover {{ background:var(--acc); color:#000; }}
.copy.ok {{ background:#1e7d34; border-color:#1e7d34; color:#fff; }}
</style></head><body>
<header>
  <h1>Wooffy &middot; Pinterest Manual Poster</h1>
  <div class="stat"><b id="done">0</b>/40 posted</div>
  <div class="bar"><i id="fill"></i></div>
  <select id="fboard"><option value="">All boards</option>{board_opts}</select>
  <select id="fstate">
    <option value="all">All pins</option>
    <option value="todo">Not posted</option>
    <option value="done">Posted</option>
  </select>
  <button class="ghost" id="reset">Reset ticks</button>
</header>
<main id="grid">{''.join(cards)}</main>
<script>
const KEY = 'wooffy_pin_posted_v1';
let state = JSON.parse(localStorage.getItem(KEY) || '{{}}');
function save() {{ localStorage.setItem(KEY, JSON.stringify(state)); }}
function applyFilter(c) {{
  const b = document.getElementById('fboard').value;
  const s = document.getElementById('fstate').value;
  const on = !!state[c.dataset.pin];
  const board = c.querySelector('.board').textContent.replace('BOARD \\u2192 ','');
  let show = true;
  if (b && board !== b) show = false;
  if (s === 'todo' && on) show = false;
  if (s === 'done' && !on) show = false;
  c.classList.toggle('hide', !show);
}}
function refresh() {{
  let done = 0;
  document.querySelectorAll('.card').forEach(c => {{
    const on = !!state[c.dataset.pin];
    c.classList.toggle('is-done', on);
    c.querySelector('input[type=checkbox]').checked = on;
    if (on) done++;
    applyFilter(c);
  }});
  document.getElementById('done').textContent = done;
  document.getElementById('fill').style.width = (done/40*100) + '%';
}}
document.addEventListener('change', e => {{
  if (e.target.matches('input[type=checkbox]')) {{ state[e.target.dataset.pin] = e.target.checked; save(); refresh(); }}
  if (e.target.matches('#fboard,#fstate')) refresh();
}});
document.addEventListener('click', e => {{
  if (e.target.matches('.copy')) {{
    const txt = e.target.closest('.field').querySelector('[data-copy]').textContent;
    navigator.clipboard.writeText(txt).then(() => {{
      const b = e.target, t = b.textContent;
      b.textContent = 'copied \\u2713'; b.classList.add('ok');
      setTimeout(() => {{ b.textContent = t; b.classList.remove('ok'); }}, 1200);
    }});
  }}
  if (e.target.id === 'reset') {{ if (confirm('Clear all posted ticks?')) {{ state = {{}}; save(); refresh(); }} }}
}});
refresh();
</script></body></html>"""


def main() -> None:
    text = MD.read_text(encoding="utf-8")
    pins = parse_pins(text)
    print(f"Parsed {len(pins)} pins. Downloading images...")
    out = build_html(pins)
    OUT.write_text(out, encoding="utf-8")
    print(f"Wrote {OUT}")
    missing = [p["num"] for p in pins if not (p["title"] and p["link"] and p["board"])]
    if missing:
        print(f"WARNING incomplete pins: {missing}", file=sys.stderr)
    else:
        print("All pins have title + link + board.")


if __name__ == "__main__":
    main()
