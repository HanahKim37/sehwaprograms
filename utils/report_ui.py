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
        
        /* 1. 전체 컨테이너: A4 용지 느낌의 긴 호흡 */
        .rpt-container {
            max-width: 900px;
            margin: 0 auto;
            font-family: 'Noto Sans KR', sans-serif;
            background-color: #ffffff;
            padding: 40px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }

        /* 2. 헤더 영역 */
        .rpt-header {
            border-bottom: 2px solid #222;
            padding-bottom: 10px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }
        .rpt-title {
            font-size: 32px; font-weight: 900; color: #111; letter-spacing: -1px;
        }
        .rpt-meta {
            font-size: 16px; font-weight: 700; color: #555; text-align: right;
        }

        /* 3. 섹션 공통 */
        .rpt-section-title {
            font-size: 22px; font-weight: 800; color: #1e293b;
            margin-top: 50px; margin-bottom: 15px;
            border-left: 6px solid #3b82f6; padding-left: 12px;
            display: flex; align-items: center;
        }

        /* 4. 종합 평가 (형광펜 효과) */
        .rpt-summary-box {
            background-color: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 25px;
            font-size: 16px;
            line-height: 1.8;
            color: #333;
            text-align: justify;
        }
        .highlight-marker {
            background: linear-gradient(to top, #fef08a 40%, transparent 40%);
            font-weight: 800;
            padding: 0 2px;
        }

        /* 5. 상세 분석 (근거 문장 포함) */
        .detail-card {
            background: #fff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }
        .detail-header {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 15px; border-bottom: 1px dashed #ddd; padding-bottom: 10px;
        }
        .detail-name { font-size: 18px; font-weight: 800; color: #333; }
        .detail-score { font-size: 16px; font-weight: 700; color: #3b82f6; }
        
        .evidence-box {
            background-color: #f1f5f9;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #94a3b8;
        }
        .evidence-title { font-size: 13px; font-weight: 800; color: #64748b; margin-bottom: 5px; }
        .evidence-text { font-size: 14px; color: #475569; line-height: 1.6; }

        /* 6. 강점/보완 박스 */
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .box-color { padding: 20px; border-radius: 12px; height: 100%; }
        .box-green { background: #f0fdf4; border: 1px solid #bbf7d0; }
        .box-red { background: #fef2f2; border: 1px solid #fecaca; }
        .box-head { font-weight: 800; font-size: 16px; margin-bottom: 10px; display: block; }
        
        /* 7. 추천 (이유 포함) */
        .rec-item {
            margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eee;
        }
        .rec-title { font-size: 16px; font-weight: 800; color: #111; }
        .rec-reason { font-size: 14px; color: #555; margin-top: 5px; line-height: 1.5; }

        @media print {
            .stDownloadButton { display: none !important; }
            .rpt-container { box-shadow: none; border: none; width: 100%; max-width: 100%; padding: 0; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def _html_list_styled(items: list[str]) -> str:
    if not items: return "-"
    li = "".join([f"<li style='margin-bottom:5px;'>{str(x)}</li>" for x in items])
    return f"<ul style='padding-left:20px; margin:0;'>{li}</ul>"

def _highlight_text(text: str, keywords: list[str]) -> str:
    """단순 텍스트에서 키워드를 찾아 형광펜 효과 적용"""
    text = str(text).replace("\n", "<br>")
    for kw in keywords:
        if len(kw) > 1:
            text = text.replace(kw, f"<span class='highlight-marker'>{kw}</span>")
    return text

def render_report_modal(st, report: Dict[str, Any], sid: str, sname: str, radar_png: Optional[BytesIO] = None, pdf_bytes: Optional[bytes] = None):
    @st.dialog(f"📑 {sname} 학생 심층 분석 리포트", width="large")
    def _show():
        inject_report_css(st)
        
        # 데이터 추출
        overall = report.get("종합 평가", "")
        detail = report.get("3대 평가 항목별 상세 분석", {})
        strengths = report.get("핵심 강점", [])
        weaknesses = report.get("보완 추천 영역", [])
        books = report.get("추천 도서", [])
        majors = report.get("역량 기반 추천 학과", [])
        
        # 키워드 추출 (간단 로직: 전공명 + 강점 키워드)
        keywords = []
        if majors and isinstance(majors[0], dict):
            keywords.append(majors[0].get("학과", ""))
        keywords += [s.split()[0] for s in strengths[:3] if s] # 강점의 첫 어절들 하이라이트

        # [컨테이너 시작]
        st.markdown("<div class='rpt-container'>", unsafe_allow_html=True)

        # 1. 제목 및 학생 정보 (우측 정렬 요구사항 반영)
        st.markdown(f"""
            <div class='rpt-header'>
                <div class='rpt-title'>SH-Insight<br>종합 분석 보고서</div>
                <div class='rpt-meta'>
                    학번: {sid}<br>
                    성명: {sname}
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 2. 종합 평가 (굵게 하이라이트)
        st.markdown("<div class='rpt-section-title'>1. 종합 평가</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='rpt-summary-box'>
                {_highlight_text(overall, keywords)}
            </div>
        """, unsafe_allow_html=True)

        # 3. 역량 그래프 (중앙 배치)
        st.markdown("<div class='rpt-section-title'>2. 역량 시각화</div>", unsafe_allow_html=True)
        if radar_png:
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                st.image(radar_png, use_container_width=True)
        else:
            st.warning("그래프 데이터 없음")

        # 4. 3대 평가 상세 (평가 근거 문장 필수 포함)
        st.markdown("<div class='rpt-section-title'>3. 영역별 상세 분석 및 근거</div>", unsafe_allow_html=True)
        
        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            data = detail.get(key, {})
            score = data.get("점수", 0)
            analysis = data.get("분석", "-")
            evidence = data.get("평가 근거 문장", [])

            st.markdown(f"""
                <div class='detail-card'>
                    <div class='detail-header'>
                        <span class='detail-name'>{key}</span>
                        <span class='detail-score'>{'★'*(score//2)} {score}점</span>
                    </div>
                    <div style='margin-bottom:15px; font-weight:700; color:#333;'>
                        {analysis}
                    </div>
                    <div class='evidence-box'>
                        <div class='evidence-title'>📢 평가 근거 문장 (생기부 발췌)</div>
                        <div class='evidence-text'>
                            {_html_list_styled(evidence)}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # 5. 강점 및 보완 (반반 레이아웃)
        st.markdown("<div class='rpt-section-title'>4. 강점 및 보완점</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='grid-2'>
                <div class='box-color box-green'>
                    <span class='box-head' style='color:#15803d;'>✅ 핵심 강점</span>
                    <div style='font-size:14px; line-height:1.6;'>
                        {_html_list_styled(strengths)}
                    </div>
                </div>
                <div class='box-color box-red'>
                    <span class='box-head' style='color:#b91c1c;'>⚠️ 보완 필요</span>
                    <div style='font-size:14px; line-height:1.6;'>
                        {_html_list_styled(weaknesses)}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 6. 추천 도서 및 학과 (이유 포함)
        st.markdown("<div class='rpt-section-title'>5. 맞춤형 추천 (이유 포함)</div>", unsafe_allow_html=True)
        
        c_maj, c_book = st.columns(2)
        
        with c_maj:
            st.markdown("<h4 style='border-bottom:2px solid #333; padding-bottom:5px;'>🎓 추천 학과</h4>", unsafe_allow_html=True)
            for m in majors[:3]:
                if isinstance(m, dict):
                    st.markdown(f"""
                        <div class='rec-item'>
                            <div class='rec-title'>{m.get('학과','-')}</div>
                            <div class='rec-reason'>💡 {m.get('근거','-')}</div>
                        </div>
                    """, unsafe_allow_html=True)

        with c_book:
            st.markdown("<h4 style='border-bottom:2px solid #333; padding-bottom:5px;'>📚 추천 도서</h4>", unsafe_allow_html=True)
            for b in books[:3]:
                if isinstance(b, dict):
                    st.markdown(f"""
                        <div class='rec-item'>
                            <div class='rec-title'>{b.get('도서','-')} <small>({b.get('저자','')})</small></div>
                            <div class='rec-reason'>💡 {b.get('추천 이유','-')}</div>
                        </div>
                    """, unsafe_allow_html=True)

        # PDF 다운로드
        if pdf_bytes:
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.download_button("📄 PDF로 리포트 저장", data=pdf_bytes, file_name=f"{sname}_Report.pdf", mime="application/pdf", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    _show()
