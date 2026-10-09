"""Generates every SVG in assets/ for both GitHub themes. Edit content here, not the SVGs."""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "'Segoe UI', Inter, -apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"

THEMES = {
    "dark": dict(bg="#0A101F", surface="#111A2E", inset="#0D1526", border="#1E2A44",
                 text="#F8FAFC", muted="#94A3B8", primary="#22D3EE", accent="#A78BFA",
                 green="#10B981", dots="#334155", cta1="#0E7490", cta2="#6D28D9"),
    "light": dict(bg="#FFFFFF", surface="#F8FAFC", inset="#FFFFFF", border="#E2E8F0",
                  text="#0F172A", muted="#475569", primary="#0891B2", accent="#7C3AED",
                  green="#059669", dots="#CBD5E1", cta1="#0891B2", cta2="#7C3AED"),
}

SERVICES = [
    ("AI Lead Capture", "Every call, chat and form answered instantly"),
    ("AI Appointment & Sales Agents", "Qualifies leads and books meetings 24/7"),
    ("CRM & Pipeline Automation", "Follow-ups and reminders on autopilot"),
    ("Support & Operations AI", "Answers FAQs and routes tickets all day"),
    ("Reviews & Reactivation", "Win back past customers, grow reviews"),
    ("Custom SaaS & Internal Tools", "Dashboards and tools your team will use"),
]

RESULTS = [
    ("DENTAL PRACTICE", "+145%", "new patients", "+$14.2K monthly revenue"),
    ("E-COMMERCE BRAND", "62%", "cart recovery rate", "3.4x ROAS improvement"),
    ("REAL ESTATE AGENCY", "+135%", "lead volume", "28% lead-to-client rate"),
]

METRICS = [
    ("2–6 wks", "Time to go live", "primary"),
    ("3x", "More appointments in 60 days", "accent"),
    ("4.8 / 5", "Average client rating", "green"),
    ("24/7", "Support, weekends included", "primary"),
]

PROJECTS = [
    ("90min", "Football SaaS platform", "SaaS", "TypeScript", "#3178C6"),
    ("crmdesignxyz", "CRM & sales pipeline dashboard", "CRM", "TypeScript", "#3178C6"),
    ("email-marketing", "Email campaigns & automation", "Automation", "TypeScript", "#3178C6"),
    ("instagram", "Social media UI build", "UI", "HTML", "#E34F26"),
]


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}" font-family="{FONT}">\n{body}\n</svg>\n')


def t(x, y, s, size, fill, weight=400, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def card(x, y, w, h, c, r=18):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{c["surface"]}" stroke="{c["border"]}"/>'


def pill(x, y, label, color, size=12, pad=14, h=26):
    w = len(label) * size * 0.62 + pad * 2
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="{h/2}" fill="{color}" fill-opacity="0.12" '
            f'stroke="{color}" stroke-opacity="0.35"/>'
            + t(x + w / 2, y + h / 2 + size * 0.36, label, size, color, 600, "middle")), w


# ---------- hero ----------
ICONS = {
    # 32x32 glyphs centred on (0,0)
    "user": '<circle cx="0" cy="-4" r="4.5" fill="none" stroke="{c}" stroke-width="2"/>'
            '<path d="M-8 9 a8 7 0 0 1 16 0" fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round"/>',
    "send": '<path d="M-8 -7 L9 0 L-8 7 L-5 0 Z" fill="none" stroke="{c}" stroke-width="2" stroke-linejoin="round"/>',
    "cal": '<rect x="-8" y="-7" width="16" height="15" rx="3" fill="none" stroke="{c}" stroke-width="2"/>'
           '<path d="M-8 -2 H8 M-4 -10 V-5 M4 -10 V-5" stroke="{c}" stroke-width="2" stroke-linecap="round"/>'
           '<path d="M-3 3 l2 2 l4 -4" fill="none" stroke="{c}" stroke-width="1.8" stroke-linecap="round"/>',
}


def hero(c):
    W, H = 1200, 400
    b = [f'''<defs>
  <pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="{c["dots"]}"/></pattern>
  <radialGradient id="g1" cx="0.85" cy="0.1" r="0.6"><stop offset="0" stop-color="{c["primary"]}" stop-opacity="0.22"/><stop offset="1" stop-color="{c["primary"]}" stop-opacity="0"/></radialGradient>
  <radialGradient id="g2" cx="0.05" cy="1" r="0.55"><stop offset="0" stop-color="{c["accent"]}" stop-opacity="0.18"/><stop offset="1" stop-color="{c["accent"]}" stop-opacity="0"/></radialGradient>
  <linearGradient id="name" x1="0" x2="1"><stop offset="0" stop-color="{c["text"]}"/><stop offset="1" stop-color="{c["primary"]}"/></linearGradient>
  <clipPath id="frame"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="24"/></clipPath>
</defs>''',
         f'<g clip-path="url(#frame)"><rect width="{W}" height="{H}" fill="{c["bg"]}"/>'
         f'<rect width="{W}" height="{H}" fill="url(#dots)" opacity="0.45"/>'
         f'<rect width="{W}" height="{H}" fill="url(#g1)"/><rect width="{W}" height="{H}" fill="url(#g2)"/></g>',
         f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="24" fill="none" stroke="{c["border"]}" stroke-width="2"/>']

    # left column
    b.append(f'<rect x="60" y="56" width="300" height="30" rx="15" fill="{c["primary"]}" fill-opacity="0.1" stroke="{c["primary"]}" stroke-opacity="0.35"/>')
    b.append(f'<circle cx="78" cy="71" r="4" fill="{c["green"]}"><animate attributeName="opacity" values="1;0.25;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    b.append(t(92, 76, "AI REVENUE SYSTEMS AGENCY", 12, c["primary"], 700, extra='letter-spacing="1.6"'))
    b.append(t(58, 158, "Ahmad Amir", 62, "url(#name)", 800, extra='letter-spacing="-1"'))
    b.append(t(60, 196, "Founder, Infinite Rankers LLC", 22, c["accent"], 600))
    b.append(t(60, 246, "We build AI systems that capture leads,", 20, c["muted"]))
    b.append(t(60, 274, "follow up, and close sales for US businesses.", 20, c["muted"]))
    x = 60
    for label, col in (("Orlando, FL", c["text"]), ("Live in 2–6 weeks", c["primary"]), ("Month-to-month", c["green"])):
        p, w = pill(x, 306, label, col, 13, 14, 30)
        b.append(p)
        x += w + 10

    # right column: animated pipeline
    px, py, pw, ph = 750, 50, 400, 300
    b.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="18" fill="{c["surface"]}" stroke="{c["border"]}"/>')
    b.append(t(px + 22, py + 34, "Live pipeline", 14, c["text"], 700))
    b.append(f'<circle cx="{px+pw-86}" cy="{py+29}" r="4" fill="{c["green"]}"><animate attributeName="opacity" values="1;0.25;1" dur="1.2s" repeatCount="indefinite"/></circle>')
    b.append(t(px + pw - 22, py + 34, "running", 12, c["green"], 600, "end"))
    rows = [("user", "New lead captured", "Website chat · 4 sec ago", "Captured", c["green"]),
            ("send", "AI follow-up sent", "SMS + email · instant", "Sent", c["primary"]),
            ("cal", "Appointment booked", "Calendar · Tue 10:30 AM", "Booked", c["accent"])]
    dur = 7
    for i, (icon, title, sub, status, col) in enumerate(rows):
        ry = py + 56 + i * 68
        # visible at t=0 (so static renders show the full card), fade out, then re-enter one by one
        on = 0.80 + i * 0.05
        kt = f"0;0.70;0.75;{on:.2f};{on+0.04:.2f};1"
        b.append(f'<g><animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="{kt}" dur="{dur}s" repeatCount="indefinite"/>'
                 f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;0 8;0 8;0 0;0 0" keyTimes="{kt}" dur="{dur}s" repeatCount="indefinite"/>')
        b.append(f'<rect x="{px+18}" y="{ry}" width="{pw-36}" height="56" rx="12" fill="{c["inset"]}" stroke="{c["border"]}"/>')
        b.append(f'<circle cx="{px+48}" cy="{ry+28}" r="17" fill="{col}" fill-opacity="0.14"/>')
        b.append(f'<g transform="translate({px+48} {ry+28})">{ICONS[icon].format(c=col)}</g>')
        b.append(t(px + 76, ry + 25, title, 15, c["text"], 600))
        b.append(t(px + 76, ry + 44, sub, 12, c["muted"]))
        sw = len(status) * 12 * 0.62 + 24
        b.append(f'<rect x="{px+pw-30-sw:.0f}" y="{ry+16}" width="{sw:.0f}" height="24" rx="12" fill="{col}" fill-opacity="0.14"/>')
        b.append(t(px + pw - 30 - sw / 2, ry + 32, status, 12, col, 700, "middle"))
        b.append('</g>')
    b.append(f'<line x1="{px+22}" y1="{py+ph-42}" x2="{px+pw-22}" y2="{py+ph-42}" stroke="{c["border"]}"/>')
    b.append(t(px + 22, py + ph - 16, "Avg. client books", 13, c["muted"]))
    b.append(t(px + pw - 22, py + ph - 16, "3x more appointments in 60 days", 13, c["accent"], 700, "end"))
    return svg(W, H, "\n".join(b), "Ahmad Amir, Founder of Infinite Rankers LLC")


def metrics(c):
    W, H, w, gap = 1200, 120, 285, 20
    b = []
    for i, (big, label, key) in enumerate(METRICS):
        x = i * (w + gap)
        b.append(card(x + 1, 1, w - 2, H - 2, c, 16))
        b.append(f'<rect x="{x+1}" y="20" width="4" height="{H-40}" rx="2" fill="{c[key]}"/>')
        b.append(t(x + 28, 62, big, 36, c[key], 800))
        b.append(t(x + 28, 92, label, 14, c["muted"]))
    return svg(W, H, "\n".join(b), "Key numbers")


def services(c):
    W, w, h, gx, gy = 1200, 386, 156, 21, 20
    H = h * 2 + gy
    keys = ["primary", "accent", "green"]
    b = []
    for i, (title, desc) in enumerate(SERVICES):
        x, y = (i % 3) * (w + gx), (i // 3) * (h + gy)
        col = c[keys[i % 3]]
        b.append(card(x + 1, y + 1, w - 2, h - 2, c, 16))
        b.append(f'<rect x="{x+24}" y="{y+24}" width="44" height="44" rx="12" fill="{col}" fill-opacity="0.14"/>')
        b.append(t(x + 46, y + 52, f"0{i+1}", 16, col, 800, "middle"))
        b.append(t(x + 24, y + 104, title, 18, c["text"], 700))
        b.append(t(x + 24, y + 130, desc, 14, c["muted"]))
    return svg(W, H, "\n".join(b), "Services")


def results(c):
    W, w, H, gx = 1200, 386, 210, 21
    keys = ["primary", "accent", "green"]
    b = []
    for i, (tag, big, label, second) in enumerate(RESULTS):
        x = i * (w + gx)
        col = c[keys[i]]
        b.append(card(x + 1, 1, w - 2, H - 2, c, 16))
        b.append(t(x + 26, 42, tag, 12, col, 700, extra='letter-spacing="1.4"'))
        b.append(t(x + 24, 104, big, 50, c["text"], 800, extra='letter-spacing="-1"'))
        b.append(t(x + 26, 132, label, 15, c["muted"]))
        b.append(f'<line x1="{x+26}" y1="152" x2="{x+w-26}" y2="152" stroke="{c["border"]}"/>')
        b.append(f'<circle cx="{x+31}" cy="178" r="5" fill="{col}"/>')
        b.append(t(x + 44, 183, second, 15, c["text"], 600))
    return svg(W, H, "\n".join(b), "Client results")


def project(c, name, desc, tag, lang, lang_col):
    W, H = 590, 150
    b = [card(1, 1, W - 2, H - 2, c, 16)]
    b.append(f'<path d="M26 34 h14 l4 5 h14 v20 h-32 z" fill="none" stroke="{c["primary"]}" stroke-width="2" stroke-linejoin="round"/>')
    b.append(t(72, 54, name, 22, c["text"], 700))
    p, pw = pill(0, 0, tag, c["accent"], 12, 12, 24)
    b.append(f'<g transform="translate({W-26-pw:.0f} 34)">{p}</g>')
    b.append(t(28, 94, desc, 15, c["muted"]))
    b.append(f'<circle cx="34" cy="121" r="6" fill="{lang_col}"/>')
    b.append(t(48, 126, lang, 13, c["muted"], 600))
    b.append(t(W - 28, 126, "View repo →", 13, c["primary"], 700, "end"))
    return svg(W, H, "\n".join(b), f"{name}: {desc}")


def cta(c):
    W, H = 1200, 210
    b = [f'''<defs><linearGradient id="cg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c["cta1"]}"/><stop offset="1" stop-color="{c["cta2"]}"/></linearGradient>
<pattern id="cd" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="#FFFFFF"/></pattern></defs>''',
         f'<rect width="{W}" height="{H}" rx="24" fill="url(#cg)"/>',
         f'<rect width="{W}" height="{H}" rx="24" fill="url(#cd)" opacity="0.12"/>',
         t(60, 86, "Losing leads after hours?", 36, "#FFFFFF", 800, extra='letter-spacing="-0.5"'),
         t(60, 124, "Book a free 30-minute strategy call. We'll map where AI can", 17, "#FFFFFF", 400, extra='fill-opacity="0.85"'),
         t(60, 150, "capture, follow up and close for your business.", 17, "#FFFFFF", 400, extra='fill-opacity="0.85"'),
         f'<rect x="850" y="76" width="292" height="58" rx="29" fill="#FFFFFF"/>',
         t(996, 112, "Book Free Strategy Call  →", 17, c["cta2"] if c is THEMES["dark"] else c["accent"], 800, "middle")]
    return svg(W, H, "\n".join(b), "Book a free strategy call")


def main():
    OUT.mkdir(exist_ok=True)
    for theme, c in THEMES.items():
        files = {"hero": hero(c), "metrics": metrics(c), "services": services(c),
                 "results": results(c), "cta": cta(c)}
        for p in PROJECTS:
            files[f"project-{p[0]}"] = project(c, *p)
        for name, content in files.items():
            (OUT / f"{name}-{theme}.svg").write_text(content, encoding="utf-8")
    print("wrote", len(list(OUT.glob("*.svg"))), "files to", OUT)


if __name__ == "__main__":
    main()
