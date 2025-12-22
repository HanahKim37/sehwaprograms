def inject_report_css(st):
    st.markdown(
        """
        <style>
        .report-title{ text-align:center; font-size:38px; font-weight:800; margin:10px 0 12px 0; }
        .report-meta{ text-align:right; font-size:16px; color:#374151; margin:4px 0 6px 0; }
        .report-hr{ border:none; border-top:2px solid #111827; margin:10px 0 18px 0; }
        .section-title{ display:flex; align-items:center; gap:10px; font-size:24px; font-weight:800; margin:18px 0 10px 0; }
        .section-bar{ width:6px; height:22px; border-radius:3px; background:#9CA3AF; }
        .badge{ display:inline-block; padding:6px 10px; border-radius:999px; border:1px solid #E5E7EB; background:#F9FAFB;
                font-size:13px; font-weight:700; color:#374151; margin-left:6px; }
        .box{ background:#fff; border:1px solid #E5E7EB; border-radius:16px; padding:18px; margin:10px 0 16px 0;
              box-shadow:0 1px 2px rgba(0,0,0,0.04); line-height:1.85; font-size:16px; white-space:pre-wrap; word-break:keep-all; }
        </style>
        """,
        unsafe_allow_html=True
    )


def _esc(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace("\n", "<br/>")
    )


def render_report_modal(st, report: dict, sid: str, sname: str, radar_png, pdf_bytes: bytes | None):
    majors = report.get("역량 기반 추천 학과", [])
    hope = ""
    if isinstance(majors, list) and majors:
        hope = str(majors[0].get("학과", "") if isinstance(majors[0], dict) else majors[0]).strip()
    hope = hope if hope else "미기재"

    @st.dialog("SH-Insight 심층 분석 보고서", width="large")
    def show():
        st.markdown("<div class='report-title'>SH-Insight 심층 분석 보고서</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='report-meta'>{_esc(sid)} / {_esc(sname)}</div>", unsafe_allow_html=True)
        st.markdown("<hr class='report-hr'/>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div class='section-title'>
              <span class='section-bar'></span>
              <span>종합 평가 <span class='badge'>예상 희망 진로: {_esc(hope)}</span></span>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(f"<div class='box'>{_esc(report.get('종합 평가','') or '')}</div>", unsafe_allow_html=True)

        st.markdown(
            "<div class='section-title'><span class='section-bar'></span><span>핵심 역량 분석</span></div>",
            unsafe_allow_html=True
        )

        # 레이더는 호출 측에서 이미 st.pyplot로 출력했을 수 있으므로,
        # 여기서는 '이미지 표시'만 원하면 st.image(radar_png)로도 가능.
        if radar_png:
            st.image(radar_png, width=320)

        if pdf_bytes:
            st.download_button(
                "📄 PDF로 저장",
                data=pdf_bytes,
                file_name=f"SH-Insight_{sid}_{sname}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    show()
