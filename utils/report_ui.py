from __future__ import annotations
import re
from io import BytesIO
from typing import Any, Dict, Optional

def inject_report_css(st=None):
    if st is None:
        import streamlit as st

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;800&display=swap');
        
        /* 전체 컨테이너 및 폰트 */
        .rpt-wrap { 
            max-width: 1040px; margin: 0 auto; 
            font-family: 'Pretendard', sans-serif;
            background-color: #fcfcfd; padding: 20px; border-radius: 24px;
        }

        /* 헤더 섹션 */
        .rpt-h1 {
            text-align: center; font-size: 34px; font-weight: 800;
            letter-spacing: -1px; margin: 20px 0 5px 0; color: #1e293b;
        }
        .rpt-meta {
            text-align: center; font-size: 15px; color: #64748b;
            margin-bottom: 25px; font-weight: 500;
        }
        .rpt-hr { 
            height: 3px; background: linear-gradient(90deg, #3b82f6, #2dd4bf); 
            border: none; margin: 10px auto 30px auto; width: 60px; border-radius: 10px;
        }

        /* 섹션 타이틀 스타일 업그레이드 */
        .rpt-sec-title {
            display: flex; align-items: center; gap: 12px;
            margin: 40px 0 15px 0;
        }
        .rpt-sec-bar {
            width: 6px; height: 24px; border-radius: 4px;
            background: #3b82f6;
        }
        .rpt-sec-text {
            font-size: 20px; font-weight: 800; color: #0f172a; letter-spacing: -0.5px;
        }
        .rpt-sec-sub { margin-left: auto; }

        /* 카드 디자인: 깊이감과 테두리 강조 */
        .rpt-card {
            background: #ffffff; border: 1px solid #f1f5f9; border-radius: 20px;
            padding: 24px; box-shadow: 0 4px 20px rgba(15, 23, 42, 0.04);
            margin-bottom: 16px;
        }
        .rpt-body {
            font-size: 15px; line-height: 1.8; color: #334155; word-break: keep-all;
        }
        .rpt-strong { font-weight: 800; color: #2563eb; background: #eff6ff; padding: 0 4px; border-radius: 4px; }

        /* 칩 디자인 강화 */
        .rpt-chip {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 6px 14px; border-radius: 8px;
            background: #f1f5f9; color: #475569; font-size: 13px; font-weight: 700;
        }
        .rpt-chip-major { background: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
        
        /* 강점/보완 박스 시각화 */
        .rpt-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
        .rpt-colorbox {
            border-radius: 20px; padding: 20px; border: 1px solid transparent;
        }
        .rpt-colorbox.good { background: #f0fdf4; border-color: #dcfce7; }
        .rpt-colorbox.bad { background: #fff1f2; border-color: #ffe4e6; }
        .rpt-box-title { font-size: 16px; font-weight: 800; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }
        .rpt-box-title.good { color: #166534; }
        .rpt-box-title.bad { color: #991b1b; }

        /* 리스트 스타일 */
        .rpt-list { margin: 0; padding-left: 20px; list-style-type: none; }
        .rpt-list li { margin: 8px 0; position: relative; color: #334155; font-size: 14px; }
        .rpt-list li::before { 
            content: "•"; color: currentColor; position: absolute; left: -15px; font-weight: bold; 
        }

        /* KPI 별점 & 점수 */
        .rpt-kpi-head {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px dashed #e2e8f0;
        }
        .rpt-kpi-title { font-size: 17px; font-weight: 800; color: #1e293b; }
        .rpt-stars { font-size: 16px; color: #f59e0b; letter-spacing: 2px; }
        .rpt-score { font-size: 14px; color: #94a3b8; font-weight: 700; margin-left: 8px; }

        /* 추천도서 카드 프리미엄화 */
        .book-card {
            background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 16px; margin-top: 12px; transition: transform 0.2s;
        }
        .book-title { font-weight: 800; font-size: 15px; color: #0f172a; margin: 8px 0 4px 0; }
        .book-author { color: #64748b; font-size: 13px; font-weight: 600; }

        /* 하단 그리드 */
        .rpt-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
        .rpt-topic {
            background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px;
            padding: 18px; border-top: 4px solid #3b82f6;
        }
        
        @media (max-width: 960px) { .rpt-grid-2, .rpt-grid-3 { grid-template-columns: 1fr; } }
        
        /* 인쇄 최적화 */
        @media print {
            .stDownloadButton, .stButton { display: none !important; }
            .rpt-wrap { padding: 0; background: white; }
            .rpt-card { box-shadow: none; border: 1px solid #eee; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 유틸리티 함수 (기존 로직 유지) ---
def _escape_html(text: str) -> str:
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _stars(score: Any, max_score: int = 10) -> str:
    try: s = int(score)
    except: s = 0
    s = max(0, min(s, max_score))
    return "★" * (s//2) + "☆" * (5 - s//2)  # 5성 체계로 시각화 최적화

def _safe_list(x) -> list[str]:
    if isinstance(x, list): return [str(v).strip() for v in x if str(v).strip()]
    return []

def _html_list(items: list[str]) -> str:
    if not items: return "<ul class='rpt-list'><li>-</li></ul>"
    li = "".join([f"<li>{_escape_html(v)}</li>" for v in items])
    return f"<ul class='rpt-list'>{li}</ul>"

def _pick_book_chip_class(category: str) -> str:
    c = (category or "").strip()
    if any(k in c for k in ["약점", "보완"]): return "red"
    if any(k in c for k in ["관심", "심화"]): return "green"
    return "blue"

def _extract_keywords(expected_major: str, strengths: list[str], needs: list[str]) -> list[str]:
    pool = [expected_major] if expected_major else []
    pool += strengths[:4] + needs[:3]
    keywords = []
    for t in pool:
        t = re.sub(r"\([^)]*\)", "", t).strip()
        t = re.split(r"[·/,:;]| - ", t)[0].strip()
        if 2 <= len(t) <= 12: keywords.append(t)
    keywords = list(dict.fromkeys(keywords))
    keywords.sort(key=len, reverse=True)
    return keywords[:8]

def _highlight_keywords_html(text: str, keywords: list[str]) -> str:
    escaped = _escape_html(text).replace("\n", "<br/>")
    for kw in keywords:
        kw_e = _escape_html(kw)
        if kw_e: escaped = escaped.replace(kw_e, f"<span class='rpt-strong'>{kw_e}</span>")
    return escaped

# --- 메인 렌더링 함수 ---
def render_report_modal(st, report: Dict[str, Any], sid: str, sname: str, radar_png: Optional[BytesIO] = None, pdf_bytes: Optional[bytes] = None):
    @st.dialog(f"📊 {sname} 학생 심층 분석 리포트", width="large")
    def _show():
        inject_report_css(st)
        
        # 데이터 파싱
        majors = report.get("역량 기반 추천 학과", [])
        expected_major = majors[0].get("학과", "") if majors and isinstance(majors[0], dict) else ""
        strengths = _safe_list(report.get("핵심 강점", []))
        needs = _safe_list(report.get("보완 추천 영역", []))
        
        st.markdown("<div class='rpt-wrap'>", unsafe_allow_html=True)

        # 1. Header
        st.markdown(f"<div class='rpt-h1'>SH-Insight 분석 보고서</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='rpt-meta'>학번: {sid}  |  성명: {sname}  |  2024학년도 정기 분석</div>", unsafe_allow_html=True)
        st.markdown("<hr class='rpt-hr'/>", unsafe_allow_html=True)

        # 2. 종합 평가 (Full Width)
        st.markdown(f"""
            <div class='rpt-sec-title'>
                <div class='rpt-sec-bar'></div>
                <div class='rpt-sec-text'>AI 종합 판정</div>
                <div class='rpt-sec-sub'><span class='rpt-chip rpt-chip-major'>🎯 희망 직무: {expected_major or '미정'}</span></div>
            </div>
            <div class='rpt-card'>
                <div class='rpt-body'>{_highlight_keywords_html(report.get("종합 평가", ""), _extract_keywords(expected_major, strengths, needs))}</div>
            </div>
        """, unsafe_allow_html=True)

        # 3. 역량 시각화 (Radar Chart & Strength/Weakness)
        st.markdown("""
            <div class='rpt-sec-title'>
                <div class='rpt-sec-bar'></div>
                <div class='rpt-sec-text'>핵심 역량 밸런스</div>
            </div>
        """, unsafe_allow_html=True)
        
        col_img, col_txt = st.columns([1, 1.2])
        with col_img:
            if radar_png: st.image(radar_png, use_container_width=True)
            else: st.info("역량 데이터 분석 중...")
        
        with col_txt:
            st.markdown(f"""
                <div class='rpt-colorbox good'>
                    <div class='rpt-box-title good'>✨ 주요 강점</div>
                    {_html_list(strengths)}
                </div>
                <div style='height:12px'></div>
                <div class='rpt-colorbox bad'>
                    <div class='rpt-box-title bad'>🚩 보완 필요 사항</div>
                    {_html_list(needs)}
                </div>
            """, unsafe_allow_html=True)

        # 4. 상세 분석 (Cards)
        st.markdown("<div class='rpt-sec-title'><div class='rpt-sec-bar'></div><div class='rpt-sec-text'>평가 항목별 상세 분석</div></div>", unsafe_allow_html=True)
        detail = report.get("3대 평가 항목별 상세 분석", {})
        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            v = detail.get(key, {})
            score = v.get("점수", 0)
            st.markdown(f"""
                <div class='rpt-card'>
                    <div class='rpt-kpi-head'>
                        <div class='rpt-kpi-title'>{key}</div>
                        <div class='rpt-stars'>{_stars(score)}<span class='rpt-score'>{score}/10</span></div>
                    </div>
                    <div class='rpt-body'><b>💡 분석:</b> {v.get("분석", "-")}</div>
                </div>
            """, unsafe_allow_html=True)

        # 5. 하단 3단 정보 (추천 학과)
        st.markdown("<div class='rpt-sec-title'><div class='rpt-sec-bar'></div><div class='rpt-sec-text'>역량 기반 추천 학과</div></div>", unsafe_allow_html=True)
        st.markdown("<div class='rpt-grid-3'>", unsafe_allow_html=True)
        for m in (majors[:3] if majors else [{"학과": "-", "근거": "-"}] * 3):
            dept = m.get("학과", "-")
            why = m.get("근거", "-")
            st.markdown(f"""
                <div class='rpt-topic'>
                    <div class='rpt-chip rpt-chip-major' style='margin-bottom:10px;'>Best Match</div>
                    <div class='book-title' style='font-size:17px;'>{dept}</div>
                    <p style='font-size:13px; color:#475569; line-height:1.5;'>{why}</p>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # PDF Download Button
        if pdf_bytes:
            st.markdown("<div style='height:30px'></div>", unsafe_allow_html=True)
            st.download_button("📥 정식 보고서 PDF 다운로드", data=pdf_bytes, file_name=f"Report_{sname}.pdf", mime="application/pdf", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    _show()
