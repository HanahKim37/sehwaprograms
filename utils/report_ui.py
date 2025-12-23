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
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700;900&display=swap');
        
        /* 메인 컨테이너 스타일 */
        .report-container {
            font-family: 'Noto Sans KR', sans-serif;
            color: #333;
            line-height: 1.6;
        }

        /* 1. 헤더 (중앙 정렬, 박스 제거) */
        .rpt-header {
            text-align: center;
            padding-bottom: 20px;
            margin-bottom: 30px;
            border-bottom: 2px solid #333;
        }
        .rpt-title { font-size: 32px; font-weight: 900; color: #111; margin: 0 0 5px 0; }
        .rpt-sub { font-size: 14px; color: #666; margin: 0; }
        .rpt-meta { text-align: right; font-size: 14px; font-weight: 700; color: #555; margin-top: 15px; }

        /* 2. 섹션 타이틀 */
        .rpt-section-title {
            font-size: 20px; font-weight: 800; color: #1e293b;
            margin-top: 40px; margin-bottom: 15px;
            border-left: 5px solid #2563eb; padding-left: 12px;
            display: flex; align-items: center;
        }

        /* 3. 종합 평가 (형광펜) */
        .rpt-summary-box {
            background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 24px; font-size: 16px; text-align: justify; color: #334155;
        }
        .highlight-marker { 
            background: linear-gradient(to top, #fef08a 40%, transparent 40%); 
            font-weight: 800; padding: 0 2px; 
        }

        /* 4. 박스 공통 */
        .box-panel {
            padding: 20px; border-radius: 12px; height: 100%; border: 1px solid transparent;
        }
        .bg-green { background: #f0fdf4; border-color: #bbf7d0; }
        .bg-red { background: #fef2f2; border-color: #fecaca; }
        .bg-blue { background: #eff6ff; border-color: #dbeafe; }
        .bg-gray { background: #f8fafc; border-color: #e2e8f0; }
        
        .box-head { display: block; font-weight: 800; font-size: 16px; margin-bottom: 12px; color: #333; }
        .box-list { margin: 0; padding-left: 18px; font-size: 14px; }
        .box-list li { margin-bottom: 6px; }

        /* 5. 상세 분석 카드 */
        .detail-card {
            background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
            padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .detail-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .detail-title { font-size: 18px; font-weight: 800; color: #1e293b; }
        .star-gold { color: #f59e0b; font-size: 18px; letter-spacing: 2px; }
        .star-gray { color: #e2e8f0; font-size: 18px; letter-spacing: 2px; }
        
        .evidence-box {
            background-color: #f1f5f9; border-radius: 8px; padding: 15px; margin-top: 12px;
            border-left: 4px solid #94a3b8; font-size: 13.5px; color: #475569;
        }

        /* 6. 추천 도서 */
        .book-item {
            background: #fff; border: 1px solid #e2e8f0; border-radius: 8px;
            padding: 12px; margin-bottom: 10px;
        }
        .book-tag {
            display: inline-block; font-size: 11px; font-weight: 800; color: #fff;
            background: #3b82f6; padding: 2px 6px; border-radius: 4px; margin-right: 6px;
        }
        .book-title { font-weight: 800; color: #1e293b; font-size: 14px; }
        .book-reason { font-size: 13px; color: #666; margin-top: 5px; border-top: 1px dashed #eee; padding-top: 5px;}

        /* 7. 추천 학과 */
        .major-card {
            background: #fff; border: 1px solid #cbd5e1; border-radius: 12px;
            padding: 15px; text-align: center; position: relative; margin-top: 10px; height: 100%;
        }
        .major-badge {
            position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
            background: #0f172a; color: #fff; font-size: 11px; font-weight: 800;
            padding: 4px 10px; border-radius: 20px;
        }

        @media print {
            .stButton, .stDownloadButton { display: none !important; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def _html_list_styled(items: list[str]) -> str:
    if not items: return "-"
    li = "".join([f"<li>{str(x)}</li>" for x in items])
    return f"<ul class='box-list'>{li}</ul>"

def _highlight_text(text: str, keywords: list[str]) -> str:
    text = str(text).replace("\n", "<br>")
    for kw in keywords:
        if kw and len(kw) > 1:
            text = text.replace(kw, f"<span class='highlight-marker'>{kw}</span>")
    return text

def _stars_html(score: int) -> str:
    try: score = int(score)
    except: score = 0
    full = "★" * (score // 2)
    empty = "☆" * (5 - (score // 2))
    return f"<span class='star-gold'>{full}</span><span class='star-gray'>{empty}</span>"

def render_report_modal(st, report: Dict[str, Any], sid: str, sname: str, radar_png: Optional[BytesIO] = None, pdf_bytes: Optional[bytes] = None):
    @st.dialog(f"📊 {sname} 학생 분석 결과", width="large")
    def _show():
        inject_report_css(st)
        
        # 데이터 파싱
        overall = report.get("종합 평가", "")
        detail = report.get("3대 평가 항목별 상세 분석", {}) or {}
        strengths = report.get("핵심 강점", [])
        weaknesses = report.get("보완 추천 영역", [])
        growth = report.get("맞춤형 성장 제안", {}) or {}
        strat = growth.get("생활기록부 중점 보완 전략", "")
        events = growth.get("추천 학교 행사", [])
        books = report.get("추천 도서", [])
        majors = report.get("역량 기반 추천 학과", [])

        # 키워드
        keywords = []
        if majors and isinstance(majors[0], dict): keywords.append(majors[0].get("학과", ""))
        keywords += [s.split()[0] for s in strengths[:3] if s]

        # --- 보고서 시작 ---
        st.markdown("<div class='report-container'>", unsafe_allow_html=True)

        # 1. 헤더 (중앙 정렬)
        st.markdown(f"""
            <div class='rpt-header'>
                <div class='rpt-title'>종합 분석 보고서</div>
                <div class='rpt-sub'>AI Student Record Analysis Report</div>
                <div class='rpt-meta'>학번: {sid} ｜ 성명: {sname}</div>
            </div>
        """, unsafe_allow_html=True)

        # 2. 종합 평가
        st.markdown("<div class='rpt-section-title'>1. 종합 평가</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='rpt-summary-box'>{_highlight_text(overall, keywords)}</div>", unsafe_allow_html=True)

        # 3. 그래프 및 강점/보완
        st.markdown("<div class='rpt-section-title'>2. 역량 시각화 및 분석</div>", unsafe_allow_html=True)
        
        # 그래프 중앙 배치 (크기 줄임)
        if radar_png:
            c1, c2, c3 = st.columns([1, 1.5, 1])
            with c2:
                st.image(radar_png, use_container_width=True)
        
        # 강점/보완 2단 배치
        col_str, col_weak = st.columns(2)
        with col_str:
            st.markdown(f"""
                <div class='box-panel bg-green'>
                    <span class='box-head' style='color:#15803d;'>✅ 핵심 강점</span>
                    {_html_list_styled(strengths)}
                </div>
            """, unsafe_allow_html=True)
        with col_weak:
            st.markdown(f"""
                <div class='box-panel bg-red'>
                    <span class='box-head' style='color:#b91c1c;'>⚠️ 보완 추천 영역</span>
                    {_html_list_styled(weaknesses)}
                </div>
            """, unsafe_allow_html=True)

        # 4. 상세 분석
        st.markdown("<div class='rpt-section-title'>3. 평가 항목별 상세 분석</div>", unsafe_allow_html=True)
        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            v = detail.get(key, {})
            score = v.get('점수', 0)
            
            st.markdown(f"""
                <div class='detail-card'>
                    <div class='detail-head'>
                        <span class='detail-title'>{key}</span>
                        <div>{_stars_html(score)} <span style='font-weight:bold; color:#666;'>({score}/10)</span></div>
                    </div>
                    <div style='font-size:15px; color:#333; margin-bottom:8px;'>{v.get('분석', '-')}</div>
                    <div class='evidence-box'>
                        <div style='font-weight:800; margin-bottom:5px;'>📢 평가 근거 문장</div>
                        {_html_list_styled(v.get('평가 근거 문장', [])[:3])}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # 5. 성장 제안 (2단)
        st.markdown("<div class='rpt-section-title'>4. 맞춤형 성장 제안</div>", unsafe_allow_html=True)
        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            st.markdown(f"""
                <div class='box-panel bg-blue' style='margin-bottom:15px;'>
                    <span class='box-head' style='color:#1d4ed8;'>📌 생활기록부 중점 전략</span>
                    <div style='font-size:14px;'>{strat or '-'}</div>
                </div>
                <div class='box-panel bg-blue'>
                    <span class='box-head' style='color:#1d4ed8;'>🏫 추천 학교 행사</span>
                    {_html_list_styled(events[:4])}
                </div>
            """, unsafe_allow_html=True)
            
        with g_col2:
            # 도서 목록 HTML 조립
            books_html = ""
            for b in books[:3]:
                if isinstance(b, dict):
                    books_html += f"""
                        <div class='book-item'>
                            <div>
                                <span class='book-tag'>{b.get('분류', '추천')}</span>
                                <span class='book-title'>{b.get('도서', '-')}</span>
                                <span style='font-size:12px; color:#666;'>({b.get('저자','')})</span>
                            </div>
                            <div class='book-reason'>{b.get('추천 이유', '-')}</div>
                        </div>
                    """
            
            st.markdown(f"""
                <div class='box-panel bg-gray'>
                    <span class='box-head' style='color:#333;'>📚 추천 도서</span>
                    {books_html}
                </div>
            """, unsafe_allow_html=True)

        # 6. 추천 학과
        st.markdown("<div class='rpt-section-title'>5. 역량 기반 추천 학과</div>", unsafe_allow_html=True)
        maj_cols = st.columns(3)
        for i, m in enumerate(majors[:3]):
            with maj_cols[i]:
                if isinstance(m, dict):
                    st.markdown(f"""
                        <div class='major-card'>
                            <div class='major-badge'>TOP {i+1}</div>
                            <div style='font-weight:800; font-size:16px; margin:10px 0; color:#1e293b;'>{m.get('학과','-')}</div>
                            <div style='font-size:12px; color:#64748b; line-height:1.4;'>{m.get('근거','-')}</div>
                        </div>
                    """, unsafe_allow_html=True)

        # PDF 저장 버튼
        if pdf_bytes:
            st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
            st.download_button(
                "📥 보고서 PDF 저장", 
                data=pdf_bytes, 
                file_name=f"{sname}_분석보고서.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )
            
        st.markdown("</div>", unsafe_allow_html=True)

    _show()
