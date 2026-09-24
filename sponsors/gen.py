"""Generate the GitHub Sponsors profile art (light + dark SVGs).

Style mirrors the resume: monochrome grid lines, hatched dividers, mono labels,
handwritten margin notes. Fonts are subset + embedded as base64 woff2 because
GitHub serves SVGs as sandboxed images (no web fonts).

  python3 -m venv venv && ./venv/bin/pip install fonttools brotli
  ./venv/bin/python sponsors/gen.py        # writes sponsors/*.svg

Fonts: Geist + Geist Mono (Vercel, OFL) from ~/Library/Fonts, Caveat (OFL) from
FONT_DIR. Edit PROJECTS / STATS below and re-run to refresh the art.
"""
import base64, io, logging, os
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools import subset

logging.getLogger("fontTools.subset").setLevel(logging.ERROR)
OUT = Path(__file__).parent
HOME_FONTS = Path.home() / "Library/Fonts"
FONT_DIR = Path(os.environ.get("FONT_DIR", OUT.parent.parent / "fonts"))
FONTS = {
    "sans": HOME_FONTS / "Geist-Regular.otf",
    "sans-semi": HOME_FONTS / "Geist-SemiBold.otf",
    "mono": HOME_FONTS / "GeistMono-Regular.otf",
    "hand": FONT_DIR / "Caveat.ttf",
}

THEMES = {
    "light": dict(mode="light", bg="#ffffff", fg="#09090b", fg2="#3f3f46", muted="#71717a",
                  line="#e4e4e7", hatch="#e4e4e7", soft="#f4f4f5", accent="#2563eb", ok="#16a34a", warn="#d97706"),
    "dark": dict(mode="dark", bg="#09090b", fg="#fafafa", fg2="#d4d4d8", muted="#a1a1aa",
                 line="#27272a", hatch="#27272a", soft="#18181b", accent="#3b82f6", ok="#22c55e", warn="#f59e0b"),
}

STATS = [
    ("100k+", "monthly visitors on\nDarkHorseStocks"),
    ("28+", "projects worked across"),
    ("3", "mobile apps on iOS + Android"),
    ("6", "open-source projects"),
]

# ponytail: status is static text; stars/versions don't auto-update. Re-run gen.py after releases.
PROJECTS = [
    dict(slug="ilovenotch", kind="macOS app", name="ILoveNotch", status=("building", "warn"),
         note="my daily driver", url="github.com/niyamvora/ILoveNotch", logo="logos/ilovenotch.png",
         desc="Your MacBook's notch, finally useful: now playing, file shelf, calendar, "
              "tasks, timers and your AI usage. Native SwiftUI, near-zero idle CPU.",
         stack=["Swift", "SwiftUI", "AppKit", "macOS"]),
    dict(slug="fontfetch", kind="CLI + npm", name="fontfetch", status=("npm", "ok"),
         note="zero deps!", url="github.com/niyamvora/fontfetch",
         desc="Paste a URL, get every webfont: extracted, licence-classified and "
              "project-ready with CSS, manifest and framework configs.",
         stack=["TypeScript", "Node", "CLI", "npm"]),
    dict(slug="component-picker", kind="Chrome extension + MCP", name="Component Picker", status=("v1.8", "ok"),
         note="agents can drive it", url="github.com/niyamvora/component-picker",
         desc="Click any component on any site, copy an AI-ready bundle: HTML, resolved "
              "CSS, hover states, responsive diffs. Ships an MCP server for agents.",
         stack=["TypeScript", "Chrome MV3", "CDP", "MCP"]),
    dict(slug="shinobidata-mcp", kind="MCP server", name="ShinobiData MCP", status=("live", "ok"),
         note="free for everyone", url="shinobidata.com/mcp", logo="logos/shinobidata.png",
         desc="Portfolio analytics + US-equity research inside Claude, ChatGPT and any "
              "MCP client. 32 OAuth-protected tools, 10k+ tickers.",
         stack=["MCP", "OAuth 2.1", "TypeScript", "Postgres"]),
    dict(slug="chimes", kind="interactive web", name="Chimes", status=("live", "ok"),
         note="drag the strings", url="niyamvora.github.io/chimes",
         desc="Every country becomes a beaded doorway curtain, woven from its architecture, "
              "wisdom and language, with synthesized chimes you can play.",
         stack=["JavaScript", "Web Audio", "Canvas"]),
    dict(slug="notionaly", kind="AI prompts + skills", name="Notionaly", status=("live", "ok"),
         note="photo to line art", url="github.com/niyamvora/niyam-notionaly",
         desc="Notion-style illustrations, icons and infographics with AI. Monochrome "
              "hand-drawn line art as SVG/PNG, prompts for ChatGPT, Claude and Gemini.",
         stack=["Prompts", "SVG", "Codex skills"]),
]

# Product dock. "{mode}" in a logo path picks the light/dark file.
PRODUCTS = [
    ("DarkHorseStocks", "100k+ visitors / mo", "logos/darkhorsestocks.png"),
    ("SimpliDeliver", "100k messages / min", "logos/simplideliver-{mode}.png"),
    ("ShinobiData", "US stock research", "logos/shinobidata.png"),
    ("Enigma", "E2E-encrypted chat", "logos/enigma.png"),
    ("ILoveNotch", "macOS notch app", "logos/ilovenotch.png"),
]

ROLES = ["Full-Stack Engineer", "Forward Deployed Engineer", "Product Engineer", "Technical PM", "AI / MCP Engineer"]

PROOF = [
    ("-75%", "AWS bill after consolidation"),
    ("95%", "faster search, 627 ms to 30 ms"),
    ("11+", "payment gateways integrated"),
    ("500+", "apartments taken online"),
]

JOURNEY = [
    ("2012", "B.Tech, Electronics", "& Communication"),
    ("2016", "Into finance: CA Inter,", "3-yr articleship, CFA L1"),
    ("2017", "Joined DarkHorseStocks", "at zero users"),
    ("2022", "SimpliDeliver", "multi-channel CRM"),
    ("2024", "ShinobiData, Maisonnha", "fintech + hospitality"),
    ("2026", "OpCreative + open source", "ILoveNotch, fontfetch, MCP"),
]

WALL = [("Platinum", 2), ("Gold", 3), ("Silver", 4), ("Spark Supporters", 6)]

# ---------------------------------------------------------------- font helpers
_tt = {k: TTFont(p) for k, p in FONTS.items()}


def width(text, font, size):
    f = _tt[font]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(c), cmap[ord("?")])][0] for c in text) * size / upm


def wrap(text, font, size, max_w):
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if width(trial, font, size) <= max_w:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    return lines + [cur]


def font_face(used):
    """@font-face rules with each font subset to exactly the characters used."""
    css = []
    for key, chars in used.items():
        opts = subset.Options()
        opts.flavor, opts.layout_features = "woff2", ["kern", "liga"]
        f = TTFont(FONTS[key])
        missing = set("".join(chars)) - {chr(c) for c in f.getBestCmap()}
        assert not missing, f"{key} font has no glyph for {missing}"  # would silently fall back to a system font
        s = subset.Subsetter(opts)
        s.populate(text="".join(sorted(set(chars))) + " ?")
        s.subset(f)
        buf = io.BytesIO()
        f.flavor = "woff2"
        f.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        css.append(f"@font-face{{font-family:'{key}';src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    return "".join(css)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    def __init__(self, w, h, t):
        self.w, self.h, self.t, self.parts, self.used = w, h, t, [], {}

    def text(self, x, y, s, font="sans", size=16, fill="fg", anchor="start", extra=""):
        self.used.setdefault(font, []).append(s)
        self.parts.append(
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}" font-size="{size}" '
            f'fill="{self.t.get(fill, fill)}" text-anchor="{anchor}" {extra}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, color="line", w=1, extra=""):
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{self.t.get(color, color)}" stroke-width="{w}" {extra}/>')

    def hatch(self, x, y, w, h):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#hatch)"/>')
        self.line(x, y, x + w, y)
        self.line(x, y + h, x + w, y + h)

    def raw(self, s):
        self.parts.append(s)

    def render(self, title):
        t = self.t
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(title)}">'
            f"<title>{esc(title)}</title>"
            f"<defs><style>{font_face(self.used)}</style>"
            f'<pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<line x1="0" y1="0" x2="0" y2="7" stroke="{t["hatch"]}" stroke-width="1.6"/></pattern></defs>'
            f'<rect width="100%" height="100%" fill="{t["bg"]}"/>' + "".join(self.parts) + "</svg>")


def pill(svg, right_x, y, label, tone):
    w = width(label, "mono", 12) + 30
    x = right_x - w
    t = svg.t
    svg.raw(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="12" fill="none" stroke="{t["line"]}"/>')
    svg.raw(f'<circle cx="{x + 12:.1f}" cy="{y + 12}" r="3.5" fill="{t[tone]}"/>')
    svg.text(x + 21, y + 16.5, label, "mono", 12, "fg2")


def chips(svg, x, y, items):
    for it in items:
        w = width(it, "mono", 12) + 18
        svg.raw(f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="24" rx="5" fill="{svg.t["soft"]}" stroke="{svg.t["line"]}"/>')
        svg.text(x + 9, y + 16.5, it, "mono", 12, "fg2")
        x += w + 8


# icons: 16px lucide-style strokes
ICONS = {
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "link": '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    "x": '<path d="M4 4l16 16M20 4L4 20"/>',
    "code": '<path d="M8 8l-4 4 4 4M16 8l4 4-4 4"/>',
    "heart": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
}


def icon(svg, name, x, y, color="muted"):
    svg.raw(f'<g transform="translate({x},{y}) scale(0.75)" fill="none" stroke="{svg.t[color]}" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')


def arrow(svg, d, color="muted"):
    svg.raw(f'<path d="{d}" fill="none" stroke="{svg.t[color]}" stroke-width="1.4" stroke-linecap="round"/>')


# ---------------------------------------------------------------- art
def banner(t):
    W, H, L, R = 1280, 470, 132, 1148
    s = SVG(W, H, t)
    s.line(L, 0, L, H)
    s.line(R, 0, R, H)
    s.hatch(0, 0, W, 22)
    # header
    s.raw(f'<circle cx="{L + 70}" cy="96" r="50" fill="{t["soft"]}" stroke="{t["line"]}"/>')
    s.text(L + 70, 110, "NV", "sans", 38, "fg", "middle")
    s.line(L + 140, 22, L + 140, 170)
    nx = L + 164
    s.text(nx, 98, "Niyam Vora", "sans-semi", 50, "fg")
    bx = nx + width("Niyam Vora", "sans-semi", 50) + 22
    s.raw(f'<circle cx="{bx}" cy="82" r="12" fill="{t["accent"]}"/>'
          f'<path d="M{bx - 5} 82l3.5 3.5 6.5-7" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')
    s.line(nx - 24, 124, R, 124)
    s.text(nx, 153, "Product Manager / Full-Stack Engineer. I ship products that compound.", "mono", 15, "muted")
    s.hatch(0, 170, W, 22)
    # info rows
    rows = [("pin", "Hanoi, Vietnam · ICT (UTC+7)", "link", "niyamvora.vercel.app"),
            ("clock", "9+ years · fintech, SaaS, CRM, devtools", "x", "x.com/niyamvora"),
            ("code", "PM @OpCreative · ShinobiData · SimpliDeliver", "heart", "github.com/sponsors/niyamvora")]
    mid = L + (R - L) // 2 + 30
    s.line(mid - 20, 192, mid - 20, 300)
    for i, (i1, t1, i2, t2) in enumerate(rows):
        y = 224 + i * 32
        icon(s, i1, L + 24, y - 13)
        s.text(L + 52, y, t1, "mono", 15, "fg2")
        icon(s, i2, mid + 4, y - 13)
        s.text(mid + 32, y, t2, "mono", 15, "fg2")
    s.hatch(0, 300, W, 22)
    # stats
    cw = (R - L) / len(STATS)
    for i, (num, label) in enumerate(STATS):
        x = L + i * cw
        if i:
            s.line(x, 322, x, 448)
        lines = label.split("\n")
        s.text(x + 26, 392 - 8 * (len(lines) - 1), num, "sans-semi", 46, "fg")
        for j, ln in enumerate(lines):
            s.text(x + 26, 424 - 9 * (len(lines) - 1) + j * 18, ln, "mono", 13, "muted")
        if i == 0:
            s.raw(f'<circle cx="{x + 26 + width(num, "sans-semi", 46) + 14}" cy="{360 - 8 * (len(lines) - 1)}" r="5" fill="{t["accent"]}"/>')
    s.hatch(0, 448, W, 22)
    # margin notes
    s.text(22, 70, "finance", "hand", 21, "muted", extra='transform="rotate(-6 22 70)"')
    arrow(s, "M86 60 h22 M102 54 l6 6 l-6 6")
    s.text(20, 94, "engineering,", "hand", 21, "muted", extra='transform="rotate(-6 20 94)"')
    s.text(26, 118, "built layer", "hand", 21, "muted", extra='transform="rotate(-6 26 118)"')
    s.text(30, 142, "by layer", "hand", 21, "muted", extra='transform="rotate(-6 30 142)"')
    arrow(s, "M66 150 C 80 158, 96 150, 112 128 M104 128 l8 0 l-1 8")
    s.text(1162, 350, "every sponsor", "hand", 21, "muted", extra='transform="rotate(5 1162 350)"')
    s.text(1166, 374, "ships more", "hand", 21, "muted", extra='transform="rotate(5 1166 374)"')
    s.text(1170, 398, "open source", "hand", 21, "muted", extra='transform="rotate(5 1170 398)"')
    arrow(s, "M1206 408 C 1214 424, 1204 436, 1190 440 M1196 434 l-6 6 l8 2")
    return s.render("Niyam Vora — Product Manager / Full-Stack Engineer")


def card(t, i, p):
    W, H, P = 620, 300, 26
    s = SVG(W, H, t)
    s.raw(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{t["line"]}"/>')
    s.raw(f'<clipPath id="c"><rect width="{W}" height="{H}" rx="14"/></clipPath>')
    s.raw('<g clip-path="url(#c)">')
    s.hatch(0, 0, W, 16)
    s.raw("</g>")
    s.text(P, 46, f"{i:02d}", "mono", 13, "muted")
    s.text(P + 28, 46, p["kind"], "mono", 13, "muted")
    pill(s, W - P, 28, p["status"][0], p["status"][1])
    s.line(0, 66, W, 66)
    nx = P
    if p.get("logo"):  # optional project logo, embedded so the card stays one self-contained file
        s.raw(image(p["logo"], t, P - 4, 78, 46))
        nx += 52
    s.text(nx, 112, p["name"], "sans-semi", 32, "fg")
    ax = nx + width(p["name"], "sans-semi", 32) + 10
    arrow(s, f"M{ax} 104 l12 -12 M{ax + 3} 92 h9 v9", "muted")
    s.text(W - P, 110, p["note"], "hand", 22, "accent", "end", extra=f'transform="rotate(-4 {W - P} 110)"')
    for j, ln in enumerate(wrap(p["desc"], "sans", 16, W - 2 * P)[:3]):
        s.text(P, 146 + j * 24, ln, "sans", 16, "fg2")
    chips(s, P, 216, p["stack"])
    s.line(0, 256, W, 256)
    s.text(P, 284, "↗  " + p["url"], "mono", 13, "muted")
    return s.render(f'{p["name"]} — {p["desc"]}')


def image(path, t, x, y, size):
    b64 = base64.b64encode((OUT / path.format(mode=t["mode"])).read_bytes()).decode()
    return f'<image href="data:image/png;base64,{b64}" x="{x}" y="{y}" width="{size}" height="{size}"/>'


def dock(t):
    W, H, I = 1280, 300, 104
    s = SVG(W, H, t)
    s.hatch(0, 0, W, 20)
    s.text(40, 60, "PRODUCTS I'VE BUILT & WORKED ON", "mono", 13, "muted", extra='letter-spacing="1.5"')
    s.line(40 + width("PRODUCTS I'VE BUILT & WORKED ON", "mono", 13) + 30, 55, W - 40, 55)
    cw = (W - 80) / len(PRODUCTS)
    for i, (name, sub, logo) in enumerate(PRODUCTS):
        cx = 40 + cw * i + cw / 2
        s.raw(f'<rect x="{cx - I / 2 + 2}" y="{92 + 4}" width="{I}" height="{I}" rx="{I * .225}" fill="{t["fg"]}" opacity=".08"/>')
        s.raw(image(logo, t, cx - I / 2, 88, I))
        s.raw(f'<rect x="{cx - I / 2}" y="88" width="{I}" height="{I}" rx="{I * .225}" fill="none" stroke="{t["line"]}"/>')
        s.text(cx, 228, name, "sans-semi", 19, "fg", "middle")
        s.text(cx, 252, sub, "mono", 12, "muted", "middle")
    s.text(40 + cw / 2 - I / 2 - 14, 110, "where it", "hand", 19, "accent", "end", extra='transform="rotate(-8 90 110)"')
    s.text(40 + cw / 2 - I / 2 - 14, 132, "started", "hand", 19, "accent", "end", extra='transform="rotate(-8 90 132)"')
    arrow(s, f"M{40 + cw / 2 - I / 2 - 40} 142 C {40 + cw / 2 - I / 2 - 30} 160, {40 + cw / 2 - I / 2 - 14} 158, {40 + cw / 2 - I / 2 - 6} 148", "accent")
    s.hatch(0, H - 20, W, 20)
    return s.render("Products: " + ", ".join(p[0] for p in PRODUCTS))


def hire(t):
    W, H, L, R = 1280, 440, 40, 1240
    s = SVG(W, H, t)
    s.hatch(0, 0, W, 20)
    # pulsing "available" dot (SMIL animates inside <img> SVGs on GitHub)
    s.raw(f'<circle cx="{L + 8}" cy="54" r="6" fill="{t["ok"]}"><animate attributeName="r" values="6;15" dur="1.8s" repeatCount="indefinite"/>'
          f'<animate attributeName="opacity" values=".45;0" dur="1.8s" repeatCount="indefinite"/></circle>'
          f'<circle cx="{L + 8}" cy="54" r="6" fill="{t["ok"]}"/>')
    s.text(L + 28, 59, "OPEN FOR WORK", "mono", 14, "ok", extra='letter-spacing="2"')
    s.text(R, 59, "Remote · UTC+7 · full-time, contract or consulting", "mono", 14, "muted", "end")
    s.line(0, 88, W, 88)
    s.text(L, 148, "I ship your next product, end to end.", "sans-semi", 42, "fg")
    s.text(L, 184, "Business layer + systems layer: CA + CFA background, production TypeScript, mobile and AWS.",
           "mono", 15, "muted")
    x = L
    for r in ROLES:
        w = width(r, "sans", 16) + 32
        s.raw(f'<rect x="{x:.1f}" y="210" width="{w:.1f}" height="36" rx="18" fill="{t["soft"]}" stroke="{t["line"]}"/>')
        s.text(x + 16, 233, r, "sans", 16, "fg")
        x += w + 10
    s.text(R, 236, "let's build", "hand", 26, "accent", "end", extra=f'transform="rotate(-6 {R} 236)"')
    s.hatch(0, 272, W, 20)
    cw = (R - L) / len(PROOF)
    for i, (num, label) in enumerate(PROOF):
        cx = L + i * cw
        if i:
            s.line(cx, 292, cx, 420)
        s.text(cx + (24 if i else 0), 360, num, "sans-semi", 44, "fg")
        s.text(cx + (24 if i else 0), 392, label, "mono", 13, "muted")
    s.hatch(0, 420, W, 20)
    return s.render("Open for work: " + ", ".join(ROLES))


def journey(t):
    W, H, L, R, Y = 1280, 280, 130, 1150, 150
    s = SVG(W, H, t)
    s.hatch(0, 0, W, 20)
    s.text(40, 60, "THE PATH", "mono", 13, "muted", extra='letter-spacing="1.5"')
    s.line(40 + width("THE PATH", "mono", 13) + 30, 55, W - 40, 55)
    s.line(L, Y, R, Y, "muted", 1.5)
    step = (R - L) / (len(JOURNEY) - 1)
    for i, (year, a, b) in enumerate(JOURNEY):
        x, last = L + i * step, i == len(JOURNEY) - 1
        s.raw(f'<circle cx="{x}" cy="{Y}" r="{9 if last else 6}" fill="{t["accent"] if last else t["bg"]}" '
              f'stroke="{t["accent"] if last else t["fg"]}" stroke-width="2"/>')
        s.text(x, Y - 22, year, "sans-semi", 20, "accent" if last else "fg", "middle")
        s.text(x, Y + 36, a, "mono", 12.5, "fg2", "middle")
        s.text(x, Y + 54, b, "mono", 12.5, "muted", "middle")
    s.text(L + step * 1.5, Y - 58, "finance to engineering", "hand", 22, "accent", "middle",
           extra=f'transform="rotate(-4 {L + step * 1.5} {Y - 58})"')
    s.text(R + 16, Y - 58, "you are here", "hand", 20, "accent", "middle", extra=f'transform="rotate(-6 {R} {Y - 58})"')
    s.hatch(0, H - 20, W, 20)
    return s.render("The path: " + "; ".join(f"{y} {a} {b}" for y, a, b in JOURNEY))


def divider(t):
    s = SVG(1280, 24, t)
    s.hatch(0, 1, 1280, 22)
    return s.render("divider")


def wall(t):
    W, L = 1280, 40
    rows_h = [(n, k, 120 if k <= 2 else 96 if k <= 3 else 76 if k <= 4 else 58) for n, k in WALL]
    H = 40 + sum(h + 56 for _, _, h in rows_h) + 30
    s = SVG(W, H, t)
    s.hatch(0, 0, W, 20)
    y = 40
    for name, k, h in rows_h:
        s.text(L, y + 22, name.upper(), "mono", 13, "muted", extra='letter-spacing="1.5"')
        s.line(L + width(name.upper(), "mono", 13) + 30, y + 17, W - L, y + 17)
        y += 36
        gap = 16
        cw = (W - 2 * L - gap * (k - 1)) / k
        for j in range(k):
            x = L + j * (cw + gap)
            s.raw(f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{h}" rx="10" fill="none" '
                  f'stroke="{t["muted"]}" stroke-opacity=".55" stroke-dasharray="6 6"/>')
            if j == 0:
                s.text(x + cw / 2, y + h / 2 + 7, "your logo here", "hand", 22 if h > 60 else 19, "muted", "middle")
        y += h + 20
    s.hatch(0, H - 20, W, 20)
    return s.render("Sponsors — your logo here")


if __name__ == "__main__":
    for mode, t in THEMES.items():
        (OUT / f"banner-{mode}.svg").write_text(banner(t))
        (OUT / f"divider-{mode}.svg").write_text(divider(t))
        (OUT / f"wall-{mode}.svg").write_text(wall(t))
        (OUT / f"products-{mode}.svg").write_text(dock(t))
        (OUT / f"hire-{mode}.svg").write_text(hire(t))
        (OUT / f"journey-{mode}.svg").write_text(journey(t))
        for i, p in enumerate(PROJECTS, 1):
            (OUT / f"card-{p['slug']}-{mode}.svg").write_text(card(t, i, p))
    for f in sorted(OUT.glob("*.svg")):
        print(f"{f.stat().st_size / 1024:6.1f} KB  {f.name}")
