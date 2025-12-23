# utils/report_ui.py
from __future__ import annotations

import re
from io import BytesIO
from typing import Any, Dict, Optional


def inject_report_css(st=None):
    if st is None:
        import streamlit as st  # noqa

    st.markdown(
        """
        <style>
        .rpt-wrap{ max-width: 1040px; margin: 0 auto; }

        .rpt-h1{
            text-align:center; font-size:30px; font-weight:900;
            letter-spacing:-0.5px; margin: 4px 0 10px 0; color:#111827;
        }
        .rpt-meta{
            text-align:right; font-size:13px; color:#6b7280;
            margin: 0 0 8px 0; font-weight:700;
        }
        .rpt-hr{ height:2px; background:#111827; border:none; margin: 8px 0 18px 0; }

        /* 섹션 타이틀 */
        .rpt-sec-title{
            display:flex; align-items:center; gap:10px;
            margin: 18px 0 10px 0;
        }
        .rpt-sec-bar{
            width:10px; height:22px; border-radius:8px;
            background: linear-gradient(180deg, #9ca3af, #6b7280);
            flex: 0 0 auto;
        }
        .rpt-sec-text{
            font-size:18px; font-weight:900; color:#111827; letter-spacing:-0.3px;
        }
        .rpt-sec-sub{ margin-left:auto; text-align:right; }

        /* 카드 */
        .rpt-card{
            background:#fff; border:1px solid #e5e7eb; border-radius:16px;
            padding:16px; box-shadow:0 10px 22px rgba(17,24,39,0.06);
        }
        .rpt-body{
            font-size:14px; line-height:1.75; color:#111827; word-break:keep-all;
        }
        .rpt-strong{ font-weight:900; }

        /* 칩 */
        .rpt-chip{
            display:inline-flex; align-items:center; gap:6px;
            padding:6px 10px; border-radius:999px;
            border:1px solid #e5e7eb; background:#f9fafb;
            color:#111827; font-size:12px; font-weight:900; white-space:nowrap;
        }
        .rpt-chip-major{ background:#eff6ff; border-color:#bfdbfe; color:#1d4ed8; }
        .rpt-chip-good{ background:#ecfdf5; border-color:#a7f3d0; color:#065f46; }
        .rpt-chip-need{ background:#fef2f2; border-color:#fecaca; color:#991b1b; }

        /* 추천도서 분류 칩 규칙 */
        .book-chip{ margin-bottom: 8px; }
        .book-chip.red{ background:#fef2f2; border-color:#fecaca; color:#991b1b; }
        .book-chip.green{ background:#ecfdf5; border-color:#a7f3d0; color:#065f46; }
        .book-chip.blue{ background:#eff6ff; border-color:#bfdbfe; color:#1d4ed8; }
        .book-chip.gray{ background:#f9fafb; border-color:#e5e7eb; color:#374151; }

        /* 그리드 */
        .rpt-grid-2{ display:grid; grid-template-columns: 1fr 1fr; gap:12px; }
        .rpt-grid-3{ display:grid; grid-template-columns: 1fr 1fr 1fr; gap:12px; }
        @media (max-width: 960px){
            .rpt-grid-2, .rpt-grid-3{ grid-template-columns: 1fr; }
        }

        /* 강점/보완 색 박스 */
        .rpt-colorbox{
            border-radius:16px; padding:14px; border:1px solid #e5e7eb;
        }
        .rpt-colorbox.good{ background:#ecfdf5; border-color:#a7f3d0; }
        .rpt-colorbox.bad{ background:#fef2f2; border-color:#fecaca; }
        .rpt-box-title{ font-size:15px; font-weight:900; margin:0 0 8px 0; }
        .rpt-box-title.good{ color:#065f46; }
        .rpt-box-title.bad{ color:#991b1b; }

        /* 리스트 */
        .rpt-list{ margin:10px 0 0 0; padding-left:18px; }
        .rpt-list li{ margin:6px 0; line-height:1.6; font-size:13.5px; color:#111827; }

        /* KPI 카드 */
        .rpt-kpi-head{
            display:flex; align-items:flex-end; justify-content:space-between;
            gap:10px; margin-bottom:8px;
        }
        .rpt-kpi-title{ font-size:16px; font-weight:900; color:#111827; }
        .rpt-stars{ font-size:14px; font-weight:900; color:#111827; letter-spacing:1px; white-space:nowrap; }
        .rpt-score{ font-size:12px; color:#6b7280; font-weight:900; margin-left:8px; }

        /* 근거 문장 박스 */
        .rpt-evidence{
            background:#f9fafb; border:1px solid #e5e7eb; border-radius:14px;
            padding:12px; margin:10px 0;
        }
        .rpt-evidence-title{ font-size:13px; font-weight:900; color:#374151; margin:0 0 6px 0; }

        /* 주제 박스 */
        .rpt-topic{
            background:#eff6ff; border:1px solid #bfdbfe; border-radius:16px;
            padding:14px;
        }
        .rpt-topic p{ margin:6px 0 0 0; font-size:13.5px; line-height:1.6; color:#111827; }

        /* 추천학과 카드 */
        .rpt-major-card{
            background:#fff; border:1px solid #e5e7eb; border-radius:16px;
            padding:14px; box-shadow:0 10px 22px rgba(17,24,39,0.06);
            min-height: 120px;
        }
        .rpt-major-title{ font-size:15px; font-weight:900; margin:0 0 8px 0; color:#111827; }
        .rpt-major-body{ font-size:13.5px; line-height:1.6; color:#111827; }

        /* 추천도서 카드 */
        .book-card{
            background:#fff; border:1px solid #e5e7eb; border-radius:16px;
            padding:12px; margin-top:10px;
        }
        .book-title{
            font-weight:900; font-size:14px; color:#111827;
        }
        .book-author{ color:#6b7280; font-weight:900; font-size:12px; }
        </style>
        """,
        unsafe_allow_html=True
    )


def _escape_html(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
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


def _pick_book_chip_class(category: str) -> str:
    c = (category or "").strip()
    if any(k in c for k in ["약점", "보완"]):
        return "red"
    if any(k in c for k in ["관심", "심화"]):
        return "green"
    if any(k in c for k in ["진로", "연계"]):
        return "blue"
    return "gray"


def _extract_keywords(expected_major: str, strengths: list[str], needs: list[str]) -> list[str]:
    """
    종합평가 키워드 굵게:
    - 예상 진로(학과) / 강점 / 보완 리스트에서 2~8개 키워드 뽑음
    """
    pool = []
    if expected_major:
        pool.append(expected_major)

    pool += strengths[:4]
    pool += needs[:3]

    # 너무 긴 문장형을 키워드로 쓰지 않도록 정리(짧은 명사/구 중심)
    keywords = []
    for t in pool:
        t = re.sub(r"\([^)]*\)", "", t).strip()
        t = re.split(r"[·/,:;]| - ", t)[0].strip()
        if 2 <= len(t) <= 12:
            keywords.append(t)

    # 중복 제거 + 길이 긴 것 우선(치환 안정)
    keywords = list(dict.fromkeys(keywords))
    keywords.sort(key=len, reverse=True)
    return keywords[:8]


def _highlight_keywords_html(text: str, keywords: list[str]) -> str:
    """
    HTML escape 후, 키워드만 <span class='rpt-strong'>로 강조.
    """
    escaped = _escape_html(text).replace("\n", "<br/>")
    if not keywords:
        return escaped

    for kw in keywords:
        kw_e = _escape_html(kw)
        if not kw_e:
            continue
        # 단순 replace는 오탐이 있을 수 있으나, 생활기록부 텍스트 UI 목적이면 실용적
        escaped = escaped.replace(kw_e, f"<span class='rpt-strong'>{kw_e}</span>")
    return escaped


def render_report_modal(
    st,
    report: Dict[str, Any],
    sid: str,
    sname: str,
    radar_png: Optional[BytesIO] = None,
    pdf_bytes: Optional[bytes] = None,
):
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

        # ✅ 종합평가 키워드 굵게
        keywords = _extract_keywords(expected_major, strengths, needs)
        overall_html = _highlight_keywords_html(overall if overall else "내용이 비어 있습니다.", keywords)

        st.markdown("<div class='rpt-wrap'>", unsafe_allow_html=True)

        # 헤더
        st.markdown("<div class='rpt-h1'>SH-Insight 심층 분석 보고서</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='rpt-meta'>{_escape_html(sid)} / {_escape_html(sname)}</div>", unsafe_allow_html=True)
        st.markdown("<hr class='rpt-hr'/>", unsafe_allow_html=True)

        # 종합평가
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
              <div class='rpt-body'>{overall_html}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 핵심역량 + 그래프(반드시 보이게)
        st.markdown(
            """
            <div class='rpt-sec-title'>
              <div class='rpt-sec-bar'></div>
              <div class='rpt-sec-text'>핵심 역량 분석</div>
              <div class='rpt-sec-sub'>
                <span class='rpt-chip'>학업역량 · 학업 외 소양 · 학업태도</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div class='rpt-card'>", unsafe_allow_html=True)
        if radar_png is not None:
            cL, cM, cR = st.columns([1, 1.3, 1])
            with cM:
                st.image(radar_png, width=260)
        else:
            st.warning("레이더 그래프가 생성되지 않았습니다. (점수 데이터 또는 그래프 함수 확인 필요)")
        st.markdown("</div>", unsafe_allow_html=True)

        # 강점/보완
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

        # 3대 평가
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
                      <div class='rpt-stars'>{stars}<span class='rpt-score'>({score}/10)</span></div>
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

        # 성장 제안 + 추천도서
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
            strat = str(growth.get("생활기록부 중점 보완 전략", "") or "").strip() if isinstance(growth, dict) else ""
            events = growth.get("추천 학교 행사", []) if isinstance(growth, dict) else []

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
                for b in books[:8]:
                    if isinstance(b, dict):
                        cat = str(b.get("분류", "") or "")
                        title = str(b.get("도서", "") or "")
                        author = str(b.get("저자", "") or "")
                        why = str(b.get("추천 이유", "") or "")

                        chip_cls = _pick_book_chip_class(cat)
                        st.markdown(
                            f"""
                            <div class='book-card'>
                              <div class='rpt-chip book-chip {chip_cls}'>[{_escape_html(cat) if cat else "분류"}]</div>
                              <div class='book-title'>{_escape_html(title) if title else "-"}</div>
                              <div class='book-author'>{_escape_html(author) if author else ""}</div>
                              <div class='rpt-body' style='margin-top:8px;'>{_escape_html(why).replace("\\n","<br/>") if why else "-"}</div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f"- {b}")
            else:
                st.markdown("<div class='rpt-body'>-</div>", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

        # 영역별 주제
        st.markdown(
            """
            <div class='rpt-sec-title'>
              <div class='rpt-sec-bar'></div>
              <div class='rpt-sec-text'>영역별 심화 탐구 주제 제안</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        t_aut = str(topics.get("자율", "") or "") if isinstance(topics, dict) else ""
        t_car = str(topics.get("진로", "") or "") if isinstance(topics, dict) else ""
        t_clu = str(topics.get("동아리", "") or "") if isinstance(topics, dict) else ""

        st.markdown("<div class='rpt-grid-3'>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='rpt-topic'><span class='rpt-chip'>자율</span><p>{_escape_html(t_aut) if t_aut else '-'}</p></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='rpt-topic'><span class='rpt-chip'>진로</span><p>{_escape_html(t_car) if t_car else '-'}</p></div>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<div class='rpt-topic'><span class='rpt-chip'>동아리</span><p>{_escape_html(t_clu) if t_clu else '-'}</p></div>",
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

        # 추천학과 3박스
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
                      <div class='rpt-chip rpt-chip-major'>추천 학과</div>
                      <div style='height:8px'></div>
                      <div class='rpt-major-title'>{_escape_html(dept) if dept else '-'}</div>
                      <div class='rpt-major-body'>{_escape_html(why).replace("\\n","<br/>") if why else '-'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    "<div class='rpt-major-card'><div class='rpt-major-title'>-</div><div class='rpt-major-body'>-</div></div>",
                    unsafe_allow_html=True
                )
        st.markdown("</div>", unsafe_allow_html=True)

        # PDF 저장
        if pdf_bytes:
            st.download_button(
                "📄 PDF로 저장",
                data=pdf_bytes,
                file_name=f"SH-Insight_{sid}_{sname}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

    _show()
