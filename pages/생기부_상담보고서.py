# pages/생기부_상담보고서.py
import streamlit as st
import pandas as pd

from utils.sidebar import render_sidebar
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche
from utils.ai_report_generator import generate_sh_insight_report
from utils.report_generator import build_pdf_from_report

from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ===============================
# 기본 설정
# ===============================
st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")
render_sidebar()

# ===============================
# 스타일 (가독성 중심, 예시 이미지 기반)
# ===============================
st.markdown("""
<style>
.card{
    background:#ffffff;
    border:1px solid #e5e7eb;
    border-radius:16px;
    padding:20px;
    margin:14px 0;
}
.card-title{
    font-size:17px;
    font-weight:800;
    margin-bottom:10px;
}
.summary{
    font-size:15px;
    line-height:1.7;
    color:#111827;
}
.badge{
    display:inline-block;
    padding:4px 12px;
    border-radius:999px;
    font-size:12px;
    background:#f3f4f6;
    margin-right:6px;
}
.stars{
    font-size:18px;
    color:#f59e0b;
    margin-bottom:6px;
}
.evi{
    background:#f9fafb;
    border-left:4px solid #9ca3af;
    border-radius:10px;
    padding:10px 12px;
    margin:6px 0;
    font-size:13px;
}
</style>
""", unsafe_allow_html=True)

st.title("📘 생기부 기반 상담 보고서 (SH-Insight)")

# ===============================
# 유틸
# ===============================
def render_stars(score):
    try:
        s = int(round(score))
    except:
        s = 0
    return "⭐" * (s // 2) + "☆" * (5 - s // 2)

def render_radar(scores: dict):
    labels = ["Academic", "Attitude", "Character"]
    values = [scores.get(k, 0) for k in ["학업역량","학업태도","학업 외 소양"]]
    values += values[:1]

    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(2.6,2.6), subplot_kw=dict(polar=True))
    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.15)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_ylim(0,10)

    st.pyplot(fig, use_container_width=False)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf

# ===============================
# 결과창 (🔴 여기만 UI 변경)
# ===============================
def render_report_modal(report: dict, sid: str, sname: str):
    @st.dialog(f"📊 SH-Insight 상담 보고서 · {sid} / {sname}", width="large")
    def show():

        overall = report.get("종합 평가","")
        detail = report.get("3대 평가 항목별 상세 분석",{})
        strengths = report.get("핵심 강점",[])
        needs = report.get("보완 추천 영역",[])

        # --- 요약 카드 ---
        st.markdown(
            f"""
            <div class='card'>
              <div class='card-title'>종합 요약</div>
              <div class='summary'>
                {"<br>".join(overall.split("다.")[:3])}다.
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # --- 스냅샷 ---
        c1, c2 = st.columns([1,1.4])

        with c1:
            st.markdown("<div class='card'><div class='card-title'>역량 스냅샷</div>", unsafe_allow_html=True)
            scores = {k:v.get("점수",0) for k,v in detail.items()}
            radar_png = render_radar(scores)
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("<div class='card'><div class='card-title'>핵심 지표</div>", unsafe_allow_html=True)
            for k,v in detail.items():
                st.markdown(
                    f"<div class='stars'>{render_stars(v.get('점수',0))} {k} ({v.get('점수',0)}/10)</div>",
                    unsafe_allow_html=True
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # --- 상세 분석 (접기) ---
        for k,v in detail.items():
            with st.expander(f"📌 {k} 자세히 보기"):
                st.write(v.get("분석",""))
                st.markdown("**평가 근거**")
                for e in v.get("평가 근거 문장",[])[:5]:
                    st.markdown(f"<div class='evi'>{e}</div>", unsafe_allow_html=True)

        # --- 강점 / 보완 ---
        st.markdown("<div class='card'><div class='card-title'>핵심 강점</div>", unsafe_allow_html=True)
        for s in strengths:
            st.markdown(f"- {s}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='card'><div class='card-title'>보완 추천 영역</div>", unsafe_allow_html=True)
        for n in needs:
            st.markdown(f"- {n}")
        st.markdown("</div>", unsafe_allow_html=True)

        # --- PDF ---
        pdf = build_pdf_from_report(report, radar_png, sid, sname)
        st.download_button("📄 PDF로 저장", pdf, file_name=f"SH-Insight_{sid}.pdf")

    show()
