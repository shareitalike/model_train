from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, HRFlowable
)
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import os
from loguru import logger
from ..core.config import get_settings

settings = get_settings()


class PDFExporter:
    def __init__(self):
        self._fn = "Helvetica"
        self._fb = "Helvetica-Bold"
        self._load_font()

    def _load_font(self):
        try:
            if os.path.exists(settings.DEVANAGARI_FONT):
                pdfmetrics.registerFont(TTFont("NotoDevanagari", settings.DEVANAGARI_FONT))
                pdfmetrics.registerFont(TTFont("NotoDevanagari-Bold", settings.DEVANAGARI_FONT_BOLD))
                self._fn = "NotoDevanagari"
                self._fb = "NotoDevanagari-Bold"
                logger.info("[PDFExport] Devanagari font loaded")
        except Exception as e:
            logger.warning(f"[PDFExport] Font error: {e}")

    def export(self, result_data: dict, include_confidence: bool = True) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            rightMargin=20*mm, leftMargin=20*mm,
            topMargin=25*mm, bottomMargin=20*mm,
            title="कैथी OCR आउटपुट",
            author="Kaithi Digitization System",
        )
        fn, fb = self._fn, self._fb
        styles = {
            "title":   ParagraphStyle("title",   fontName=fb, fontSize=20, spaceAfter=8, alignment=TA_CENTER),
            "heading": ParagraphStyle("heading", fontName=fb, fontSize=15, spaceAfter=6, spaceBefore=12,
                                       textColor=colors.HexColor("#1a237e")),
            "body":    ParagraphStyle("body",    fontName=fn, fontSize=13, leading=24, spaceAfter=6),
            "meta":    ParagraphStyle("meta",    fontName="Helvetica", fontSize=9, textColor=colors.grey),
        }
        story = []
        story.append(Paragraph("कैथी लिपि → हिन्दी रूपान्तरण", styles["title"]))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a237e")))
        story.append(Spacer(1, 5*mm))

        meta = result_data.get("metadata", {})
        conf = result_data.get("overall_confidence", 0)
        tbl_data = [[
            "कुल पृष्ठ", str(meta.get("total_pages", "N/A")),
            "विश्वास", f"{conf*100:.1f}%",
            "क्षेत्र", meta.get("region", "मानक"),
        ]]
        t = Table(tbl_data, colWidths=[35*mm, 25*mm, 25*mm, 25*mm, 25*mm, 30*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8eaf6")),
            ("FONTNAME", (0,0), (-1,-1), fn),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
            ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 8*mm))

        for page in result_data.get("pages", []):
            story.append(Paragraph(f"पृष्ठ {page.get('page_number', '?')}", styles["heading"]))
            hindi = page.get("corrected_text") or page.get("hindi_text", "")
            if hindi:
                for para_text in hindi.split("\n"):
                    if para_text.strip():
                        try:
                            story.append(Paragraph(para_text, styles["body"]))
                        except Exception:
                            story.append(Paragraph(
                                para_text.encode("ascii", "replace").decode(), styles["body"]
                            ))
            else:
                story.append(Paragraph("पाठ उपलब्ध नहीं", styles["meta"]))
            if include_confidence:
                p_conf = page.get("confidence", 0)
                color = "#22c55e" if p_conf >= 0.9 else "#eab308" if p_conf >= 0.7 else "#ef4444"
                story.append(Paragraph(
                    f"विश्वास: {p_conf*100:.1f}% | पंक्तियाँ: {page.get('line_count', 0)}",
                    ParagraphStyle("cf", fontName="Helvetica", fontSize=9,
                                    textColor=colors.HexColor(color))
                ))
            story.append(Spacer(1, 5*mm))
            story.append(PageBreak())

        doc.build(story)
        data = buf.getvalue()
        buf.close()
        return data
