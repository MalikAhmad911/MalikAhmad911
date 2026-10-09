"""Builds assets/activity-{dark,light}.svg from live GitHub data. Run: python scripts/activity.py"""
import json
import os
import subprocess
import urllib.request
from collections import Counter, OrderedDict
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"
FONT = "'Segoe UI', Inter, -apple-system, 'Helvetica Neue', Helvetica, Arial, sans-serif"
THEMES = {
    "dark": dict(surface="#111A2E", inset="#0D1526", border="#1E2A44", text="#F8FAFC",
                 muted="#94A3B8", primary="#22D3EE", accent="#A78BFA", green="#10B981"),
    "light": dict(surface="#F8FAFC", inset="#FFFFFF", border="#E2E8F0", text="#0F172A",
                  muted="#475569", primary="#0891B2", accent="#7C3AED", green="#059669"),
}
USER = "MalikAhmad911"


def svg(w, h, body, label):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}" font-family="{FONT}">\n{body}\n</svg>\n')


def t(x, y, s, size, fill, weight=400, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" {extra}>{escape(s)}</text>')


def card(x, y, w, h, c, r=18):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{c["surface"]}" stroke="{c["border"]}"/>'


QUERY = """query($u:String!){user(login:$u){
  contributionsCollection{totalCommitContributions contributionCalendar{totalContributions
    weeks{contributionDays{contributionCount date}}}}
  repositories(ownerAffiliations:OWNER,first:100){totalCount
    nodes{isFork languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""


def fetch():
    token = os.environ.get("GITHUB_TOKEN") or subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    req = urllib.request.Request("https://api.github.com/graphql",
                                 data=json.dumps({"query": QUERY, "variables": {"u": USER}}).encode(),
                                 headers={"Authorization": f"bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)["data"]["user"]


def summarize(u):
    cc = u["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    months = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["contributionCount"]
    langs, colors = Counter(), {}
    for repo in u["repositories"]["nodes"]:
        if repo["isFork"]:
            continue
        for e in repo["languages"]["edges"]:
            langs[e["node"]["name"]] += e["size"]
            colors[e["node"]["name"]] = e["node"]["color"] or "#64748B"
    return dict(total=cc["contributionCalendar"]["totalContributions"],
                commits=cc["totalCommitContributions"],
                repos=u["repositories"]["totalCount"],
                peak=max(d["contributionCount"] for d in days),
                months=list(months.items())[-12:], langs=langs, colors=colors)


def activity(c, s):
    W, H = 1200, 440
    b = [card(1, 1, W - 2, H - 2, c, 24)]
    b.append(t(32, 52, "Engineering at a glance", 22, c["text"], 800))
    b.append(t(W - 32, 52, f"Last 12 months · updated {date.today():%b %Y}", 13, c["muted"], 400, "end"))

    tiles = [(f"{s['total']:,}", "Contributions", "primary"), (f"{s['commits']:,}", "Commits", "accent"),
             (f"{s['repos']}", "Repositories", "green"), (f"{s['peak']}", "Commits on peak day", "primary")]
    tw = (W - 64 - 3 * 16) / 4
    for i, (big, label, key) in enumerate(tiles):
        x = 32 + i * (tw + 16)
        b.append(f'<rect x="{x:.0f}" y="76" width="{tw:.0f}" height="96" rx="14" fill="{c["inset"]}" stroke="{c["border"]}"/>')
        b.append(t(x + 22, 128, big, 36, c[key], 800))
        b.append(t(x + 22, 154, label, 13, c["muted"]))

    # languages: animated stacked bar + legend
    total = sum(s["langs"].values())
    top = s["langs"].most_common(5)
    other = total - sum(v for _, v in top)
    parts = top + ([("Other", other)] if other else [])
    lx, lw, ly = 32, 640, 236
    b.append(t(lx, 214, "Languages", 15, c["text"], 700))
    b.append(f'<clipPath id="lb"><rect x="{lx}" y="{ly}" width="{lw}" height="14" rx="7"/></clipPath>')
    b.append(f'<clipPath id="lr"><rect x="{lx}" y="{ly}" width="{lw}" height="14">'
             f'<animate attributeName="width" from="0" to="{lw}" dur="1.4s" fill="freeze"/></rect></clipPath>')
    b.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="14" rx="7" fill="{c["border"]}"/>')
    b.append('<g clip-path="url(#lb)"><g clip-path="url(#lr)">')
    x = lx
    for name, v in parts:
        w = lw * v / total
        b.append(f'<rect x="{x:.1f}" y="{ly}" width="{w + 0.5:.1f}" height="14" fill="{s["colors"].get(name, c["muted"])}"/>')
        x += w
    b.append('</g></g>')
    for i, (name, v) in enumerate(parts):
        cx, cy = lx + (i % 3) * 215, 290 + (i // 3) * 34
        col = s["colors"].get(name, c["muted"])
        b.append(f'<circle cx="{cx+6}" cy="{cy-5}" r="6" fill="{col}"/>')
        b.append(t(cx + 20, cy, name, 14, c["text"], 600))
        b.append(t(cx + 190, cy, f"{100*v/total:.1f}%", 13, c["muted"], 400, "end"))

    # monthly contributions: animated bar chart
    mx, mw, top_y, base = 720, 448, 236, 386
    b.append(t(mx, 214, "Contributions by month", 15, c["text"], 700))
    peak = max(v for _, v in s["months"]) or 1
    bw = mw / len(s["months"])
    b.append(f'<line x1="{mx}" y1="{base}" x2="{mx+mw}" y2="{base}" stroke="{c["border"]}"/>')
    for i, (ym, v) in enumerate(s["months"]):
        h = max(3, (base - top_y - 18) * v / peak)
        x = mx + i * bw + 5
        col = c["primary"] if v == peak else c["accent"]
        op = 1 if v else 0.35
        b.append(f'<rect x="{x:.1f}" y="{base-h:.1f}" width="{bw-10:.1f}" height="{h:.1f}" rx="4" fill="{col}" fill-opacity="{op}">'
                 f'<animate attributeName="height" from="0" to="{h:.1f}" dur="0.9s" begin="{0.2+i*0.06:.2f}s" fill="freeze"/>'
                 f'<animate attributeName="y" from="{base}" to="{base-h:.1f}" dur="0.9s" begin="{0.2+i*0.06:.2f}s" fill="freeze"/></rect>')
        if v == peak:
            b.append(t(x + (bw - 10) / 2, base - h - 8, str(v), 12, c["primary"], 700, "middle"))
        label = date(int(ym[:4]), int(ym[5:]), 1).strftime("%b")[0]
        b.append(t(x + (bw - 10) / 2, base + 22, label, 12, c["muted"], 400, "middle"))
    return svg(W, H, "\n".join(b), f"{s['total']} contributions, {s['commits']} commits, {s['repos']} repositories in the last year")


def main():
    s = summarize(fetch())
    for theme, c in THEMES.items():
        (OUT / f"activity-{theme}.svg").write_text(activity(c, s), encoding="utf-8")
    print({k: v for k, v in s.items() if k not in ("langs", "colors")})


if __name__ == "__main__":
    main()
