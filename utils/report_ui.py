from __future__ import annotations

import streamlit as st

from utils.report_chart import build_radar_png


def inject_report_css():
    st.markdown(
        """
        <style>
        .report-wrap { max-width: 980px; margin: 0 auto; }
        .report-title { text-align:center; font-size:34px; font-weight:800; margin: 12px 0 6px 0; }
        .report-meta { text-align:right; font-size:14px; color:#6b7280; margin: 0 0 10px 0; }
        .divider { border-top:1px solid #e5e7eb; margin: 8px 0 18px 0; }

        .section-title {
            display:flex; align-items:center; gap:10px;
            font-size:20px; font-weight:800; margin: 18px 0 10px 0;
        }
        .dot {
            width:12px; height:12px; border-radius:4px;
            background:#111827; display:inline-block;
        }

        .box {
            background:#ffffff; border:1px solid #e5e7eb; border-radius:16px;
            padding:16px 18px; box-shadow:0 1px 2px rgba(0,0,0,0.04);
            margin-bottom:14px;
        }

        .two-col { display:flex; gap:14px; }
        .col { flex:1; }

        .pill-good, .pill-bad {
            border-radius:14px; padding:14px 14px; border:1px solid;
        }
        .pill-good { background:#dcfce7; border-color:#86efac; }
        .pill-bad { background:#fee2e2; border-color:#fca5a5; }

        .tiny-box {
            background:#f8fafc; border:1px solid #e5e7eb; border-radius:12px;
            padding:12px 12px; font-size:14px;
        }

        .rating { font-size:18px; letter-spacing:1px; }
        .muted { color:#6b7280; }

        .tag {
            display:inline-block; font-size:12px; padding:4px 8px;
            border-radius:999px; border:1px solid #e5e7eb; background:#f9fafb;
            margin-right:6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _stars(score_0_10):
    try:
        s = int(round(float(score_0_10)))
    except Exception:
        s = 0
    s = max(0, min(10, s))
    return "★" * s + "☆" * (10 - s)


def _safe_get(d, key, default):
    if isinstance(d, dict):
        return d.get(key, default)
    return default


def render_report_modal(report: dict, sid: str, sname: str, pdf_bytes: bytes | None = None):
    """
    - report: generate_sh_insight_report() 결과 dict
    - sid/sname: 표시용
    - pdf_bytes: 있으면 다운로드 버튼 제공
    """

    @st.dialog("SH-Insight 심층 분석 보고서", width="large")
    def _show():
        inject_report_css()

        # -------------------------
        # 헤더
        # -------------------------
        st.markdown("<div class='report-wrap'>", unsafe_allow_html=True)
        st.markdown("<div class='report-title'>SH-Insight 심층 분석 보고서</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='report-meta'>{sid} / {sname}</div>", unsafe_allow_html=True)
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

        # -------------------------
        # 종합 평가 + 희망진로(모델이 없으면 자동 문구)
        # -------------------------
        overall = _safe_get(report, "종합 평가", "")
        hope_major = ""
        # 모델이 따로 주는 경우도 있고 없을 수도 있어 가드
        student_info = _safe_get(report, "학생 정보", {})
        if isinstance(student_info, dict):
            hope_major = student_info.get("예상 희망 진로", "") or student_info.get("희망 진로", "")

        st.markdown(
            "<div class='section-title'><span class='dot'></span><span>종합 평가</span>"
            + (f"<span class='muted' style='margin-left:auto;'>예상 희망 진로: {hope_major}</span>" if hope_major else "")
            + "</div>",
            unsafe_allow_html=True
        )
        st.markdown(f"<div class='box'>{overall}</div>", unsafe_allow_html=True)

        # -------------------------
        # 레이더(작게, 중앙)
        # -------------------------
        detail = _safe_get(report, "3대 평가 항목별 상세 분석", {})
        scores = {}
        if isinstance(detail, dict):
            for key in ["학업역량", "학업태도", "학업 외 소양"]:
                v = detail.get(key, {})
                if isinstance(v, dict):
                    scores[key] = v.get("점수", 0)

        st.markdown("<div class='section-title'><span class='dot'></span><span>핵심 역량</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='box'>", unsafe_allow_html=True)
        # radar png (PDF용)도 여기서 만들어둠
        radar_png = build_radar_png(scores)
        # Streamlit에 표시 (작게)
        st.image(radar_png.getvalue(), use_container_width=False, width=360)
        st.markdown("</div>", unsafe_allow_html=True)

        # -------------------------
        # 핵심 강점 / 보완
        # -------------------------
        strengths = _safe_get(report, "핵심 강점", [])
        needs = _safe_get(report, "보완 추천 영역", [])

        st.markdown("<div class='two-col'>", unsafe_allow_html=True)
        st.markdown("<div class='col'><div class='pill-good'><b>핵심 강점</b><br><br>", unsafe_allow_html=True)
        if isinstance(strengths, list) and strengths:
            for x in strengths:
                st.markdown(f"- {x}")
        else:
            st.markdown("- (내용 없음)")
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown("<div class='col'><div class='pill-bad'><b>보완 추천 영역</b><br><br>", unsafe_allow_html=True)
        if isinstance(needs, list) and needs:
            for x in needs:
                st.markdown(f"- {x}")
        else:
            st.markdown("- (내용 없음)")
        st.markdown("</div></div></div>", unsafe_allow_html=True)

        # -------------------------
        # 3대 평가 항목(섹션화 + 별점 + 근거 박스)
        # -------------------------
        st.markdown("<div class='section-title'><span class='dot'></span><span>3대 평가 항목별 상세 분석</span></div>", unsafe_allow_html=True)

        if isinstance(detail, dict) and detail:
            for k in ["학업역량", "학업태도", "학업 외 소양"]:
                v = detail.get(k, {})
                if not isinstance(v, dict):
                    continue

                score = v.get("점수", 0)
                evidence = v.get("평가 근거 문장", [])
                analysis = v.get("분석", "")

                st.markdown("<div class='box'>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='display:flex; align-items:center; justify-content:space-between;'>"
                    f"<div style='font-size:18px; font-weight:800;'>{k}</div>"
                    f"<div class='rating'>{_stars(score)} <span class='muted'>({score}/10)</span></div>"
                    f"</div>",
                    unsafe_allow_html=True
                )

                # 근거 문장 박스
                st.markdown("<div class='tiny-box'><b>평가 근거 문장</b><br>", unsafe_allow_html=True)
                if isinstance(evidence, list) and evidence:
                    for e in evidence[:6]:
                        st.markdown(f"- {e}")
                else:
                    st.markdown("- (근거 문장 없음)")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<br><b>분석</b>", unsafe_allow_html=True)
                st.write(analysis if analysis else "(분석 내용 없음)")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='box'>(상세 분석 데이터가 없습니다)</div>", unsafe_allow_html=True)

        # -------------------------
        # 영역별 심화 탐구 주제 제안
        # -------------------------
        topics = _safe_get(report, "영역별 심화 탐구 주제 제안", {})
        st.markdown("<div class='section-title'><span class='dot'></span><span>영역별 심화 탐구 주제 제안</span></div>", unsafe_allow_html=True)
        if isinstance(topics, dict) and topics:
            st.markdown("<div class='two-col'>", unsafe_allow_html=True)
            for key in ["자율", "진로", "동아리"]:
                val = topics.get(key, "")
                st.markdown(f"<div class='col'><div class='box'><span class='tag'>{key}</span><br><br>{val}</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='box'>(탐구 주제 제안 데이터가 없습니다)</div>", unsafe_allow_html=True)

        # -------------------------
        # 성장 제안(왼쪽) + 추천 도서(오른쪽)
        # -------------------------
        growth = _safe_get(report, "맞춤형 성장 제안", {})
        books = _safe_get(report, "추천 도서", [])

        st.markdown("<div class='section-title'><span class='dot'></span><span>맞춤형 성장 제안 & 추천 도서</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='two-col'>", unsafe_allow_html=True)

        # 왼쪽
        st.markdown("<div class='col'><div class='box'><b>생활기록부 중점 보완 전략</b><br><br>", unsafe_allow_html=True)
        strat = _safe_get(growth, "생활기록부 중점 보완 전략", "")
        st.write(strat if strat else "(내용 없음)")
        st.markdown("<br><b>추천 학교 행사</b><br>", unsafe_allow_html=True)
        evs = _safe_get(growth, "추천 학교 행사", [])
        if isinstance(evs, list) and evs:
            for e in evs:
                st.markdown(f"- {e}")
        else:
            st.markdown("- (내용 없음)")
        st.markdown("</div></div>", unsafe_allow_html=True)

        # 오른쪽 (도서)
        st.markdown("<div class='col'><div class='box'><b>추천 도서</b><br><br>", unsafe_allow_html=True)
        if isinstance(books, list) and books:
            for b in books:
                if isinstance(b, dict):
                    cat = b.get("분류", "")
                    title = b.get("도서", "")
                    author = b.get("저자", "")
                    reason = b.get("추천 이유", "")
                    st.markdown(f"<span class='tag'>{cat}</span> <b>{title}</b> <span class='muted'>({author})</span>", unsafe_allow_html=True)
                    st.write(reason)
                    st.markdown("<hr style='border:none;border-top:1px solid #eef2f7;margin:10px 0;'>", unsafe_allow_html=True)
                else:
                    st.markdown(f"- {b}")
        else:
            st.markdown("(도서 추천 없음)")
        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)  # two-col end

        # -------------------------
        # 역량 기반 추천 학과(3박스)
        # -------------------------
        majors = _safe_get(report, "역량 기반 추천 학과", [])
        st.markdown("<div class='section-title'><span class='dot'></span><span>역량 기반 추천 학과</span></div>", unsafe_allow_html=True)
        if isinstance(majors, list) and majors:
            st.markdown("<div class='two-col'>", unsafe_allow_html=True)
            # 3개까지만 시각적으로 정리
            top3 = majors[:3]
            for m in top3:
                if isinstance(m, dict):
                    st.markdown(
                        f"<div class='col'><div class='box'><b>{m.get('학과','')}</b><br><br>{m.get('근거','')}</div></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"<div class='col'><div class='box'>{m}</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='box'>(추천 학과 데이터가 없습니다)</div>", unsafe_allow_html=True)

        # PDF 다운로드 버튼
        if pdf_bytes:
            st.download_button(
                "📄 PDF로 저장",
                data=pdf_bytes,
                file_name=f"SH-Insight_{sid}_{sname}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)  # wrap end

    _show()
