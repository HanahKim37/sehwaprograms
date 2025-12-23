# utils/report_ui.py
from __future__ import annotations

from typing import Any, Dict, Optional
from io import BytesIO


# -----------------------------
# CSS
# -----------------------------
def inject_report_css(st=None):
    """
    - 메인에서 inject_report_css() (인자 없이) 호출해도 동작
    - st를 넘겨도 동작
    """
    if st is None:
        import streamlit as st  # noqa

    st.markdown(
        """
        <style>
        /* 모달 안에서만 "예쁘게" 보이도록 최대한 범위를 rpt-*로 제한 */
        .rpt-wrap{
            max-width: 1040px;
            margin: 0 auto;
        }

        /* 타이포 */
        .rpt-h1{
            text-align:center;
            font-size:30px;
            font-weight:900;
            letter-spacing:-0.5px;
            margin: 4px 0 10px 0;
            color:#111827;
        }
        .rpt-meta{
            text-align:right;
            font-size:13px;
            color:#6b7280;
            margin: 0 0 8px 0;
            font-weight:600;
        }
        .rpt-hr{
            height:2px;
            background:#111827;
            border:none;
            margin: 8px 0 18px 0;
        }

        /* 섹션 타이틀(왼쪽 바 + 아이콘) */
        .rpt-sec-title{
            display:flex;
            align-items:center;
            gap:10px;
            margin: 18px 0 10px 0;
        }
        .rpt-sec-bar{
            width:10px; height:22px; border-radius:8px;
            background: linear-gradient(180deg, #9ca3af, #6b7280);
            flex: 0 0 auto;
        }
        .rpt-sec-text{
            font-size:18px;
            font-weight:900;
            color:#111827;
            letter-spacing:-0.3px;
        }
        .rpt-sec-sub{
            font-size:13px;
            font-weight:700;
            color:#6b7280;
            margin-left:auto;
            text-align:right;
        }

        /* 카드 */
        .rpt-card{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 16px 16px;
            box-shadow: 0 8px 20px rgba(17,24,39,0.06);
        }
        .rpt-card + .rpt-card{ margin-top: 12px; }

        /* “읽기 싫은” 긴 글을 보기 좋게 */
        .rpt-body{
            font-size: 14px;
            line-height: 1.75;
            color: #111827;
            word-break: keep-all;
        }

        /* 배지/칩 */
        .rpt-chip{
            display:inline-flex;
            align-items:center;
            gap:6px;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid #e5e7eb;
            background: #f9fafb;
            color:#111827;
            font-size: 12px;
            font-weight:800;
            white-space:nowrap;
        }
        .rpt-chip-strong{
            background: #ecfdf5;
            border-color: #a7f3d0;
            color: #065f46;
        }
        .rpt-chip-need{
            background: #fef2f2;
            border-color: #fecaca;
            color: #991b1b;
        }
        .rpt-chip-major{
            background: #eff6ff;
            border-color: #bfdbfe;
            color: #1d4ed8;
        }

        /* 2열/3열 레이아웃 */
        .rpt-grid-2{
            display:grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }
        .rpt-grid-3{
            display:grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 12px;
        }
        @media (max-width: 960px){
            .rpt-grid-2{ grid-template-columns: 1fr; }
            .rpt-grid-3{ grid-template-columns: 1fr; }
        }

        /* 목록: 박스 안에 "깔끔하게" */
        .rpt-list{
            margin: 10px 0 0 0;
            padding-left: 18px;
        }
        .rpt-list li{
            margin: 6px 0;
            line-height: 1.6;
            font-size: 13.5px;
            color:#111827;
        }

        /* 강점/보완: 색 박스 안에 문구가 들어가도록 */
        .rpt-colorbox{
            border-radius: 16px;
            padding: 14px 14px;
            border: 1px solid #e5e7eb;
        }
        .rpt-colorbox.good{ background:#ecfdf5; border-color:#a7f3d0; }
        .rpt-colorbox.bad{ background:#fef2f2; border-color:#fecaca; }

        .rpt-box-title{
            font-size: 15px;
            font-weight: 900;
            margin: 0 0 8px 0;
            letter-spacing:-0.2px;
        }
        .rpt-box-title.good{ color:#065f46; }
        .rpt-box-title.bad{ color:#991b1b; }

        /* 3대 평가 항목 카드 */
        .rpt-kpi-head{
            display:flex;
            align-items:flex-end;
            justify-content:space-between;
            gap: 10px;
            margin-bottom: 8px;
        }
        .rpt-kpi-title{
            font-size: 16px;
            font-weight: 900;
            color:#111827;
            letter-spacing:-0.2px;
        }
        .rpt-stars{
            font-size: 14px;
            font-weight: 900;
            color:#111827;
            letter-spacing: 1px;
            white-space:nowrap;
        }
        .rpt-score{
            font-size: 12px;
            color:#6b7280;
            font-weight: 800;
            margin-left: 8px;
        }

        /* 근거문장 박스: 작고 정갈하게 */
        .rpt-evidence{
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 12px 12px;
            margin: 10px 0 10px 0;
        }
        .rpt-evidence-title{
            font-size: 13px;
            font-weight: 900;
            color:#374151;
            margin: 0 0 6px 0;
        }
        .rpt-evidence .rpt-list li{
            font-size: 13px;
            color:#111827;
        }

        /* 영역별 주제 박스 */
        .rpt-topic{
            background:#eff6ff;
            border: 1px solid #bfdbfe;
            border-radius: 16px;
            padding: 14px 14px;
        }
        .rpt-topic .rpt-chip{ margin-bottom: 8px; }
        .rpt-topic p{
            margin: 6px 0 0 0;
            font-size: 13.5px;
            line-height:1.6;
            color:#111827;
        }

        /* 추천학과 카드 */
        .rpt-major-card{
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 14px 14px;
            box-shadow: 0 8px 20px rgba(17,24,39,0.06);
            min-height: 120px;
        }
        .rpt-major-title{
            font-size: 15px;
            font-weight: 900;
            margin: 0 0 8px 0;
            color:#111827;
        }
        .rpt-major-body{
            font-size: 13.5px;
            line-height: 1.6;
            color:#111827;
        }

        /* Streamlit 기본 요소 spacing을 조금 정리 */
        div[data-testid="stMarkdownContainer"] > p { margin-bottom: 0.6rem; }
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


def _safe_list(x) -> list[str]:
    if isinstance(x, list):
        return [str(v).strip() for v in x if str(v).strip()]
    return []


def _html_list(items: list[str]) -> str:
    if not items:
        return "<ul class='rpt-list'><li>-</li></ul>"
    li = "".join([f"<li>{_escape_html(v)}</li>" for v in items])
    return f"<ul class='rpt-list'>{li}</ul>"


def _escape_html(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_report_modal(
    st,
    report: Dict[str, Any],
    sid: str,
    sname: str,
    radar_png: Optional[BytesIO] = None,
    pdf_bytes: Optional[bytes] = None,
):
    """
    메인에서 호출 형태 고정:
    render_report_modal(st, report, sid, sname, radar_png, pdf_bytes)
    """

    @st.dialog(f"📊 SH-Insight 심층 분석 보고서 · {sid} / {sname}", width="large")
    def _show():
        inject_report_css(st)

        majors = report.get("역량 기반 추천 학과", [])
        expected_major = ""
        if isinstance(majors, list) and majors:
            m0 = majors[0]
            expected_major = m0.get("학과", "") if isinstance(m0, dict) else str(m0)

        overall = str(report.get("종합 평가", "") or "").strip()
        strengths = _safe_list(report.get("핵심 강점", []))
        needs = _safe_list(report.get("보완 추천 영역", []))
        detail = report.get("3대 평가 항목별 상세 분석", {}) or {}
        topics = report.get("영역별 심화 탐구 주제 제안", {}) or {}
        growth = report.get("맞춤형 성장 제안", {}) or {}
        books = report.get("추천 도서", []) or []

        # ---------- Header ----------
        st.markdown("<div class='rpt-wrap'>", unsafe_allow_html=True)

        st.markdown("<div class='rpt-h1'>SH-Insight 심층 분석 보고서</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='rpt-meta'>{_escape_html(sid)} / {_escape_html(sname)}</div>", unsafe_allow_html=True)
        st.markdown("<hr class='rpt-hr'/>", unsafe_allow_html=True)

        # ---------- 종합평가 ----------
        st.markdown(
            f"""
            <div class='rpt-sec-title'>
              <div class='rpt-sec-bar'></div>
              <div class='rpt-sec-text'>종합 평가</div>
              <div class='rpt-sec-sub'>
                <span class='rpt-chip rpt-chip-major'>예상 희망 진로 · { _escape_html(expected_major) if expected_major else "분석 필요" }</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div class='rpt-card'>
              <div class='rpt-body'>{_escape_html(overall).replace("\\n", "<br/>") if overall else "내용이 비어 있습니다."}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ---------- 핵심역량 + 그래프 ----------
        st.markdown(
            """
            <div class='rpt-sec-title'>
              <div class='rpt-sec-bar'></div>
              <div class='rpt-sec-text'>핵심 역량 분석</div>
              <div class='rpt-sec-sub'>
                <span class='rpt-chip'>학업역량 · 학업태도 · 학업 외 소양</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div class='rpt-card'>", unsafe_allow_html=True)
        if radar_png is not None:
            # ✅ “가운데 조그맣게” 고정
            cL, cM, cR = st.columns([1, 1.3, 1])
            with cM:
                st.image(radar_png, width=280)
        else:
            st.info("레이더 차트 이미지가 없습니다.")
        st.markdown("</div>", unsafe_allow_html=True)

        # ---------- 강점/보완 (색 박스 내부에 문구) ----------
        st.markdown("<div class='rpt-grid-2'>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class='rpt-colorbox good'>
              <div class='rpt-box-title good'>핵심 강점</div>
              {_html_list(strengths)}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div class='rpt-colorbox bad'>
              <div class='rpt-box-title bad'>보완 추천 영역</div>
              {_html_list(needs)}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

        # ---------- 3대 평가 항목 ----------
        st.markdown(
            """
            <div class='rpt-sec-title'>
              <div class='rpt-sec-bar'></div>
              <div class='rpt-sec-text'>3대 평가 항목별 상세 분석</div>
              <div class='rpt-sec-sub'><span class='rpt-chip'>10점 만점</span></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if isinstance(detail, dict):
            for key in ["학업역량", "학업태도", "학업 외 소양"]:
                v = detail.get(key, {})
                if not isinstance(v, dict):
                    continue

                score = v.get("점수", 0)
                stars = _stars(score, 10)
                analysis = str(v.get("분석", "") or "").strip()
                evid = _safe_list(v.get("평가 근거 문장", []))

                st.markdown("<div class='rpt-card'>", unsafe_allow_html=True)
                st.markdown(
                    f"""
                    <div class='rpt-kpi-head'>
                      <div class='rpt-kpi-title'>{_escape_html(key)}</div>
                      <div class='rpt-stars'>{stars}<span class='rpt-score'>({int(score) if str(score).isdigit() else score}/10)</span></div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"""
                    <div class='rpt-evidence'>
                      <div class='rpt-evidence-title'>평가 근거 문장</div>
                      {_html_list(evid[:6])}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.markdown(
                    f"<div class='rpt-body'><b>분석</b><br/>{_escape_html(analysis).replace('\\n','<br/>') if analysis else '-'}</div>",
                    unsafe_allow_html=True
                )
                st.markdown("</div>", unsafe_allow_html=True)

        else:
            st.markdown("<div class='rpt-card'><div class='rpt-body'>-</div></div>", unsafe_allow_html=True)

        # ---------- 성장 제안(좌) + 추천도서(우) ----------
        st.markdown(
            """
            <div class='rpt-sec-title'>
              <div class='rpt-sec-bar'></div>
              <div class='rpt-sec-text'>맞춤형 성장 제안</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2 = st.columns([1.15, 0.85])

        with col1:
            strat = ""
            events = []
            if isinstance(growth, dict):
                strat = str(growth.get("생활기록부 중점 보완 전략", "") or "").strip()
                events = growth.get("추천 학교 행사", []) or []

            st.markdown("<div class='rpt-card'>", unsafe_allow_html=True)
            st.markdown("<div class='rpt-box-title'>생활기록부 중점 보완 전략</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='rpt-body'>{_escape_html(strat).replace('\\n','<br/>') if strat else '-'}</div>", unsafe_allow_html=True)

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            st.markdown("<div class='rpt-box-title'>추천 학교 행사</div>", unsafe_allow_html=True)
            st.markdown(_html_list(_safe_list(events)[:8]), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='rpt-card' style='background:#f9fafb;'>", unsafe_allow_html=True)
            st.markdown("<div class='rpt-box-title'>추천 도서</div>", unsafe_allow_html=True)

            if isinstance(books, list) and books:
                # 책 카드 느낌으로 쪼개서
                for b in books[:8]:
                    if isinstance(b, dict):
                        cat = _escape_html(str(b.get("분류", "") or ""))
                        title = _escape_html(str(b.get("도서", "") or ""))
                        author = _escape_html(str(b.get("저자", "") or ""))
                        why = _escape_html(str(b.get("추천 이유", "") or ""))
                        st.markdown(
                            f"""
                            <div class='rpt-card' style='margin-top:10px; box-shadow:none;'>
                              <div style='display:flex; gap:8px; align-items:center; margin-bottom:6px;'>
                                <span class='rpt-chip'>{cat}</span>
                              </div>
                              <div style='font-weight:900; font-size:14px; color:#111827;'>
                                {title} <span style='color:#6b7280; font-weight:800;'>({author})</span>
                              </div>
                              <div class='rpt-body' style='margin-top:6px;'>{why if why else '-'}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f"- {b}")
            else:
                st.markdown("<div class='rpt-body'>-</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # ---------- 영역별 심화 탐구 주제 ----------
        st.markdown(
            """
            <div class='rpt-sec-title'>
              <div class='rpt-sec-bar'></div>
              <div class='rpt-sec-text'>영역별 심화 탐구 주제 제안</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 자율/진로/동아리 3카드 느낌
        t_aut = str(topics.get("자율", "") or "") if isinstance(topics, dict) else ""
        t_car = str(topics.get("진로", "") or "") if isinstance(topics, dict) else ""
        t_clu = str(topics.get("동아리", "") or "") if isinstance(topics, dict) else ""

        st.markdown("<div class='rpt-grid-3'>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class='rpt-topic'>
              <span class='rpt-chip'>자율</span>
              <p>{_escape_html(t_aut) if t_aut else '-'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div class='rpt-topic'>
              <span class='rpt-chip'>진로</span>
              <p>{_escape_html(t_car) if t_car else '-'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div class='rpt-topic'>
              <span class='rpt-chip'>동아리</span>
              <p>{_escape_html(t_clu) if t_clu else '-'}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # ---------- 추천 학과 3박스 ----------
        st.markdown(
            """
            <div class='rpt-sec-title'>
              <div class='rpt-sec-bar'></div>
              <div class='rpt-sec-text'>역량 기반 추천 학과</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        majors_list = majors if isinstance(majors, list) else []
        st.markdown("<div class='rpt-grid-3'>", unsafe_allow_html=True)
        for i in range(3):
            if i < len(majors_list):
                m = majors_list[i]
                dept = m.get("학과", "") if isinstance(m, dict) else str(m)
                why = m.get("근거", "") if isinstance(m, dict) else ""
                st.markdown(
                    f"""
                    <div class='rpt-major-card'>
                      <div style='margin-bottom:8px;'>
                        <span class='rpt-chip rpt-chip-major'>추천 학과</span>
                      </div>
                      <div class='rpt-major-title'>{_escape_html(dept) if dept else '-'}</div>
                      <div class='rpt-major-body'>{_escape_html(why).replace('\\n','<br/>') if why else '-'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class='rpt-major-card'>
                      <div class='rpt-major-title'>-</div>
                      <div class='rpt-major-body'>-</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        st.markdown("</div>", unsafe_allow_html=True)

        # ---------- PDF 저장 ----------
        if pdf_bytes:
            st.download_button(
                "📄 PDF로 저장",
                data=pdf_bytes,
                file_name=f"SH-Insight_{sid}_{sname}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.markdown("</div>", unsafe_allow_html=True)  # rpt-wrap

    _show()
