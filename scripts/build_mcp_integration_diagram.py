#!/usr/bin/env python3
"""Render DevOps Open Agent → MCP integration architecture diagram."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

ROOT = Path(__file__).resolve().parents[1]
ICON = ROOT / "img" / "devops-open-agent-icon.png"
OUT_PNG = ROOT / "img" / "mcp-integration-diagram.png"
OUT_PDF = ROOT / "img" / "mcp-integration-diagram.pdf"
OUT_SVG = ROOT / "img" / "mcp-integration-diagram.svg"
TMP_PDF = ROOT / "img" / ".mcp-integration-diagram-tmp.pdf"

W, H = 1200, 640


def draw_arrow(
    c: canvas.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    color: tuple[float, float, float],
) -> None:
    c.setStrokeColorRGB(*color)
    c.setLineWidth(3)
    c.line(x1, y1, x2, y2)
    if x2 > x1:
        c.line(x2 - 10, y2 - 6, x2, y2)
        c.line(x2 - 10, y2 + 6, x2, y2)
    elif x2 < x1:
        c.line(x2 + 10, y2 - 6, x2, y2)
        c.line(x2 + 10, y2 + 6, x2, y2)
    elif y2 > y1:
        c.line(x2 - 6, y2 - 10, x2, y2)
        c.line(x2 + 6, y2 - 10, x2, y2)
    else:
        c.line(x2 - 6, y2 + 10, x2, y2)
        c.line(x2 + 6, y2 + 10, x2, y2)


def draw_card(
    c: canvas.Canvas,
    x: float,
    y: float,
    w: float,
    h: float,
    title: str,
    subtitle: str,
    stroke: tuple[float, float, float],
    badge: str | None = None,
) -> None:
    c.setFillColorRGB(0.12, 0.16, 0.23)
    c.setStrokeColorRGB(*stroke)
    c.setLineWidth(2)
    c.roundRect(x, y, w, h, 20, fill=1, stroke=1)
    mid_x = x + w / 2
    if badge:
        c.setFillColorRGB(*stroke)
        c.circle(mid_x, y + h / 2 + 24, 24, fill=1, stroke=0)
        c.setFillColorRGB(0.97, 0.98, 0.99)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(mid_x, y + h / 2 + 18, badge)
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(mid_x, y + 46, title)
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 10)
    c.drawCentredString(mid_x, y + 28, subtitle)


def draw_diagram(pdf_path: Path) -> None:
    c = canvas.Canvas(str(pdf_path), pagesize=(W, H))
    c.setTitle("DevOps Open Agent — MCP Integration")

    c.setFillColorRGB(0.04, 0.07, 0.13)
    c.roundRect(0, 0, W, H, 24, fill=1, stroke=0)

    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(W / 2, H - 42, "DevOps Open Agent — MCP Integration")
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 14)
    c.drawCentredString(
        W / 2,
        H - 68,
        "Ask questions, call remote tools, and enrich AI investigations via Model Context Protocol",
    )

    platform_x, platform_w, platform_h = 50, 200, 220
    platform_y = 300
    c.setFillColorRGB(0.09, 0.11, 0.15)
    c.setStrokeColorRGB(0.20, 0.25, 0.33)
    c.setLineWidth(2)
    c.roundRect(platform_x, platform_y, platform_w, platform_h, 24, fill=1, stroke=1)
    c.drawImage(
        ImageReader(str(ICON)),
        platform_x + 45,
        platform_y + 24,
        width=110,
        height=110,
        mask="auto",
    )
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 15)
    c.drawCentredString(platform_x + platform_w / 2, platform_y + 152, "DevOps Open Agent")
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 10)
    c.drawCentredString(platform_x + platform_w / 2, platform_y + 136, "FastAPI · Next.js UI")

    mcp_x, mcp_w, mcp_h = 320, 250, 200
    mcp_y = 290
    draw_card(
        c,
        mcp_x,
        mcp_y,
        mcp_w,
        mcp_h,
        "MCP Client",
        "Ask MCP · Tool discovery · Enrichment",
        (0.22, 0.74, 0.97),
        "MCP",
    )

    server_x, server_w, server_h = 640, 220, 200
    server_y = 290
    draw_card(
        c,
        server_x,
        server_y,
        server_w,
        server_h,
        "Remote MCP Server",
        "Streamable HTTP · Bearer auth",
        (0.55, 0.36, 0.96),
        "API",
    )

    tools_x, tools_w, tools_h = 920, 230, 200
    tools_y = 290
    draw_card(
        c,
        tools_x,
        tools_y,
        tools_w,
        tools_h,
        "External Tools",
        "GitHub · Observability · Runbooks",
        (0.02, 0.67, 0.22),
        "⚙",
    )

    llm_x, llm_w, llm_h = 320, 250, 120
    llm_y = 110
    draw_card(
        c,
        llm_x,
        llm_y,
        llm_w,
        llm_h,
        "Shared LLM Layer",
        "Plans tool calls · Synthesizes answers",
        (0.96, 0.62, 0.04),
        "AI",
    )

    agents_x, agents_w, agents_h = 50, 1090, 88
    agents_y = 520
    c.setFillColorRGB(0.09, 0.11, 0.15)
    c.setStrokeColorRGB(0.20, 0.25, 0.33)
    c.setLineWidth(2)
    c.roundRect(agents_x, agents_y, agents_w, agents_h, 18, fill=1, stroke=1)
    c.setFillColorRGB(0.97, 0.98, 0.99)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(
        agents_x + agents_w / 2,
        agents_y + 52,
        "Agent modules enriched with MCP context: Kubernetes · AWS · Cloud Cost · PR Reviewer",
    )
    c.setFillColorRGB(0.58, 0.64, 0.72)
    c.setFont("Helvetica", 10)
    c.drawCentredString(
        agents_x + agents_w / 2,
        agents_y + 34,
        "Per-user settings · Per-agent toggles · Integrations → MCP in the UI",
    )

    platform_mid_y = platform_y + platform_h / 2
    mcp_mid_y = mcp_y + mcp_h / 2
    server_mid_y = server_y + server_h / 2

    draw_arrow(c, platform_x + platform_w, platform_mid_y, mcp_x - 8, mcp_mid_y, (0.22, 0.74, 0.97))
    draw_arrow(c, mcp_x + mcp_w, mcp_mid_y, server_x - 8, server_mid_y, (0.55, 0.36, 0.96))
    draw_arrow(c, server_x + server_w, server_mid_y, tools_x - 8, server_mid_y, (0.02, 0.67, 0.22))

    llm_mid_x = llm_x + llm_w / 2
    draw_arrow(c, llm_mid_x, llm_y + llm_h, llm_mid_x, mcp_y - 8, (0.96, 0.62, 0.04))
    draw_arrow(c, platform_x + platform_w / 2, platform_y + platform_h, platform_x + platform_w / 2, agents_y - 8, (0.39, 0.45, 0.55))

    c.setFillColorRGB(0.39, 0.45, 0.55)
    c.setFont("Helvetica", 11)
    c.drawCentredString(
        W / 2,
        18,
        "Ask MCP: natural-language Q&A · Investigations: tool catalog injected before AI diagnosis",
    )

    c.save()


def write_svg() -> None:
    OUT_SVG.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1200" height="640" viewBox="0 0 1200 640">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0B1220"/><stop offset="100%" stop-color="#111827"/>
    </linearGradient>
    <filter id="shadow"><feDropShadow dx="0" dy="4" stdDeviation="8" flood-opacity="0.35"/></filter>
    <marker id="arrowBlue" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#38BDF8"/></marker>
    <marker id="arrowPurple" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#8B5CF6"/></marker>
    <marker id="arrowGreen" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#06AC38"/></marker>
    <marker id="arrowGold" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#F59E0B"/></marker>
  </defs>
  <rect width="1200" height="640" rx="24" fill="url(#bg)"/>
  <text x="600" y="42" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="24" font-weight="700">DevOps Open Agent — MCP Integration</text>
  <text x="600" y="68" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="14">Ask questions, call remote tools, and enrich AI investigations via Model Context Protocol</text>

  <g filter="url(#shadow)">
    <rect x="50" y="300" width="200" height="220" rx="24" fill="#171B26" stroke="#334155" stroke-width="2"/>
    <image x="95" y="324" width="110" height="110" xlink:href="devops-open-agent-icon.png"/>
    <text x="150" y="452" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="15" font-weight="700">DevOps Open Agent</text>
    <text x="150" y="436" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="10">FastAPI · Next.js UI</text>
  </g>

  <g filter="url(#shadow)">
    <rect x="320" y="290" width="250" height="200" rx="20" fill="#1E293B" stroke="#38BDF8" stroke-width="2"/>
    <circle cx="445" cy="404" r="24" fill="#38BDF8"/>
    <text x="445" y="409" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="14" font-weight="700">MCP</text>
    <text x="445" y="336" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="18" font-weight="700">MCP Client</text>
    <text x="445" y="318" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="10">Ask MCP · Tool discovery · Enrichment</text>
  </g>

  <g filter="url(#shadow)">
    <rect x="640" y="290" width="220" height="200" rx="20" fill="#1E293B" stroke="#8B5CF6" stroke-width="2"/>
    <circle cx="750" cy="404" r="24" fill="#8B5CF6"/>
    <text x="750" y="409" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="14" font-weight="700">API</text>
    <text x="750" y="336" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="18" font-weight="700">Remote MCP Server</text>
    <text x="750" y="318" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="10">Streamable HTTP · Bearer auth</text>
  </g>

  <g filter="url(#shadow)">
    <rect x="920" y="290" width="230" height="200" rx="20" fill="#1E293B" stroke="#06AC38" stroke-width="2"/>
    <circle cx="1035" cy="404" r="24" fill="#06AC38"/>
    <text x="1035" y="409" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="14" font-weight="700">⚙</text>
    <text x="1035" y="336" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="18" font-weight="700">External Tools</text>
    <text x="1035" y="318" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="10">GitHub · Observability · Runbooks</text>
  </g>

  <g filter="url(#shadow)">
    <rect x="320" y="110" width="250" height="120" rx="20" fill="#1E293B" stroke="#F59E0B" stroke-width="2"/>
    <circle cx="445" cy="164" r="24" fill="#F59E0B"/>
    <text x="445" y="169" text-anchor="middle" fill="#0B1220" font-family="system-ui,sans-serif" font-size="14" font-weight="700">AI</text>
    <text x="445" y="206" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="18" font-weight="700">Shared LLM Layer</text>
    <text x="445" y="188" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="10">Plans tool calls · Synthesizes answers</text>
  </g>

  <rect x="50" y="520" width="1090" height="88" rx="18" fill="#171B26" stroke="#334155" stroke-width="2"/>
  <text x="595" y="572" text-anchor="middle" fill="#F8FAFC" font-family="system-ui,sans-serif" font-size="13" font-weight="700">Agent modules enriched with MCP context: Kubernetes · AWS · Cloud Cost · PR Reviewer</text>
  <text x="595" y="554" text-anchor="middle" fill="#94A3B8" font-family="system-ui,sans-serif" font-size="10">Per-user settings · Per-agent toggles · Integrations → MCP in the UI</text>

  <line x1="250" y1="410" x2="312" y2="390" stroke="#38BDF8" stroke-width="3" marker-end="url(#arrowBlue)"/>
  <line x1="570" y1="390" x2="632" y2="390" stroke="#8B5CF6" stroke-width="3" marker-end="url(#arrowPurple)"/>
  <line x1="860" y1="390" x2="912" y2="390" stroke="#06AC38" stroke-width="3" marker-end="url(#arrowGreen)"/>
  <line x1="445" y1="230" x2="445" y2="282" stroke="#F59E0B" stroke-width="3" marker-end="url(#arrowGold)"/>
  <line x1="150" y1="520" x2="150" y2="528" stroke="#64748B" stroke-width="2"/>

  <text x="600" y="622" text-anchor="middle" fill="#64748B" font-family="system-ui,sans-serif" font-size="12">Ask MCP: natural-language Q&amp;A · Investigations: tool catalog injected before AI diagnosis</text>
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
