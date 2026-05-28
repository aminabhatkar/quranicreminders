"""
generate_image.py
-----------------
Generates a 3-slide Instagram carousel for each Quranic dua.

Slide 1  —  Title + Arabic text          (Amiri font, large)
Slide 2  —  Translation + Transliteration
Slide 3  —  Description / when to recite + source reference

One pastel colour theme is chosen per post (cycles through 5 palettes).
All slides share the same palette so the carousel feels cohesive.

Canvas: 1080 × 1080 px (Instagram square)

Fonts required in assets/fonts/:
    Amiri-Regular.ttf          — Arabic text (Slide 1)
    Amiri-Bold.ttf             — Arabic bold variant
    Cormorant-Regular.ttf      — Transliteration / body italic feel
    Cormorant-Italic.ttf       — Italic variant
    Poppins-Regular.ttf        — English body
    Poppins-Medium.ttf         — Labels, handle
    Poppins-SemiBold.ttf       — Slide titles

Required environment / file:
    duas.json                  — in project root
"""

import json
import math
import random
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

# ── Config ────────────────────────────────────────────────────────────────────
HANDLE     = "@quranic.reminders.co"
BASE_DIR   = Path(__file__).parent
FONTS_DIR  = BASE_DIR / "assets" / "fonts"
OUTPUT_DIR = BASE_DIR / "output_images"
DUAS_FILE  = BASE_DIR / "duas.json"

# Fonts
FONT_ARABIC       = FONTS_DIR / "Amiri-Regular.ttf"
FONT_ARABIC_BOLD  = FONTS_DIR / "Amiri-Bold.ttf"
FONT_SERIF        = FONTS_DIR / "Cormorant-Regular.ttf"
FONT_SERIF_ITALIC = FONTS_DIR / "Cormorant-Italic.ttf"
FONT_SANS         = FONTS_DIR / "Poppins-Regular.ttf"
FONT_SANS_MED     = FONTS_DIR / "Poppins-Medium.ttf"
FONT_SANS_SB      = FONTS_DIR / "Poppins-SemiBold.ttf"

W, H = 1080, 1080   # Instagram square

# ── Pastel Palettes ───────────────────────────────────────────────────────────
# Each palette: bg_top, bg_bottom, arabic, accent, body, muted, ornament
# Colours drawn from the Pastel Dua background templates conversation.

PALETTES = {
    "rose_blush": {
        "name":       "Rose Blush",
        "bg_top":     (253, 236, 236),   # very soft blush
        "bg_bottom":  (248, 220, 220),   # deeper blush
        "arabic":     (138,  60,  60),   # deep rose
        "accent":     (196, 122, 122),   # mid rose
        "body":       ( 80,  35,  35),   # dark rose / near-black
        "muted":      (180, 130, 130),   # muted rose
        "ornament":   (196, 122, 122),
    },
    "sage_mist": {
        "name":       "Sage Mist",
        "bg_top":     (232, 243, 236),   # very soft sage
        "bg_bottom":  (212, 232, 220),   # deeper sage
        "arabic":     ( 45, 112,  84),   # deep sage green
        "accent":     (106, 155, 122),   # mid sage
        "body":       ( 35,  70,  53),   # dark green / near-black
        "muted":      (130, 175, 150),   # muted sage
        "ornament":   (106, 155, 122),
    },
    "lavender_haze": {
        "name":       "Lavender Haze",
        "bg_top":     (238, 232, 248),   # soft lilac
        "bg_bottom":  (224, 215, 242),   # deeper lavender
        "arabic":     ( 80,  55, 138),   # deep violet
        "accent":     (138, 112, 184),   # mid lavender
        "body":       ( 55,  38, 100),   # dark violet / near-black
        "muted":      (168, 148, 210),   # muted lavender
        "ornament":   (138, 112, 184),
    },
    "golden_sand": {
        "name":       "Golden Sand",
        "bg_top":     (253, 244, 227),   # warm cream
        "bg_bottom":  (248, 232, 205),   # deeper sand
        "arabic":     (138,  96,  32),   # warm amber
        "accent":     (196, 154,  69),   # antique gold
        "body":       ( 90,  60,  18),   # dark amber / near-black
        "muted":      (200, 168, 100),   # muted gold
        "ornament":   (196, 154,  69),
    },
    "sky_bloom": {
        "name":       "Sky Bloom",
        "bg_top":     (227, 240, 253),   # powder blue
        "bg_bottom":  (210, 228, 248),   # periwinkle
        "arabic":     ( 38,  82, 138),   # deep sky blue
        "accent":     ( 90, 143, 196),   # mid blue
        "body":       ( 25,  55, 100),   # dark blue / near-black
        "muted":      (120, 168, 210),   # muted blue
        "ornament":   ( 90, 143, 196),
    },
}

PALETTE_ORDER = list(PALETTES.keys())

# ── Dummy dua (fallback) ──────────────────────────────────────────────────────
DUMMY_DUA = {
    "id":              0,
    "title":           "Dua for Good in Both Worlds",
    "arabic":          "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
    "transliteration": "Rabbana atina fid dunyaa hasanatanw wa fil aakhirati hasanatanw wa qinaa azaaban Naar",
    "translation":     "Our Lord, give us in this world that which is good and in the Hereafter that which is good, and protect us from the punishment of the Fire.",
    "surah":           "Al-Baqarah",
    "verse":           "2:201",
    "theme":           "dunya_akhira",
    "keywords":        ["dunya", "akhira", "protection"],
    "description":     "One of the most beloved duas any believer can recite. It balances asking for goodness in this life while never forgetting the hereafter. Recite it daily, especially after salah.",
    "used":            False,
}


# ── Dua picker ────────────────────────────────────────────────────────────────
def pick_dua() -> dict:
    """Returns the first unused dua from duas.json and marks it used."""
    if not DUAS_FILE.exists():
        print("Warning: duas.json not found — using dummy dua.")
        return DUMMY_DUA

    duas = json.loads(DUAS_FILE.read_text(encoding="utf-8"))
    unused = [d for d in duas if not d.get("used", False)]

    if not unused:
        print("All duas used — resetting the cycle...")
        for d in duas:
            d["used"] = False
        unused = duas

    chosen = unused[0]
    for d in duas:
        if d["id"] == chosen["id"]:
            d["used"] = True

    DUAS_FILE.write_text(
        json.dumps(duas, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f'Picked dua #{chosen["id"]}: "{chosen["title"]}"')
    return chosen


def pick_palette(dua: dict) -> dict:
    """
    Deterministically pick a palette from the dua id so the same dua
    always gets the same colour theme (useful for debugging / re-runs).
    """
    index = dua.get("id", 0) % len(PALETTE_ORDER)
    key   = PALETTE_ORDER[index]
    p     = PALETTES[key]
    print(f"Palette: {p['name']}")
    return p


# ── Text helpers ──────────────────────────────────────────────────────────────
def _line_height(font: ImageFont.FreeTypeFont) -> int:
    ascent, descent = font.getmetrics()
    return ascent + descent


def wrap_text(draw, text: str, font, max_width: int) -> list[str]:
    """Greedy word-wrap. Returns list of lines."""
    words   = text.split()
    lines, current = [], ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def wrap_arabic(draw, text: str, font, max_width: int) -> list[str]:
    """
    Arabic is RTL and words can be long. We still split on spaces
    (Arabic words are space-separated) but measure with Pillow which
    handles the glyph shaping correctly when using Amiri.
    """
    return wrap_text(draw, text, font, max_width)


def fit_text(draw, text: str, font_path: Path, box_w: int, box_h: int,
             max_size: int = 72, min_size: int = 26,
             line_spacing: float = 1.4) -> tuple:
    """
    Binary-ish search for the largest font size that fits text in box.
    Returns (font, lines, total_height).
    """
    for size in range(max_size, min_size - 1, -2):
        font   = ImageFont.truetype(str(font_path), size)
        lines  = wrap_text(draw, text, font, box_w)
        lh     = _line_height(font) * line_spacing
        total  = lh * len(lines)
        if total <= box_h:
            return font, lines, total
    font  = ImageFont.truetype(str(font_path), min_size)
    lines = wrap_text(draw, text, font, box_w)
    return font, lines, _line_height(font) * line_spacing * len(lines)


def fit_arabic(draw, text: str, font_path: Path, box_w: int, box_h: int,
               max_size: int = 96, min_size: int = 36,
               line_spacing: float = 1.6) -> tuple:
    """Same as fit_text but with Arabic-friendly defaults (bigger, more leading)."""
    for size in range(max_size, min_size - 1, -2):
        font   = ImageFont.truetype(str(font_path), size)
        lines  = wrap_arabic(draw, text, font, box_w)
        lh     = _line_height(font) * line_spacing
        total  = lh * len(lines)
        if total <= box_h:
            return font, lines, total
    font  = ImageFont.truetype(str(font_path), min_size)
    lines = wrap_arabic(draw, text, font, box_w)
    return font, lines, _line_height(font) * line_spacing * len(lines)


def draw_lines(draw, lines: list[str], font, cx: float, start_y: float,
               fill, line_spacing: float = 1.4) -> float:
    """Draw lines centred on cx. Returns y after last line."""
    lh = _line_height(font) * line_spacing
    y  = start_y
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text((cx - w / 2, y), line, font=font, fill=fill)
        y += lh
    return y


# ── Background ────────────────────────────────────────────────────────────────
def make_gradient(width: int, height: int,
                  top_rgb: tuple, bottom_rgb: tuple) -> Image.Image:
    base = Image.new("RGB", (width, height), top_rgb)
    bot  = Image.new("RGB", (width, height), bottom_rgb)
    mask = Image.new("L",   (width, height))
    mask.putdata([int(255 * y / height) for y in range(height) for _ in range(width)])
    base.paste(bot, (0, 0), mask)
    return base


# ── Decorative helpers ────────────────────────────────────────────────────────
def draw_divider(draw, cx: float, y: float, half_w: int, color: tuple,
                 thickness: int = 2):
    """Centered divider — line · diamond · line."""
    d = 6
    draw.line([(cx - half_w, y), (cx - d - 4, y)], fill=color, width=thickness)
    draw.line([(cx + d + 4,  y), (cx + half_w, y)], fill=color, width=thickness)
    draw.polygon(
        [(cx, y - d), (cx + d, y), (cx, y + d), (cx - d, y)],
        fill=color,
    )


def draw_corner_ornaments(draw, p: dict, size: int = 40, margin: int = 55):
    """Small diamond ornaments in all four corners."""
    c = p["ornament"] + (120,)   # add alpha if RGBA — but we use RGB, so just use color
    c = p["ornament"]
    positions = [
        (margin, margin),
        (W - margin, margin),
        (margin, H - margin),
        (W - margin, H - margin),
    ]
    d = size // 2
    for (x, y) in positions:
        draw.polygon(
            [(x, y - d), (x + d, y), (x, y + d), (x - d, y)],
            fill=c,
        )
        # inner dot
        r = d // 4
        draw.ellipse([(x - r, y - r), (x + r, y + r)], fill=p["bg_top"])


def draw_border(draw, p: dict, inset: int = 30, thickness: int = 1):
    """Thin rounded-rect border just inside the canvas edge."""
    c = p["ornament"]
    draw.rounded_rectangle(
        [(inset, inset), (W - inset, H - inset)],
        radius=18,
        outline=c,
        width=thickness,
    )


def draw_handle(draw, p: dict):
    """@handle centred at the bottom."""
    font = ImageFont.truetype(str(FONT_SANS_MED), 28)
    w    = draw.textlength(HANDLE, font=font)
    draw.text((W / 2 - w / 2, H - 72), HANDLE, font=font, fill=p["muted"])


def draw_slide_label(draw, p: dict, label: str):
    """Small label top-centre, e.g. 'SURAH AL-BAQARAH  ·  2:201'."""
    font = ImageFont.truetype(str(FONT_SANS_MED), 24)
    # light letter-spacing effect via thin spaces
    spaced = "\u2009".join(label.upper())
    w = draw.textlength(spaced, font=font)
    draw.text((W / 2 - w / 2, 58), spaced, font=font, fill=p["accent"])


# ── Slide renderers ───────────────────────────────────────────────────────────

def render_slide_1(dua: dict, p: dict) -> Image.Image:
    """
    Slide 1 — Title + Arabic text.
    Layout:
        [border + corner ornaments]
        [top label: SURAH · VERSE]
        [divider]
        [Title — Poppins SemiBold]
        [spacer]
        [Arabic — Amiri Bold, large, centred]
        [divider]
        [@handle]
    """
    img  = make_gradient(W, H, p["bg_top"], p["bg_bottom"])
    draw = ImageDraw.Draw(img)

    draw_border(draw, p)
    draw_corner_ornaments(draw, p)

    # Top label
    label = f"{dua['surah']}  ·  {dua['verse']}"
    draw_slide_label(draw, p, label)

    # Divider below label
    draw_divider(draw, W / 2, 115, 80, p["accent"])

    # Title
    title_font = ImageFont.truetype(str(FONT_SANS_SB), 38)
    title_lines = wrap_text(draw, dua["title"], title_font, W - 180)
    title_h = draw_lines(draw, title_lines, title_font, W / 2, 148, p["arabic"],
                         line_spacing=1.35)

    # Arabic — centred in remaining space
    arabic_box_top = title_h + 50
    arabic_box_h   = H - arabic_box_top - 160   # leave room for handle + lower divider

    arabic_font, arabic_lines, arabic_text_h = fit_arabic(
        draw, dua["arabic"], FONT_ARABIC_BOLD,
        W - 120, arabic_box_h,
        max_size=92, min_size=40,
    )

    arabic_start_y = arabic_box_top + (arabic_box_h - arabic_text_h) / 2
    arabic_end_y   = draw_lines(
        draw, arabic_lines, arabic_font, W / 2, arabic_start_y,
        p["arabic"], line_spacing=1.65,
    )

    # Divider above handle
    draw_divider(draw, W / 2, H - 105, 100, p["accent"])
    draw_handle(draw, p)

    return img


def render_slide_2(dua: dict, p: dict) -> Image.Image:
    """
    Slide 2 — Translation + Transliteration.
    Layout:
        [border + corner ornaments]
        [top label: TRANSLATION]
        [divider]
        [Translation — Cormorant Italic, large, centred]
        [spacer]
        [transliteration — Poppins Regular, smaller, muted]
        [divider]
        [@handle]
    """
    img  = make_gradient(W, H, p["bg_top"], p["bg_bottom"])
    draw = ImageDraw.Draw(img)

    draw_border(draw, p)
    draw_corner_ornaments(draw, p)

    # Top label
    draw_slide_label(draw, p, "Translation")
    draw_divider(draw, W / 2, 115, 80, p["accent"])

    margin  = 110
    box_w   = W - margin * 2
    zone_h  = 580   # space for translation text

    # Translation — large italic serif, centred
    trans_font, trans_lines, trans_h = fit_text(
        draw, f'"{dua["translation"]}"',
        FONT_SERIF_ITALIC, box_w, zone_h,
        max_size=68, min_size=30, line_spacing=1.45,
    )

    trans_start_y = 155 + (zone_h - trans_h) / 2
    trans_end_y   = draw_lines(
        draw, trans_lines, trans_font, W / 2, trans_start_y,
        p["body"], line_spacing=1.45,
    )

    # Spacer + divider
    div_y = trans_end_y + 32
    draw_divider(draw, W / 2, div_y, 120, p["accent"])

    # Transliteration — smaller, muted, italic
    translit_font = ImageFont.truetype(str(FONT_SERIF_ITALIC), 32)
    translit_lines = wrap_text(draw, dua["transliteration"], translit_font, box_w)
    draw_lines(
        draw, translit_lines, translit_font, W / 2, div_y + 28,
        p["muted"], line_spacing=1.4,
    )

    draw_divider(draw, W / 2, H - 105, 100, p["accent"])
    draw_handle(draw, p)

    return img


def render_slide_3(dua: dict, p: dict) -> Image.Image:
    """
    Slide 3 — Description / when to recite + source block.
    Layout:
        [border + corner ornaments]
        [top label: WHEN TO RECITE]
        [divider]
        [Description — Poppins Regular, body size]
        [spacer]
        [source block: Surah name (accent) · verse (muted)]
        [divider]
        [@handle]
    """
    img  = make_gradient(W, H, p["bg_top"], p["bg_bottom"])
    draw = ImageDraw.Draw(img)

    draw_border(draw, p)
    draw_corner_ornaments(draw, p)

    # Top label
    draw_slide_label(draw, p, "When to Recite")
    draw_divider(draw, W / 2, 115, 80, p["accent"])

    margin = 110
    box_w  = W - margin * 2
    zone_h = 560

    # Description
    desc_font, desc_lines, desc_h = fit_text(
        draw, dua["description"],
        FONT_SANS, box_w, zone_h,
        max_size=40, min_size=24, line_spacing=1.6,
    )

    desc_start_y = 150 + (zone_h - desc_h) / 2
    desc_end_y   = draw_lines(
        draw, desc_lines, desc_font, W / 2, desc_start_y,
        p["body"], line_spacing=1.6,
    )

    # Source block
    div_y = desc_end_y + 36
    draw_divider(draw, W / 2, div_y, 120, p["accent"])

    surah_font = ImageFont.truetype(str(FONT_SANS_SB), 32)
    sw = draw.textlength(dua["surah"], font=surah_font)
    draw.text((W / 2 - sw / 2, div_y + 28), dua["surah"],
              font=surah_font, fill=p["accent"])

    verse_font = ImageFont.truetype(str(FONT_SANS_MED), 28)
    verse_text = f"Verse {dua['verse']}"
    vw = draw.textlength(verse_text, font=verse_font)
    draw.text((W / 2 - vw / 2, div_y + 72), verse_text,
              font=verse_font, fill=p["muted"])

    draw_divider(draw, W / 2, H - 105, 100, p["accent"])
    draw_handle(draw, p)

    return img


# ── Main pipeline ─────────────────────────────────────────────────────────────
def generate(dua: dict = None) -> dict:
    """
    Full run:
      1. Pick a dua (or use the one passed in)
      2. Pick a pastel palette
      3. Render 3 Instagram carousel slides (1080×1080)
      4. Save to PNG / JPEG
      5. Return file paths + the dua used

    Returns:
        {
            "slide_1": str path,
            "slide_2": str path,
            "slide_3": str path,
            "dua":     dict,
        }
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    if dua is None:
        dua = pick_dua()

    palette = pick_palette(dua)

    # Build a clean filename slug from the dua id + title
    title_slug = (
        dua["title"]
        .lower()
        .replace(" ", "_")
        .replace("—", "")
        .replace("'", "")
        .replace(",", "")
        [:40]
    )
    date = datetime.now().strftime("%Y%m%d")
    base = f"dua_{dua['id']:03d}_{title_slug}_{date}"

    slides = {}

    print(f"\nGenerating Slide 1 — Title & Arabic ({palette['name']})...")
    s1     = render_slide_1(dua, palette)
    p1     = OUTPUT_DIR / f"{base}_slide1.jpg"
    s1.save(p1, "JPEG", quality=95)
    slides["slide_1"] = str(p1)
    print(f"  Saved: {p1.name}")

    print("Generating Slide 2 — Translation & Transliteration...")
    s2 = render_slide_2(dua, palette)
    p2 = OUTPUT_DIR / f"{base}_slide2.jpg"
    s2.save(p2, "JPEG", quality=95)
    slides["slide_2"] = str(p2)
    print(f"  Saved: {p2.name}")

    print("Generating Slide 3 — Description & Source...")
    s3 = render_slide_3(dua, palette)
    p3 = OUTPUT_DIR / f"{base}_slide3.jpg"
    s3.save(p3, "JPEG", quality=95)
    slides["slide_3"] = str(p3)
    print(f"  Saved: {p3.name}")

    slides["dua"] = dua
    return slides


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  Quranic Reminders  —  Dua Carousel Generator")
    print("=" * 55)

    result = generate()

    print("\nDone!")
    print(f"  Slide 1 (Title + Arabic)     -> {result['slide_1']}")
    print(f"  Slide 2 (Translation)        -> {result['slide_2']}")
    print(f"  Slide 3 (Description)        -> {result['slide_3']}")
    print(f'  Dua                          -> "{result["dua"]["title"]}"')
