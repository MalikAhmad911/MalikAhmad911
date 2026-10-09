"""Animated portrait banner -> assets/banner-{dark,light}.svg

Source photo and intermediate .npy data live outside the repo in SRC (they are the
source of truth; the SVG is a build product). Run: python scripts/banner.py [--preview]
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from scipy import ndimage
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans

SRC = Path(r"C:\Users\ranke\profile-src")
OUT = Path(__file__).resolve().parent.parent / "assets"
RNG = np.random.default_rng(7)

# ---------- portrait ----------
CROP = (390, 495, 790, 948)          # head + shoulders in the original 960x1280 photo
FRAME = (30, 10, 370, 395)           # final framing inside CROP (340x385, same 300:340 aspect)
GW, GH = 300, 340                    # dither grid
# rough silhouette in crop coords (400x453), refined by GrabCut
SILHOUETTE = [(150, 62), (188, 40), (246, 48), (268, 84), (264, 128), (258, 168), (244, 204),
              (292, 226), (330, 250), (346, 310), (356, 453), (14, 453), (28, 310), (44, 246),
              (92, 222), (150, 204), (154, 160), (146, 136), (142, 96)]


def segment(rgb):
    h, w = rgb.shape[:2]
    poly = Image.new("L", (w, h), 0)
    ImageDraw.Draw(poly).polygon(SILHOUETTE, fill=1)
    poly = np.array(poly).astype(bool)
    sure_fg = ndimage.binary_erosion(poly, iterations=14)
    maybe = ndimage.binary_dilation(poly, iterations=14)
    mask = np.full((h, w), cv2.GC_BGD, np.uint8)
    mask[maybe] = cv2.GC_PR_BGD
    mask[poly] = cv2.GC_PR_FGD
    mask[sure_fg] = cv2.GC_FGD
    bgd, fgd = np.zeros((1, 65)), np.zeros((1, 65))
    cv2.grabCut(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), mask, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
    fg = (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)
    fg = ndimage.binary_closing(fg, iterations=3)
    fg = ndimage.binary_opening(fg, iterations=3)      # drops thin spurs along the shoulder
    fg = ndimage.binary_fill_holes(fg)
    lab, n = ndimage.label(fg)
    if n > 1:
        fg = lab == (1 + np.argmax(ndimage.sum(fg, lab, range(1, n + 1))))
    return fg


def prep(gray_img):
    g = ImageOps.autocontrast(gray_img, cutoff=1)
    g = ImageEnhance.Contrast(g).enhance(1.3)
    return g.filter(ImageFilter.UnsharpMask(radius=3, percent=140, threshold=0))


def dither(a):
    """1-bit Floyd-Steinberg, serpentine. a: float 0..1, returns bool (True = ink)."""
    a = a.astype(np.float64).copy()
    h, w = a.shape
    out = np.zeros((h, w), bool)
    for y in range(h):
        xs = range(w) if y % 2 == 0 else range(w - 1, -1, -1)
        d = 1 if y % 2 == 0 else -1
        for x in xs:
            old = a[y, x]
            new = 1.0 if old >= 0.5 else 0.0
            out[y, x] = new == 1.0
            e = old - new
            if 0 <= x + d < w:
                a[y, x + d] += e * 7 / 16
            if y + 1 < h:
                if 0 <= x - d < w:
                    a[y + 1, x - d] += e * 3 / 16
                a[y + 1, x] += e * 5 / 16
                if 0 <= x + d < w:
                    a[y + 1, x + d] += e * 1 / 16
    return out


def build_portraits():
    photo = Image.open(SRC / "me.jpg").convert("RGB").crop(CROP)
    fg = segment(np.array(photo))
    np.save(SRC / "mask_full.npy", fg)
    # tighter framing inside the segmentation crop: face larger, less suit (still head + shoulders)
    photo = photo.crop(FRAME)
    fg = fg[FRAME[1]:FRAME[3], FRAME[0]:FRAME[2]]
    small = photo.resize((GW, GH), Image.LANCZOS)
    m = np.array(Image.fromarray(fg.astype(np.uint8) * 255).resize((GW, GH), Image.LANCZOS)) > 127

    # local contrast (CLAHE) brings out eyes, beard and hair texture before the global stretch
    gl = np.array(small.convert("L"))
    gl = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(6, 6)).apply(gl).astype(float)
    lo, hi = np.percentile(gl[m], [1, 99])
    sub = np.clip((gl - lo) / (hi - lo), 0, 1)
    sub = np.array(prep(Image.fromarray((sub * 255).astype(np.uint8))), float) / 255
    edge = ndimage.binary_erosion(m, iterations=1)

    # light: ink = dark parts. This photo's background is busy (door, hallway), so it is
    # removed here too, and shadows are lifted so the navy suit doesn't become a solid block.
    lt = 0.35 + 0.65 * sub ** 1.6                      # suit tops out at ~65% ink; face midtones deepened
    lt[~m] = 1.0
    light = ~dither(lt) & edge

    # dark: ink = lit parts of the subject only; slight gamma lift so hair and suit still read
    dk = sub ** 0.75
    dk[~m] = 0
    dark = dither(dk) & edge                           # hard-clear diffusion bleed at the edge
    np.save(SRC / "dither_light.npy", light)
    np.save(SRC / "dither_dark.npy", dark)
    np.save(SRC / "mask.npy", m)
    return {"light": light, "dark": dark}, m


# ---------- logos (rendered from real glyphs, then sampled) ----------
FONTS = Path(r"C:\Windows\Fonts")


def glyph_mask(kind):
    S = 600
    im = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(im)
    if kind == "infinity":
        f = ImageFont.truetype(str(FONTS / "seguisym.ttf"), 520)
        d.text((S / 2, S / 2), "∞", font=f, fill=255, anchor="mm")
    elif kind == "ai":
        d.rounded_rectangle((60, 60, 540, 540), radius=70, outline=255, width=34)
        f = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 300)
        d.text((S / 2, S / 2 + 8), "AI", font=f, fill=255, anchor="mm")
    elif kind == "code":
        f = ImageFont.truetype(str(FONTS / "consolab.ttf"), 300)
        d.text((S / 2, S / 2), "</>", font=f, fill=255, anchor="mm")
    a = np.array(im) > 127
    ys, xs = np.nonzero(a)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def sample_points(mask, n, box):
    """n evenly spread points inside mask, fitted into box=(cx, cy, maxw, maxh) in grid units."""
    ys, xs = np.nonzero(mask)
    pts = np.c_[xs, ys].astype(float)
    if len(pts) > 40000:
        pts = pts[RNG.choice(len(pts), 40000, replace=False)]
    c = KMeans(n, n_init=1, random_state=0).fit(pts).cluster_centers_
    h, w = mask.shape
    s = min(box[2] / w, box[3] / h)
    return np.c_[box[0] + (c[:, 0] - w / 2) * s, box[1] + (c[:, 1] - h / 2) * s]


def match(a, b):
    """Reorder b so a[i] -> b[i] is the minimum total squared-distance assignment."""
    cost = ((a[:, None, :] - b[None, :, :]) ** 2).sum(-1)
    _, col = linear_sum_assignment(cost)
    return b[col]


# ---------- SVG ----------
PAL = {
    "dark": dict(bg="#0A101F", bar="#111827", frame="#0D1526", border="#1E293B", portrait="#A78BFA",
                 chrome="#10B981", accent="#22D3EE", text="#F8FAFC", muted="#94A3B8", leader="#334155"),
    "light": dict(bg="#F8FAFC", bar="#E2E8F0", frame="#FFFFFF", border="#CBD5E1", portrait="#7C3AED",
                  chrome="#059669", accent="#0891B2", text="#0F172A", muted="#475569", leader="#CBD5E1"),
}
W, H = 1180, 610
PX, PY, SCALE = 34, 104, 1.4           # portrait origin and grid->px scale
MONO = "'JetBrains Mono','Cascadia Code',Consolas,'Courier New',monospace"
CW = 8.4                                # assumed char width at 14px; textLength enforces it

ROWS = [
    ("Name", "Ahmad Amir"),
    ("Role", "AI Engineer · Founder"),
    ("Origin", "Orlando, Florida"),
    ("Status", "Building AI revenue systems"),
    ("ToolChain", "VS Code · Git · GitHub · Vercel"),
    None,
    ("Core.AI", "LLMs · AI Agents · Automation"),
    ("Core.Lang", "TypeScript · JavaScript · Python"),
    ("Core.Frontend", "React · Next.js · Tailwind"),
    ("Core.Backend", "Node.js"),
    ("Core.Database", "PostgreSQL"),
    ("Core.Infra", "Vercel · GitHub Actions"),
    None,
    ("Grid.Mail", "contact@infiniterankers.io"),
    ("Grid.Portfolio", "infiniterankers.io"),
    ("Grid.LinkedIn", "company/infinite-rankers"),
    ("Grid.Facebook", "Infinite Rankers"),
]

# loop timeline (s): portrait 3.0, then 3x (transition 1.3 + logo 2.0), transition 1.3 back
T = [0, 3.0, 4.3, 6.3, 7.6, 9.6, 10.9, 12.9, 14.2]
LOOP = T[-1]
INTRO = 3.2
KT = ";".join(f"{t / LOOP:.4f}" for t in T)
SPL = ";".join([".45 0 .25 1"] * 8)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def runs_path(cells):
    """cells: bool grid -> compact path of horizontal runs drawn as 1-unit strokes."""
    out = []
    for y in range(cells.shape[0]):
        row = cells[y]
        if not row.any():
            continue
        x = 0
        while x < len(row):
            if row[x]:
                s = x
                while x < len(row) and row[x]:
                    x += 1
                out.append(f"M{s} {y}.5h{x - s}")
            else:
                x += 1
    return "".join(out)


def text(x, y, s, size, fill, weight=400, anchor="start", tl=None, extra=""):
    tl_attr = f' textLength="{tl:.1f}" lengthAdjust="spacingAndGlyphs"' if tl else ""
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{tl_attr} {extra}>{esc(s)}</text>')


def banner(theme, ink, travellers, logo_centroid):
    c = PAL[theme]
    ys, xs = np.nonzero(ink)
    n = len(xs)
    b = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'role="img" aria-label="Ahmad Amir — Founder, Infinite Rankers LLC" font-family="{MONO}">']
    # window chrome
    b.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="{c["bg"]}" stroke="{c["border"]}" stroke-width="2"/>')
    b.append(f'<path d="M15 1H{W-15}A14 14 0 0 1 {W-1} 15V42H1V15A14 14 0 0 1 15 1Z" fill="{c["bar"]}"/>')
    for i, col in enumerate(("#F87171", "#FBBF24", "#34D399")):
        b.append(f'<circle cx="{26 + i*22}" cy="21" r="6.5" fill="{col}"/>')
    b.append(text(W / 2, 26, "ahmad@infinite-rankers: ~/profile.sh --live", 13, c["muted"], 400, "middle"))

    # portrait frame
    fx, fy, fw, fh = 20, 60, 448, 532
    b.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="10" fill="{c["frame"]}" stroke="{c["chrome"]}" stroke-opacity="0.45"/>')
    b.append(text(fx + 14, fy + 26, "VISUAL.MAP", 12, c["chrome"], 700, extra='letter-spacing="2"'))
    b.append(text(fx + fw - 14, fy + 26, f"{n:,} pts", 12, c["muted"], 400, "end"))
    for (x, y, dx, dy) in ((fx + 8, fy + 8, 1, 1), (fx + fw - 8, fy + 8, -1, 1), (fx + 8, fy + fh - 8, 1, -1), (fx + fw - 8, fy + fh - 8, -1, -1)):
        b.append(f'<path d="M{x} {y + 14*dy}V{y}H{x + 14*dx}" fill="none" stroke="{c["chrome"]}" stroke-width="2"/>')

    g_open = f'<g transform="translate({PX} {PY}) scale({SCALE})" shape-rendering="crispEdges">'

    # layer 1: intro — 60 interleaved random groups (each scattered over the whole face)
    groups = RNG.integers(0, 60, n)
    starts = np.linspace(0.1, 2.1, 60)
    RNG.shuffle(starts)
    b.append(f'<g><set attributeName="opacity" to="0" begin="{INTRO}s" fill="freeze"/>{g_open}')
    for gi in range(60):
        sel = groups == gi
        cells = np.zeros_like(ink)
        cells[ys[sel], xs[sel]] = True
        b.append(f'<path d="{runs_path(cells)}" stroke="{c["portrait"]}" stroke-width="1" opacity="0">'
                 f'<animate attributeName="opacity" from="0" to="1" begin="{starts[gi]:.2f}s" dur="0.9s" fill="freeze"/></path>')
    b.append('</g></g>')

    # layer 2: loop portrait — 94 drift bands (k-means on noisy positions => organic, non-grid bands)
    pts = np.c_[xs, ys].astype(float)
    noisy = pts + RNG.normal(0, 4, pts.shape)
    band = KMeans(94, n_init=1, random_state=0).fit_predict(noisy)
    b.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{INTRO}s" fill="freeze"/>{g_open}')
    op = "1;1;0;0;0;0;0;0;1"
    for bi in range(94):
        sel = band == bi
        cells = np.zeros_like(ink)
        cells[ys[sel], xs[sel]] = True
        ctr = pts[sel].mean(0)
        dx, dy = 0.42 * (logo_centroid - ctr)
        mv = f"0 0;0 0;{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};0 0"
        b.append(f'<path d="{runs_path(cells)}" stroke="{c["portrait"]}" stroke-width="1">'
                 f'<animate attributeName="opacity" values="{op}" keyTimes="{KT}" dur="{LOOP}s" begin="{INTRO}s" repeatCount="indefinite"/>'
                 f'<animateTransform attributeName="transform" type="translate" values="{mv}" keyTimes="{KT}" dur="{LOOP}s" begin="{INTRO}s" repeatCount="indefinite"/></path>')
    b.append('</g></g>')

    # layer 3: travellers — morph between logos along optimal-transport paths
    tvo = "0;0;0;1;1;1;1;1;0"
    tkt = ";".join(f"{t / LOOP:.4f}" for t in (0, 3.0, 3.5, 4.3, 6.3, 9.6, 12.9, 13.6, 14.2))
    b.append(f'<g opacity="0" fill="{c["portrait"]}"><animate attributeName="opacity" values="{tvo}" keyTimes="{tkt}" dur="{LOOP}s" begin="{INTRO}s" repeatCount="indefinite"/>{g_open}')
    P0, L1, L2, L3 = travellers
    for i in range(len(P0)):
        seq = [P0[i], P0[i], L1[i], L1[i], L2[i], L2[i], L3[i], L3[i], P0[i]]
        vals = ";".join(f"{x:.0f} {y:.0f}" for x, y in seq)
        b.append(f'<rect x="-1" y="-1" width="2" height="2">'
                 f'<animateTransform attributeName="transform" type="translate" values="{vals}" keyTimes="{KT}" '
                 f'calcMode="spline" keySplines="{SPL}" dur="{LOOP}s" begin="{INTRO}s" repeatCount="indefinite"/></rect>')
    b.append('</g></g>')

    # info panel
    ix, iw = 500, 650
    b.append(text(ix, 92, "SYSTEM.INFO", 13, c["chrome"], 700, extra='letter-spacing="2"'))
    lx = ix + iw - 66
    b.append(f'<rect x="{lx}" y="76" width="66" height="22" rx="11" fill="#EF4444" fill-opacity="0.14" stroke="#EF4444" stroke-opacity="0.5"/>')
    b.append(f'<circle cx="{lx + 15}" cy="87" r="4" fill="#EF4444"><animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite"/></circle>')
    b.append(text(lx + 25, 91.5, "LIVE", 12, "#EF4444", 700, extra='letter-spacing="1"'))
    b.append(f'<line x1="{ix}" y1="110" x2="{ix + iw}" y2="110" stroke="{c["border"]}"/>')
    cols = int(iw // CW)
    y = 138
    for row in ROWS:
        if row is None:
            y += 12
            continue
        label, value = row
        dots = cols - len(label) - len(value) - 2
        b.append(text(ix, y, label, 14, c["muted"], 400, tl=len(label) * CW))
        b.append(text(ix + (len(label) + 1) * CW, y, "." * dots, 14, c["leader"], 400, tl=dots * CW))
        b.append(text(ix + iw, y, value, 14, c["text"], 600, "end", tl=len(value) * CW))
        y += 23
    handle = "@MalikAhmad911"
    pw = len(handle) * CW + 28
    py = y + 8
    b.append(f'<rect x="{ix}" y="{py}" width="{pw:.0f}" height="30" rx="15" fill="{c["accent"]}" fill-opacity="0.14" stroke="{c["accent"]}" stroke-opacity="0.5"/>')
    b.append(text(ix + 14, py + 20, handle, 14, c["accent"], 700, tl=len(handle) * CW))
    b.append(text(ix + iw, py + 20, "AI Engineer @ Infinite Rankers LLC", 13, c["muted"], 400, "end"))
    b.append('</svg>')
    return "\n".join(b)


def metrics(ink, groups_n=60):
    """Intro evenness: mean offset of each group's centroid from the portrait centroid, as a
    fraction of the portrait's spread. ~0.05 = every group covers the whole face (shimmer);
    ~0.7 = groups are spatial patches (patchy reveal)."""
    ys, xs = np.nonzero(ink)
    pts = np.c_[xs, ys].astype(float)
    g = np.random.default_rng(1).integers(0, groups_n, len(xs))
    spread = pts.std(0).mean()
    off = [np.linalg.norm(pts[g == i].mean(0) - pts.mean(0)) / spread for i in range(groups_n)]
    return float(np.mean(off))


def main():
    inks, m = build_portraits()
    centre = np.array([GW / 2, GH / 2 - 10])
    logos = [sample_points(glyph_mask(k), 900, (centre[0], centre[1], 230, 230)) for k in ("infinity", "ai", "code")]
    OUT.mkdir(exist_ok=True)
    for theme, ink in inks.items():
        ys, xs = np.nonzero(ink)
        pick = RNG.choice(len(xs), 900, replace=False)
        P0 = np.c_[xs[pick], ys[pick]].astype(float)
        L1 = match(P0, logos[0])
        L2 = match(L1, logos[1])
        L3 = match(L2, logos[2])
        svg = banner(theme, ink, (P0, L1, L2, L3), logos[0].mean(0))
        (OUT / f"banner-{theme}.svg").write_text(svg, encoding="utf-8")
        print(f"{theme}: {ink.sum():,} dots, {len(svg)/1024:.0f} KB, intro evenness {metrics(ink):.3f}")
    if "--preview" in sys.argv:
        for theme, ink in inks.items():
            Image.fromarray((~ink if theme == "light" else ink).astype(np.uint8) * 255).resize((GW * 2, GH * 2), Image.NEAREST) \
                .save(SRC / f"preview-{theme}.png")
        Image.fromarray(m.astype(np.uint8) * 255).save(SRC / "preview-mask.png")


if __name__ == "__main__":
    main()
