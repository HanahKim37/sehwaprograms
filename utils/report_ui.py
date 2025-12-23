from __future__ import annotations
import re
import base64
from io import BytesIO
from typing import Any, Dict, Optional

def inject_report_css(st=None):
    if st is None:
        import streamlit as st

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700;900&display=swap');
        
        /* 1. 보고서 전체 틀 (A4 용지 느낌) */
        .report-wrapper {
            background-color: white;
            padding: 40px;
            border-radius: 0;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            font-family: 'Noto Sans KR', sans-serif;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
        }

        /* 2. 헤더 (중앙 정렬) */
        .rpt-header {
            text-align: center;
            border-bottom: 3px solid #000;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .rpt-title {
            font-size: 36px; font-weight: 900; color: #000; margin: 0; letter-spacing: -1px;
        }
        .rpt-sub {
            font-size: 14px; color: #555; margin-top: 5px;
        }
        .rpt-info {
            text-align: right; font-weight: 700; font-size: 15px; margin-top: 15px; color: #444;
        }

        /* 3. 섹션 공통 */
        .sec-title {
            font-size: 20px; font-weight: 800; color: #111;
            margin-top: 40px; margin-bottom: 10px;
            display: flex; align-items: center; border-left: 5px solid #2563eb; padding-left: 10px;
        }

        /* 4. 종합 평가 (형광펜 효과) */
        .summary-box {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 20px;
            border-radius: 8px;
            line-height: 1.8;
            font-size: 15px;
            text-align: justify;
        }
        .highlight {
            background: linear-gradient(to top, #fff176 40%, transparent 40%);
            font-weight: 800;
        }

        /* 5. 그래프 영역 */
        .graph-container {
            display: flex; justify-content: center; margin: 20px 0;
        }
        .graph-img {
            width: 350px !important; /* 그래프 크기 강제 축소 */
            height: auto;
        }

        /* 6. 강점/보완 (2단 그리드) */
        .grid-2 {
            display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
        }
        .box-panel {
            padding: 20px; border-radius: 12px; height: 100%;
        }
        .bg-green { background: #f0fdf4; border: 1px solid #bbf7d0; }
        .bg-red { background: #fef2f2; border: 1px solid #fecaca; }
        .panel-head { font-weight: 800; font-size: 16px; display: block; margin-bottom: 10px; }
        .panel-list li { margin-bottom: 5px; font-size: 14px; }

        /* 7. 상세 분석 (별점 + 근거) */
        .detail-item {
            border: 1px solid #e5e7eb; border-radius: 10px; padding: 20px; margin-bottom: 15px;
        }
        .detail-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .star-on { color: #f59e0b; font-size: 20px; }
        .star-off { color: #e2e8f0; font-size: 20px; }
        .evidence {
            background: #f1f5f9; padding: 12px; border-radius: 6px; margin-top: 10px;
            font-size: 13px; color: #475569; border-left: 3px solid #64748b;
        }

        /* 8. 성장 제안 (좌:전략/행사, 우:도서) */
        .growth-container {
            display: flex; gap: 20px;
        }
        .col-left { flex: 1; display: flex; flex-direction: column; gap: 15px; }
        .col-right { flex: 1; }
        
        .blue-box { background: #eff6ff; border: 1px solid #dbeafe; padding: 15px; border-radius: 10px; }
        
        /* 추천도서 디자인 */
        .book-wrap { background: #fafafa; border: 1px solid #eee; padding: 20px; border-radius: 10px; height: 100%; }
        .book-card {
            background: white; border: 1px solid #ddd; padding: 12px; border-radius: 8px; margin-bottom: 10px;
        }
        .book-tag {
            background: #2563eb; color: white; font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: bold; vertical-align: middle; margin-right: 5px;
        }
        .book-title { font-weight: 800; font-size: 14px; color: #222; }
        .book-auth { font-size: 12px; color: #666; }
        .book-why { font-size: 12px; color: #555; margin-top: 5px; line-height: 1.4; border-top: 1px dashed #eee; padding-top: 5px; }

        /* 9. 추천학과 카드 */
        .major-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; }
        .major-box {
            background: white; border: 2px solid #e5e7eb; border-radius: 12px; padding: 15px; text-align: center;
        }
        .major-rank {
            background: #111; color: #fff; font-size: 11px; padding: 3px 8px; border-radius: 10px; display: inline-block; margin-bottom: 5px; font-weight: bold;
        }

        /* 인쇄 설정 */
        @media print {
            .stButton, .stDownloadButton { display: none !important; }
            .report-wrapper { box-shadow: none; border: none; padding: 0; margin: 0; width: 100%; max-width: 100%; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def _get_star_html(score):
    score = int(score)
    fill = "★" * (score // 2)
    empty = "☆" * (5 - (score // 2))
    return f"<span class='star-on'>{fill}</span><span class='star-off'>{empty}</span>"

def _list_to_html(items):
    if not items: return "-"
    return "".join([f"<li>{x}</li>" for x in items])

def _highlight(text, keywords):
    text = str(text).replace("\n", "<br>")
    for k in keywords:
        if len(k) > 1:
            text = text.replace(k, f"<span class='highlight'>{k}</span>")
    return text

def _img_to_base64(img_bytes):
    if img_bytes is None: return ""
    return base64.b64encode(img_bytes.getvalue()).decode()

def render_report_modal(st, report: Dict[str, Any], sid: str, sname: str, radar_png: Optional[BytesIO] = None, pdf_bytes: Optional[bytes] = None):
    @st.dialog(f"분석 결과 확인", width="large")
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

        # 이미지 base64 변환 (HTML 안에 직접 넣기 위해)
        img_b64 = _img_to_base64(radar_png)
        img_tag = f"<img src='data:image/png;base64,{img_b64}' class='graph-img'>" if img_b64 else "<div style='text-align:center; color:#ccc;'>그래프 없음</div>"

        # 하이라이트 키워드
        keywords = []
        if majors and isinstance(majors[0], dict): keywords.append(majors[0].get("학과", ""))
        keywords += [s.split()[0] for s in strengths[:3] if s]

        # --------------------------------------------------------------------------------
        # [HTML 생성 시작] - Streamlit 레이아웃을 쓰지 않고 통 HTML로 만듭니다.
        # --------------------------------------------------------------------------------
        
        html_content = f"""
        <div class="report-wrapper">
            <div class="rpt-header">
                <h1 class="rpt-title">종합 분석 보고서</h1>
                <div class="rpt-sub">AI Student Record Analysis Report</div>
                <div class="rpt-info">학번: {sid} &nbsp;|&nbsp; 성명: {sname}</div>
            </div>

            <div class="sec-title">1. 종합 평가</div>
            <div class="summary-box">
                {_highlight(overall, keywords)}
            </div>

            <div class="sec-title">2. 역량 분석 및 전략</div>
            
            <div class="graph-container">
                {img_tag}
            </div>

            <div class="grid-2">
                <div class="box-panel bg-green">
                    <span class="panel-head" style="color:#15803d;">✅ 핵심 강점</span>
                    <ul class="panel-list">{_list_to_html(strengths)}</ul>
                </div>
                <div class="box-panel bg-red">
                    <span class="panel-head" style="color:#b91c1c;">⚠️ 보완 추천 영역</span>
                    <ul class="panel-list">{_list_to_html(weaknesses)}</ul>
                </div>
            </div>

            <div class="sec-title">3. 평가 항목별 상세 분석</div>
        """

        # 상세 분석 반복문
        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            v = detail.get(key, {})
            score = v.get('점수', 0)
            html_content += f"""
            <div class="detail-item">
                <div class="detail-head">
                    <span style="font-weight:800; font-size:18px;">{key}</span>
                    <div>
                        {_get_star_html(score)}
                        <span style="font-weight:bold; margin-left:5px;">({score}/10)</span>
                    </div>
                </div>
                <div style="font-size:14px; margin-bottom:5px;">{v.get('분석', '-')}</div>
                <div class="evidence">
                    <b>📢 평가 근거 문장</b><br>
                    <ul>{_list_to_html(v.get('평가 근거 문장', [])[:3])}</ul>
                </div>
            </div>
            """

        # 성장 제안 (좌: 전략/행사, 우: 도서)
        book_items = ""
        for b in books[:3]:
            if isinstance(b, dict):
                book_items += f"""
                <div class="book-card">
                    <div>
                        <span class="book-tag">{b.get('분류', '추천')}</span>
                        <span class="book-title">{b.get('도서', '-')}</span>
                        <span class="book-auth">({b.get('저자', '')})</span>
                    </div>
                    <div class="book-why">{b.get('추천 이유', '-')}</div>
                </div>
                """

        html_content += f"""
            <div class="sec-title">4. 맞춤형 성장 제안</div>
            <div class="growth-container">
                <div class="col-left">
                    <div class="blue-box">
                        <span class="panel-head" style="color:#1d4ed8;">📌 생활기록부 중점 전략</span>
                        <div style="font-size:14px;">{strat or '-'}</div>
                    </div>
                    <div class="blue-box">
                        <span class="panel-head" style="color:#1d4ed8;">🏫 추천 학교 행사</span>
                        <ul class="panel-list">{_list_to_html(events[:4])}</ul>
                    </div>
                </div>
                <div class="col-right">
                    <div class="book-wrap">
                        <span class="panel-head" style="color:#333;">📚 추천 도서</span>
                        {book_items}
                    </div>
                </div>
            </div>
        """

        # 추천 학과
        html_content += f"""
            <div class="sec-title">5. 역량 기반 추천 학과</div>
            <div class="major-grid">
        """
        for i, m in enumerate(majors[:3]):
            if isinstance(m, dict):
                html_content += f"""
                <div class="major-box">
                    <div class="major-rank">TOP {i+1}</div>
                    <div style="font-weight:800; font-size:16px; margin:5px 0;">{m.get('학과','-')}</div>
                    <div style="font-size:12px; color:#666; line-height:1.4;">{m.get('근거','-')}</div>
                </div>
                """
        html_content += "</div></div>" # End grid & wrapper

        # --------------------------------------------------------------------------------
        # [HTML 렌더링 실행]
        # --------------------------------------------------------------------------------
        st.markdown(html_content, unsafe_allow_html=True)

        # PDF 다운로드 버튼 (화면 최하단)
        if pdf_bytes:
            st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
            col_d1, col_d2, col_d3 = st.columns([1,2,1])
            with col_d2:
                st.download_button(
                    "📄 PDF 파일로 저장하기", 
                    data=pdf_bytes, 
                    file_name=f"{sname}_분석보고서.pdf", 
                    mime="application/pdf", 
                    use_container_width=True
                )

    _show()
