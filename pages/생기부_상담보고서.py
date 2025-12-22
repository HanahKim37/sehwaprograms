import streamlit as st
import pandas as pd

from utils.sidebar import render_sidebar
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche
from utils.ai_report_generator import generate_sh_insight_report

from io import BytesIO
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import numpy as np

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ===============================
# 기본 설정
# ===============================
st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")
render_sidebar()

# ===============================
# 스타일 (결과창 UI만 개선)
# ===============================
st.markdown("""
<style>
div[data-testid="stDataEditor"]{
    margin-left:auto;
    margin-right:auto;
    max-width:900px;
}
.card{
    background:#ffffff;
    border:1px solid #e5e7eb;
    border-radius:16px;
    padding:20px;
    margin:14px 0;
}
.card-title{
    font-size:18px;
    font-weight:700;
    margin-bottom:10px;
    color:#111827;
}
.card-text{
    font-size:14px;
    line-height:1.7;
    color:#374151;
}
.pill-good{
    background:#f0fdf4;
    border:1px solid #bbf7d0;
    border-radius:12px;
    padding:12px;
}
.pill-bad{
    background:#fef2f2;
    border:1px solid #fecaca;
    border-radius:12px;
    padding:12px;
}
.stars{
    font-size:18px;
    color:#f59e0b;
    margin-bottom:6px;
}
.evidence{
    background:#f9fafb;
    border-left:4px solid #9ca3af;
    border-radius:8px;
    padding:10px 12px;
    margin:6px 0;
    font-size:13px;
    color:#374151;
}
</style>
""", unsafe_allow_html=True)

st.title("📘 생기부 기반 상담 보고서 (SH-Insight)")
st.markdown("세특·행특·창체 파일을 업로드하고 학생을 선택해 상담 보고서를 생성합니다.")

# ===============================
# 유틸 함수 (기존 로직 유지)
# ===============================
def get_id_col(df: pd.DataFrame) -> str:
    for c in ["번호", "학번", "학생번호", "student_id", "ID"]:
        if c in df.columns:
            return c
    return "번호"

def normalize_id_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()

def extract_text(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return ""
    drop_cols = {"번호", "학번", "학생번호", "성명", "이름", "학년", "반", "담임", "과목"}
    cols = [c for c in df.columns if c not in drop_cols]
    texts = []
    for c in cols:
        if pd.api.types.is_object_dtype(df[c]):
            texts += df[c].dropna().astype(str).tolist()
    return "\n".join(texts)

def calc_year_count(*dfs):
    years = set()
    for df in dfs:
        if "학년" in df.columns:
            years.update(df["학년"].dropna().astype(str).tolist())
    return len(years)

# ===============================
# 별점 / 레이더
# ===============================
def render_stars(score):
    try:
        score = int(score)
    except:
        score = 0
    return "⭐" * round(score/2) + "☆" * (5 - round(score/2))

def render_radar_chart(scores: dict):
    try:
        font_manager.fontManager.addfont("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")
        rc("font", family="NanumGothic")
    except:
        pass

    labels = ["학업역량", "학업태도", "학업 외 소양"]
    values = [scores.get(k, 0) for k in labels]
    values += values[:1]

    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(3.2, 3.2))
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(np.pi/2)
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

# ===============================
# PDF
# ===============================
def build_pdf_bytes(report: dict, radar_png: BytesIO, sid: str, sname: str) -> bytes:
    buf = BytesIO()
    pdfmetrics.registerFont(TTFont("Nanum", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"))
    styles = getSampleStyleSheet()
    for s in styles.byName.values():
        s.fontName = "Nanum"

    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=16*mm, rightMargin=16*mm,
        topMargin=16*mm, bottomMargin=16*mm)

    story = []
    story.append(Paragraph("SH-Insight 심층 분석 보고서", styles["Title"]))
    story.append(Paragraph(f"{sid} / {sname}", styles["Normal"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("종합 평가", styles["Heading2"]))
    story.append(Paragraph(report.get("종합 평가",""), styles["BodyText"]))
    story.append(Spacer(1, 10))

    if radar_png:
        story.append(Paragraph("핵심 역량", styles["Heading2"]))
        story.append(RLImage(radar_png, width=110*mm, height=100*mm))
        story.append(Spacer(1, 10))

    for k, v in report.get("3대 평가 항목별 상세 분석", {}).items():
        story.append(Paragraph(f"{k} ({v.get('점수',0)}/10)", styles["Heading3"]))
        story.append(Paragraph(v.get("분석",""), styles["BodyText"]))
        for e in v.get("평가 근거 문장", [])[:5]:
            story.append(Paragraph(f"- {e}", styles["BodyText"]))
        story.append(Spacer(1, 8))

    doc.build(story)
    return buf.getvalue()

# ===============================
# 파일 업로드 / 명렬 / 생성
# ===============================
st.header("1️⃣ 파일 업로드")
uploaded_files = st.file_uploader(
    "세특·행특·창체 파일 3개 업로드",
    type=["xlsx"],
    accept_multiple_files=True,
)

file_seteuk = file_haeng = file_chang = None
if uploaded_files:
    for f in uploaded_files:
        if "세특" in f.name: file_seteuk = f
        elif "행특" in f.name: file_haeng = f
        elif "창체" in f.name: file_chang = f

if st.button("📋 명렬 보기"):
    df_seteuk = load_seteuk(file_seteuk)
    df_haeng = load_haengteuk(file_haeng)
    df_chang = load_changche(file_chang)

    for df in (df_seteuk, df_haeng, df_chang):
        df[get_id_col(df)] = normalize_id_series(df[get_id_col(df)])

    frames = []
    for df in (df_seteuk, df_haeng, df_chang):
        frames.append(df[[get_id_col(df), "성명"]])

    df_students = pd.concat(frames).drop_duplicates()
    df_students = df_students[df_students[get_id_col(df_students)].str.isdigit()]

    df_students["성명"] = df_students["성명"].apply(lambda x: x[0]+"ㅇ"+x[-1])
    st.session_state["students_table"] = pd.DataFrame({
        "선택": False,
        "학번": df_students[get_id_col(df_students)],
        "성명": df_students["성명"]
    })

    st.session_state["df_seteuk"] = df_seteuk
    st.session_state["df_haeng"] = df_haeng
    st.session_state["df_chang"] = df_chang

if "students_table" in st.session_state:
    edited = st.data_editor(st.session_state["students_table"], hide_index=True)
    st.session_state["students_table"] = edited

    if st.button("🧠 선택 학생 보고서 생성"):
        for _, r in edited[edited["선택"]].iterrows():
            sid = r["학번"]
            sname = r["성명"]

            report = generate_sh_insight_report(
                student_id=sid,
                masked_name=sname,
                year_count=3,
                seteuk_text=extract_text(st.session_state["df_seteuk"]),
                haengteuk_text=extract_text(st.session_state["df_haeng"]),
                changche_text=extract_text(st.session_state["df_chang"]),
            )

            @st.dialog(f"📊 SH-Insight 심층 분석 보고서 · {sid} / {sname}", width="large")
            def show():
                st.markdown(f"<div class='card'><div class='card-title'>종합 평가</div><div class='card-text'>{report.get('종합 평가','')}</div></div>", unsafe_allow_html=True)

                scores = {k:v.get("점수",0) for k,v in report.get("3대 평가 항목별 상세 분석",{}).items()}
                radar_png = render_radar_chart(scores)

                for k, v in report.get("3대 평가 항목별 상세 분석",{}).items():
                    st.markdown(f"<div class='card'><div class='card-title'>{k}</div><div class='stars'>{render_stars(v.get('점수',0))}</div><div class='card-text'>{v.get('분석','')}</div></div>", unsafe_allow_html=True)

                pdf = build_pdf_bytes(report, radar_png, sid, sname)
                st.download_button("📄 PDF로 저장", pdf, file_name=f"{sid}.pdf")

            show()
