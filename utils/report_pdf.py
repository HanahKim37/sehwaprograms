# utils/report_pdf.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# -----------------------------
# PDF 한글 폰트 자동 등록 (ReportLab)
# -----------------------------
def _register_korean_font() -> str:
    """
    가능한 한 한글 폰트를 등록한다.
    - 서버에 폰트가 없을 수 있으므로, 여러 경로 탐색 + 로컬 fonts 폴더 탐색
    성공 시 폰트명 반환. 실패 시 'Helvetica' 반환(한글 깨질 수 있음).
    """
    candidates = []

    # 흔한 리눅스/윈도/맥 경로
    candidates += [
        ("NanumGothic", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
        ("NanumGothic", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
        ("NotoSansKR", "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf"),
        ("NotoSansKR", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        ("AppleGothic", "/System/Library/Fonts/AppleGothic.ttf"),
        ("MalgunGothic", "C:/Windows/Fonts/malgun.ttf"),
    ]

    # 프로젝트 내부 utils/fonts 폴더 권장
    here = Path(__file__).resolve().parent
    fonts_dir = here / "fonts"
    if fonts_dir.exists():
        for p in list(fonts_dir.glob("*.ttf")) + list(fonts_dir.glob("*.otf")) + list(fonts_dir.glob("*.ttc")):
            # 파일명 기반으로 폰트명 지정
            name = p.stem.replace(" ", "")
            candidates.append((name, str(p)))

    for font_name, font_path in candidates:
        try:
            if Path(font_path).exists():
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                return font_name
        except Exception:
            continue

    return "Helvetica"


# -----------------------------
# 작은 유틸
# -----------------------------
def _safe_list(x) -> List[str]:
    if isinstance(x, list):
        return [str(v) for v in x if str(v).strip()]
    return []


def _section_title(text: str) -> Paragraph:
    styles = getSampleStyleSheet()
    return Paragraph(f"<b>{text}</b>", styles["Heading2"])


def _bar_section_title(text: str, styles: Dict[str, ParagraphStyle]) -> Table:
    """
    사진처럼 왼쪽에 얇은 바가 있는 섹션 제목.
    """
    bar = Table(
        [[Paragraph("", styles["Normal"]), Paragraph(f"<b>{text}</b>", styles["H2Custom"])]],
        colWidths=[4*mm, 170*mm]
    )
    bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#9CA3AF")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return bar


def _card_paragraph(text: str, styles: Dict[str, ParagraphStyle]) -> Table:
    """
    박스(카드) 형태로 문단을 감싼다.
    """
    p = Paragraph(text.replace("\n", "<br/>"), styles["BodyCustom"])
    t = Table([[p]], colWidths=[174*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E7EB")),
        ("ROUNDRECT", (0, 0), (-1, -1), 10, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def _pill_list_box(title: str, items: List[str], bg: colors.Color, border: colors.Color, styles: Dict[str, ParagraphStyle]) -> Table:
    """
    사진처럼 '색 박스 안에 문구'가 들어가는 형태.
    """
    rows = [[Paragraph(f"<b>{title}</b>", styles["CardTitle"])]]
    if items:
        for it in items:
            rows.append([Paragraph(f"• {it}", styles["BodyCustom"])])
    else:
        rows.append([Paragraph("-", styles["BodyCustom"])])

    t = Table(rows, colWidths=[85*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("BOX", (0, 0), (-1, -1), 0.8, border),
        ("ROUNDRECT", (0, 0), (-1, -1), 12, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWSPACING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _stars(score: int, max_score: int = 10) -> str:
    s = max(0, min(int(score), max_score))
    return "★" * s + "☆" * (max_score - s)


# -----------------------------
# 메인: PDF 생성
# -----------------------------
def build_pdf_bytes(
    report: Dict[str, Any],
    radar_png: Optional[BytesIO],
    sid: str,
    sname: str,
) -> bytes:
    font_name = _register_korean_font()

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=18*mm,
        leftMargin=18*mm,
        topMargin=16*mm,
        bottomMargin=16*mm
    )

    base = getSampleStyleSheet()
    styles: Dict[str, ParagraphStyle] = {}

    styles["TitleCenter"] = ParagraphStyle(
        "TitleCenter",
        parent=base["Title"],
        alignment=1,
        fontName=font_name,
        fontSize=20,
        leading=24,
        spaceAfter=8
    )
    styles["RightSmall"] = ParagraphStyle(
        "RightSmall",
        parent=base["Normal"],
        alignment=2,
        fontName=font_name,
        fontSize=10,
        textColor=colors.HexColor("#374151")
    )
    styles["H2Custom"] = ParagraphStyle(
        "H2Custom",
        parent=base["Heading2"],
        fontName=font_name,
        fontSize=14,
        textColor=colors.HexColor("#111827"),
        spaceAfter=4
    )
    styles["CardTitle"] = ParagraphStyle(
        "CardTitle",
        parent=base["Heading3"],
        fontName=font_name,
        fontSize=12,
        textColor=colors.HexColor("#111827"),
        spaceAfter=6
    )
    styles["BodyCustom"] = ParagraphStyle(
        "BodyCustom",
        parent=base["BodyText"],
        fontName=font_name,
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#111827")
    )

    story = []

    # 1) 제목 가운데 크게
    story.append(Paragraph("SH-Insight 심층 분석 보고서", styles["TitleCenter"]))

    # 2) 학생 정보 오른쪽 정렬 + 줄
    story.append(Paragraph(f"{sid} / {sname}", styles["RightSmall"]))
    hr = Table([[""]], colWidths=[174*mm], rowHeights=[0.6*mm])
    hr.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#111827"))]))
    story.append(Spacer(1, 4))
    story.append(hr)
    story.append(Spacer(1, 12))

    # 예상 희망 진로(추천 학과 1순위)
    majors = report.get("역량 기반 추천 학과", [])
    expected_major = ""
    if isinstance(majors, list) and majors:
        m0 = majors[0]
        if isinstance(m0, dict):
            expected_major = str(m0.get("학과", ""))
        else:
            expected_major = str(m0)

    # 3) 종합 평가 섹션
    story.append(_bar_section_title(f"종합 평가 (예상 희망 진로: {expected_major})", styles))
    story.append(Spacer(1, 6))
    story.append(_card_paragraph(str(report.get("종합 평가", "") or ""), styles))
    story.append(Spacer(1, 16))

    # 4) 핵심 역량 분석 + 레이더(가운데 작게)
    story.append(_bar_section_title("핵심 역량 분석", styles))
    story.append(Spacer(1, 8))
    if radar_png is not None:
        img = RLImage(radar_png, width=85*mm, height=75*mm)  # 가운데 조그맣게
        img.hAlign = "CENTER"
        story.append(img)
        story.append(Spacer(1, 12))
    else:
        story.append(Paragraph("-", styles["BodyCustom"]))
        story.append(Spacer(1, 10))

    # 강점/보완 2박스
    strengths = _safe_list(report.get("핵심 강점", []))
    needs = _safe_list(report.get("보완 추천 영역", []))

    left_box = _pill_list_box(
        "핵심 강점 (Core Strengths)",
        strengths,
        bg=colors.HexColor("#ECFDF5"),
        border=colors.HexColor("#A7F3D0"),
        styles=styles
    )
    right_box = _pill_list_box(
        "보완 추천 영역 (Needs Improvement)",
        needs,
        bg=colors.HexColor("#FEF2F2"),
        border=colors.HexColor("#FECACA"),
        styles=styles
    )

    two = Table([[left_box, right_box]], colWidths=[87*mm, 87*mm])
    two.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(two)
    story.append(Spacer(1, 18))

    # 5) 3대 평가 항목별 상세 분석
    story.append(_bar_section_title("3대 평가 항목별 상세 분석", styles))
    story.append(Spacer(1, 10))

    detail = report.get("3대 평가 항목별 상세 분석", {})
    if isinstance(detail, dict):
        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            v = detail.get(key, {})
            if not isinstance(v, dict):
                continue

            score = int(v.get("점수", 0) or 0)
            star_line = _stars(score, 10)

            # 헤더(왼쪽 항목명, 오른쪽 별/점수)
            head = Table(
                [[
                    Paragraph(f"<b>{key}</b>", styles["CardTitle"]),
                    Paragraph(f"{star_line} ({score}/10)", styles["RightSmall"])
                ]],
                colWidths=[120*mm, 54*mm]
            )
            head.setStyle(TableStyle([
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(head)

            # 근거 문장 박스(작은 박스)
            evid = _safe_list(v.get("평가 근거 문장", []))
            evid_rows = [[Paragraph("<b>평가 근거 문장</b>", styles["BodyCustom"])]]
            for e in evid[:6]:
                evid_rows.append([Paragraph(f"• {e}", styles["BodyCustom"])])

            evid_table = Table(evid_rows, colWidths=[174*mm])
            evid_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E7EB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(evid_table)
            story.append(Spacer(1, 8))

            # 분석 박스
            story.append(_card_paragraph(str(v.get("분석", "") or ""), styles))
            story.append(Spacer(1, 16))
    else:
        story.append(Paragraph("-", styles["BodyCustom"]))
        story.append(Spacer(1, 12))

    # 6) 맞춤형 성장 제안 (좌) + 추천 도서 (우)
    story.append(_bar_section_title("맞춤형 성장 제안 (Growth Suggestions)", styles))
    story.append(Spacer(1, 10))

    growth = report.get("맞춤형 성장 제안", {})
    books = report.get("추천 도서", [])

    left_items = []
    if isinstance(growth, dict):
        left_items.append(Paragraph("<b>생활기록부 중점 보완 전략</b>", styles["CardTitle"]))
        left_items.append(Paragraph(str(growth.get("생활기록부 중점 보완 전략", "") or "-").replace("\n", "<br/>"), styles["BodyCustom"]))
        left_items.append(Spacer(1, 6))
        left_items.append(Paragraph("<b>추천 학교 행사</b>", styles["CardTitle"]))
        행사 = growth.get("추천 학교 행사", [])
        if isinstance(행사, list) and 행사:
            for it in 행사[:6]:
                left_items.append(Paragraph(f"• {it}", styles["BodyCustom"]))
        else:
            left_items.append(Paragraph("-", styles["BodyCustom"]))

    left_card = Table([[left_items]], colWidths=[85*mm])
    left_card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E7EB")),
        ("ROUNDRECT", (0, 0), (-1, -1), 12, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    right_rows = [[Paragraph("<b>추천 도서</b>", styles["CardTitle"])]]
    if isinstance(books, list) and books:
        for b in books[:8]:
            if isinstance(b, dict):
                cat = str(b.get("분류", ""))
                title = str(b.get("도서", ""))
                author = str(b.get("저자", ""))
                why = str(b.get("추천 이유", ""))
                right_rows.append([Paragraph(f"<b>[{cat}]</b> {title} ({author})<br/>{why}", styles["BodyCustom"])])
            else:
                right_rows.append([Paragraph(str(b), styles["BodyCustom"])])
    else:
        right_rows.append([Paragraph("-", styles["BodyCustom"])])

    right_card = Table(right_rows, colWidths=[85*mm])
    right_card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E7EB")),
        ("ROUNDRECT", (0, 0), (-1, -1), 12, colors.HexColor("#E5E7EB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    two2 = Table([[left_card, right_card]], colWidths=[87*mm, 87*mm])
    two2.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(two2)
    story.append(Spacer(1, 18))

    # 7) 영역별 심화 탐구 주제 제안 (하늘색 배경 박스)
    story.append(_bar_section_title("영역별 심화 탐구 주제 제안", styles))
    story.append(Spacer(1, 10))

    topics = report.get("영역별 심화 탐구 주제 제안", {})
    topic_rows = [[Paragraph("💡 <b>영역별 심화 탐구 주제 제안</b>", styles["CardTitle"])]]
    for k in ["자율", "진로", "동아리"]:
        v = ""
        if isinstance(topics, dict):
            v = str(topics.get(k, "") or "")
        topic_rows.append([Paragraph(f"<b>[{k}]</b> {v}", styles["BodyCustom"])])

    topic_card = Table(topic_rows, colWidths=[174*mm])
    topic_card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#BFDBFE")),
        ("ROUNDRECT", (0, 0), (-1, -1), 12, colors.HexColor("#BFDBFE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("ROWSPACING", (0, 0), (-1, -1), 8),
    ]))
    story.append(topic_card)
    story.append(Spacer(1, 18))

    # 8) 역량 기반 추천 학과 (3박스)
    story.append(_bar_section_title("역량 기반 추천 학과", styles))
    story.append(Spacer(1, 10))

    majors = report.get("역량 기반 추천 학과", [])
    cards = []
    if isinstance(majors, list) and majors:
        for m in majors[:3]:
            if isinstance(m, dict):
                dept = str(m.get("학과", ""))
                reason = str(m.get("근거", ""))
            else:
                dept = str(m)
                reason = ""
            cell = Table(
                [[Paragraph(f"<b>{dept}</b>", styles["CardTitle"])],
                 [Paragraph(reason.replace("\n", "<br/>"), styles["BodyCustom"])]],
                colWidths=[55*mm]
            )
            cell.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#E5E7EB")),
                ("ROUNDRECT", (0, 0), (-1, -1), 12, colors.HexColor("#E5E7EB")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]))
            cards.append(cell)

    while len(cards) < 3:
        cards.append(Table([[Paragraph("-", styles["BodyCustom"])]], colWidths=[55*mm]))

    majors_row = Table([[cards[0], cards[1], cards[2]]], colWidths=[58*mm, 58*mm, 58*mm])
    majors_row.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(majors_row)

    # 빌드
    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf
