#!/usr/bin/env python3
"""Render platform → agents → AI analysis → Slack flow diagram."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "img" / "devops-open-agent-icon.png"
OUT_PNG = ROOT / "img" / "slack-flow-diagram.png"
OUT_PDF = ROOT / "img" / "slack-flow-diagram.pdf"
OUT_SVG = ROOT / "img" / "slack-flow-diagram.svg"
TMP_PDF = ROOT / "img" / ".slack-flow-diagram-tmp.pdf"

W, H = 1400, 720

AGENTS = [
    ("Kubernetes Debugging Agent", "K8s", (0.23, 0.51, 0.96)),
    ("AWS DevOps Agent", "AWS", (0.98, 0.45, 0.09)),
    ("Cloud Cost Detector", "$", (0.06, 0.73, 0.51)),
    ("PR Reviewer", "PR", (0.65, 0.55, 0.98)),
]

LLM_PROVIDERS = [
    ("Anthropic", "Claude", (0.96, 0.62, 0.04)),
    ("OpenAI", "GPT", (0.06, 0.73, 0.51)),
    ("Ollama", "Local LLM", (0.13, 0.83, 0.93)),
]

CARD_W = 300
CARD_H = 72
CARD_GAP = 12


def draw_arrow(c: canvas.Canvas, x1: float, y1: float, x2: float, y2: float, color: tuple[float, float, float]) -> None:
    c.setStrokeColorRGB(*color)
    c.setLineWidth(3)
    c.line(x1, y1, x2, y2)
    if x2 > x1:
        c.line(x2 - 10, y2 - 6, x2, y2)
        c.line(x2 - 10, y2 + 6, x2, y2)


def draw_down_arrow(c: canvas.Canvas, x: float, y1: float, y2: float, color: tuple[float, float, float]) -> None:
    c.setStrokeColorRGB(*color)
    c.setLineWidth(2.5)
    c.line(x, y1, x, y2)
    c.line(x - 6, y2 + 10, x, y2)
    c.line(x + 6, y2 + 10, x, y2)


def agent_stack_geometry() -> tuple[float, float, list[float]]:
    """Return column x, stack center y, and top y of each card."""
    stack_h = len(AGENTS) * CARD_H + (len(AGENTS) - 1) * CARD_GAP
    center_y = 355
    stack_top = center_y - stack_h / 2
    card_ys = [stack_top + index * (CARD_H + CARD_GAP) for index in range(len(AGENTS))]
    return 310, center_y, card_ys


def draw_agent_card(
    c: canvas.Canvas,
    px: float,
    py: float,
    label: str,
    initial: str,
    color: tuple[float, float, float],
) -> None:
    mid_y = py + CARD_H / 2
    c.setFillColorRGB(0.09, 0.11, 0.15)
    c.setStrokeColorRGB(0.20, 0.25, 0.33)
    c.setLineWidth(2)
    c.roundRect(px, py, CARD_W, CARD_H, 14, fill=1, stroke=1)

    c.setFillColorRGB(*color)
    c.circle(px + 36, mid_y, 20, fill=1, stroke=0)
    c.setFillColorRGB(0.04, 0.07, 0.13)
    c.setFont("Helvetica-Bold", 10 if len(initial) > 2 else 12)
    c.drawCentredString(px + 36, mid_y - 4, initial)

    c.setFillColorRGB(0.97, 0.98, 0.99)
    font_size = 12 if len(label) > 24 else 14
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(px + 72, mid_y + 2, label)


def draw_diagram(pdf_path: Path) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=(W, H))
    c.setTitle("DevOps Open Agent — AI Recommendations to Slack")

    c.setFillColorRGB(0.04, 0.07, 0.13)
    c.roundRect(0, 0, W, H, 24, fill=1, stroke=0)

    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(W / 2, H - 42, "DevOps Open Agent — AI Recommendations to Slack")
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 14)
    c.drawCentredString(
        W / 2,
        H - 68,
        "One platform · Four agents · Shared AI analysis · Notifications to your channel",
    )

    col_x, center_y, card_ys = agent_stack_geometry()

    # DevOps Open Agent
    box_x, box_w, box_h = 45, 200, 250
    box_y = center_y - box_h / 2
    c.setFillColorRGB(0.09, 0.11, 0.15)
    c.setStrokeColorRGB(0.20, 0.25, 0.33)
    c.setLineWidth(2)
    c.roundRect(box_x, box_y, box_w, box_h, 28, fill=1, stroke=1)

    icon_size = 115
    c.drawImage(
        ImageReader(str(ICON)),
        box_x + (box_w - icon_size) / 2,
        box_y + 28,
        width=icon_size,
        height=icon_size,
        mask="auto",
    )
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(box_x + box_w / 2, box_y + 168, "DevOps Open Agent")
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 11)
    c.drawCentredString(box_x + box_w / 2, box_y + 150, "Open Source Platform")

    draw_arrow(c, box_x + box_w, center_y, col_x - 18, center_y, (0.22, 0.74, 0.97))

    # Agent column container
    stack_h = len(AGENTS) * CARD_H + (len(AGENTS) - 1) * CARD_GAP
    stack_top = card_ys[0]
    col_pad = 16
    c.setFillColorRGB(0.07, 0.09, 0.13)
    c.setStrokeColorRGB(0.22, 0.74, 0.97)
    c.setLineWidth(2)
    c.roundRect(
        col_x - col_pad,
        stack_top - 36,
        CARD_W + col_pad * 2,
        stack_h + 52,
        20,
        fill=1,
        stroke=1,
    )
    c.setFillColorRGB(0.22, 0.74, 0.97)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(col_x + CARD_W / 2, stack_top - 14, "SUPPORTED AGENTS")

    for index, (label, initial, color) in enumerate(AGENTS):
        py = card_ys[index]
        draw_agent_card(c, col_x, py, label, initial, color)
        if index < len(AGENTS) - 1:
            draw_down_arrow(
                c,
                col_x + CARD_W / 2,
                py + CARD_H + 2,
                card_ys[index + 1] - 4,
                (0.22, 0.74, 0.97),
            )

    agents_right = col_x + CARD_W + col_pad
    ai_x, ai_w, ai_h = 720, 250, 250
    ai_y = center_y - ai_h / 2

    draw_arrow(c, agents_right + 8, center_y, ai_x, center_y, (0.65, 0.55, 0.98))

    c.setFillColorRGB(0.12, 0.16, 0.23)
    c.setStrokeColorRGB(0.65, 0.55, 0.98)
    c.setLineWidth(2)
    c.roundRect(ai_x, ai_y, ai_w, ai_h, 22, fill=1, stroke=1)
    c.setFillColorRGB(0.65, 0.55, 0.98)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(ai_x + ai_w / 2, ai_y + ai_h - 34, "SHARED AI LAYER")
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(ai_x + ai_w / 2, ai_y + ai_h - 68, "AI Analysis")
    c.setFillColorRGB(0.80, 0.84, 0.88)
    c.setFont("Helvetica", 11)
    c.drawCentredString(ai_x + ai_w / 2, ai_y + ai_h - 92, "Root cause · Recommendations")

    pill_w, pill_h = 200, 34
    pill_x = ai_x + (ai_w - pill_w) / 2
    for i, (provider, subtitle, color) in enumerate(LLM_PROVIDERS):
        py = ai_y + 58 - i * 42
        c.setFillColorRGB(0.09, 0.11, 0.15)
        c.setStrokeColorRGB(*color)
        c.roundRect(pill_x, py, pill_w, pill_h, 12, fill=1, stroke=1)
        c.setFillColorRGB(*color)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(pill_x + 14, py + 11, provider)
        c.setFillColorRGB(0.58, 0.64, 0.72)
        c.setFont("Helvetica", 10)
        c.drawString(pill_x + 100, py + 12, subtitle)

    slack_x, slack_w, slack_h = 1040, 155, 175
    slack_y = center_y - slack_h / 2
    draw_arrow(c, ai_x + ai_w + 5, center_y, slack_x - 8, center_y, (0.29, 0.08, 0.29))

    c.setFillColorRGB(0.12, 0.16, 0.23)
    c.setStrokeColorRGB(0.29, 0.08, 0.29)
    c.setLineWidth(2)
    c.roundRect(slack_x, slack_y, slack_w, slack_h, 22, fill=1, stroke=1)

    c.setFillColorRGB(0.29, 0.08, 0.29)
    c.roundRect(slack_x + 47, slack_y + 58, 60, 60, 14, fill=1, stroke=0)
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(slack_x + 77, slack_y + 74, "#")

    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(slack_x + slack_w / 2, slack_y + 42, "Slack")
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 10)
    c.drawCentredString(slack_x + slack_w / 2, slack_y + 22, "Your channel")

    c.setFillColorRGB(0.39, 0.45, 0.55)
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        W / 2,
        18,
        "Investigations & PR reviews · AI recommendations delivered via webhook or bot · Per-user Integrations tab",
    )

    c.save()


def write_svg() -> None:
    col_x, center_y, card_ys = agent_stack_geometry()
    stack_h = len(AGENTS) * CARD_H + (len(AGENTS) - 1) * CARD_GAP
    stack_top = card_ys[0]
    col_pad = 16

    agent_blocks = []
    down_arrows = []
    for index, (label, initial, color) in enumerate(AGENTS):
        py = card_ys[index]
        mid_y = py + CARD_H / 2
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
        )
        font_size = 12 if len(label) > 24 else 14
        agent_blocks.append(
            f"""    <rect x="{col_x}" y="{py}" width="{CARD_W}" height="{CARD_H}" rx="14" fill="#171B26" stroke="#334155" stroke-width="2"/>
    <circle cx="{col_x + 36}" cy="{mid_y}" r="20" fill="{hex_color}"/>
    <text x="{col_x + 36}" y="{mid_y + 4}" text-anchor="middle" fill="#0B1220" font-family="system-ui,sans-serif" font-size="11" font-weight="700">{initial}</text>
    <text x="{col_x + 72}" y="{mid_y + 5}" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="{font_size}" font-weight="700">{label}</text>"""
        )
        if index < len(AGENTS) - 1:
            next_py = card_ys[index + 1]
            arrow_x = col_x + CARD_W / 2
            down_arrows.append(
                f'    <line x1="{arrow_x}" y1="{py + CARD_H + 2}" x2="{arrow_x}" y2="{next_py - 4}" stroke="#38BDF8" stroke-width="2.5" marker-end="url(#arrowBlueDown)"/>'
            )

    provider_pills = []
    pill_x = 745
    for i, (provider, subtitle, color) in enumerate(LLM_PROVIDERS):
        py = 313 - i * 42
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
        )
        provider_pills.append(
            f"""    <rect x="{pill_x}" y="{py}" width="200" height="34" rx="12" fill="#171B26" stroke="{hex_color}" stroke-width="1.5"/>
    <text x="{pill_x + 14}" y="{py + 22}" fill="{hex_color}" font-family="system-ui,sans-serif" font-size="11" font-weight="700">{provider}</text>
    <text x="{pill_x + 100}" y="{py + 22}" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="10">{subtitle}</text>"""
        )

    OUT_SVG.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1400" height="720" viewBox="0 0 1400 720">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0B1220"/><stop offset="100%" stop-color="#111827"/>
    </linearGradient>
    <filter id="shadow"><feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.35"/></filter>
    <marker id="arrowBlue" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#38BDF8"/></marker>
    <marker id="arrowBlueDown" markerWidth="10" markerHeight="10" refX="5" refY="8" orient="auto"><path d="M0,0 L5,10 L10,0 Z" fill="#38BDF8"/></marker>
    <marker id="arrowPurple" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#A78BFA"/></marker>
    <marker id="arrowSlack" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#4A154B"/></marker>
  </defs>
  <rect width="1400" height="720" rx="24" fill="url(#bg)"/>
  <text x="700" y="42" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="24" font-weight="700">DevOps Open Agent — AI Recommendations to Slack</text>
  <text x="700" y="68" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="14">One platform · Four agents · Shared AI analysis · Notifications to your channel</text>

  <g filter="url(#shadow)">
    <rect x="45" y="230" width="200" height="250" rx="28" fill="#171B26" stroke="#334155" stroke-width="2"/>
    <image x="67" y="258" width="156" height="156" xlink:href="devops-open-agent-icon.png"/>
    <text x="145" y="423" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="16" font-weight="700">DevOps Open Agent</text>
    <text x="145" y="443" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="11">Open Source Platform</text>
  </g>

  <line x1="245" y1="{center_y}" x2="292" y2="{center_y}" stroke="#38BDF8" stroke-width="3" marker-end="url(#arrowBlue)"/>

  <g filter="url(#shadow)">
    <rect x="{col_x - col_pad}" y="{stack_top - 36}" width="{CARD_W + col_pad * 2}" height="{stack_h + 52}" rx="20" fill="#121722" stroke="#38BDF8" stroke-width="2"/>
    <text x="{col_x + CARD_W / 2}" y="{stack_top - 14}" text-anchor="middle" fill="#38BDF8" font-family="system-ui,sans-serif" font-size="11" font-weight="700">SUPPORTED AGENTS</text>
{chr(10).join(agent_blocks)}
{chr(10).join(down_arrows)}
  </g>

  <line x1="{col_x + CARD_W + col_pad + 8}" y1="{center_y}" x2="720" y2="{center_y}" stroke="#A78BFA" stroke-width="3" marker-end="url(#arrowPurple)"/>
  <g filter="url(#shadow)">
    <rect x="720" y="230" width="250" height="250" rx="22" fill="#1E293B" stroke="#A78BFA" stroke-width="2"/>
    <text x="845" y="446" text-anchor="middle" fill="#A78BFA" font-family="system-ui,sans-serif" font-size="12" font-weight="700">SHARED AI LAYER</text>
    <text x="845" y="412" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="24" font-weight="700">AI Analysis</text>
    <text x="845" y="388" text-anchor="middle" fill="#CBD5E1" font-family="system-ui,sans-serif" font-size="11">Root cause · Recommendations</text>
{chr(10).join(provider_pills)}
  </g>

  <line x1="970" y1="{center_y}" x2="1032" y2="{center_y}" stroke="#4A154B" stroke-width="3" marker-end="url(#arrowSlack)"/>
  <g filter="url(#shadow)">
    <rect x="1040" y="267" width="155" height="175" rx="22" fill="#1E293B" stroke="#4A154B" stroke-width="2"/>
    <rect x="1087" y="325" width="60" height="60" rx="14" fill="#4A154B"/>
    <text x="1117" y="363" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="28" font-weight="700">#</text>
    <text x="1117" y="309" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="22" font-weight="700">Slack</text>
    <text x="1117" y="289" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="10">Your channel</text>
  </g>

  <text x="700" y="698" text-anchor="middle" fill="#64748B" font-family="system-ui,sans-serif" font-size="12">Investigations &amp; PR reviews · AI recommendations delivered via webhook or bot · Per-user Integrations tab</text>
</svg>""",
        encoding="utf-8",
    )


def pdf_to_png(pdf_path: Path, png_path: Path) -> None:
    try:
        import fitz

        doc = fitz.open(pdf_path)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(png_path)
        return
    except Exception:
        pass
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(str(pdf_path), dpi=200)
        images[0].save(png_path, "PNG")
        return
    except Exception:
        pass
    raise RuntimeError("Install pymupdf or pdf2image to export PNG")


def main() -> None:
    if not ICON.exists():
        raise FileNotFoundError(f"Missing icon: {ICON}")
    draw_diagram(TMP_PDF)
    TMP_PDF.replace(OUT_PDF)
    pdf_to_png(OUT_PDF, OUT_PNG)
    write_svg()
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_PDF}")
    print(f"Wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
