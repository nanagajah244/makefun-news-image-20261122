#!/usr/bin/env python3
"""news-image-20261122 — Sunday 22 November 2026 world news in one image.

Pure-stdlib Python 3.13 program. Renders a dense 1024x1024 newspaper front
page with an embedded 5x7 bitmap font and a hand-rolled PNG encoder
(zlib/struct only). Deterministic: same bytes on every run, no randomness,
no clock, no network, no reading the current date. The date is fixed text.
Writes one image to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (247, 243, 234)
INK = (26, 26, 26)
RED = (176, 30, 36)
BLUE = (31, 58, 95)
GREY = (90, 86, 78)
RULE = (180, 172, 156)
LIGHT = (238, 232, 218)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, '#' = on, '.' = off. Original transcription
# of a classic 5x7 bitmap alphabet, written out by hand for this program.
FONT = {}
def _g(ch, rows):
    FONT[ch] = rows

_g('A', [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"])
_g('B', ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."])
_g('C', [".####", "#....", "#....", "#....", "#....", "#....", ".####"])
_g('D', ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."])
_g('E', ["#####", "#....", "#....", "####.", "#....", "#....", "#####"])
_g('F', ["#####", "#....", "#....", "####.", "#....", "#....", "#...."])
_g('G', [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."])
_g('H', ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"])
_g('I', ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"])
_g('J', ["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."])
_g('K', ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"])
_g('L', ["#....", "#....", "#....", "#....", "#....", "#....", "#####"])
_g('M', ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"])
_g('N', ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"])
_g('O', [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."])
_g('P', ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."])
_g('Q', [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"])
_g('R', ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"])
_g('S', [".####", "#....", "#....", ".###.", "....#", "....#", "####."])
_g('T', ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."])
_g('U', ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."])
_g('V', ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."])
_g('W', ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"])
_g('X', ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"])
_g('Y', ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."])
_g('Z', ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"])
_g('0', [".###.", "#..##", "#.#.#", "#.#.#", "##..#", "#...#", ".###."])
_g('1', ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."])
_g('2', [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"])
_g('3', ["####.", "....#", "....#", ".###.", "....#", "....#", "####."])
_g('4', ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."])
_g('5', ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."])
_g('6', [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."])
_g('7', ["#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."])
_g('8', [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."])
_g('9', [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."])
_g(' ', [".....", ".....", ".....", ".....", ".....", ".....", "....."])
_g('.', [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."])
_g(',', [".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."])
_g(':', [".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."])
_g(';', [".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."])
_g('!', ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."])
_g('?', [".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."])
_g('-', [".....", ".....", ".....", ".###.", ".....", ".....", "....."])
_g('\u2014', [".....", ".....", ".....", "#####", ".....", ".....", "....."])
_g('\u2019', ["..##.", "..#..", ".#...", ".....", ".....", ".....", "....."])
_g("'", ["..##.", "..#..", ".#...", ".....", ".....", ".....", "....."])
_g('"', [".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."])
_g('/', ["....#", "....#", "...#.", "...#.", "..#..", "..#..", ".#..."])
_g('(', ["...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"])
_g(')', ["##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."])
_g('%', ["##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"])
_g('$', ["..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."])
_g('&', [".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"])
_g('+', [".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."])
_g('=', [".....", ".....", ".###.", ".....", ".###.", ".....", "....."])
_g('*', [".....", ".#.#.", ".###.", "#####", ".###.", ".#.#.", "....."])
_g('@', [".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."])
_g('#', [".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."])
_g('_', [".....", ".....", ".....", ".....", ".....", ".....", "#####"])
_g('\u00b7', [".....", ".....", ".##..", ".##..", ".....", ".....", "....."])
_g('a', [".....", ".....", ".###.", "....#", ".####", "#...#", ".####"])
_g('b', ["#....", "#....", "####.", "#...#", "#...#", "#...#", "####."])
_g('c', [".....", ".....", ".####", "#....", "#....", "#....", ".####"])
_g('d', ["....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"])
_g('e', [".....", ".....", ".###.", "#...#", "#####", "#....", ".###."])
_g('f', ["..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#..."])
_g('g', [".....", ".####", "#...#", "#...#", ".####", "#...#", ".###."])
_g('h', ["#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"])
_g('i', [".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."])
_g('j', ["...#.", ".....", "..##.", "...#.", "...#.", "...#.", ".##.."])
_g('k', ["#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."])
_g('l', [".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."])
_g('m', [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"])
_g('n', [".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"])
_g('o', [".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."])
_g('p', [".....", ".....", "####.", "#...#", "#...#", "####.", "#...."])
_g('q', [".....", ".....", ".####", "#...#", "#...#", ".####", "....#"])
_g('r', [".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."])
_g('s', [".....", ".....", ".####", "#....", ".###.", "....#", "####."])
_g('t', [".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."])
_g('u', [".....", ".....", "#...#", "#...#", "#...#", "#...#", ".####"])
_g('v', [".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."])
_g('w', [".....", ".....", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"])
_g('x', [".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"])
_g('y', [".....", ".....", "#...#", "#...#", ".####", "....#", ".###."])
_g('z', [".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"])

CHAR_W = 6  # glyph 5 + 1 spacing, in font units

def text_width(text, scale):
    return sum(CHAR_W for _ in text) * scale - scale

# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg) * (w * h)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x); y0 = max(0, y)
        x1 = min(self.w, x + w); y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            off = (yy * self.w + x0) * 3
            self.px[off:off + len(row)] = row

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill_rect(x, y, thick, h, color)

    def draw_text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch)
            if glyph is None:
                glyph = FONT[' ']
            for gy in range(7):
                row = glyph[gy]
                for gx in range(5):
                    if row[gx] == '#':
                        self.fill_rect(cx + gx * scale, y + gy * scale,
                                       scale, scale, color)
            cx += CHAR_W * scale
        return cx

    def draw_text_centered(self, cx, y, text, scale, color):
        w = text_width(text, scale)
        self.draw_text(cx - w // 2, y, text, scale, color)
        return w

def wrap(text, max_width, scale):
    """Greedy word wrap; returns list of lines fitting max_width px."""
    unit = CHAR_W * scale
    max_chars = max(1, max_width // unit)
    lines = []
    for para in text.split('\n'):
        words = para.split(' ')
        cur = ''
        for word in words:
            trial = word if not cur else cur + ' ' + word
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                # hard-split overlong words
                while len(word) > max_chars:
                    lines.append(word[:max_chars])
                    word = word[max_chars:]
                cur = word
        if cur:
            lines.append(cur)
    return lines

def draw_wrapped(cv, x, y, text, max_width, scale, color, line_gap=4):
    lines = wrap(text, max_width, scale)
    for i, line in enumerate(lines):
        cv.draw_text(x, y + i * (7 * scale + line_gap), line, scale, color)
    return y + len(lines) * (7 * scale + line_gap)

# ------------------------------------------------------------------ content
LEAD_TAG = "LEAD  \u00b7  CLIMATE"
LEAD_HEAD = "COP31 COLLAPSES: NO DEAL AS FOSSIL FUELS GO UNMENTIONED"
LEAD_BODY = ("Nearly 200 nations leave the Antalya climate summit with no "
             "agreement, two days past deadline, after the EU rejects a draft "
             "that never mentions fossil fuels.")

# (tag, headline, detail) — headline and detail each wrap to at most 2 lines
# at scale 2 inside a 322 px tile (26 chars per line); enforced by asserts.
TILES = [
    ("GULF", "Iran hits Bahrain site",
     "Missiles hit a plant; two hurt, 3 tankers hit."),
    ("LIBYA", "Drone blast hits Russian ship",
     "Suspected Ukrainian drones hit a ship at Benghazi."),
    ("UKRAINE", "Drone hits flats near Kyiv",
     "Drone hits flats in Dymer; 14 missing."),
    ("UKRAINE", "Missile hits Kryvyi Rih",
     "Two killed, 60 wounded in Zelenskyy's hometown."),
    ("MEXICO", "'El Chapo Isidro' captured",
     "Cartel boss seized in Sinaloa; 11 killed."),
    ("INDONESIA", "Factory fire: 3 dead, 36 missing",
     "Candy plant burns in Cikande, Banten."),
    ("NIGERIA", "Boat capsizes: 24 dead",
     "A vessel carrying mourners overturns in Bayelsa."),
    ("EUROPE", "UK and EU strike new deals",
     "London and Brussels agree closer post-Brexit ties."),
    ("SPACE", "BepiColombo reaches Mercury",
     "ESA confirms orbit after an eight-year trip."),
    ("TENNIS", "Alcaraz wins ATP Finals",
     "The Spaniard beats No. 1 Zverev 6-2, 7-6 in Turin."),
    ("MOTOR RACING", "Verstappen wins in Las Vegas",
     "A third Vegas win in four years, 30 lead changes."),
    ("USA", "FBI probes crime database hack",
     "An intrusion into the national crime database."),
    ("USA", "Bayer's $7.25bn deal approved",
     "A Missouri judge clears the Roundup settlement."),
    ("USA", "Nvidia faces reported SEC probe",
     "Regulators said to examine its accounting."),
    ("SOUTH KOREA", "Minister quits over exam scandal",
     "Education chief Choi Kyo-jin quits."),
    ("ITALY", "Paolo Bulgari dies at 89",
     "The jeweller who built a global luxury brand."),
    ("JAPAN", "Shuri Castle hall restored",
     "Okinawa rebuilds the hall seven years after fire."),
    ("USA", "Trump curbs contractor replies",
     "Contractors must notify the White House first."),
]

# (utc time, event) — times are when each item was reported on the day (UTC);
# each event wraps to at most 3 lines at scale 2 inside a 157 px column.
TIMELINE = [
    ("12:13", "Shuri Castle hall reopens in Okinawa"),
    ("14:10", "Drone hits flats in Dymer"),
    ("14:42", "Cikande fire; 3 dead, 36 missing"),
    ("17:10", "Alcaraz beats Zverev, wins ATP Finals"),
    ("20:12", "COP31 ends in Antalya with no deal"),
    ("21:44", "Drone blast hits ship, Benghazi"),
]

FOOTER = ("THE WORLD IN NUMBERS \u2014 S&P 500 -3.7% \u00b7 NASDAQ -5.3% \u00b7 "
          "BAYER $7.25BN \u00b7 24 DEAD IN NIGERIA BOAT \u00b7 "
          "36 MISSING IN CIKANDE \u00b7 BEPICOLOMBO: 6BN MILES")

# ------------------------------------------------------------------- render
def render():
    cv = Canvas(W, H, PAPER)
    mx = 16  # side margin

    # top accent bar
    cv.fill_rect(0, 0, W, 8, RED)

    # masthead
    cv.draw_text_centered(W // 2, 18, "THE WORLD IN ONE PAGE", 2, GREY)
    cv.draw_text_centered(W // 2, 46, "SUNDAY 22 NOVEMBER 2026", 6, INK)
    cv.fill_rect(mx, 96, W - 2 * mx, 3, RED)
    cv.hline(mx, 104, W - 2 * mx, INK, 1)

    # lead story
    y = 116
    cv.draw_text(mx, y, LEAD_TAG, 2, RED)
    y = 140
    y = draw_wrapped(cv, mx, y, LEAD_HEAD, W - 2 * mx, 4, INK, line_gap=6)
    y += 6
    y = draw_wrapped(cv, mx, y, LEAD_BODY, W - 2 * mx, 2, INK, line_gap=4)
    cv.hline(mx, 254, W - 2 * mx, RULE, 1)

    # tile grid: 3 columns x 6 rows
    gx0, gy0 = mx, 266
    gw = (W - 2 * mx - 2 * 12) // 3   # 322
    gh = 96
    for i, (tag, head, detail) in enumerate(TILES):
        col, row = i % 3, i // 3
        x = gx0 + col * (gw + 12)
        ty = gy0 + row * gh
        cv.draw_text(x, ty, tag, 2, RED)
        hy = ty + 20
        head_lines = wrap(head, gw, 2)
        assert len(head_lines) <= 2, head
        hy = draw_wrapped(cv, x, hy, head, gw, 2, INK, line_gap=3)
        det_lines = wrap(detail, gw, 2)
        assert len(det_lines) <= 2, detail
        draw_wrapped(cv, x, hy + 2, detail, gw, 2, GREY, line_gap=3)
        if col < 2:
            cv.vline(x + gw + 6, ty, gh - 10, RULE, 1)

    # timeline strip
    ty0 = 852
    cv.hline(mx, ty0, W - 2 * mx, INK, 2)
    cv.draw_text(mx, ty0 + 10, "THE DAY IN UTC", 2, RED)
    cv.draw_text(mx + text_width("THE DAY IN UTC", 2) + 16, ty0 + 10,
                 "AS REPORTED, IN TIME ORDER", 2, GREY)
    tw = (W - 2 * mx - 5 * 10) // 6   # ~157
    for i, (t, ev) in enumerate(TIMELINE):
        x = mx + i * (tw + 10)
        cv.draw_text(x, ty0 + 34, t, 2, RED)
        ev_lines = wrap(ev, tw, 2)
        assert len(ev_lines) <= 3, ev
        draw_wrapped(cv, x, ty0 + 56, ev, tw, 2, INK, line_gap=3)
    cv.hline(mx, 962, W - 2 * mx, INK, 2)

    # footer: world in numbers, two lines
    fy = 974
    foot_lines = wrap(FOOTER, W - 2 * mx, 2)
    assert len(foot_lines) <= 2, FOOTER
    fy = draw_wrapped(cv, mx, fy, FOOTER, W - 2 * mx, 2, BLUE, line_gap=4)
    cv.fill_rect(0, H - 6, W, 6, RED)
    return cv

# ---------------------------------------------------------------------- PNG
def encode_png(cv):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)  # filter: none
        off = yy * cv.w * 3
        raw += cv.px[off:off + cv.w * 3]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        c += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
        return c

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    return png

def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(render())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes)" % (path, len(png)))

if __name__ == "__main__":
    main()
