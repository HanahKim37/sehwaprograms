# utils/report_generator.py
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage

def build_pdf_from_report(report: dict, radar_png: BytesIO, sid: str, sname: str) -> bytes:
    """
    ai_report_generator에서 생성된 JSON(report)을
    PDF로 변환하는 전용 모듈
    """

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=16*mm,
        rightMargin=16*mm,
        topMargin=16*mm,
        bottomMargin=16*mm,
    )

    styles = getSampleStyleSheet()
    story = []

    # 제목
    story.append(Paragraph("SH-Insight 심층 분석 보고서", styles["Title"]))
    story.append(Paragraph(f"{sid} / {sname}", styles["Normal"]))
    story.append(Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M"), styles["Normal"]))
    story.append(Spacer(1, 12))

    # 종합 평가
    story.append(Paragraph("종합 평가", styles["Heading2"]))
    story.append(Paragraph(report.get("종합 평가", ""), styles["BodyText"]))
    story.append(Spacer(1, 10))

    # 레이더
    if radar_png is not None:
        story.append(Paragraph("핵심 역량 분포", styles["Heading2"]))
        story.append(RLImage(radar_png, width=110*mm, height=100*mm))
        story.append(Spacer(1, 12))

    # 3대 평가
    detail = report.get("3대 평가 항목별 상세 분석", {})
    for area, data in detail.items():
        story.append(Paragraph(f"{area} ({data.get('점수',0)}/10)", styles["Heading3"]))
        story.append(Paragraph(data.get("분석",""), styles["BodyText"]))
        for ev in data.get("평가 근거 문장", [])[:5]:
            story.append(Paragraph(f"- {ev}", styles["BodyText"]))
        story.append(Spacer(1, 8))

    doc.build(story)
    return buf.getvalue()
