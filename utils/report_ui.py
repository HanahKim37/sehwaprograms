from __future__ import annotations
import base64
import textwrap
from io import BytesIO
from typing import Any, Dict, Optional

def _img_to_base64(img_bytes):
    """이미지를 HTML에 넣기 위해 base64로 변환"""
    if img_bytes is None: return ""
    return base64.b64encode(img_bytes.getvalue()).decode()

def _get_star_html(score):
    """점수를 별 아이콘으로 변환"""
    try:
        score = int(score)
    except:
        score = 0
    
    # 꽉 찬 별(★)과 빈 별(☆) 생성
    fill = "★" * (score // 2)
    empty = "☆" * (5 - (score // 2))
    return f"<span style='color:#f59e0b; font-size:18px;'>{fill}</span><span style='color:#e2e8f0; font-size:18px;'>{empty}</span>"

def _list_to_html(items):
    """리스트를 HTML ul/li 태그로 변환"""
    if not items: return "<li style='margin-bottom:4px;'>-</li>"
    return "".join([f"<li style='margin-bottom:4px;'>{str(x)}</li>" for x in items])

def _highlight(text, keywords):
    """키워드 형광펜 효과"""
    text = str(text).replace("\n", "<br>")
    for k in keywords:
        if k and len(k) > 1:
            text = text.replace(k, f"<span style='background:linear-gradient(to top, #fef08a 40%, transparent 40%); font-weight:800; padding:0 2px;'>{k}</span>")
    return text

def inject_report_css(st=None):
    """
    메인 페이지에서 호출하는 CSS 주입 함수.
    이 함수가 없으면 ImportError가 발생하므로 필수입니다.
    """
    if st is None:
        import streamlit as st

    # 인쇄 시 불필요한 요소 숨김 및 폰트 설정
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700;900&display=swap');
        @media print {
            .stSidebar, .stButton, .stDownloadButton, header, footer { display: none !important; }
            .block-container { padding: 0 !important; }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def render_report_modal(st, report: Dict[str, Any], sid: str, sname: str, radar_png: Optional[BytesIO] = None, pdf_bytes: Optional[bytes] = None):
    """
    모달 창에 보고서를 렌더링합니다.
    HTML 들여쓰기 문제를 해결하여 코드가 아닌 디자인된 UI가 나오도록 수정했습니다.
    """
    @st.dialog(f"📊 {sname} 학생 분석 결과", width="large")
    def _show():
        
        # 1. 데이터 준비
        overall = report.get("종합 평가", "")
        detail = report.get("3대 평가 항목별 상세 분석", {}) or {}
        strengths = report.get("핵심 강점", [])
        weaknesses = report.get("보완 추천 영역", [])
        growth = report.get("맞춤형 성장 제안", {}) or {}
        strat = growth.get("생활기록부 중점 보완 전략", "")
        events = growth.get("추천 학교 행사", [])
        books = report.get("추천 도서", [])
        majors = report.get("역량 기반 추천 학과", [])

        # 이미지 처리
        img_b64 = _img_to_base64(radar_png)
        img_tag = f"<img src='data:image/png;base64,{img_b64}' style='width:300px; height:auto; margin:0 auto; display:block;'>" if img_b64 else "<div style='text-align:center; color:#ccc; padding:50px;'>그래프 데이터 없음</div>"

        # 하이라이트 키워드
        keywords = []
        if majors and isinstance(majors[0], dict): keywords.append(majors[0].get("학과", ""))
        keywords += [s.split()[0] for s in strengths[:3] if s]

        # --------------------------------------------------------------------------------
        # 2. HTML 생성 (들여쓰기 제거 - 중요!)
        # --------------------------------------------------------------------------------
        
        # 기본 스타일
        style_block = """
        <style>
            .rpt-container {
                font-family: 'Noto Sans KR', sans-serif;
                background-color: #ffffff;
                color: #333333;
                padding: 30px;
                border-radius: 10px;
                border: 1px solid #e5e7eb;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
            .rpt-header {
                text-align: center;
                border-bottom: 2px solid #111;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .rpt-title { font-size: 32px; font-weight: 900; color: #111; margin: 0; }
            .rpt-sub { font-size: 14px; color: #666; margin-top: 5px; }
            .rpt-meta { text-align: right; font-weight: 700; font-size: 14px; margin-top: 15px; color: #444; }
            .sec-title {
                font-size: 20px; font-weight: 800; color: #1e293b;
                margin-top: 40px; margin-bottom: 12px;
                display: flex; align-items: center; gap: 8px;
                border-left: 5px solid #2563eb;
                padding-left: 10px;
            }
            .summary-box {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 20px;
                font-size: 15px;
                line-height: 1.7;
                text-align: justify;
            }
            .grid-2 {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-top: 20px;
            }
            .box-panel { padding: 15px; border-radius: 10px; height: 100%; }
            .bg-green { background: #f0fdf4; border: 1px solid #bbf7d0; }
            .bg-red { background: #fef2f2; border: 1px solid #fecaca; }
            .bg-blue { background: #eff6ff; border: 1px solid #dbeafe; }
            .panel-head { display: block; font-weight: 800; font-size: 16px; margin-bottom: 10px; }
            .panel-list { padding-left: 20px; margin: 0; font-size: 14px; }
            .detail-card {
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                background: #fff;
            }
            .evidence-box {
                background: #f3f4f6;
                padding: 12px;
                border-radius: 6px;
                margin-top: 10px;
                font-size: 13px;
                color: #4b5563;
                border-left: 4px solid #9ca3af;
            }
            .book-container {
                background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 15px; height: 100%;
            }
            .book-item {
                background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin-bottom: 8px;
            }
            .book-tag {
                display: inline-block; font-size: 10px; font-weight: 800; color: #fff; background: #3b82f6;
                padding: 2px 5px; border-radius: 4px; margin-right: 5px; vertical-align: middle;
            }
            .major-grid {
                display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;
            }
            .major-item {
                background: #fff; border: 2px solid #e5e7eb; border-radius: 10px; padding: 15px; text-align: center;
            }
            .major-badge {
                display: inline-block; background: #111; color: #fff; font-size: 11px; font-weight: bold;
                padding: 3px 8px; border-radius: 10px; margin-bottom: 5px;
            }
            @media (max-width: 768px) {
                .grid-2, .major-grid { grid-template-columns: 1fr; }
            }
        </style>
        """

        # 상세 분석 HTML 조립
        details_html = ""
        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            v = detail.get(key, {})
            score = v.get('점수', 0)
            analysis = v.get('분석', '-')
            evidence = _list_to_html(v.get('평가 근거 문장', [])[:3])
            
            details_html += f"""
            <div class="detail-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <span style="font-weight:800; font-size:18px; color:#1e293b;">{key}</span>
                    <div>
                        {_get_star_html(score)}
                        <span style="font-weight:bold; color:#555; margin-left:5px;">({score}/10)</span>
                    </div>
                </div>
                <div style="font-size:14px; color:#333; margin-bottom:5px;">{analysis}</div>
                <div class="evidence-box">
                    <div style="font-weight:800; margin-bottom:5px;">📢 평가 근거 문장</div>
                    <ul style="padding-left:20px; margin:0;">{evidence}</ul>
                </div>
            </div>
            """

        # 추천 도서 HTML 조립
        books_html = ""
        for b in books[:3]:
            if isinstance(b, dict):
                books_html += f"""
                <div class="book-item">
                    <div>
                        <span class="book-tag">{b.get('분류', '추천')}</span>
                        <span style="font-weight:800; font-size:14px;">{b.get('도서', '-')}</span>
                        <span style="font-size:12px; color:#666;">({b.get('저자', '')})</span>
                    </div>
                    <div style="font-size:12px; color:#555; margin-top:5px; border-top:1px dashed #eee; padding-top:4px;">
                        {b.get('추천 이유', '-')}
                    </div>
                </div>
                """

        # 추천 학과 HTML 조립
        majors_html = ""
        for i, m in enumerate(majors[:3]):
            if isinstance(m, dict):
                majors_html += f"""
                <div class="major-item">
                    <span class="major-badge">TOP {i+1}</span>
                    <div style="font-weight:800; font-size:16px; margin:5px 0; color:#1e293b;">{m.get('학과','-')}</div>
                    <div style="font-size:12px; color:#666; line-height:1.4;">{m.get('근거','-')}</div>
                </div>
                """

        # 전체 HTML 조립 (textwrap.dedent 사용 대신 들여쓰기 없이 바로 작성하여 문제 원천 차단)
        full_html = f"""
{style_block}
<div class="rpt-container">
    <div class="rpt-header">
        <h1 class="rpt-title">종합 분석 보고서</h1>
        <div class="rpt-sub">AI Student Record Analysis Report</div>
        <div class="rpt-meta">학번: {sid} &nbsp;|&nbsp; 성명: {sname}</div>
    </div>

    <div class="sec-title">1. 종합 평가</div>
    <div class="summary-box">
        {_highlight(overall, keywords)}
    </div>

    <div class="sec-title">2. 역량 분석 및 전략</div>
    <div style="display:flex; justify-content:center; margin: 20px 0;">
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
    {details_html}

    <div class="sec-title">4. 맞춤형 성장 제안</div>
    <div class="grid-2">
        <div style="display:flex; flex-direction:column; gap:15px;">
            <div class="box-panel bg-blue" style="height:auto;">
                <span class="panel-head" style="color:#1d4ed8;">📌 생활기록부 중점 전략</span>
                <div style="font-size:14px; line-height:1.6;">{strat or '-'}</div>
            </div>
            <div class="box-panel bg-blue" style="height:auto;">
                <span class="panel-head" style="color:#1d4ed8;">🏫 추천 학교 행사</span>
                <ul class="panel-list">{_list_to_html(events[:4])}</ul>
            </div>
        </div>
        <div class="book-container">
            <span class="panel-head" style="color:#333;">📚 추천 도서</span>
            {books_html}
        </div>
    </div>

    <div class="sec-title">5. 역량 기반 추천 학과</div>
    <div class="major-grid">
        {majors_html}
    </div>
</div>
"""
        
        # 3. 최종 렌더링
        st.markdown(full_html, unsafe_allow_html=True)

        # PDF 다운로드 버튼
        if pdf_bytes:
            st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
            st.download_button(
                "📥 보고서 PDF 저장", 
                data=pdf_bytes, 
                file_name=f"{sname}_분석보고서.pdf", 
                mime="application/pdf", 
                use_container_width=True
            )

    _show()
