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
        
        /* 1. 보고서 전체 컨테이너 (여백 문제 해결) */
        .rpt-container {
            max-width: 900px; margin: 0 auto;
            font-family: 'Noto Sans KR', sans-serif;
            background-color: #ffffff; padding: 50px;
            border: 1px solid #e0e0e0; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin-top: -20px; /* 상단 불필요 여백 제거 */
        }

        /* 2. 헤더 타이틀 */
        .rpt-header {
            text-align: center; border-bottom: 2px solid #1e293b; 
            padding-bottom: 20px; margin-bottom: 30px;
        }
        .rpt-title { font-size: 32px; font-weight: 900; color: #1e293b; margin: 0; letter-spacing: -1px; }
        .rpt-meta { text-align: right; font-size: 14px; font-weight: 700; color: #64748b; margin-top: 10px; }

        /* 3. 섹션 공통 */
        .rpt-sec-title {
            font-size: 20px; font-weight: 800; color: #0f172a;
            margin-top: 40px; margin-bottom: 15px;
            display: flex; align-items: center; gap: 8px;
        }
        .rpt-sec-bar { width: 5px; height: 18px; background: #3b82f6; border-radius: 2px; }

        /* 4. 하이라이트 (형광펜 효과 개선) */
        .highlight-box {
            background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 20px; font-size: 15px; line-height: 1.8; text-align: justify; color: #334155;
        }
        .highlight-marker {
            background-color: #fef3c7; /* 부드러운 노란색 배경 */
            color: #92400e; font-weight: 800;
            padding: 2px 4px; border-radius: 4px;
            box-decoration-break: clone;
        }

        /* 5. 별점 스타일 (모양 개선) */
        .star-gold { color: #f59e0b; font-size: 18px; letter-spacing: 1px; }
        .star-gray { color: #e2e8f0; font-size: 18px; letter-spacing: 1px; }

        /* 6. 상세 분석 카드 */
        .detail-card {
            background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; 
            padding: 20px; margin-bottom: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        }
        .evidence-box {
            background-color: #f1f5f9; border-radius: 8px; padding: 15px; margin-top: 12px;
            border-left: 4px solid #94a3b8; font-size: 13.5px; color: #475569;
        }

        /* 7. 강점/보완 박스 */
        .box-wrapper { height: 100%; border-radius: 12px; padding: 20px; }
        .bg-green { background: #f0fdf4; border: 1px solid #bbf7d0; }
        .bg-red { background: #fef2f2; border: 1px solid #fecaca; }
        .bg-blue { background: #eff6ff; border: 1px solid #dbeafe; }
        .box-head { font-weight: 800; font-size: 16px; margin-bottom: 12px; display: block; }
        .box-list li { margin-bottom: 6px; font-size: 14px; color: #334155; }

        /* 8. 추천 도서 (디자인 전면 수정) */
        .book-container { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; height: 100%; }
        .book-item { 
            background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; 
            padding: 12px; margin-bottom: 10px; 
        }
        .book-tag { 
            display: inline-block; font-size: 11px; font-weight: 800; 
            color: #fff; background: #3b82f6; padding: 2px 6px; border-radius: 4px; margin-right: 6px;
        }
        .book-title { font-weight: 800; color: #1e293b; font-size: 14px; }
        .book-author { font-size: 12px; color: #64748b; margin-left: 4px; }
        .book-reason { font-size: 13px; color: #475569; margin-top: 6px; line-height: 1.4; }

        /* 9. 추천 학과 (뱃지 디자인) */
        .major-card {
            background: #fff; border: 1px solid #cbd5e1; border-radius: 12px;
            padding: 15px; text-align: center; position: relative; margin-top: 10px;
        }
        .major-badge {
            position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
            background: #0f172a; color: #fff; font-size: 11px; font-weight: 800;
            padding: 4px 10px; border-radius: 20px;
        }
        .major-name { font-weight: 800; font-size: 16px; color: #1e293b; margin-top: 8px; margin-bottom: 6px; }
        .major-desc { font-size: 12px; color: #64748b; line-height: 1.4; }

        @media print {
            .stDownloadButton { display: none !important; }
            .rpt-container { padding: 0; border: none; box-shadow: none; margin: 0; width: 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def _stars_html(score: int) -> str:
    """점수를 받아 예쁜 별 아이콘 HTML 반환"""
    full = "★" * (score // 2)
    empty = "☆" * (5 - (score // 2))
    return f"<span class='star-gold'>{full}</span><span class='star-gray'>{empty}</span>"

def _html_list_styled(items: list[str]) -> str:
    if not items: return "-"
    li = "".join([f"<li>{str(x)}</li>" for x in items])
    return f"<ul class='box-list' style='padding-left:18px; margin:0;'>{li}</ul>"

def _highlight_text(text: str, keywords: list[str]) -> str:
    text = str(text).replace("\n", "<br>")
    for kw in keywords:
        if len(kw) > 1:
            # 부드러운 형광펜 효과 적용
            text = text.replace(kw, f"<span class='highlight-marker'>{kw}</span>")
    return text

def render_report_modal(st, report: Dict[str, Any], sid: str, sname: str, radar_png: Optional[BytesIO] = None, pdf_bytes: Optional[bytes] = None):
    @st.dialog(f"📊 {sname} 분석 보고서", width="large")
    def _show():
        inject_report_css(st)
        
        # 데이터 파싱
        overall = report.get("종합 평가", "")
        detail = report.get("3대 평가 항목별 상세 분석", {})
        strengths = report.get("핵심 강점", [])
        weaknesses = report.get("보완 추천 영역", [])
        growth = report.get("맞춤형 성장 제안", {}) or {}
        strat = growth.get("생활기록부 중점 보완 전략", "")
        events = growth.get("추천 학교 행사", [])
        books = report.get("추천 도서", [])
        majors = report.get("역량 기반 추천 학과", [])

        # 하이라이트 키워드 선정
        keywords = []
        if majors and isinstance(majors[0], dict): keywords.append(majors[0].get("학과", ""))
        keywords += [s.split()[0] for s in strengths[:3] if s]

        # [HTML 컨테이너 시작]
        st.markdown("<div class='rpt-container'>", unsafe_allow_html=True)

        # 1. 헤더 (박스 없이 깔끔하게)
        st.markdown(f"""
            <div class='rpt-header'>
                <p class='rpt-title'>종합 분석 보고서</p>
                <div class='rpt-meta'>학번: {sid} ｜ 성명: {sname}</div>
            </div>
        """, unsafe_allow_html=True)

        # 2. 종합 평가 (형광펜 하이라이트 적용)
        st.markdown("<div class='rpt-sec-title'><div class='rpt-sec-bar'></div>종합 평가</div>", unsafe_allow_html=True)
        st.markdown(f"""
            <div class='highlight-box'>
                {_highlight_text(overall, keywords)}
            </div>
        """, unsafe_allow_html=True)

        # 3. 역량 시각화 (그래프 크기 축소 + 강점/보완 2단 배치)
        st.markdown("<div class='rpt-sec-title'><div class='rpt-sec-bar'></div>역량 분석 시각화</div>", unsafe_allow_html=True)
        
        # 그래프 크기 조절: 가운데 컬럼을 작게(0.8) 설정
        c1, c2, c3 = st.columns([1, 0.8, 1])
        with c2:
            if radar_png:
                st.image(radar_png, use_container_width=True)
        
        # 그래프 바로 아래 강점/보완 배치
        col_str, col_weak = st.columns(2)
        with col_str:
            st.markdown(f"""
                <div class='box-wrapper bg-green'>
                    <span class='box-head' style='color:#15803d;'>✅ 핵심 강점</span>
                    {_html_list_styled(strengths)}
                </div>
            """, unsafe_allow_html=True)
        with col_weak:
            st.markdown(f"""
                <div class='box-wrapper bg-red'>
                    <span class='box-head' style='color:#b91c1c;'>⚠️ 보완 추천 영역</span>
                    {_html_list_styled(weaknesses)}
                </div>
            """, unsafe_allow_html=True)

        # 4. 상세 분석 (별점 아이콘 적용 + 근거 포함)
        st.markdown("<div class='rpt-sec-title'><div class='rpt-sec-bar'></div>평가 항목별 상세 분석</div>", unsafe_allow_html=True)
        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            v = detail.get(key, {})
            score = v.get("점수", 0)
            
            st.markdown(f"""
                <div class='detail-card'>
                    <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                        <span style='font-weight:800; font-size:17px; color:#1e293b;'>{key}</span>
                        <div>
                            {_stars_html(score)} 
                            <span style='font-weight:800; color:#334155; margin-left:5px;'>({score}/10)</span>
                        </div>
                    </div>
                    <div style='font-size:14px; color:#334155;'>{v.get('분석', '-')}</div>
                    <div class='evidence-box'>
                        <div style='font-weight:800; margin-bottom:5px;'>📢 평가 근거 문장</div>
                        {_html_list_styled(v.get('평가 근거 문장', [])[:3])}
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # 5. 맞춤형 성장 제안 (좌:전략/행사, 우:도서)
        st.markdown("<div class='rpt-sec-title'><div class='rpt-sec-bar'></div>맞춤형 성장 제안</div>", unsafe_allow_html=True)
        
        grow_L, grow_R = st.columns(2)
        
        # [좌측] 전략 + 행사
        with grow_L:
            # HTML을 한 덩어리로 묶어서 출력
            st.markdown(f"""
                <div class='box-wrapper bg-blue' style='margin-bottom:15px;'>
                    <span class='box-head' style='color:#1d4ed8;'>📌 생활기록부 중점 전략</span>
                    <div style='font-size:14px; line-height:1.6;'>{strat or '-'}</div>
                </div>
                <div class='box-wrapper bg-blue'>
                    <span class='box-head' style='color:#1d4ed8;'>🏫 추천 학교 행사</span>
                    {_html_list_styled(events[:4])}
                </div>
            """, unsafe_allow_html=True)

        # [우측] 추천 도서 (박스 안에 내용 완벽 포함)
        with grow_R:
            # 도서 목록 HTML 생성
            books_html = ""
            for b in books[:3]:
                if isinstance(b, dict):
                    # 분류(이유)에 따른 태그 생성
                    cat = b.get("분류", "추천")
                    # HTML 조립
                    books_html += f"""
                        <div class='book-item'>
                            <div>
                                <span class='book-tag'>{cat}</span>
                                <span class='book-title'>{b.get('도서','-')}</span>
                                <span class='book-author'>({b.get('저자','-')})</span>
                            </div>
                            <div class='book-reason'>{b.get('추천 이유','-')}</div>
                        </div>
                    """
            
            # 최종 도서 박스 출력
            st.markdown(f"""
                <div class='book-container'>
                    <span class='box-head' style='color:#334155;'>📚 추천 도서</span>
                    {books_html}
                </div>
            """, unsafe_allow_html=True)

        # 6. 추천 학과 (카드 디자인 + Badge)
        st.markdown("<div class='rpt-sec-title'><div class='rpt-sec-bar'></div>역량 기반 추천 학과</div>", unsafe_allow_html=True)
        
        maj_cols = st.columns(3)
        for i, m in enumerate(majors[:3]):
            with maj_cols[i]:
                if isinstance(m, dict):
                    st.markdown(f"""
                        <div class='major-card'>
                            <div class='major-badge'>TOP {i+1}</div>
                            <div class='major-name'>{m.get('학과','-')}</div>
                            <div class='major-desc'>{m.get('근거','-')}</div>
                        </div>
                    """, unsafe_allow_html=True)

        # PDF 다운로드
        if pdf_bytes:
            st.markdown("<br><hr>", unsafe_allow_html=True)
            st.download_button("📥 리포트 PDF 저장", data=pdf_bytes, file_name=f"{sname}_Report.pdf", mime="application/pdf", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True) # 컨테이너 종료

    _show()
