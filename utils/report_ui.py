from __future__ import annotations
import base64
from io import BytesIO
from typing import Any, Dict, Optional

def _img_to_base64(img_bytes):
    if img_bytes is None: return ""
    return base64.b64encode(img_bytes.getvalue()).decode()

def _normalize_score(score):
    """점수 10점 만점 변환"""
    try:
        s = float(score)
        if s > 10: return int(s / 10)
        return int(s)
    except: return 0

def _get_star_html(score):
    """별점 생성"""
    s = _normalize_score(score)
    full = "★" * (s // 2)
    empty = "☆" * (5 - (s // 2))
    return f"<span style='color:#f59e0b; font-size:18px; letter-spacing:1px;'>{full}</span><span style='color:#e2e8f0; font-size:18px; letter-spacing:1px;'>{empty}</span>"

def _list_to_html(items):
    """리스트 HTML 변환 (공백 제거)"""
    if not items: return "<li style='margin-bottom:4px;'>-</li>"
    # 리스트 항목 생성 시 줄바꿈/들여쓰기 제거
    return "".join([f"<li style='margin-bottom:4px;'>{str(x)}</li>" for x in items])

def _highlight(text, keywords):
    """형광펜 효과 (인라인 스타일 강제 적용)"""
    text = str(text).replace("\n", "<br>")
    if not keywords: return text
    
    # 노란색 형광펜 스타일 직접 주입
    style = "background:linear-gradient(to top, #fef08a 50%, transparent 50%); font-weight:800; padding:0 2px;"
    
    for k in keywords:
        if k and len(k) > 1:
            text = text.replace(k, f"<span style='{style}'>{k}</span>")
    return text

def inject_report_css(st=None):
    if st is None: import streamlit as st
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700;900&display=swap');
    .rpt-container { font-family: 'Noto Sans KR', sans-serif; color: #333; line-height: 1.6; }
    .rpt-header { text-align: center; padding-bottom: 20px; margin-bottom: 30px; border-bottom: 2px solid #333; }
    .rpt-title { font-size: 32px; font-weight: 900; color: #111; margin: 0 0 5px 0; }
    .rpt-sub { font-size: 14px; color: #666; margin: 0; }
    .rpt-meta { text-align: right; font-size: 14px; font-weight: 700; color: #555; margin-top: 15px; }
    .rpt-section-title { font-size: 20px; font-weight: 800; color: #1e293b; margin-top: 40px; margin-bottom: 15px; border-left: 5px solid #2563eb; padding-left: 12px; display: flex; align-items: center; }
    .rpt-summary-box { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; font-size: 16px; text-align: justify; color: #334155; }
    .box-panel { padding: 20px; border-radius: 12px; height: 100%; border: 1px solid transparent; }
    .bg-green { background: #f0fdf4; border-color: #bbf7d0; }
    .bg-red { background: #fef2f2; border-color: #fecaca; }
    .bg-blue { background: #eff6ff; border-color: #dbeafe; }
    .bg-gray { background: #f8fafc; border-color: #e2e8f0; }
    .box-head { display: block; font-weight: 800; font-size: 16px; margin-bottom: 12px; color: #333; }
    .box-list { margin: 0; padding-left: 18px; font-size: 14px; }
    .detail-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .detail-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
    .detail-title { font-size: 18px; font-weight: 800; color: #1e293b; }
    .evidence-box { background-color: #f1f5f9; border-radius: 8px; padding: 15px; margin-top: 12px; border-left: 4px solid #94a3b8; font-size: 13.5px; color: #475569; }
    .book-item { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .book-tag { display: inline-block; font-size: 11px; font-weight: 800; color: #fff; background: #3b82f6; padding: 2px 6px; border-radius: 4px; margin-right: 6px; }
    .book-title { font-weight: 800; color: #1e293b; font-size: 14px; }
    .book-author { font-size: 12px; color: #666; margin-left: 4px; }
    .book-reason { font-size: 13px; color: #555; margin-top: 5px; border-top: 1px dashed #eee; padding-top: 5px; }
    .major-card { background: #fff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 15px; text-align: center; position: relative; margin-top: 10px; height: 100%; }
    .major-badge { position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: #0f172a; color: #fff; font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 20px; }
    @media print { .stButton, .stDownloadButton { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

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

        # 키워드 추출 (강점의 첫 단어들)
        keywords = [s.split()[0] for s in strengths[:3] if s]

        # --- HTML 조립 (들여쓰기 절대 금지) ---
        
        # 1. 헤더
        st.markdown(f"<div class='rpt-container'><div class='rpt-header'><div class='rpt-title'>종합 분석 보고서</div><div class='rpt-sub'>AI Student Record Analysis Report</div><div class='rpt-meta'>학번: {sid} ｜ 성명: {sname}</div></div>", unsafe_allow_html=True)

        # 2. 종합 평가 (하이라이트 적용)
        st.markdown(f"<div class='rpt-section-title'>1. 종합 평가</div><div class='rpt-summary-box'>{_highlight(overall, keywords)}</div>", unsafe_allow_html=True)

        # 3. 그래프 및 강점/보완
        st.markdown("<div class='rpt-section-title'>2. 역량 시각화 및 분석</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            if radar_png: st.image(radar_png, use_container_width=True)
        
        c_str, c_weak = st.columns(2)
        with c_str:
            st.markdown(f"<div class='box-panel bg-green'><span class='box-head' style='color:#15803d;'>✅ 핵심 강점</span><ul class='box-list'>{_list_to_html(strengths)}</ul></div>", unsafe_allow_html=True)
        with c_weak:
            st.markdown(f"<div class='box-panel bg-red'><span class='box-head' style='color:#b91c1c;'>⚠️ 보완 추천 영역</span><ul class='box-list'>{_list_to_html(weaknesses)}</ul></div>", unsafe_allow_html=True)

        # 4. 상세 분석
        st.markdown("<div class='rpt-section-title'>3. 평가 항목별 상세 분석</div>", unsafe_allow_html=True)
        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            v = detail.get(key, {})
            score = _normalize_score(v.get('점수', 0))
            
            # HTML 문자열 한 줄로 연결
            card_html = f"<div class='detail-card'><div class='detail-head'><span class='detail-title'>{key}</span><div>{_get_star_html(score)} <span style='font-weight:bold; color:#666;'>({score}/10)</span></div></div><div style='font-size:15px; color:#333; margin-bottom:8px;'>{v.get('분석', '-')}</div><div class='evidence-box'><div style='font-weight:800; margin-bottom:5px;'>📢 평가 근거 문장</div><ul style='padding-left:20px; margin:0;'>{_list_to_html(v.get('평가 근거 문장', [])[:3])}</ul></div></div>"
            st.markdown(card_html, unsafe_allow_html=True)

        # 5. 성장 제안
        st.markdown("<div class='rpt-section-title'>4. 맞춤형 성장 제안</div>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        
        with g1:
            st.markdown(f"<div class='box-panel bg-blue' style='margin-bottom:15px;'><span class='box-head' style='color:#1d4ed8;'>📌 생활기록부 중점 전략</span><div style='font-size:14px;'>{strat or '-'}</div></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='box-panel bg-blue'><span class='box-head' style='color:#1d4ed8;'>🏫 추천 학교 행사</span><ul class='box-list'>{_list_to_html(events[:4])}</ul></div>", unsafe_allow_html=True)
            
        with g2:
            # 책 리스트 HTML 생성 (들여쓰기 없이)
            books_html = ""
            for b in books[:3]:
                if isinstance(b, dict):
                    # 문자열 이어붙이기
                    books_html += f"<div class='book-item'><div><span class='book-tag'>{b.get('분류', '추천')}</span> <span class='book-title'>{b.get('도서', '-')}</span> <span class='book-author'>({b.get('저자','')})</span></div><div class='book-reason'>{b.get('추천 이유', '-')}</div></div>"
            
            st.markdown(f"<div class='box-panel bg-gray'><span class='box-head' style='color:#333;'>📚 추천 도서</span>{books_html}</div>", unsafe_allow_html=True)

        # 6. 추천 학과
        st.markdown("<div class='rpt-section-title'>5. 역량 기반 추천 학과</div>", unsafe_allow_html=True)
        maj_cols = st.columns(3)
        for i, m in enumerate(majors[:3]):
            with maj_cols[i]:
                if isinstance(m, dict):
                    st.markdown(f"<div class='major-card'><div class='major-badge'>TOP {i+1}</div><div style='font-weight:800; font-size:16px; margin:10px 0; color:#1e293b;'>{m.get('학과','-')}</div><div style='font-size:12px; color:#64748b; line-height:1.4;'>{m.get('근거','-')}</div></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True) # 컨테이너 닫기

        if pdf_bytes:
            st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
            st.download_button("📥 보고서 PDF 저장", data=pdf_bytes, file_name=f"{sname}_분석보고서.pdf", mime="application/pdf", use_container_width=True)

    _show()
