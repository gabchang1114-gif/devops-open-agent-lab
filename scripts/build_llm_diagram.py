#!/usr/bin/env python3
"""Render LLM provider architecture diagram as PNG."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "img" / "devops-open-agent-icon.png"
OUT_PNG = ROOT / "img" / "llm-provider-diagram.png"
OUT_PDF = ROOT / "img" / "llm-provider-diagram.pdf"
TMP_PDF = ROOT / "img" / ".llm-provider-diagram-tmp.pdf"

W, H = 1200, 520


def draw_diagram(pdf_path: Path) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=(W, H))
    c.setTitle("DevOps Open Agent LLM Provider Architecture")

    # Background
    c.setFillColorRGB(0.04, 0.07, 0.13)
    c.roundRect(0, 0, W, H, 24, fill=1, stroke=0)

    # Title
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(W / 2, H - 42, "DevOps Open Agent — LLM Provider Architecture")
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 14)
    c.drawCentredString(W / 2, H - 68, "One platform · Shared LLM layer · Your choice of provider")

    # DevOps Open Agent box
    box_x, box_y, box_w, box_h = 70, 130, 220, 230
    c.setFillColorRGB(0.09, 0.11, 0.15)
    c.setStrokeColorRGB(0.20, 0.25, 0.33)
    c.setLineWidth(2)
    c.roundRect(box_x, box_y, box_w, box_h, 28, fill=1, stroke=1)

    icon_size = 130
    icon_x = box_x + (box_w - icon_size) / 2
    icon_y = box_y + 20
    c.drawImage(
        ImageReader(str(ICON)),
        icon_x,
        icon_y,
        width=icon_size,
        height=icon_size,
        mask="auto",
    )
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 17)
    c.drawCentredString(box_x + box_w / 2, box_y + 168, "DevOps Open Agent")
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 11)
    c.drawCentredString(box_x + box_w / 2, box_y + 150, "K8s · AWS · Cost · PR Review")

    center_y = box_y + box_h / 2

    # Arrow to LLM
    c.setStrokeColorRGB(0.22, 0.74, 0.97)
    c.setLineWidth(3)
    c.line(290, center_y, 430, center_y)
    c.line(420, center_y, 430, center_y)
    c.line(420, center_y - 6, 430, center_y)
    c.line(420, center_y + 6, 430, center_y)

    # LLM box
    llm_x, llm_y, llm_w, llm_h = 430, 175, 240, 140
    c.setFillColorRGB(0.12, 0.16, 0.23)
    c.setStrokeColorRGB(0.22, 0.74, 0.97)
    c.roundRect(llm_x, llm_y, llm_w, llm_h, 20, fill=1, stroke=1)
    c.setFillColorRGB(0.22, 0.74, 0.97)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(llm_x + llm_w / 2, llm_y + 102, "SHARED AI LAYER")
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(llm_x + llm_w / 2, llm_y + 72, "LLM")
    c.setFillColorRGB(0.80, 0.84, 0.88)
    c.setFont("Helvetica", 11)
    c.drawCentredString(llm_x + llm_w / 2, llm_y + 48, "llm_factory.py")
    c.drawCentredString(llm_x + llm_w / 2, llm_y + 30, "Context · Prompts · RCA")

    # Branch hub
    hub_x = 760
    c.setStrokeColorRGB(0.65, 0.55, 0.98)
    c.setLineWidth(3)
    c.line(670, center_y, hub_x, center_y)

    providers = [
        (390, "Ollama", "Local / self-hosted LLM", "LLM_PROVIDER=ollama", (0.13, 0.83, 0.93), "O"),
        (260, "OpenAI", "GPT-4o / GPT-4o-mini", "LLM_PROVIDER=openai", (0.06, 0.73, 0.51), "AI"),
        (130, "Anthropic", "Claude Sonnet / Opus", "LLM_PROVIDER=anthropic", (0.96, 0.62, 0.04), "A"),
    ]

    for y, name, subtitle, env, color, initial in providers:
        c.line(hub_x, center_y, hub_x, y)
        c.line(hub_x, y, 860, y)
        c.line(850, y, 860, y)
        c.line(850, y - 6, 860, y)
        c.line(850, y + 6, 860, y)

        px, py, pw, ph = 860, y - 60, 260, 120
        c.setFillColorRGB(0.09, 0.11, 0.15)
        c.setStrokeColorRGB(0.20, 0.25, 0.33)
        c.roundRect(px, py, pw, ph, 18, fill=1, stroke=1)

        c.setFillColorRGB(*color)
        c.circle(900, y, 22, fill=1, stroke=0)
        c.setFillColorRGB(0.04, 0.07, 0.13)
        c.setFont("Helvetica-Bold", 13)
        c.drawCentredString(900, y - 4, initial)

        c.setFillColorRGB(0.97, 0.98, 0.99)
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(990, y + 12, name)
        c.setFillColorRGB(0.58, 0.64, 0.72)
        c.setFont("Helvetica", 12)
        c.drawCentredString(990, y - 8, subtitle)
        c.setFillColorRGB(0.39, 0.45, 0.55)
        c.setFont("Helvetica", 10)
        c.drawCentredString(990, y - 26, env)

    c.setFillColorRGB(0.39, 0.45, 0.55)
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        W / 2,
        18,
        "Configure provider in backend/.env · All four agent modules use the same LLM layer",
    )

    c.save()


def pdf_to_png(pdf_path: Path, png_path: Path) -> None:
    try:
        from pdf2image import convert_from_path

        images = convert_from_path(str(pdf_path), dpi=200)
        images[0].save(png_path, "PNG")
        return
    except Exception:
        pass

    # Fallback: render with Pillow via reportlab-produced PDF using macOS sips not for pdf
    # Use pymupdf if available
    try:
        import fitz

        doc = fitz.open(pdf_path)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(png_path)
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
    print(f"Wrote {OUT_PNG}")
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
