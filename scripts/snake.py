"""Decorative snake animation -> assets/snake-{dark,light}.svg

A contribution-style grid filled with dots; the snake repeatedly hunts the nearest dot
(BFS on the grid) until the board is clear, then the loop restarts. Purely decorative:
the dots are generated here, not read from GitHub. Run: python scripts/snake.py
"""
from collections import deque
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "assets"
COLS, ROWS, PITCH, CELL, PAD = 53, 7, 16, 12, 16
FILL = 0.42                  # share of cells holding a dot
STEP = 0.07                  # seconds per grid move
SEGMENTS = 6

PAL = {
    "dark": dict(empty="#1E293B", levels=["#0E7490", "#22D3EE", "#A78BFA", "#F0ABFC"], snake="#10B981"),
    "light": dict(empty="#EBEDF0", levels=["#A5F3FC", "#22D3EE", "#0891B2", "#7C3AED"], snake="#7C3AED"),
}


def board(seed=11):
    rng = np.random.default_rng(seed)
    filled = rng.random((COLS, ROWS)) < FILL
    level = rng.choice(4, (COLS, ROWS), p=[0.4, 0.3, 0.2, 0.1])
    return {(x, y): int(level[x, y]) for x in range(COLS) for y in range(ROWS) if filled[x, y]}


def hunt(dots):
    """Grid path (list of cells) starting just above the board, eating every dot nearest-first."""
    pos, path, eaten_at, left = (0, -1), [(0, -1)], {}, set(dots)
    while left:
        prev, q, seen = {pos: None}, deque([pos]), None
        while q:
            cur = q.popleft()
            if cur in left:
                seen = cur
                break
            x, y = cur
            for nx, ny in ((x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)):
                if -1 <= nx <= COLS and -1 <= ny <= ROWS and (nx, ny) not in prev:
                    prev[(nx, ny)] = cur
                    q.append((nx, ny))
        step, back = seen, []
        while step != pos:
            back.append(step)
            step = prev[step]
        path += back[::-1]
        pos = seen
        left.discard(seen)
        eaten_at[seen] = len(path) - 1
    for _ in range(SEGMENTS + 2):             # slither off the board's right edge
        pos = (pos[0] + 1, pos[1])
        path.append(pos)
    return path, eaten_at


def xy(cell):
    return PAD + cell[0] * PITCH + CELL / 2, PAD + cell[1] * PITCH + CELL / 2


def render(theme, dots, path, eaten_at):
    c = PAL[theme]
    n = len(path) - 1
    dur = n * STEP
    W, H = PAD * 2 + COLS * PITCH - (PITCH - CELL), PAD * 2 + ROWS * PITCH - (PITCH - CELL)
    b = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'role="img" aria-label="Snake animation">']
    for x in range(COLS):
        for y in range(ROWS):
            b.append(f'<rect x="{PAD + x*PITCH}" y="{PAD + y*PITCH}" width="{CELL}" height="{CELL}" rx="2.5" fill="{c["empty"]}"/>')
    for cell, lvl in dots.items():
        cx, cy = xy(cell)
        t = eaten_at[cell] / n
        b.append(f'<circle cx="{cx}" cy="{cy}" r="{4 + lvl * 0.5}" fill="{c["levels"][lvl]}">'
                 f'<animate attributeName="r" values="{4 + lvl*0.5};{4 + lvl*0.5};0;0" '
                 f'keyTimes="0;{t:.4f};{min(t + 0.004, 1):.4f};1" dur="{dur:.2f}s" repeatCount="indefinite"/></circle>')
    pts = [xy(p) for p in path]
    for k in range(SEGMENTS):
        seq = [pts[max(i - k, 0)] for i in range(len(pts))]
        vals = ";".join(f"{x:.0f} {y:.0f}" for x, y in seq)
        size = CELL - k * 1.2
        b.append(f'<rect x="{-size/2:.1f}" y="{-size/2:.1f}" width="{size:.1f}" height="{size:.1f}" rx="{size/2.6:.1f}" '
                 f'fill="{c["snake"]}" fill-opacity="{1 - k*0.1:.2f}">'
                 f'<animateTransform attributeName="transform" type="translate" values="{vals}" '
                 f'dur="{dur:.2f}s" repeatCount="indefinite"/></rect>')
    b.append('</svg>')
    return "\n".join(b)


def main():
    dots = board()
    path, eaten_at = hunt(dots)
    for theme in PAL:
        s = render(theme, dots, path, eaten_at)
        (OUT / f"snake-{theme}.svg").write_text(s, encoding="utf-8")
    print(f"{len(dots)} dots, {len(path)} moves, loop {len(path) * STEP:.1f}s, {len(s) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
