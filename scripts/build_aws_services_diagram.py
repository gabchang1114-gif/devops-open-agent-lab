#!/usr/bin/env python3
"""Render AWS services architecture diagram as PNG and PDF."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "img" / "devops-open-agent-icon.png"
OUT_PNG = ROOT / "img" / "aws-services-diagram.png"
OUT_PDF = ROOT / "img" / "aws-services-diagram.pdf"
OUT_SVG = ROOT / "img" / "aws-services-diagram.svg"
TMP_PDF = ROOT / "img" / ".aws-services-diagram-tmp.pdf"

W, H = 1200, 620

SERVICES = [
    # row 1
    ("EC2", "Instances & EBS", "EC2", (0.98, 0.45, 0.09)),
    ("Lambda", "Functions & metrics", "λ", (0.66, 0.33, 0.97)),
    ("S3", "Buckets & posture", "S3", (0.13, 0.77, 0.37)),
    # row 2
    ("VPC", "Subnets & routing", "VPC", (0.23, 0.51, 0.96)),
    ("Security Groups", "Ingress / egress", "SG", (0.94, 0.27, 0.27)),
    ("Load Balancers", "ALB / NLB / targets", "LB", (0.02, 0.71, 0.83)),
    # row 3
    ("Auto Scaling", "ASG capacity", "AS", (0.92, 0.70, 0.03)),
    ("CloudWatch", "Metrics & alarms", "CW", (0.93, 0.28, 0.60)),
    ("CloudTrail", "API audit events", "CT", (0.39, 0.40, 0.95)),
]


def draw_diagram(pdf_path: Path) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=(W, H))
    c.setTitle("DevOps Open Agent AWS Services Architecture")

    c.setFillColorRGB(0.04, 0.07, 0.13)
    c.roundRect(0, 0, W, H, 24, fill=1, stroke=0)

    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(W / 2, H - 42, "DevOps Open Agent — AWS Services Architecture")
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 14)
    c.drawCentredString(W / 2, H - 68, "One platform · AWS DevOps Agent · All supported services per region")

    box_x, box_y, box_w, box_h = 70, 195, 220, 220
    c.setFillColorRGB(0.09, 0.11, 0.15)
    c.setStrokeColorRGB(0.20, 0.25, 0.33)
    c.setLineWidth(2)
    c.roundRect(box_x, box_y, box_w, box_h, 28, fill=1, stroke=1)

    icon_size = 130
    c.drawImage(
        ImageReader(str(ICON)),
        box_x + (box_w - icon_size) / 2,
        box_y + 20,
        width=icon_size,
        height=icon_size,
        mask="auto",
    )
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(box_x + box_w / 2, box_y + 168, "DevOps Open Agent")
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 11)
    c.drawCentredString(box_x + box_w / 2, box_y + 150, "AWS DevOps Agent module")

    center_y = box_y + box_h / 2

    c.setStrokeColorRGB(0.98, 0.45, 0.09)
    c.setLineWidth(3)
    c.line(290, center_y, 430, center_y)
    c.line(420, center_y, 430, center_y)
    c.line(420, center_y - 6, 430, center_y)
    c.line(420, center_y + 6, 430, center_y)

    llm_x, llm_y, llm_w, llm_h = 430, 230, 240, 150
    c.setFillColorRGB(0.12, 0.16, 0.23)
    c.setStrokeColorRGB(0.98, 0.45, 0.09)
    c.roundRect(llm_x, llm_y, llm_w, llm_h, 20, fill=1, stroke=1)
    c.setFillColorRGB(0.98, 0.45, 0.09)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(llm_x + llm_w / 2, llm_y + 112, "AWS SERVICES")
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(llm_x + llm_w / 2, llm_y + 82, "Discovery")
    c.setFillColorRGB(0.80, 0.84, 0.88)
    c.setFont("Helvetica", 11)
    c.drawCentredString(llm_x + llm_w / 2, llm_y + 58, "investigation_service.py")
    c.drawCentredString(llm_x + llm_w / 2, llm_y + 40, "Collectors · Topology · AI RCA")

    hub_x = 760
    row_ys = [465, 305, 145]
    c.setStrokeColorRGB(0.98, 0.75, 0.14)
    c.setLineWidth(3)
    c.line(670, center_y, hub_x, center_y)
    c.line(hub_x, row_ys[0], hub_x, row_ys[2])
    for y in row_ys:
        c.line(hub_x, y, 790, y)
        c.line(780, y, 790, y)
        c.line(780, y - 6, 790, y)
        c.line(780, y + 6, 790, y)

    col_xs = [800, 935, 1070]
    card_w, card_h = 125, 90
    for index, (name, subtitle, initial, color) in enumerate(SERVICES):
        row = index // 3
        col = index % 3
        y = row_ys[row]
        px = col_xs[col]
        py = y - card_h / 2

        c.setFillColorRGB(0.09, 0.11, 0.15)
        c.setStrokeColorRGB(0.20, 0.25, 0.33)
        c.roundRect(px, py, card_w, card_h, 16, fill=1, stroke=1)

        c.setFillColorRGB(*color)
        c.circle(px + 28, y, 16, fill=1, stroke=0)
        c.setFillColorRGB(0.04, 0.07, 0.13)
        c.setFont("Helvetica-Bold", 9 if len(initial) > 2 else 11)
        c.drawCentredString(px + 28, y - 4, initial)

        c.setFillColorRGB(0.97, 0.98, 0.99)
        font_size = 13 if len(name) > 12 else 15
        c.setFont("Helvetica-Bold", font_size)
        c.drawCentredString(px + 78, y + 10, name)
        c.setFillColorRGB(0.58, 0.64, 0.72)
        c.setFont("Helvetica", 9)
        c.drawCentredString(px + 78, y - 8, subtitle)

    c.setFillColorRGB(0.39, 0.45, 0.55)
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        W / 2,
        18,
        "Account & region scoped · CloudWatch / CloudTrail lookback configurable · Focused modes per issue type",
    )

    c.save()


def write_svg() -> None:
    rows_y = [465, 305, 145]
    cols_x = [800, 935, 1070]
    svg_services = []
    for i, (name, subtitle, initial, _) in enumerate(SERVICES):
        row, col = divmod(i, 3)
        x, y = cols_x[col], rows_y[row]
        font = 14 if len(name) > 12 else 16
        svg_services.append(
            f"""  <g filter="url(#shadow)">
    <rect x="{x}" y="{y - 45}" width="125" height="90" rx="16" fill="#171B26" stroke="#334155" stroke-width="2"/>
    <text x="{x + 78}" y="{y - 12}" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="{font}" font-weight="700">{name}</text>
    <text x="{x + 78}" y="{y + 6}" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="10">{subtitle}</text>
  </g>"""
        )

    spine = "\n".join(
        f'  <line x1="760" y1="{y}" x2="790" y2="{y}" stroke="#FBBF24" stroke-width="3" marker-end="url(#arrowAmber)"/>'
        for y in rows_y
    )

    OUT_SVG.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="620" viewBox="0 0 1200 620">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0B1220"/><stop offset="100%" stop-color="#111827"/>
    </linearGradient>
    <filter id="shadow"><feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.35"/></filter>
    <marker id="arrowOrange" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#F97316"/></marker>
    <marker id="arrowAmber" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#FBBF24"/></marker>
  </defs>
  <rect width="1200" height="620" rx="24" fill="url(#bg)"/>
  <text x="600" y="42" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="24" font-weight="700">DevOps Open Agent — AWS Services Architecture</text>
  <text x="600" y="68" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="14">One platform · AWS DevOps Agent · All supported services per region</text>
  <g filter="url(#shadow)">
    <rect x="70" y="195" width="220" height="220" rx="28" fill="#171B26" stroke="#334155" stroke-width="2"/>
    <image x="95" y="210" width="170" height="170" xlink:href="devops-open-agent-icon.png"/>
    <text x="180" y="390" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="18" font-weight="700">DevOps Open Agent</text>
    <text x="180" y="412" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="12">AWS DevOps Agent module</text>
  </g>
  <line x1="290" y1="305" x2="430" y2="305" stroke="#F97316" stroke-width="3" marker-end="url(#arrowOrange)"/>
  <g filter="url(#shadow)">
    <rect x="430" y="230" width="240" height="150" rx="20" fill="#1E293B" stroke="#F97316" stroke-width="2"/>
    <text x="550" y="278" text-anchor="middle" fill="#F97316" font-family="system-ui,sans-serif" font-size="13" font-weight="700">AWS SERVICES</text>
    <text x="550" y="312" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="22" font-weight="700">Discovery</text>
    <text x="550" y="339" text-anchor="middle" fill="#CBD5E1" font-family="system-ui,sans-serif" font-size="12">investigation_service.py</text>
    <text x="550" y="359" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="11">Collectors · Topology · AI RCA</text>
  </g>
  <line x1="670" y1="305" x2="760" y2="305" stroke="#FBBF24" stroke-width="3"/>
  <line x1="760" y1="145" x2="760" y2="465" stroke="#FBBF24" stroke-width="3"/>
{spine}
{chr(10).join(svg_services)}
  <text x="600" y="598" text-anchor="middle" fill="#64748B" font-family="system-ui,sans-serif" font-size="12">Account &amp; region scoped · CloudWatch / CloudTrail lookback configurable · Focused modes per issue type</text>
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
