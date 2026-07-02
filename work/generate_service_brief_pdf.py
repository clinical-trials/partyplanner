from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "gpu-retirement-service-brief.pdf"

IMG_TRIBUTE = Path("/Users/lgm/Downloads/36970f6d561325e5e793f3d71e70e906753a6c5ffb74f1526a68734dea782c77.png")
IMG_REWIRE = Path("/Users/lgm/Downloads/84678242f24bdf0eec5c1a99d4e82b3f1f57531a9061b1e720e48c27e6a0b9e4.png")
IMG_POSTER = ROOT / "outputs" / "assets" / "nvidia-retirement-concept.png"

W, H = landscape(letter)

NAVY = colors.HexColor("#07131f")
INK = colors.HexColor("#10202d")
CREAM = colors.HexColor("#fff8e7")
PAPER = colors.HexColor("#f7f1e4")
GOLD = colors.HexColor("#d8bd75")
GREEN = colors.HexColor("#76b900")
CYAN = colors.HexColor("#42d7d9")
MUTED = colors.HexColor("#637080")
LINE = colors.HexColor("#d8cfbb")
WHITE = colors.white


def register_fonts():
    candidates = [
        ("/System/Library/Fonts/Supplemental/Arial.ttf", "Body"),
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", "BodyBold"),
        ("/System/Library/Fonts/Supplemental/Georgia.ttf", "Serif"),
        ("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", "SerifBold"),
    ]
    for path, name in candidates:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(name, path))


def fit_font(text, font, size, max_width, min_size=7):
    while size > min_size and pdfmetrics.stringWidth(text, font, size) > max_width:
        size -= 0.4
    return size


def text(c, s, x, y, size=12, font="Body", color=INK, max_width=None):
    if max_width:
        size = fit_font(s, font, size, max_width)
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawString(x, y, s)


def centered(c, s, x, y, w, size=12, font="Body", color=INK):
    size = fit_font(s, font, size, w)
    c.setFillColor(color)
    c.setFont(font, size)
    c.drawCentredString(x + w / 2, y, s)


def wrap_lines(s, font, size, width):
    lines = []
    for para in s.split("\n"):
        words = para.split()
        line = ""
        for word in words:
            trial = f"{line} {word}".strip()
            if pdfmetrics.stringWidth(trial, font, size) <= width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def paragraph(c, s, x, y, w, size=10.5, font="Body", color=INK, leading=14, max_lines=None):
    c.setFillColor(color)
    c.setFont(font, size)
    lines = wrap_lines(s, font, size, w)
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def rounded(c, x, y, w, h, fill, stroke=None, radius=12, width=1):
    c.setFillColor(fill)
    c.setStrokeColor(stroke or fill)
    c.setLineWidth(width)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1 if stroke else 0)


def image_fit(c, path, x, y, w, h, radius=10):
    if not path.exists():
        rounded(c, x, y, w, h, colors.HexColor("#dde5e9"), radius=radius)
        centered(c, "Image missing", x, y + h / 2, w, 12, "BodyBold", MUTED)
        return
    with Image.open(path) as img:
        iw, ih = img.size
    scale = max(w / iw, h / ih)
    sw, sh = iw * scale, ih * scale
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, w, h, radius)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(str(path), x + (w - sw) / 2, y + (h - sh) / 2, sw, sh, preserveAspectRatio=True, mask="auto")
    c.restoreState()
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.2)
    c.roundRect(x, y, w, h, radius, fill=0, stroke=1)


def footer(c, page, dark=False):
    col = colors.HexColor("#8f9aa6") if dark else MUTED
    c.setFillColor(col)
    c.setFont("Body", 8.5)
    c.drawString(36, 22, "GPU Retirement Send-Offs - service brief")
    c.drawRightString(W - 36, 22, f"{page}/4")


def badge(c, label, x, y, fill=GREEN, w=None):
    w = w or pdfmetrics.stringWidth(label, "BodyBold", 9.5) + 20
    rounded(c, x, y, w, 22, fill, radius=11)
    centered(c, label, x, y + 7, w, 9.5, "BodyBold", WHITE)


def bullet(c, s, x, y, w, color=INK, accent=GREEN, size=10.2):
    c.setFillColor(accent)
    c.circle(x + 4, y + 4, 3.2, fill=1, stroke=0)
    return paragraph(c, s, x + 15, y, w - 15, size=size, font="Body", color=color, leading=13, max_lines=2)


def page1(c):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    image_fit(c, IMG_TRIBUTE, 405, 70, 350, 430, radius=16)
    image_fit(c, IMG_REWIRE, 510, 292, 220, 150, radius=12)
    c.setFillColor(colors.Color(0, 0, 0, alpha=0.28))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    text(c, "GPU RETIREMENT SEND-OFFS", 44, 482, 15, "BodyBold", GREEN)
    c.setFont("SerifBold", 44)
    c.setFillColor(CREAM)
    c.drawString(44, 416, "A real party planning")
    c.drawString(44, 366, "service for legacy careers.")
    paragraph(
        c,
        "For early employees, senior technical leaders, and successful retirees who deserve a personal send-off without making family or coworkers organize everything.",
        48,
        318,
        318,
        size=14,
        font="Body",
        color=colors.HexColor("#dce7e6"),
        leading=19,
    )
    badge(c, "memory intake", 50, 250, CYAN, 105)
    badge(c, "tribute deck", 165, 250, GREEN, 94)
    badge(c, "cake tasting", 269, 250, GOLD, 94)

    rounded(c, 48, 92, 306, 116, colors.Color(1, 1, 1, alpha=0.08), GOLD, radius=14, width=1)
    text(c, "Basic formula", 66, 178, 13, "BodyBold", GOLD)
    paragraph(
        c,
        "We sell relief: gather the memories, design the tribute, coordinate the cake, music, photos, giveaways, vendors, and run the event so guests can be present.",
        66,
        154,
        268,
        size=11.2,
        font="Body",
        color=CREAM,
        leading=15,
    )
    footer(c, 1, dark=True)


def page2(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    text(c, "The Service Bundle", 42, 494, 28, "SerifBold", INK)
    paragraph(c, "One calm planning package that turns a career into a memorable event.", 44, 462, 410, 12.5, "Body", MUTED, 16)
    image_fit(c, IMG_POSTER, 568, 346, 174, 132, radius=12)

    items = [
        ("Memory intake", "Short interviews, photos, career facts, favorite stories, and guest prompts."),
        ("Tribute deck", "A polished visual story with milestones, team impact, reflections, and photos."),
        ("Cake brief + tasting", "Flavor tasting, design direction, inscription, serving count, reveal moment, and delivery plan."),
        ("Group photo", "Shot list, timing, location, family-only, coworker-only, and everybody-together moments."),
        ("Music cues", "Arrival playlist, walk-up cues, tribute moment, cake reveal, closing song, and optional theme song."),
        ("Giveaways", "Tasteful keepsakes: cards, pins, shirts, photo prints, mugs, challenge coins, or desk objects."),
        ("Run-of-show", "Timed event flow with roles, speeches, vendor arrivals, transitions, and cues."),
        ("Vendor coordination", "Venue, catering, cake, photo/video, AV, printing, rentals, music, and day-of support."),
    ]

    x0, y0 = 44, 410
    card_w, card_h = 236, 70
    gap_x, gap_y = 22, 18
    for i, (head, body) in enumerate(items):
        col = i % 2
        row = i // 2
        x = x0 + col * (card_w + gap_x)
        y = y0 - row * (card_h + gap_y)
        rounded(c, x, y, card_w, card_h, WHITE, LINE, radius=10, width=0.8)
        c.setFillColor(GREEN if i != 2 else GOLD)
        c.rect(x, y, 5, card_h, fill=1, stroke=0)
        text(c, head, x + 16, y + 46, 12.2, "BodyBold", INK, max_width=card_w - 30)
        paragraph(c, body, x + 16, y + 29, card_w - 30, 9.2, "Body", MUTED, 11, max_lines=3)

    rounded(c, 568, 220, 174, 88, colors.HexColor("#eef7ee"), GREEN, radius=12, width=1)
    text(c, "Simple promise", 586, 278, 12, "BodyBold", INK)
    paragraph(c, "A meaningful send-off without asking an assistant, spouse, or coworker to become an event producer.", 586, 254, 140, 9.8, "Body", INK, 12)
    footer(c, 2)


def page3(c):
    c.setFillColor(colors.HexColor("#fbfaf4"))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    text(c, "Two Party Formats", 42, 494, 28, "SerifBold", INK)
    paragraph(c, "The buyer chooses the emotional center. The service bundle adapts around it.", 44, 462, 460, 12.5, "Body", MUTED, 16)

    image_fit(c, IMG_TRIBUTE, 44, 272, 320, 162, radius=14)
    image_fit(c, IMG_REWIRE, 428, 272, 320, 162, radius=14)

    rounded(c, 44, 78, 320, 176, WHITE, LINE, radius=12, width=1)
    text(c, "Coworker-Only Tribute", 66, 218, 17, "SerifBold", INK)
    y = 190
    for s in [
        "Career timeline, team memories, and NDA-safe achievement highlights.",
        "Tribute deck, group photo, speeches, light food and drink, and music cues.",
        "Best for company-centered retirements, founder-era employees, and senior contributors.",
    ]:
        y = bullet(c, s, 66, y, 260)
        y -= 8

    rounded(c, 428, 78, 320, 176, WHITE, LINE, radius=12, width=1)
    text(c, "Family + Friends Legacy Party", 450, 218, 17, "SerifBold", INK)
    y = 190
    for s in [
        "Full human story: career, family, mentorship, hobbies, travel, volunteering, and next chapter.",
        "Cake tasting, cake reveal, memory table, family photos, music, speeches, and keepsakes.",
        "Best when the celebration should feel warm, personal, and bigger than the job title.",
    ]:
        y = bullet(c, s, 450, y, 260, accent=GOLD)
        y -= 8
    footer(c, 3)


def page4(c):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    text(c, "Business Formula", 42, 494, 28, "SerifBold", CREAM)
    paragraph(c, "Keep the launch offer plain. Learn from real events. Then add margin where the work creates value.", 44, 462, 520, 12.5, "Body", colors.HexColor("#cfd8d7"), 16)

    rounded(c, 44, 302, 330, 114, colors.Color(1, 1, 1, alpha=0.08), GOLD, radius=14, width=1.1)
    text(c, "First 5 parties", 66, 378, 17, "SerifBold", GOLD)
    text(c, "actual event cost + 10%", 66, 344, 26, "BodyBold", CREAM, max_width=280)
    paragraph(c, "Designed to build the business, prove the process, create examples, and learn what buyers value most. Gratuity is always appreciated.", 66, 320, 280, 10.2, "Body", colors.HexColor("#dce7e6"), 13)

    rounded(c, 420, 302, 328, 114, colors.Color(1, 1, 1, alpha=0.08), GREEN, radius=14, width=1.1)
    text(c, "After pilots", 442, 378, 17, "SerifBold", GREEN)
    text(c, "direct costs + planning fee + add-ons + margin", 442, 344, 18, "BodyBold", CREAM, max_width=274)
    paragraph(c, "The fee covers memory intake, creative direction, vendor coordination, run-of-show, and day-of management.", 442, 320, 270, 10.2, "Body", colors.HexColor("#dce7e6"), 13)

    text(c, "Where the money is made", 48, 250, 18, "SerifBold", CREAM)
    money = [
        ("Planning fee", "Core coordination and day-of management."),
        ("Tribute production", "Deck, video reflections, memory gallery, keepsake PDF."),
        ("Cake + catering", "Cake tasting, brief, delivery coordination, food plan."),
        ("Giveaways", "Keepsakes with tasteful markup and package options."),
        ("Photo/video", "Group photo, short recap, guest message booth."),
        ("Music", "Playlist cues, custom theme song, or live musician coordination."),
    ]
    x, y = 48, 202
    for i, (head, body) in enumerate(money):
        cx = x + (i % 3) * 238
        cy = y - (i // 3) * 78
        rounded(c, cx, cy, 208, 54, colors.Color(1, 1, 1, alpha=0.075), None, radius=10)
        text(c, head, cx + 14, cy + 33, 11.5, "BodyBold", GOLD if i % 2 else GREEN)
        paragraph(c, body, cx + 14, cy + 18, 176, 8.8, "Body", colors.HexColor("#dce7e6"), 10, max_lines=2)

    rounded(c, 44, 36, 704, 50, GREEN, radius=12)
    centered(c, "Website headline: Retirement parties for people whose careers deserve a real send-off.", 58, 55, 676, 15, "BodyBold", NAVY)
    footer(c, 4, dark=True)


def main():
    register_fonts()
    c = canvas.Canvas(str(OUT), pagesize=landscape(letter))
    page1(c)
    c.showPage()
    page2(c)
    c.showPage()
    page3(c)
    c.showPage()
    page4(c)
    c.save()
    print(OUT)


if __name__ == "__main__":
    main()
