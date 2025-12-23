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
        
        /* 1. 보고서 컨테이너 */
        .rpt-container {
            max-width: 900px; margin: 0 auto;
            font-family: 'Noto Sans KR', sans-serif;
            background-color: #ffffff; padding: 50px;
            border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }

        /* 2. 헤더 (중앙 정렬 수정) */
        .rpt-title-box {
            text-align: center; margin-bottom: 20px;
            border-bottom: 3px solid #1e293b; padding-bottom: 15px;
        }
        .rpt-title { font-size: 36px; font-weight: 900; color: #1e293b; letter-spacing: -1px; margin: 0; }
        .rpt-sub-title { font-size: 16px; color: #64748b; margin-top: 5px; font-weight: 500; }
        .rpt-meta-info { text-align: right; font-size: 15px; font-weight: 700; color: #334155; margin-top: 10px; }

        /* 3. 섹션 타이틀 */
        .rpt-section-title {
            font-size: 22px; font-weight: 800; color: #0f172a;
            margin-top: 40px; margin-bottom: 15px;
            display: flex; align-items: center; gap: 8px;
        }
        .rpt-section-bar { width: 5px; height: 20px; background: #3b82f6; }

        /* 4. 종합 평가 박스 */
        .rpt-summary-box {
            background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 24px; font-size: 16px; line-height: 1.8; text-align: justify; color: #334155;
        }
        .highlight-marker { background: linear-gradient(to top, #fef08a 40%, transparent 40%); font-weight: 800; padding: 0 2px; }

        /* 5. 강점/보완 박스 (그래프 하단) */
        .box-color { border-radius: 12px; padding: 20px; height: 100%; }
        .box-green { background: #f0fdf4; border: 1px solid #bbf7d0; }
        .box-red { background: #fef2f2; border: 1px solid #fecaca; }
        .box-blue { background: #eff6ff; border: 1px solid #dbeafe; }
        .box-head { font-weight: 800; font-size: 16px; margin-bottom: 10px; display: block; }

        /* 6. 상세 분석 카드 */
        .detail-card {
            background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin-bottom: 15px;
        }
        .evidence-box {
            background-color: #f1f5f9; border-radius: 8px; padding: 12px; margin-top: 10px;
            border-left: 3px solid #94a3b8; font-size: 13.5px; color: #475569;
        }

        /* 7. 추천 리스트 스타일 */
        .rec-item { margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px dashed #e2e8f0; }
        .rec-item:last-child { border-bottom: none; }
        .rec-title { font-weight: 800; font-size: 15px; color: #1e293b; }
        .rec-desc { font-size: 13px; color: #64748b; margin-top: 4px; line-height: 1.4; }

        @media print {
            .stDownloadButton { display: none !important; }
            .rpt-container { width: 100%; max-width: 100%; padding: 0; box-shadow: none; border: none; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def _html_list_styled(items: list[str]) -> str:
    if not items: return "-"
    li = "".join([f"<li style='margin-bottom:4px;'>{str(x)}</li>" for x in items])
    return f"<ul style='padding-left:18px; margin:0; font-size:14px; line-height:1.6;'>{li}</ul>"

def _highlight_text(text: str, keywords: list[str]) -> str:
    text = str(text).replace("\n", "<br>")
    for kw in keywords:
        if len(kw) > 1:
            text = text.replace(kw, f"<span class='highlight-marker'>{kw}</span>")
    return text

def render_report_modal(st, report: Dict[str, Any], sid: str, sname: str, radar_png: Optional[BytesIO] = None, pdf_bytes: Optional[bytes] = None):
    @st.dialog(f"📑 {sname} 학생 종합 보고서", width="large")
    def _show():
        inject_report_css(st)
        
        # 데이터 준비
        overall = report.get("종합 평가", "")
        detail = report.get("3대 평가 항목별 상세 분석", {})
        strengths = report.get("핵심 강점", [])
        weaknesses = report.get("보완 추천 영역", [])
        growth = report.get("맞춤형 성장 제안", {}) or {}
        strat = growth.get("생활기록부 중점 보완 전략", "")
        events = growth.get("추천 학교 행사", [])
        books = report.get("추천 도서", [])
        majors = report.get("역량 기반 추천 학과", [])

        # 하이라이트 키워드
        keywords = []
        if majors and isinstance(majors[0], dict): keywords.append(majors[0].get("학과", ""))
        keywords += [s.split()[0] for s in strengths[:3] if s]

        st.markdown("<div class='rpt-container'>", unsafe_allow_html=True)

        # 1. 헤더 (중앙 정렬)
        st.markdown(f"""
            <div class='rpt-title-box'>
                <h1 class='rpt-title'>종합 분석 보고서</h1>
                <div class='rpt-sub-title'>SH-Insight Student Report</div>
            </div>
            <div class='rpt-meta-info'>
                학번: {sid} &nbsp;|&nbsp; 성명: {sname}
            </div>
        """, unsafe_allow_html=True)

        # 2. 종합 평가
        st.markdown(f"""
            <div class='rpt-section-title'><div class='rpt-section-bar'></div>종합 평가</div>
            <div class='rpt-summary-box'>
                {_highlight_text(overall, keywords)}
            </div>
        """, unsafe_allow_html=True)

        # 3. 역량 시각화 (그래프)
        st.markdown("<div class='rpt-section-title'><div class='rpt-section-bar'></div>역량 분석 및 강점·보완</div>", unsafe_allow_html=True)
        
        # 3-1. 그래프 중앙 배치
        if radar_png:
            col_g1, col_g2, col_g3 = st.columns([1, 2, 1])
            with col_g2:
                st.image(radar_png, use_container_width=True)
        
        # 3-2. 그래프 바로 아래 강점/보완 (2단)
        c_str, c_weak = st.columns(2)
        with c_str:
            st.markdown(f"""
                <div class='box-color box-green'>
                    <span class='box-head' style='color:#15803d;'>✅ 핵심 강점</span>
                    {_html_list_styled(strengths)}
                </div>
            """, unsafe_allow_html=True)
        with c_weak:
            st.markdown(f"""
                <div class='box-color box-red'>
                    <span class='box-head' style='color:#b91c1c;'>⚠️ 보완 추천 영역</span>
                    {_html_list_styled(weaknesses)}
                </div>
            """, unsafe_allow_html=True)

        # 4. 상세 분석 (근거 포함)
        st.markdown("<div class='rpt-section-title'><div class='rpt-section-bar'></div>평가 항목별 상세 분석</div>", unsafe_allow_html=True)
        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            v = detail.get(key, {})
            st.markdown(f"""
                <div class='detail-card'>
                    <div style='display:flex; justify-content:space-between; margin-bottom:8px;'>
                        <span style='font-weight:800; font-size:17px;'>{key}</span>
                        <span style='font-weight:700; color:#3b82f6;'>{v.get('점수',0)}점</span>
                    </div>
                    <div style='font-size:14px; margin-bottom:8px;'>{v.get('분석', '-')}</div>
                    <div class='evidence-box'>
                        <b>📢 근거:</b> {_html_list_styled(v.get('평가 근거 문장', [])[:3])}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # 5. 맞춤형 성장 제안 (요청하신 2단 레이아웃)
        st.markdown("<div class='rpt-section-title'><div class='rpt-section-bar'></div>맞춤형 성장 제안</div>", unsafe_allow_html=True)
        
        col_L, col_R = st.columns(2)
        
        # 왼쪽: 전략 + 학교 행사
        with col_L:
            # 전략
            st.markdown(f"""
                <div class='box-color box-blue' style='height:auto; margin-bottom:15px;'>
                    <span class='box-head' style='color:#1d4ed8;'>📌 생활기록부 중점 보완 전략</span>
                    <div style='font-size:14px; line-height:1.6;'>{strat or '-'}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # 행사
            st.markdown(f"""
                <div class='box-color box-blue' style='height:auto;'>
                    <span class='box-head' style='color:#1d4ed8;'>🏫 추천 학교 행사</span>
                    {_html_list_styled(events[:5])}
                </div>
            """, unsafe_allow_html=True)

        # 오른쪽: 추천 도서
        with col_R:
            st.markdown("<div class='box-color' style='background:#f8fafc; border:1px solid #e2e8f0;'>", unsafe_allow_html=True)
            st.markdown("<span class='box-head'>📚 추천 도서</span>", unsafe_allow_html=True)
            for b in books[:4]:
                if isinstance(b, dict):
                    st.markdown(f"""
                        <div class='rec-item'>
                            <div class='rec-title'>{b.get('도서','-')}</div>
                            <div class='rec-desc'>{b.get('추천 이유','-')}</div>
                        </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # 6. 추천 학과 (마무리)
        st.markdown("<div class='rpt-section-title'><div class='rpt-section-bar'></div>추천 학과</div>", unsafe_allow_html=True)
        maj_cols = st.columns(3)
        for i, m in enumerate(majors[:3]):
            with maj_cols[i]:
                if isinstance(m, dict):
                     st.markdown(f"""
                        <div style='background:#fff; border:1px solid #ddd; padding:15px; border-radius:10px; text-align:center;'>
                            <div style='font-weight:800; color:#333; margin-bottom:5px;'>{m.get('학과','-')}</div>
                            <div style='font-size:12px; color:#666;'>{m.get('근거','-')}</div>
                        </div>
                     """, unsafe_allow_html=True)

        if pdf_bytes:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.download_button("📥 보고서 PDF 저장", data=pdf_bytes, file_name=f"{sname}_보고서.pdf", mime="application/pdf", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    _show()
