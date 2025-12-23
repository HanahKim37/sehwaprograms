# utils/report_ui.py
from __future__ import annotations

from typing import Any, Dict, Optional
from io import BytesIO

def inject_report_css(st=None):
    """
    ✅ 메인에서 inject_report_css() 처럼 인자 없이 호출해도 동작하도록 설계.
    - st가 None이면 내부에서 streamlit을 import해서 사용.
    - st를 넘겨도 동작(호환).
    """
    if st is None:
        import streamlit as st  # noqa: F401

    st.markdown(
        """
        <style>
        /* 보고서 모달(UI) 전용 스타일 - 메인 화면 영향 최소 */
        .rpt-title{
            text-align:center;
            font-size:28px;
            font-weight:800;
            margin:6px 0 8px 0;
        }
        .rpt-meta{
            text-align:right;
            font-size:13px;
            color:#374151;
            margin:0 0 6px 0;
        }
        .rpt-hr{
            height:2px; background:#111827; border:none; margin:8px 0 14px 0;
        }
        .rpt-bar-title{
            display:flex; align-items:center; gap:10px;
            font-size:18px; font-weight:800; margin:10px 0 10px 0;
        }
        .rpt-bar{
            width:10px; height:22px; border-radius:6px; background:#9CA3AF;
        }
        .rpt-card{
            background:#fff;
            border:1px solid #e5e7eb;
            border-radius:14px;
            padding:16px 16px;
            box-shadow:0 1px 2px rgba(0,0,0,0.04);
            margin:10px 0 14px 0;
        }
        .rpt-two{
            display:grid;
            grid-template-columns: 1fr 1fr;
            gap:12px;
        }
        .rpt-pill-good{
            background:#ecfdf5;
            border:1px solid #a7f3d0;
            border-radius:14px;
            padding:14px;
        }
        .rpt-pill-bad{
            background:#fef2f2;
            border:1px solid #fecaca;
            border-radius:14px;
            padding:14px;
        }
        .rpt-subtitle{
            font-size:16px;
            font-weight:800;
            margin:0 0 8px 0;
        }
        .rpt-evidence{
            background:#f9fafb;
            border:1px solid #e5e7eb;
            border-radius:12px;
            padding:12px 12px;
            margin:10px 0 10px 0;
            font-size:13px;
        }
        .rpt-section{
            border:1px solid #e5e7eb;
            border-radius:14px;
            padding:14px;
            margin:10px 0 14px 0;
            background:#ffffff;
        }
        .rpt-section h4{
            margin:0 0 6px 0;
            font-size:16px;
            font-weight:800;
        }
        .rpt-stars{
            font-size:15px;
            letter-spacing:1px;
            color:#111827;
            margin:0 0 8px 0;
            text-align:right;
        }
        .rpt-bluebox{
            background:#eff6ff;
            border:1px solid #bfdbfe;
            border-radius:14px;
            padding:14px;
            margin:10px 0 14px 0;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def _stars(score: Any, max_score: int = 10) -> str:
    try:
        s = int(score)
    except Exception:
        s = 0
    s = max(0, min(s, max_score))
    return "★" * s + "☆" * (max_score - s)


def render_report_modal(
    st,
    report: Dict[str, Any],
    sid: str,
    sname: str,
    radar_png: Optional[BytesIO] = None,
    pdf_bytes: Optional[bytes] = None,
):
    """
    ✅ 메인에서 호출하는 형태를 고정:
    render_report_modal(st, report, sid, sname, radar_png, pdf_bytes)
    """

    @st.dialog(f"📊 SH-Insight 심층 분석 보고서 · {sid} / {sname}", width="large")
    def _show():
        # 모달 내부 CSS 주입
        inject_report_css(st)

        majors = report.get("역량 기반 추천 학과", [])
        expected_major = ""
        if isinstance(majors, list) and majors:
            m0 = majors[0]
            expected_major = m0.get("학과", "") if isinstance(m0, dict) else str(m0)

        overall = str(report.get("종합 평가", "") or "")
        strengths = report.get("핵심 강점", []) or []
        needs = report.get("보완 추천 영역", []) or []
        detail = report.get("3대 평가 항목별 상세 분석", {}) or {}
        topics = report.get("영역별 심화 탐구 주제 제안", {}) or {}
        growth = report.get("맞춤형 성장 제안", {}) or {}
        books = report.get("추천 도서", []) or []

        # 1) 제목 가운데 크게
        st.markdown("<div class='rpt-title'>SH-Insight 심층 분석 보고서</div>", unsafe_allow_html=True)

        # 2) 학생 정보 오른쪽 정렬 + 줄
        st.markdown(f"<div class='rpt-meta'>{sid} / {sname}</div>", unsafe_allow_html=True)
        st.markdown("<hr class='rpt-hr'/>", unsafe_allow_html=True)

        # 3) 종합 평가 (예상 희망 진로 포함)
        st.markdown(
            f"""
            <div class='rpt-bar-title'>
              <div class='rpt-bar'></div>
              <div>종합 평가 <span style="font-weight:700;color:#374151;">(예상 희망 진로: {expected_major})</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(f"<div class='rpt-card'>{overall}</div>", unsafe_allow_html=True)

        # 4) 레이더 (가운데 작게)
        st.markdown(
            """
            <div class='rpt-bar-title'>
              <div class='rpt-bar'></div>
              <div>핵심 역량 분석</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if radar_png is not None:
            st.image(radar_png, width=320)
        else:
            st.info("레이더 차트 이미지가 없습니다.")

        # 5) 핵심 강점 / 보완 영역 (색 박스 내부)
        st.markdown("<div class='rpt-two'>", unsafe_allow_html=True)

        st.markdown("<div class='rpt-pill-good'>", unsafe_allow_html=True)
        st.markdown("<div class='rpt-subtitle'>핵심 강점</div>", unsafe_allow_html=True)
        if isinstance(strengths, list) and strengths:
            for x in strengths:
                st.markdown(f"- {x}")
        else:
            st.markdown("-")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='rpt-pill-bad'>", unsafe_allow_html=True)
        st.markdown("<div class='rpt-subtitle'>보완 추천 영역</div>", unsafe_allow_html=True)
        if isinstance(needs, list) and needs:
            for x in needs:
                st.markdown(f"- {x}")
        else:
            st.markdown("-")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # 6) 3대 평가 항목별 상세 분석 + 별점(10)
        st.markdown(
            """
            <div class='rpt-bar-title'>
              <div class='rpt-bar'></div>
              <div>3대 평가 항목별 상세 분석</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        for key in ["학업역량", "학업태도", "학업 외 소양"]:
            v = detail.get(key, {})
            if not isinstance(v, dict):
                continue

            score = v.get("점수", 0)
            st.markdown("<div class='rpt-section'>", unsafe_allow_html=True)
            st.markdown(f"<h4>{key}</h4>", unsafe_allow_html=True)
            st.markdown(f"<div class='rpt-stars'>{_stars(score)} ({score}/10)</div>", unsafe_allow_html=True)

            evid = v.get("평가 근거 문장", []) or []
            st.markdown("<div class='rpt-evidence'><b>평가 근거 문장</b><br/>", unsafe_allow_html=True)
            if isinstance(evid, list) and evid:
                for e in evid[:6]:
                    st.markdown(f"• {e}")
            else:
                st.markdown("-")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<b>분석</b>", unsafe_allow_html=True)
            st.write(v.get("분석", ""))
            st.markdown("</div>", unsafe_allow_html=True)

        # 7) 맞춤형 성장 제안 (좌) + 추천 도서 (우)
        st.markdown(
            """
            <div class='rpt-bar-title'>
              <div class='rpt-bar'></div>
              <div>맞춤형 성장 제안</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("<div class='rpt-card'>", unsafe_allow_html=True)
            st.markdown("<div class='rpt-subtitle'>생활기록부 중점 보완 전략</div>", unsafe_allow_html=True)
            if isinstance(growth, dict):
                st.write(growth.get("생활기록부 중점 보완 전략", "") or "-")
            else:
                st.write("-")

            st.markdown("<div class='rpt-subtitle' style='margin-top:12px;'>추천 학교 행사</div>", unsafe_allow_html=True)
            ev = growth.get("추천 학교 행사", []) if isinstance(growth, dict) else []
            if isinstance(ev, list) and ev:
                for it in ev[:8]:
                    st.markdown(f"- {it}")
            else:
                st.markdown("-")
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("<div class='rpt-card' style='background:#f9fafb;'>", unsafe_allow_html=True)
            st.markdown("<div class='rpt-subtitle'>추천 도서</div>", unsafe_allow_html=True)
            if isinstance(books, list) and books:
                for b in books[:10]:
                    if isinstance(b, dict):
                        st.markdown(f"**[{b.get('분류','')}] {b.get('도서','')} ({b.get('저자','')})**")
                        st.write(b.get("추천 이유", "") or "")
                    else:
                        st.markdown(f"- {b}")
            else:
                st.markdown("-")
            st.markdown("</div>", unsafe_allow_html=True)

        # 8) 영역별 심화 탐구 주제 제안
        st.markdown(
            """
            <div class='rpt-bar-title'>
              <div class='rpt-bar'></div>
              <div>영역별 심화 탐구 주제 제안</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<div class='rpt-bluebox'>", unsafe_allow_html=True)
        for k in ["자율", "진로", "동아리"]:
            txt = topics.get(k, "") if isinstance(topics, dict) else ""
            st.markdown(f"**{k}**: {txt or '-'}")
        st.markdown("</div>", unsafe_allow_html=True)

        # 9) 추천 학과 3박스
        st.markdown(
            """
            <div class='rpt-bar-title'>
              <div class='rpt-bar'></div>
              <div>역량 기반 추천 학과</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        majors_list = majors if isinstance(majors, list) else []
        cols = st.columns(3)
        for i in range(3):
            with cols[i]:
                if i < len(majors_list):
                    m = majors_list[i]
                    dept = m.get("학과", "") if isinstance(m, dict) else str(m)
                    why = m.get("근거", "") if isinstance(m, dict) else ""
                    st.markdown("<div class='rpt-card'>", unsafe_allow_html=True)
                    st.markdown(f"<div class='rpt-subtitle'>{dept}</div>", unsafe_allow_html=True)
                    st.write(why or "-")
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='rpt-card'>-</div>", unsafe_allow_html=True)

        # 10) PDF 저장
        if pdf_bytes:
            st.download_button(
                "📄 PDF로 저장",
                data=pdf_bytes,
                file_name=f"SH-Insight_{sid}_{sname}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    _show()
