import os
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def _candidate_font_paths():
    here = os.path.dirname(os.path.abspath(__file__))
    proj_root = os.path.abspath(os.path.join(here, ".."))
    return [
        os.path.join(proj_root, "assets", "NanumGothic.ttf"),
        os.path.join(proj_root, "assets", "NotoSansKR-Regular.ttf"),
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]


def setup_reportlab_korean_font() -> str | None:
    for fp in _candidate_font_paths():
        if fp and os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("KOR", fp))
                return "KOR"
            except Exception:
                continue
    return None


def build_pdf_bytes(report: dict, radar_png, sid: str, sname: str) -> bytes:
    """
    웹 레이아웃을 PDF로 최대한 비슷하게 구성.
    폰트가 없으면 Helvetica로라도 PDF는 생성되도록 설계.
    """
    kor_font = setup_reportlab_korean_font()
    base_font = kor_font if kor_font else "Helvetica"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title", parent=styles["Title"], fontName=base_font,
        fontSize=22, leading=28, alignment=1, spaceAfter=8
    )
    meta_style = ParagraphStyle(
        "meta", parent=styles["Normal"], fontName=base_font,
        fontSize=10.5, textColor=colors.HexColor("#374151"),
        alignment=2, spaceAfter=6
    )
    h_style = ParagraphStyle(
        "h", parent=styles["Heading2"], fontName=base_font,
        fontSize=14.5, spaceBefore=12, spaceAfter=8
    )
    body_style = ParagraphStyle(
        "body", parent=styles["BodyText"], fontName=base_font,
        fontSize=10.8, leading=16, textColor=colors.HexColor("#111827")
    )
    small_style = ParagraphStyle(
        "small", parent=styles["BodyText"], fontName=base_font,
        fontSize=9.8, leading=14, textColor=colors.HexColor("#374151")
    )

    def card_wrap(inner_tbl, w_mm=174):
        wrap = Table([[inner_tbl]], colWidths=[w_mm * mm])
        wrap.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E7EB")),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        return wrap

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=18 * mm, leftMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm
    )
    story = []

    # 타이틀
    story.append(Paragraph("SH-Insight 심층 분석 보고서", title_style))
    story.append(Paragraph(f"{sid} / {sname}  |  생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}", meta_style))

    # 구분선
    line = Table([[""]], colWidths=[174 * mm], rowHeights=[1])
    line.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#111827"))]))
    story.append(line)
    story.append(Spacer(1, 10))

    # 종합 평가
    majors = report.get("역량 기반 추천 학과", [])
    hope = ""
    if isinstance(majors, list) and majors:
        hope = str(majors[0].get("학과", "") if isinstance(majors[0], dict) else majors[0]).strip()
    hope = hope if hope else "미기재"

    story.append(Paragraph(f"종합 평가 (예상 희망 진로: {hope})", h_style))
    overall = str(report.get("종합 평가", "") or "").replace("\n", "<br/>")
    overall_tbl = Table([[Paragraph(overall, body_style)]], colWidths=[174 * mm])
    story.append(card_wrap(overall_tbl))
    story.append(Spacer(1, 10))

    # 레이더
    story.append(Paragraph("핵심 역량 분석", h_style))
    if radar_png is not None:
        img = RLImage(radar_png, width=70 * mm, height=62 * mm)
        center = Table([[img]], colWidths=[174 * mm])
        center.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(center)
        story.append(Spacer(1, 10))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
