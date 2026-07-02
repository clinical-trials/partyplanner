from __future__ import annotations

import csv
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.pdfmetrics import stringWidth


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
PDF = OUT / "gpu-retirement-business-website-plan.pdf"
CSV = OUT / "gpu-retirement-revenue-model.csv"
IMG_POWERPOINT = Path("/Users/lgm/Downloads/36970f6d561325e5e793f3d71e70e906753a6c5ffb74f1526a68734dea782c77.png")
IMG_REWIREMENT = Path("/Users/lgm/Downloads/84678242f24bdf0eec5c1a99d4e82b3f1f57531a9061b1e720e48c27e6a0b9e4.png")
IMG_POSTER = OUT / "assets" / "nvidia-retirement-concept.png"


W, H = landscape(letter)

INK = colors.HexColor("#07110E")
DEEP = colors.HexColor("#0D1B18")
PANEL = colors.HexColor("#13241F")
SOFT = colors.HexColor("#F7F8F0")
PAPER = colors.HexColor("#FBF8EF")
LINE = colors.HexColor("#D7CAB2")
GREEN = colors.HexColor("#A6FF4D")
MINT = colors.HexColor("#5FFFD3")
GOLD = colors.HexColor("#F4CA64")
PEACH = colors.HexColor("#FFB08A")
TEAL = colors.HexColor("#0F5361")
MUTED = colors.HexColor("#61706A")
WHITE = colors.white


def money(value: float) -> str:
    return "${:,.0f}".format(value)


def wrap(c, text, font, size, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = word if not current else f"{current} {word}"
        if stringWidth(test, font, size) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_text(c, text, x, y, max_width, font="Helvetica", size=10, leading=None, color=INK, max_lines=None):
    leading = leading or size * 1.28
    c.setFont(font, size)
    c.setFillColor(color)
    lines = wrap(c, text, font, size, max_width)
    if max_lines:
        lines = lines[:max_lines]
    for i, line in enumerate(lines):
        c.drawString(x, y - i * leading, line)
    return y - len(lines) * leading


def draw_center(c, text, x, y, width, font="Helvetica", size=10, color=INK):
    c.setFont(font, size)
    c.setFillColor(color)
    c.drawCentredString(x + width / 2, y, text)


def rounded(c, x, y, w, h, fill, stroke=LINE, radius=12, sw=1):
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(sw)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)


def pill(c, text, x, y, w, fill=DEEP, color=GREEN):
    c.setFillColor(fill)
    c.setStrokeColor(GREEN)
    c.roundRect(x, y, w, 0.28 * inch, 0.14 * inch, stroke=1, fill=1)
    draw_center(c, text, x, y + 0.09 * inch, w, "Helvetica-Bold", 7.5, color)


def title(c, kicker, main, sub=None, dark=False):
    color = WHITE if dark else INK
    kc = GOLD if dark else TEAL
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(kc)
    c.drawString(0.55 * inch, H - 0.62 * inch, kicker.upper())
    c.setFont("Helvetica-Bold", 25)
    c.setFillColor(color)
    c.drawString(0.55 * inch, H - 1.02 * inch, main)
    if sub:
        draw_text(c, sub, 0.55 * inch, H - 1.32 * inch, 6.6 * inch, "Helvetica", 10, color=color if dark else MUTED)


def footer(c, page):
    c.setStrokeColor(colors.HexColor("#D8D8C8"))
    c.line(0.55 * inch, 0.36 * inch, W - 0.55 * inch, 0.36 * inch)
    c.setFont("Helvetica", 7)
    c.setFillColor(MUTED)
    c.drawString(0.55 * inch, 0.2 * inch, "Independent service concept. Not affiliated with, endorsed by, or sponsored by NVIDIA Corporation.")
    c.drawRightString(W - 0.55 * inch, 0.2 * inch, f"{page}")


def draw_image_fit(c, path, x, y, w, h):
    if not path.exists():
        rounded(c, x, y, w, h, colors.HexColor("#EDE8DC"))
        draw_center(c, "image missing", x, y + h / 2, w, "Helvetica", 10, MUTED)
        return
    img = ImageReader(str(path))
    iw, ih = img.getSize()
    scale = min(w / iw, h / ih)
    dw, dh = iw * scale, ih * scale
    c.drawImage(img, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh, preserveAspectRatio=True, mask="auto")


def card(c, x, y, w, h, heading, body, accent=GREEN, fill=WHITE):
    rounded(c, x, y, w, h, fill, stroke=colors.HexColor("#D8D2C0"), radius=10)
    c.setFillColor(accent)
    c.roundRect(x + 0.12 * inch, y + h - 0.18 * inch, 0.42 * inch, 0.06 * inch, 0.03 * inch, stroke=0, fill=1)
    draw_text(c, heading, x + 0.16 * inch, y + h - 0.42 * inch, w - 0.32 * inch, "Helvetica-Bold", 12, color=INK)
    draw_text(c, body, x + 0.16 * inch, y + h - 0.72 * inch, w - 0.32 * inch, "Helvetica", 8.5, color=MUTED)


def metric(c, x, y, w, label, value, note, fill=WHITE):
    rounded(c, x, y, w, 0.95 * inch, fill, stroke=colors.HexColor("#D8D2C0"), radius=10)
    draw_center(c, value, x, y + 0.51 * inch, w, "Helvetica-Bold", 18, INK)
    draw_center(c, label, x, y + 0.26 * inch, w, "Helvetica-Bold", 7.5, TEAL)
    draw_center(c, note, x, y + 0.11 * inch, w, "Helvetica", 6.8, MUTED)


def row_rule(c, y):
    c.setStrokeColor(colors.HexColor("#DDD4C2"))
    c.line(0.65 * inch, y, W - 0.65 * inch, y)


def export_csv():
    rows = [
        ["Pilot First Five", 5, "cost + 10%", 3200, 3520, 1600, "gratuity optional"],
        ["Conservative Year 1", 24, "mixed packages", 5835, 140040, 59625, "after first five"],
        ["Base Year 1", 54, "mixed packages", 7078, 382212, 159149, "after first five"],
        ["Aggressive Year 2", 154, "mixed packages", 8268, 1273272, 528498, "requires contractors"],
    ]
    with CSV.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Scenario", "Events", "Pricing", "Avg cost basis", "Avg billed per event", "Operating profit before owner salary/tax", "Notes"])
        writer.writerows(rows)


def page_cover(c):
    c.setFillColor(DEEP)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor(GREEN)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(0.55 * inch, H - 0.55 * inch, "RETIREMENT PARTY PLANNER BUSINESS")
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 33)
    c.drawString(0.55 * inch, H - 1.22 * inch, "GPU Retirement")
    c.drawString(0.55 * inch, H - 1.68 * inch, "Send-Offs")
    draw_text(c, "A warm, NDA-aware celebration service for technical teams, families, and retirees who deserve a real send-off.", 0.58 * inch, H - 2.07 * inch, 4.2 * inch, "Helvetica", 12, color=colors.HexColor("#E7F8DF"))
    pill(c, "business plan + website plan + revenue model", 0.58 * inch, H - 2.78 * inch, 2.95 * inch)
    rounded(c, 5.5 * inch, 0.7 * inch, 4.85 * inch, 6.35 * inch, colors.HexColor("#101D24"), stroke=GOLD, radius=18)
    draw_image_fit(c, IMG_POWERPOINT, 5.72 * inch, 3.95 * inch, 4.4 * inch, 2.65 * inch)
    draw_image_fit(c, IMG_REWIREMENT, 5.72 * inch, 1.0 * inch, 4.4 * inch, 2.65 * inch)
    metric(c, 0.58 * inch, 1.0 * inch, 1.35 * inch, "pilot", "5", "events at cost + 10%", fill=colors.HexColor("#EEF6E8"))
    metric(c, 2.08 * inch, 1.0 * inch, 1.35 * inch, "base case", "$382K", "annual revenue", fill=colors.HexColor("#EEF6E8"))
    metric(c, 3.58 * inch, 1.0 * inch, 1.35 * inch, "signature", "$4.8K", "package from", fill=colors.HexColor("#EEF6E8"))
    c.showPage()


def page_business(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    title(c, "Business model", "What this business actually sells", "The product is not a party theme. It is relief: someone else turns a career into a kind, polished, safe-to-share celebration.")
    card(c, 0.65 * inch, 4.95 * inch, 3.0 * inch, 1.25 * inch, "Primary buyer", "Managers, spouses, families, retirement committees, alumni groups, and team leads who need a meaningful celebration without inventing the process.", TEAL)
    card(c, 3.95 * inch, 4.95 * inch, 3.0 * inch, 1.25 * inch, "Core offer", "A planning service that bundles memory intake, tribute deck, cake brief, group photo, music cues, giveaways, run-of-show, and vendor coordination.", GREEN)
    card(c, 7.25 * inch, 4.95 * inch, 3.0 * inch, 1.25 * inch, "Defensible angle", "NDA-aware career storytelling for technical teams, balanced with family-friendly warmth and retiree comfort.", GOLD)
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(INK)
    c.drawString(0.65 * inch, 4.25 * inch, "Launch policy: first 5 parties")
    rounded(c, 0.65 * inch, 2.78 * inch, 9.6 * inch, 1.16 * inch, colors.HexColor("#FFF3D9"), stroke=GOLD, radius=14)
    draw_text(c, "First five parties are offered at cost + 10% to build the business, validate the offer, collect testimonials, capture visual examples, and refine vendor pricing. This is a deliberate pilot strategy, not the long-term price anchor.", 0.92 * inch, 3.58 * inch, 8.95 * inch, "Helvetica-Bold", 12, color=INK)
    draw_text(c, "Gratuity is always appreciated, but never required and never used to make the model work. Pricing should stand on its own.", 0.92 * inch, 3.03 * inch, 8.95 * inch, "Helvetica", 10.5, color=MUTED)
    labels = [("1", "Pilot at cost + 10%"), ("2", "Document every workflow"), ("3", "Package repeatable moments"), ("4", "Move to margin pricing")]
    for i, (num, lab) in enumerate(labels):
        x = 0.8 * inch + i * 2.45 * inch
        c.setFillColor(DEEP)
        c.circle(x, 1.75 * inch, 0.19 * inch, stroke=0, fill=1)
        draw_center(c, num, x - 0.19 * inch, 1.69 * inch, 0.38 * inch, "Helvetica-Bold", 10, GREEN)
        draw_text(c, lab, x + 0.32 * inch, 1.86 * inch, 1.55 * inch, "Helvetica-Bold", 9.3, color=INK)
    footer(c, 2)
    c.showPage()


def page_packages(c):
    c.setFillColor(SOFT)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    title(c, "Offer ladder", "Packages that feel human, not corporate", "Use clear tiers, then attach memorable moments: cake, group photo, music, giveaway, story wall, and tribute deck.")
    packages = [
        ("Pilot Five", "cost + 10%", "First five client events. Covers vendors, materials, contractor costs, and a small coordination margin. Goal: proof, photos, testimonials, and timing data.", PEACH),
        ("Founders' Toast", "$1,750+", "Warm small-room send-off with theme direction, short deck, welcome board, and run-of-show.", GREEN),
        ("GPU Giant", "$4,800+", "Signature package with story intake, cake brief, group photo, giveaway prompts, soundtrack planning, deck, and vendor coordination.", MINT),
        ("Legendary Send-Off", "$9,500+", "Full milestone event with premium tribute, custom soundtrack or montage, photo wall, keepsakes, on-site support, and memory package.", GOLD),
    ]
    for i, (name, price, desc, accent) in enumerate(packages):
        x = 0.65 * inch + (i % 2) * 4.95 * inch
        y = 4.35 * inch - (i // 2) * 2.05 * inch
        rounded(c, x, y, 4.55 * inch, 1.65 * inch, WHITE, stroke=colors.HexColor("#D8D2C0"), radius=16)
        c.setFillColor(accent)
        c.roundRect(x, y + 1.42 * inch, 4.55 * inch, 0.23 * inch, 0.1 * inch, stroke=0, fill=1)
        draw_text(c, name, x + 0.2 * inch, y + 1.15 * inch, 2.55 * inch, "Helvetica-Bold", 15, color=INK)
        draw_text(c, price, x + 3.15 * inch, y + 1.16 * inch, 1.0 * inch, "Helvetica-Bold", 14, color=TEAL)
        draw_text(c, desc, x + 0.2 * inch, y + 0.78 * inch, 4.05 * inch, "Helvetica", 9.2, color=MUTED)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(INK)
    c.drawString(0.65 * inch, 1.2 * inch, "Attachable moments")
    moments = ["Career soundtrack", "Cake design", "Group photo", "Giveaway table", "NDA story package", "Catering coordination"]
    for i, m in enumerate(moments):
        pill(c, m, 2.55 * inch + (i % 3) * 2.1 * inch, 1.06 * inch - (i // 3) * 0.38 * inch, 1.75 * inch, fill=WHITE, color=TEAL)
    footer(c, 3)
    c.showPage()


def page_revenue(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    title(c, "Revenue model", "Pilot learning first, margin second", "The first five parties validate costs and demand. After that, package pricing becomes the margin engine.")
    metric(c, 0.65 * inch, 4.96 * inch, 1.95 * inch, "pilot billing", "cost + 10%", "first 5 events", fill=colors.HexColor("#FFF3D9"))
    metric(c, 2.85 * inch, 4.96 * inch, 1.95 * inch, "base avg", "$7,078", "revenue per event", fill=WHITE)
    metric(c, 5.05 * inch, 4.96 * inch, 1.95 * inch, "base annual", "$382K", "54 events/year", fill=WHITE)
    metric(c, 7.25 * inch, 4.96 * inch, 1.95 * inch, "base profit", "$159K", "before owner salary/tax", fill=WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(INK)
    c.drawString(0.7 * inch, 4.18 * inch, "Scenario revenue")
    scenarios = [("Conservative", 140040, GREEN), ("Base Case", 382212, GOLD), ("Aggressive", 1273272, MINT)]
    maxv = max(v for _, v, _ in scenarios)
    for i, (name, value, color) in enumerate(scenarios):
        y = 3.68 * inch - i * 0.52 * inch
        draw_text(c, name, 0.8 * inch, y + 0.1 * inch, 1.4 * inch, "Helvetica-Bold", 9, color=INK)
        draw_text(c, money(value), 2.05 * inch, y + 0.1 * inch, 1.1 * inch, "Helvetica", 9, color=MUTED)
        c.setFillColor(colors.HexColor("#E7EDE1"))
        c.roundRect(3.1 * inch, y, 5.8 * inch, 0.18 * inch, 0.08 * inch, stroke=0, fill=1)
        c.setFillColor(color)
        c.roundRect(3.1 * inch, y, 5.8 * inch * value / maxv, 0.18 * inch, 0.08 * inch, stroke=0, fill=1)
    rounded(c, 0.7 * inch, 0.95 * inch, 9.5 * inch, 1.35 * inch, colors.HexColor("#F4FBEF"), stroke=colors.HexColor("#D4DEC9"), radius=14)
    draw_text(c, "Important operating assumption", 0.95 * inch, 1.95 * inch, 4.5 * inch, "Helvetica-Bold", 12, color=INK)
    draw_text(c, "Do not build pricing around gratuity. Gratuity can be welcomed after excellent service, but margins should come from package design, reusable templates, add-on attachment, and vendor control.", 0.95 * inch, 1.62 * inch, 8.9 * inch, "Helvetica", 10, color=MUTED)
    footer(c, 4)
    c.showPage()


def page_website(c):
    c.setFillColor(SOFT)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    title(c, "Website plan", "Make the website useful before it sells", "The site should work like a tiny planning assistant: inspire, help sketch the event, then convert.")
    steps = [
        ("1. Hero", "A send-off they will actually love. Use warm tech legacy visuals, not a cold vendor pitch."),
        ("2. Ideas", "Cake, group photo, giveaway, career soundtrack, story wall, and tribute deck examples."),
        ("3. Planner", "Visitor enters date, tone, guests, and must-have moments. Site generates checklist and brief."),
        ("4. Quote", "Planner brief flows into quote notes. Buyer sees package and add-on estimate."),
        ("5. Trust", "Confidentiality, independent status, review pass, and family/team participation."),
    ]
    for i, (head, body) in enumerate(steps):
        y = 5.75 * inch - i * 0.9 * inch
        c.setFillColor(DEEP)
        c.circle(0.85 * inch, y + 0.08 * inch, 0.18 * inch, stroke=0, fill=1)
        draw_center(c, str(i + 1), 0.67 * inch, y + 0.02 * inch, 0.36 * inch, "Helvetica-Bold", 9, GREEN)
        draw_text(c, head, 1.18 * inch, y + 0.19 * inch, 2.2 * inch, "Helvetica-Bold", 12, color=INK)
        draw_text(c, body, 3.05 * inch, y + 0.19 * inch, 6.4 * inch, "Helvetica", 9.2, color=MUTED)
        row_rule(c, y - 0.24 * inch)
    rounded(c, 6.9 * inch, 0.76 * inch, 3.15 * inch, 1.35 * inch, colors.HexColor("#FFF3D9"), stroke=GOLD, radius=12)
    draw_text(c, "Design cue from new images", 7.12 * inch, 1.78 * inch, 2.65 * inch, "Helvetica-Bold", 10.5, color=INK)
    draw_text(c, "Use tribute-gallery modules, personal reflection video cards, compass/new-adventure motifs, and polished achievement timelines.", 7.12 * inch, 1.5 * inch, 2.65 * inch, "Helvetica", 8.3, color=MUTED)
    footer(c, 5)
    c.showPage()


def page_delivery(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    title(c, "Party planner operating system", "What gets built behind the website", "The business scales when every event follows a repeatable planning system.")
    left_items = [
        ("Intake", "Retiree name, tone, surprise tolerance, guest count, date, venue, confidentiality level."),
        ("Memory collection", "Coworker prompts, family notes, photos, favorite songs, career moments, safe achievements."),
        ("Creative kit", "Theme board, deck outline, cake brief, group photo plan, giveaway cards, soundtrack plan."),
        ("Run-of-show", "Arrival, welcome, food, cake/photo, tribute, music cue, send-off, cleanup."),
    ]
    for i, (head, body) in enumerate(left_items):
        card(c, 0.65 * inch, 5.58 * inch - i * 1.18 * inch, 4.55 * inch, 0.88 * inch, head, body, accent=GREEN if i % 2 == 0 else GOLD)
    rounded(c, 5.55 * inch, 1.05 * inch, 4.7 * inch, 5.35 * inch, DEEP, stroke=GOLD, radius=18)
    draw_text(c, "Pilot data to capture", 5.9 * inch, 5.95 * inch, 3.9 * inch, "Helvetica-Bold", 18, color=WHITE)
    for i, line in enumerate([
        "Actual vendor cost by category",
        "Planner hours by phase",
        "Which add-ons attach most often",
        "Which moments retirees mention afterward",
        "Photos/testimonials approved for marketing",
        "What buyers found confusing",
        "What should become a template",
    ]):
        y = 5.45 * inch - i * 0.48 * inch
        c.setFillColor(GREEN)
        c.circle(5.9 * inch, y + 0.05 * inch, 0.055 * inch, stroke=0, fill=1)
        draw_text(c, line, 6.1 * inch, y + 0.12 * inch, 3.65 * inch, "Helvetica", 10, color=colors.HexColor("#EAF7E2"))
    footer(c, 6)
    c.showPage()


def page_goto_market(c):
    c.setFillColor(SOFT)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    title(c, "Go-to-market", "Build proof through the first five parties", "The launch strategy is not discounting forever. It is learning cheaply and converting proof into premium pricing.")
    phases = [
        ("0-30 days", "Finish MVP site, publish idea pages, create sample themes, and prepare pilot checklist."),
        ("31-60 days", "Run first two cost + 10% events, capture photos/testimonials, refine cost model."),
        ("61-90 days", "Run remaining pilot events, publish examples, raise standard package pricing."),
        ("After pilots", "Sell signature package, add contractors, and focus on referrals from every event."),
    ]
    for i, (head, body) in enumerate(phases):
        x = 0.65 * inch + i * 2.45 * inch
        rounded(c, x, 4.25 * inch, 2.1 * inch, 1.65 * inch, WHITE, stroke=colors.HexColor("#D8D2C0"), radius=14)
        draw_text(c, head, x + 0.15 * inch, 5.45 * inch, 1.78 * inch, "Helvetica-Bold", 12, color=INK)
        draw_text(c, body, x + 0.15 * inch, 5.08 * inch, 1.78 * inch, "Helvetica", 8.3, color=MUTED)
    c.setFont("Helvetica-Bold", 15)
    c.setFillColor(INK)
    c.drawString(0.65 * inch, 3.35 * inch, "Search pages to publish")
    tags = ["engineer retirement party ideas", "tech retirement cake ideas", "corporate retirement giveaways", "retirement group photo ideas", "NDA-friendly tribute deck", "retirement party music ideas"]
    for i, tag in enumerate(tags):
        pill(c, tag, 0.7 * inch + (i % 2) * 4.85 * inch, 2.78 * inch - (i // 2) * 0.45 * inch, 4.05 * inch, fill=WHITE, color=TEAL)
    rounded(c, 0.7 * inch, 0.72 * inch, 9.55 * inch, 0.78 * inch, colors.HexColor("#F4FBEF"), stroke=colors.HexColor("#D4DEC9"), radius=12)
    draw_text(c, "Referral loop: every event should end with a group photo, a memory package, a thank-you email, and a soft referral ask to adjacent teams.", 0.95 * inch, 1.17 * inch, 8.9 * inch, "Helvetica-Bold", 10.5, color=INK)
    footer(c, 7)
    c.showPage()


def page_risks(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    title(c, "Risks and controls", "Keep the service premium, safe, and kind", "The biggest risks are tone, confidentiality, brand confusion, and underpricing the planner's labor.")
    risks = [
        ("Affiliation risk", "Use an independent-service disclaimer. Avoid implying NVIDIA sponsorship."),
        ("Confidentiality risk", "Use NDA-aware intake, public-safe copy, and optional review pass."),
        ("Tone risk", "Capture humor boundaries, surprise tolerance, songs to avoid, and family input."),
        ("Margin risk", "Do not price from vibes. Track actual costs, planner hours, and contractor spend."),
        ("Capacity risk", "Template decks, prompts, vendor briefs, playlists, and run-of-show documents."),
        ("Website risk", "Lead with retiree joy before price. The site should feel useful, not transactional."),
    ]
    for i, (head, body) in enumerate(risks):
        x = 0.65 * inch + (i % 2) * 4.9 * inch
        y = 5.38 * inch - (i // 2) * 1.25 * inch
        card(c, x, y, 4.45 * inch, 0.95 * inch, head, body, accent=PEACH if i % 2 else GREEN)
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(INK)
    c.drawString(0.65 * inch, 1.45 * inch, "Next decision")
    draw_text(c, "Position this as a GPU/NVIDIA-inspired specialty first, then broaden to retirement parties for technical teams after the first proof events.", 0.65 * inch, 1.12 * inch, 8.7 * inch, "Helvetica-Bold", 13, color=TEAL)
    footer(c, 8)
    c.showPage()


def build():
    export_csv()
    c = canvas.Canvas(str(PDF), pagesize=landscape(letter))
    c.setTitle("GPU Retirement Send-Offs Business and Website Plan")
    page_cover(c)
    page_business(c)
    page_packages(c)
    page_revenue(c)
    page_website(c)
    page_delivery(c)
    page_goto_market(c)
    page_risks(c)
    c.save()
    print(PDF)
    print(CSV)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    build()
