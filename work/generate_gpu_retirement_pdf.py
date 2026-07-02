from __future__ import annotations

import csv
import html
import os
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs"
ASSET = OUTPUT_DIR / "assets" / "nvidia-retirement-concept.png"
PDF_PATH = OUTPUT_DIR / "gpu-retirement-business-website-plan.pdf"
CSV_PATH = OUTPUT_DIR / "gpu-retirement-revenue-model.csv"


GREEN = colors.HexColor("#A6FF4D")
MINT = colors.HexColor("#5FFFD3")
GOLD = colors.HexColor("#F4CA64")
PEACH = colors.HexColor("#FFB08A")
DARK = colors.HexColor("#07110E")
PANEL = colors.HexColor("#10221D")
INK = colors.HexColor("#17211D")
MUTED = colors.HexColor("#5A675F")
LIGHT = colors.HexColor("#F7FFF2")
LINE = colors.HexColor("#C8DAC1")


@dataclass
class Scenario:
    name: str
    leads_per_month: float
    close_rate: float
    events_per_year: int
    package_revenue_per_event: float
    addon_revenue_per_event: float
    gross_margin: float
    fixed_costs: float

    @property
    def avg_revenue_per_event(self) -> float:
        return self.package_revenue_per_event + self.addon_revenue_per_event

    @property
    def annual_revenue(self) -> float:
        return self.events_per_year * self.avg_revenue_per_event

    @property
    def gross_profit(self) -> float:
        return self.annual_revenue * self.gross_margin

    @property
    def operating_profit(self) -> float:
        return self.gross_profit - self.fixed_costs


SCENARIOS = [
    Scenario("Conservative", 8, 0.25, 24, 4285, 1550, 0.62, 27200),
    Scenario("Base Case", 15, 0.30, 54, 4978, 2100, 0.61, 74000),
    Scenario("Aggressive", 40, 0.32, 154, 5518, 2750, 0.58, 210000),
]


def money(value: float) -> str:
    return "${:,.0f}".format(value)


def percent(value: float) -> str:
    return "{:.0%}".format(value)


def p(text: str, style: ParagraphStyle):
    return Paragraph(text, style)


def bullet(text: str, styles):
    return Paragraph(f"- {text}", styles["Bullet"])


def table(data, widths, header=True, align_right_cols=None):
    align_right_cols = align_right_cols or []
    header_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=9.4,
        textColor=LIGHT,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=7.8,
        leading=9.6,
        textColor=INK,
    )
    converted = []
    for row_index, row in enumerate(data):
        converted_row = []
        for cell in row:
            if isinstance(cell, str):
                style = header_style if header and row_index == 0 else cell_style
                converted_row.append(Paragraph(html.escape(cell), style))
            else:
                converted_row.append(cell)
        converted.append(converted_row)
    t = Table(converted, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = [
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#DDE8D8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.8),
    ]
    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK),
                ("TEXTCOLOR", (0, 0), (-1, 0), LIGHT),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    for col in align_right_cols:
        style.append(("ALIGN", (col, 1 if header else 0), (col, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


def header_footer(canvas, doc):
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(DARK)
    canvas.rect(0, height - 0.42 * inch, width, 0.42 * inch, stroke=0, fill=1)
    canvas.setFillColor(GREEN)
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.drawString(doc.leftMargin, height - 0.27 * inch, "GPU Retirement Send-Offs")
    canvas.setFillColor(colors.HexColor("#DCEAD6"))
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(width - doc.rightMargin, height - 0.27 * inch, f"Page {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#C8DAC1"))
    canvas.line(doc.leftMargin, 0.48 * inch, width - doc.rightMargin, 0.48 * inch)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(
        doc.leftMargin,
        0.3 * inch,
        "Independent concept. Not affiliated with, endorsed by, or sponsored by NVIDIA Corporation.",
    )
    canvas.restoreState()


def add_section(story, title, subtitle, styles):
    story.append(Spacer(1, 0.1 * inch))
    story.append(p(title, styles["SectionTitle"]))
    if subtitle:
        story.append(p(subtitle, styles["Lead"]))
    story.append(Spacer(1, 0.12 * inch))


def make_revenue_chart(scenarios):
    max_revenue = max(s.annual_revenue for s in scenarios)
    rows = [[p("<b>Scenario</b>", chart_style), p("<b>Annual revenue</b>", chart_style), ""]]
    for s in scenarios:
        width = max(0.3, 3.1 * (s.annual_revenue / max_revenue))
        bar = Table([[""]], colWidths=[width * inch], rowHeights=[0.16 * inch])
        bar.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), GREEN if s.name == "Base Case" else MINT),
                    ("BOX", (0, 0), (-1, -1), 0.1, colors.white),
                ]
            )
        )
        rows.append([s.name, money(s.annual_revenue), bar])
    return Table(rows, colWidths=[1.2 * inch, 1.15 * inch, 3.35 * inch], hAlign="LEFT")


def export_revenue_csv():
    with CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Scenario",
                "Leads per month",
                "Close rate",
                "Events per year",
                "Package revenue per event",
                "Addon revenue per event",
                "Average revenue per event",
                "Annual revenue",
                "Gross margin",
                "Gross profit",
                "Fixed costs",
                "Operating profit before owner salary and tax",
            ]
        )
        for s in SCENARIOS:
            writer.writerow(
                [
                    s.name,
                    s.leads_per_month,
                    percent(s.close_rate),
                    s.events_per_year,
                    round(s.package_revenue_per_event),
                    round(s.addon_revenue_per_event),
                    round(s.avg_revenue_per_event),
                    round(s.annual_revenue),
                    percent(s.gross_margin),
                    round(s.gross_profit),
                    round(s.fixed_costs),
                    round(s.operating_profit),
                ]
            )


def build_pdf():
    export_revenue_csv()
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.72 * inch,
        bottomMargin=0.65 * inch,
        title="GPU Retirement Business and Website Plan",
        author="Codex",
    )

    base = getSampleStyleSheet()
    styles = {
        "Title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=28,
            leading=30,
            alignment=TA_LEFT,
            textColor=LIGHT,
            spaceAfter=10,
        ),
        "Subtitle": ParagraphStyle(
            "Subtitle",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#E7F8DF"),
        ),
        "SectionTitle": ParagraphStyle(
            "SectionTitle",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=DARK,
            spaceBefore=8,
            spaceAfter=5,
        ),
        "Subhead": ParagraphStyle(
            "Subhead",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=INK,
            spaceBefore=6,
            spaceAfter=3,
        ),
        "Body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.6,
            leading=13.2,
            textColor=INK,
            spaceAfter=6,
        ),
        "Lead": ParagraphStyle(
            "Lead",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10.4,
            leading=14.4,
            textColor=MUTED,
            spaceAfter=8,
        ),
        "Bullet": ParagraphStyle(
            "Bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=12.4,
            textColor=INK,
            leftIndent=10,
            firstLineIndent=-7,
            spaceAfter=2.2,
        ),
        "Small": ParagraphStyle(
            "Small",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.7,
            leading=10,
            textColor=MUTED,
        ),
        "Metric": ParagraphStyle(
            "Metric",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=17,
            textColor=DARK,
            alignment=TA_CENTER,
        ),
        "MetricLabel": ParagraphStyle(
            "MetricLabel",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.6,
            leading=9.5,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }

    global chart_style
    chart_style = styles["Small"]

    story = []

    # Cover panel
    cover_data = []
    left = [
        p("GPU Retirement Send-Offs", styles["Title"]),
        p("Business Plan + Website Plan + Revenue Model", styles["Subtitle"]),
        Spacer(1, 0.12 * inch),
        p(
            "A warm, NDA-aware celebration service for technical teams, retirees, families, and coworkers who want a send-off that feels human, personal, and easy to plan.",
            styles["Subtitle"],
        ),
        Spacer(1, 0.22 * inch),
        table(
            [
                ["Core promise", "Help teams celebrate the person behind the work."],
                ["Primary buyer", "Manager, spouse, family member, team lead, or retirement committee."],
                ["Revenue engine", "Packages, add-ons, planning deposits, vendor coordination, and repeat referrals."],
            ],
            [1.45 * inch, 3.2 * inch],
            header=False,
        ),
    ]
    if ASSET.exists():
        img = Image(str(ASSET), width=1.85 * inch, height=3.3 * inch)
        cover_data = [[left, img]]
        cover_table = Table(cover_data, colWidths=[4.65 * inch, 1.9 * inch])
    else:
        cover_table = Table([[left]], colWidths=[6.55 * inch])
    cover_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DARK),
                ("BOX", (0, 0), (-1, -1), 0.8, GREEN),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 20),
                ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                ("TOPPADDING", (0, 0), (-1, -1), 18),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
            ]
        )
    )
    story.append(cover_table)
    story.append(Spacer(1, 0.2 * inch))

    metric_data = [
        [p("3", styles["Metric"]), p("$4.8K", styles["Metric"]), p("$7.1K", styles["Metric"]), p("54", styles["Metric"])],
        [
            p("package tiers", styles["MetricLabel"]),
            p("signature package from", styles["MetricLabel"]),
            p("base-case avg revenue/event", styles["MetricLabel"]),
            p("base-case events/year", styles["MetricLabel"]),
        ],
    ]
    mt = Table(metric_data, colWidths=[1.55 * inch] * 4)
    mt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F4FBEF")),
                ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, LINE),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(mt)
    story.append(PageBreak())

    add_section(story, "1. Executive Summary", "The business packages the work nobody has time to do: make a technical career feel human, funny, respectful, and safe to share.", styles)
    for item in [
        "The core product is a retirement celebration planning service for technical teams and their families.",
        "The brand promise is emotional first: a send-off the retiree will actually love.",
        "The differentiation is the combination of warm event design, NDA-aware career storytelling, tech-team humor, and ready-to-buy add-ons.",
        "The initial website should convert through a Party Planner Toolkit, package tiers, a quote builder, and a simple inquiry workflow.",
        "Revenue comes from fixed packages plus high-margin services such as story decks, soundtracks, giveaway kits, group-photo setup, and vendor coordination.",
    ]:
        story.append(bullet(item, styles))

    add_section(story, "2. Business Concept", "", styles)
    concept = [
        ["Element", "Decision"],
        ["Working name", "GPU Retirement Send-Offs"],
        ["Market entry", "Start with NVIDIA/GPU-inspired retirement parties, then broaden to technical teams and engineering leaders."],
        ["Audience", "Managers, spouses, family members, coworkers, retirement committees, and retirees themselves."],
        ["Outcome", "A memorable, low-stress celebration with cake, photos, music, stories, giveaways, deck, and day-of rhythm."],
        ["Brand guardrail", "Independent service. No implied NVIDIA affiliation, sponsorship, or endorsement."],
    ]
    story.append(table(concept, [1.35 * inch, 5.05 * inch]))
    story.append(Spacer(1, 0.12 * inch))

    add_section(story, "3. Target Customers", "", styles)
    customer_rows = [
        ["Segment", "Need", "Message"],
        ["Team manager", "Plan a meaningful event quickly without mishandling confidential achievements.", "We make the tribute warm, safe, and easy to coordinate."],
        ["Spouse or family", "Show the whole person, not just the job title.", "We include family stories, photos, cake, music, and memory prompts."],
        ["Retirement committee", "Get structure, budget clarity, and deliverables.", "Pick a package, add the moments, and generate a planning brief."],
        ["Retiree", "Feel honored without being embarrassed.", "The tone is kind, personal, and never a generic corporate send-off."],
    ]
    story.append(table(customer_rows, [1.25 * inch, 2.45 * inch, 2.7 * inch]))
    story.append(PageBreak())

    add_section(story, "4. Offer Architecture", "Packages should feel emotional first and practical second. Prices are starting points and should be refined with real vendor quotes.", styles)
    package_rows = [
        ["Package", "Starting price", "Best for", "Core deliverables"],
        ["Founders' Toast", "$1,750+", "Small team-room celebration", "Theme direction, welcome board, short deck, run-of-show, remote checklist"],
        ["GPU Giant", "$4,800+", "Signature team celebration", "Theme, NDA-aware story intake, 15-slide deck, cake direction, photo setup, giveaway prompts, vendor coordination"],
        ["Legendary Send-Off", "$9,500+", "Executive, lab-wide, family-forward event", "Full event creative, soundtrack/montage, premium cake, group photo wall, giveaway kit, on-site support, memory package"],
    ]
    story.append(table(package_rows, [1.25 * inch, 0.88 * inch, 1.55 * inch, 2.72 * inch], align_right_cols=[1]))
    story.append(Spacer(1, 0.16 * inch))

    addon_rows = [
        ["Add-on", "Price", "Primary cost", "Gross margin logic"],
        ["Custom shirts and gear", "$650", "Print/vendor costs", "Good visual impact; lower margin but strong party value."],
        ["NDA-safe career story package", "$900", "Interview and writing time", "High-margin expertise product."],
        ["Career soundtrack package", "$1,200", "Audio production or curation", "High emotional value; scalable with templates."],
        ["GPU birthday cake design", "$850", "Bakery coordination and design brief", "Moderate margin; strong delight factor."],
        ["Team group photo setup", "$1,100", "Photographer/prints", "Moderate margin; creates keepsake value."],
        ["Giveaway table kit", "$950", "Prize sourcing and print materials", "Moderate margin; easy upsell."],
        ["Catering coordination", "$1,500", "Coordination labor", "High-margin if food is billed direct to client."],
    ]
    story.append(table(addon_rows, [1.55 * inch, 0.65 * inch, 1.45 * inch, 2.75 * inch], align_right_cols=[1]))

    ops_rows = [
        ["Phase", "Activity", "Owner"],
        ["Lead", "Visitor uses planner, quote builder, or inquiry form.", "Website"],
        ["Discovery", "Learn retiree personality, tone, event date, guest count, confidentiality needs.", "Planner"],
        ["Story intake", "Collect memories, photos, music preferences, cake details, and safe achievements.", "Planner + client"],
        ["Creative build", "Deck, signage, soundtrack, giveaway cards, run-of-show, and vendor briefs.", "Creative team"],
        ["Vendor coordination", "Cake, photo, food, prints, AV, and venue rules.", "Planner"],
        ["Event", "Host flow, photo moment, cake reveal, toast, send-off, and keepsakes.", "Planner/on-site lead"],
        ["Follow-up", "Deliver memory package, group photo, playlist, and referral request.", "Planner"],
    ]
    story.append(
        KeepTogether(
            [
                Spacer(1, 0.1 * inch),
                p("5. Operations Model", styles["SectionTitle"]),
                Spacer(1, 0.12 * inch),
                table(ops_rows, [1.05 * inch, 4.1 * inch, 1.25 * inch]),
            ]
        )
    )
    add_section(story, "6. Website Plan", "The site should feel like a real celebration planner, not a joke flyer or a cold procurement page.", styles)
    sitemap_rows = [
        ["Page/Section", "Purpose", "Core content"],
        ["Home", "Create emotional buy-in and route to planning.", "Hero, retiree experience, moments, day-of flow, packages, quote."],
        ["Celebration Ideas", "Inspire buyers and improve search value.", "Cake ideas, photo ideas, giveaway ideas, music, games, memory prompts."],
        ["Packages", "Make buying easier.", "Package comparison, add-ons, FAQ, what is included."],
        ["How It Works", "Reduce trust friction.", "Planning call, intake, confidentiality review, design, vendor coordination, day-of support."],
        ["Request Quote", "Convert.", "Planner brief, event details, quote builder, contact details."],
    ]
    story.append(table(sitemap_rows, [1.4 * inch, 2.1 * inch, 2.9 * inch]))
    story.append(Spacer(1, 0.12 * inch))

    story.append(p("Homepage section order", styles["Subhead"]))
    for item in [
        "Hero: A send-off they will actually love.",
        "Retiree experience: dignity, joy, stories, family, and keepsakes.",
        "Celebration moments: story wall, cake reveal, group photo, giveaway table, career soundtrack, deck.",
        "Day-of flow: arrival, welcome, cake/photo, tribute, send-off.",
        "Party Planner Toolkit: generate a checklist and copyable brief.",
        "Packages and quote builder: choose level, add moments, request quote.",
        "Privacy and disclaimer: confidentiality guardrails and independent status.",
    ]:
        story.append(bullet(item, styles))

    add_section(story, "7. Website Functionality", "", styles)
    functionality_rows = [
        ["Feature", "Why it matters", "MVP behavior"],
        ["Party Planner Toolkit", "Makes the site useful before purchase.", "Captures date, tone, guest range, must-have moments; generates checklist and brief."],
        ["Quote Builder", "Creates budget clarity.", "Packages plus add-ons produce an estimated budget and email-ready inquiry."],
        ["Brief to Quote Notes", "Connects planning and conversion.", "Push generated brief into quote notes."],
        ["Idea Bank", "Keeps retirees and families engaged.", "Cake, photo, giveaway, music, games, and memory prompts."],
        ["Confidentiality Messaging", "Protects brand and technical details.", "Explain safe story intake and review pass."],
    ]
    story.append(table(functionality_rows, [1.45 * inch, 2.35 * inch, 2.6 * inch]))
    add_section(story, "8. Revenue Model", "Directional, assumption-based model. Replace these assumptions with real lead, close-rate, vendor-cost, and labor data after early pilots.", styles)
    scenario_rows = [
        ["Scenario", "Leads/mo", "Close", "Events/yr", "Avg rev/event", "Annual rev", "Gross profit", "Op. profit*"],
    ]
    for s in SCENARIOS:
        scenario_rows.append(
            [
                s.name,
                str(round(s.leads_per_month)),
                percent(s.close_rate),
                str(s.events_per_year),
                money(s.avg_revenue_per_event),
                money(s.annual_revenue),
                money(s.gross_profit),
                money(s.operating_profit),
            ]
        )
    story.append(table(scenario_rows, [1.05 * inch, 0.65 * inch, 0.58 * inch, 0.68 * inch, 1.0 * inch, 1.0 * inch, 0.98 * inch, 0.98 * inch], align_right_cols=[1, 3, 4, 5, 6, 7]))
    story.append(p("*Operating profit is before owner salary, taxes, debt service, and unusual one-time costs.", styles["Small"]))
    story.append(Spacer(1, 0.12 * inch))
    story.append(make_revenue_chart(SCENARIOS))
    story.append(Spacer(1, 0.18 * inch))

    story.append(p("Revenue assumptions", styles["Subhead"]))
    for item in [
        "Conservative case: 8 qualified leads per month, 25 percent close rate, 24 events per year.",
        "Base case: 15 qualified leads per month, 30 percent close rate, 54 events per year.",
        "Aggressive case: 40 qualified leads per month, 32 percent close rate, 154 events per year.",
        "Average revenue per event includes a package plus add-ons. It does not assume catering is marked up as food revenue unless separately contracted.",
        "Gross margin assumes a mix of owner/planner labor, contractors, printing, audio/photo vendors, cake coordination, software, and contingency.",
    ]:
        story.append(bullet(item, styles))

    unit_rows = [
        ["Product", "Price", "Est. variable cost", "Gross profit", "Margin"],
        ["Founders' Toast", "$1,750", "$530", "$1,220", "70%"],
        ["GPU Giant", "$4,800", "$1,660", "$3,140", "65%"],
        ["Legendary Send-Off", "$9,500", "$4,100", "$5,400", "57%"],
        ["NDA-safe story package", "$900", "$225", "$675", "75%"],
        ["Career soundtrack package", "$1,200", "$350", "$850", "71%"],
        ["Giveaway table kit", "$950", "$475", "$475", "50%"],
        ["Catering coordination", "$1,500", "$450", "$1,050", "70%"],
    ]
    story.append(
        KeepTogether(
            [
                Spacer(1, 0.1 * inch),
                p("9. Unit Economics", styles["SectionTitle"]),
                Spacer(1, 0.12 * inch),
                table(unit_rows, [1.72 * inch, 0.78 * inch, 1.18 * inch, 0.98 * inch, 0.7 * inch], align_right_cols=[1, 2, 3, 4]),
            ]
        )
    )

    add_section(story, "10. Go-To-Market Plan", "", styles)
    for title, points in [
        (
            "Pilot phase",
            [
                "Run 3 to 5 discounted pilot events for technical teams, alumni groups, or friends of retirees.",
                "Capture photos of decor, cake, group photo setup, and memory cards with permission.",
                "Measure planning time, vendor costs, add-on attachment, and buyer objections.",
            ],
        ),
        (
            "Lead generation",
            [
                "Publish search-focused idea pages: engineer retirement party ideas, tech retirement cake ideas, group photo ideas, and retirement giveaways.",
                "Build a one-page inquiry funnel around the Party Planner Toolkit and Quote Builder.",
                "Ask every event for referrals to adjacent teams and former coworkers.",
            ],
        ),
        (
            "Sales process",
            [
                "Offer a free 20-minute celebration theme audit.",
                "Convert to a planning deposit or package agreement after the audit.",
                "Use add-ons as clear moments, not as a confusing menu of parts.",
            ],
        ),
    ]:
        story.append(p(title, styles["Subhead"]))
        for point in points:
            story.append(bullet(point, styles))

    risk_rows = [
        ["Risk", "Control"],
        ["Trademark or affiliation confusion", "Use independent-service disclaimer and avoid official-logo-heavy sales language."],
        ["Confidential achievements", "Use NDA-aware intake, public-safe copy, and optional review pass."],
        ["Tone misses the retiree", "Capture comfort level, humor boundaries, songs to avoid, surprise tolerance, and family input."],
        ["Vendor cost overruns", "Use estimate language, separate pass-through vendor costs, and require approval on outside costs."],
        ["Planner capacity", "Template recurring assets and use contractors for photo, audio, design, and on-site support."],
        ["Website feels too cold", "Keep retiree experience, memory prompts, and celebration moments above pricing."],
    ]
    story.append(
        KeepTogether(
            [
                Spacer(1, 0.1 * inch),
                p("11. Risks and Controls", styles["SectionTitle"]),
                Spacer(1, 0.12 * inch),
                table(risk_rows, [2.0 * inch, 4.4 * inch]),
            ]
        )
    )

    add_section(story, "12. Next 30 Days", "", styles)
    for item in [
        "Turn the current single-page site into the MVP: hero, retiree experience, celebration moments, Party Planner Toolkit, packages, quote builder, and FAQ.",
        "Create 3 sample themes: GPU Giant, Warm Family Send-Off, and Lab Legend Celebration.",
        "Generate a warmer hero collage with cake, group photo, memory cards, and giveaway table.",
        "Run the first pilot with a simple planning checklist, vendor estimate sheet, and post-event feedback form.",
        "Update the revenue model with actual labor hours, vendor quotes, lead sources, close rate, and add-on attachment rate.",
    ]:
        story.append(bullet(item, styles))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    build_pdf()
    print(PDF_PATH)
    print(CSV_PATH)
