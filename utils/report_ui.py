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
        
        .rpt-wrap { max-width: 1080px; margin: 0 auto; font-family: 'Pretendard', sans-serif; color: #334155; }

        /* 섹션 타이틀 (이미지 스타일) */
        .rpt-main-title { font-size: 24px; font-weight: 800; color: #1e293b; margin: 30px 0 15px 0; display: flex; align-items: center; gap: 10px; }
        .rpt-main-title::before { content: ""; width: 4px; height: 20px; background: #3b82f6; border-radius: 2px; }

        /* 대형 상단 카드 (종합 역량치) */
        .rpt-top-card {
            background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); margin-bottom: 20px;
        }

        /* 공통 카드 스타일 */
        .rpt-sub-card {
            background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 20px; height: 100%;
        }

        /* 컬러 박스 (이미지 배색 반영) */
        .box-green { background-color: #f0fdf4; border: 1px solid #dcfce7; border-radius: 8px; padding: 15px; }
        .box-red { background-color: #fff1f2; border: 1px solid #ffe4e6; border-radius: 8px; padding: 15px; }
        .box-gray { background-color: #f8fafc; border: 1px solid #f1f5f9; border-radius: 8px; padding: 15px; }
        .box-blue { background-color: #eff6ff; border: 1px solid #dbeafe; border-radius: 8px; padding: 15px; }

        .box-title { font-weight: 800; font-size: 16px; margin-bottom: 10px; }
        .text-green { color: #166534; }
        .text-red { color: #991b1b; }

        /* 점수 및 별점 */
        .rpt-stars { color: #fbbf24; font-size: 14px; font-weight: 800; }
        .rpt-score-val { color: #64748b; font-size: 12px; margin-left: 5px; }

        /* 하단 태그 스타일 */
        .rpt-tag {
            display: inline-block; padding: 8px 16px; border-radius: 8px; 
            border: 1px solid #3b82f6; color: #3b82f6; font-weight: 600; font-size: 14px;
            margin-right: 8px; margin-bottom: 8px; background: #ffffff;
        }

        /* 추천 학과 카드 (이미지 하단) */
        .major-item {
            border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; background: #fff;
        }
        .major-badge {
            font-size: 10px; background: #eff6ff; color: #3b82f6; 
            padding: 2px 6px; border-radius: 4px; font-weight: 800; margin-bottom: 5px; display: inline-block;
        }

        @media print { .stDownloadButton { display: none !important; } }
        </style>
        """,
        unsafe_allow_html=True
    )

def _html_list(items: list[str]) -> str:
    if not items: return "<div style='color:#94a3b8'>-</div>"
    li = "".join([f"<li style='margin-bottom:5px; font-size:13px;'>• {str(i)}</li>" for i in items])
    return f"<ul style='list-style:none; padding:0; margin:0;'>{li}</ul>"

def render_report_modal(st, report: Dict[str, Any], sid: str, sname: str, radar_png: Optional[BytesIO] = None, pdf_bytes: Optional[bytes] = None):
    @st.dialog(f"📊 {sname} 학생 분석 보고서", width="large")
    def _show():
        inject_report_css(st)
        
        # 데이터 정리
        majors = report.get("역량 기반 추천 학과", [])
        expected_major = majors[0].get("학과", "") if majors and isinstance(majors[0], dict) else "미지정"
        detail = report.get("3대 평가 항목별 상세 분석", {})
        growth = report.get("맞춤형 성장 제안", {})
        topics = report.get("영역별 심화 탐구 주제 제안", {})

        st.markdown("<div class='rpt-wrap'>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # 1. 종합 역량치 (이미지 상단 레이아웃)
        # ---------------------------------------------------------
        st.markdown("<div class='rpt-main-title'>종합 역량치</div>", unsafe_allow_html=True)
        st.markdown("<div class='rpt-top-card'>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns([1.5, 1, 1.2])
        with c1:
            st.markdown(f"<div style='font-size:18px; font-weight:800; margin-bottom:15px;'>🎯 희망 진로: <span style='color:#3b82f6'>{expected_major}</span></div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:14px; line-height:1.7; color:#475569;'>{report.get('종합 평가', '')}</div>", unsafe_allow_html=True)
        
        with c2:
            if radar_png: st.image(radar_png, use_container_width=True)
        
        with c3:
            # 상단 핵심 지표
            for key in ["학업역량", "학업태도"]:
                v = detail.get(key, {})
                score = v.get("점수", 0)
                st.markdown(f"""
                    <div style='margin-bottom:15px;'>
                        <div style='font-weight:800; font-size:15px; margin-bottom:5px;'>{key} <span class='rpt-score-val'>({score}/10)</span></div>
                        <div class='rpt-stars'>{'★'*(score//2)}{'☆'*(5-score//2)}</div>
                    </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # 2. 3대 영역별 상세 분석 (이미지 중단 좌측) & 강점/보완 (우측)
        # ---------------------------------------------------------
        st.markdown("<div class='rpt-main-title'>3대 영역별 상세 분석</div>", unsafe_allow_html=True)
        
        col_L, col_R = st.columns([1.2, 1])
        
        with col_L:
            st.markdown("<div class='rpt-sub-card'>", unsafe_allow_html=True)
            for key in ["학업역량", "학업태도", "학업 외 소양"]:
                v = detail.get(key, {})
                st.markdown(f"""
                    <div style='margin-bottom:20px;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <span style='font-weight:800; font-size:15px;'>{key}</span>
                            <span class='rpt-stars'>{'★'*(v.get('점수',0)//2)} <small style='color:#94a3b8'>({v.get('점수',0)}/10)</small></span>
                        </div>
                        <div style='font-size:13px; color:#64748b; margin-top:5px; line-height:1.5;'>{v.get('분석', '-')}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # 생기부 보완 전략 (이미지 중간 회색 박스)
            st.markdown("<div class='box-gray'>", unsafe_allow_html=True)
            st.markdown("<div class='box-title'>📋 생기부 중점 보완 전략</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:13px;'>{growth.get('생활기록부 중점 보완 전략', '-')}</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_R:
            # 강점 / 보완 박스 (이미지 우측 상단)
            st.markdown(f"""
                <div class='box-green' style='margin-bottom:12px;'>
                    <div class='box-title text-green'>✅ 핵심 강점</div>
                    {_html_list(report.get('핵심 강점', []))}
                </div>
                <div class='box-red' style='margin-bottom:12px;'>
                    <div class='box-title text-red'>⚠️ 보완 추천 영역</div>
                    {_html_list(report.get('보완 추천 영역', []))}
                </div>
            """, unsafe_allow_html=True)
            
            # 추천 도서 (이미지 우측 하단)
            st.markdown("<div class='box-blue'>", unsafe_allow_html=True)
            st.markdown("<div class='box-title' style='color:#1d4ed8;'>📚 추천 도서</div>", unsafe_allow_html=True)
            for b in report.get("추천 도서", [])[:3]:
                if isinstance(b, dict):
                    st.markdown(f"<div style='font-size:13px; margin-bottom:4px;'>• <b>{b.get('도서','-')}</b> ({b.get('저자','')})</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # 3. 영역별 심화 탐구 주제 (이미지 하단 태그 스타일)
        # ---------------------------------------------------------
        st.markdown("<div class='rpt-main-title'>영역별 심화 탐구 주제 제안</div>", unsafe_allow_html=True)
        
        # 태그 나열
        tag_html = ""
        for k, v in topics.items():
            if v: tag_html += f"<div class='rpt-tag'>{k} : {v}</div>"
        st.markdown(f"<div>{tag_html}</div>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # 4. 역량 기반 추천 학과 (최하단 카드)
        # ---------------------------------------------------------
        st.markdown("<div class='rpt-main-title'>역량 기반 추천 학과</div>", unsafe_allow_html=True)
        m_cols = st.columns(3)
        for i, m in enumerate(majors[:3]):
            with m_cols[i]:
                st.markdown(f"""
                    <div class='major-item'>
                        <span class='major-badge'>TOP {i+1}</span>
                        <div style='font-weight:800; font-size:16px; margin-bottom:8px;'>{m.get('학과','-')}</div>
                        <div style='font-size:12px; color:#64748b; line-height:1.4;'>{m.get('근거','-')}</div>
                    </div>
                """, unsafe_allow_html=True)

        # PDF 버튼
        if pdf_bytes:
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button("🟦 정식 보고서 PDF 다운로드", data=pdf_bytes, file_name=f"Report_{sname}.pdf", mime="application/pdf", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    _show()
