import streamlit as st
import pandas as pd

from utils.sidebar import render_sidebar
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche
from utils.ai_report_generator import generate_sh_insight_report

from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import numpy as np

st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")
render_sidebar()

# =========================================================
# ✅ UI 전용 CSS (기존 기능 영향 없음)
# =========================================================
st.markdown("""
<style>
.report-card{
    background:#ffffff;
    border:1px solid #e5e7eb;
    border-radius:14px;
    padding:20px 22px;
    margin-bottom:18px;
}
.report-title{
    font-size:18px;
    font-weight:700;
    margin-bottom:10px;
    color:#111827;
}
.report-text{
    font-size:14px;
    line-height:1.7;
    color:#374151;
}
.good-box{
    background:#f0fdf4;
    border:1px solid #bbf7d0;
    border-radius:10px;
    padding:12px;
}
.bad-box{
    background:#fef2f2;
    border:1px solid #fecaca;
    border-radius:10px;
    padding:12px;
}
.evidence{
    background:#f9fafb;
    border-left:4px solid #9ca3af;
    padding:10px 14px;
    margin:8px 0;
    font-size:13px;
}
.stars{
    color:#f59e0b;
    font-size:18px;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# ✅ UI 전용 함수 (기존 로직 무관)
# =========================================================

def render_stars(score_10: int):
    stars = round(score_10 / 2)
    return "⭐" * stars + "☆" * (5 - stars)


def render_radar_chart(scores: dict):
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    font_manager.fontManager.addfont(font_path)
    rc("font", family="NanumGothic")

    labels = ["학업역량", "학업태도", "학업 외 소양"]
    values = [scores.get(k, 0) for k in labels]
    values += values[:1]

    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(3.4, 3.4))
    ax = fig.add_subplot(111, polar=True)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels)
    ax.set_ylim(0, 10)

    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.15)

    st.pyplot(fig, clear_figure=True)

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


# =========================================================
# ⬇️⬇️⬇️
# ⬇️ 기존 코드 전체 그대로 ⬇️
# ⬇️ (파일 업로드 / 명렬 / AI 호출 등) ⬇️
# =========================================================
# ⚠️ 여기 아래는 당신의 기존 코드 그대로 두세요
# ⚠️ 단, 아래 “render_report_modal” 함수만 교체
# =========================================================

def render_report_modal(report: dict, sid: str, sname: str):
    @st.dialog(f"📊 SH-Insight 심층 분석 보고서 · {sid} / {sname}", width="large")
    def _show():

        overall = report.get("종합 평가","")
        strengths = report.get("핵심 강점",[])
        needs = report.get("보완 추천 영역",[])
        detail = report.get("3대 평가 항목별 상세 분석",{})

        st.markdown(f"""
        <div class="report-card">
            <div class="report-title">종합 평가</div>
            <div class="report-text">{overall}</div>
        </div>
        """, unsafe_allow_html=True)

        # 레이더 차트
        scores = {k:v.get("점수",0) for k,v in detail.items() if isinstance(v,dict)}
        st.markdown('<div class="report-card"><div class="report-title">핵심 역량</div>', unsafe_allow_html=True)
        radar_png = render_radar_chart(scores)
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="report-card"><div class="report-title">핵심 강점</div><div class="good-box">', unsafe_allow_html=True)
            for s in strengths:
                st.markdown(f"- {s}")
            st.markdown('</div></div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="report-card"><div class="report-title">보완 추천 영역</div><div class="bad-box">', unsafe_allow_html=True)
            for s in needs:
                st.markdown(f"- {s}")
            st.markdown('</div></div>', unsafe_allow_html=True)

        for k, v in detail.items():
            if not isinstance(v, dict):
                continue

            st.markdown(f"""
            <div class="report-card">
                <div class="report-title">{k}</div>
                <div class="stars">{render_stars(v.get("점수",0))}</div>
                <div class="report-text">{v.get("분석","")}</div>
            """, unsafe_allow_html=True)

            for e in v.get("평가 근거 문장",[])[:5]:
                st.markdown(f'<div class="evidence">{e}</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

    _show()
