import streamlit as st
import pandas as pd

from utils.sidebar import render_sidebar
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche
from utils.ai_report_generator import generate_sh_insight_report

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")
render_sidebar()

# -----------------------------
# 스타일
# -----------------------------
st.markdown("""
<style>
.card {
    background-color:#f8fafc;
    border-radius:12px;
    padding:20px;
    margin-bottom:20px;
    border:1px solid #e5e7eb;
}
.card-title {
    font-size:20px;
    font-weight:700;
    margin-bottom:10px;
}
.bad {
    background:#fee2e2;
    padding:10px;
    border-radius:10px;
}
.good {
    background:#dcfce7;
    padding:10px;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

st.title("📘 생기부 기반 상담 보고서 (SH-Insight)")

# -----------------------------
# 1️⃣ 파일 업로드
# -----------------------------
uploaded_files = st.file_uploader(
    "세특·행특·창체 파일 업로드",
    type=["xlsx"],
    accept_multiple_files=True
)

file_seteuk = file_haeng = file_chang = None
if uploaded_files:
    for f in uploaded_files:
        if "세특" in f.name:
            file_seteuk = f
        elif "행특" in f.name:
            file_haeng = f
        elif "창체" in f.name:
            file_chang = f

# -----------------------------
# 2️⃣ 명렬 생성
# -----------------------------
if st.button("📋 명렬 보기"):

    df_seteuk = load_seteuk(file_seteuk)
    df_haeng = load_haengteuk(file_haeng)
    df_chang = load_changche(file_chang)

    for df in (df_seteuk, df_haeng, df_chang):
        df["번호"] = df["번호"].astype(str)

    df_students = (
        pd.concat([df_seteuk[["번호","성명"]],
                   df_haeng[["번호","성명"]],
                   df_chang[["번호","성명"]]])
        .drop_duplicates()
    )

    st.session_state["students_table"] = pd.DataFrame({
        "선택": False,
        "학번": df_students["번호"],
        "성명": df_students["성명"].apply(lambda x: x[0]+"ㅇ"+x[-1])
    })

    st.session_state["df_seteuk"] = df_seteuk
    st.session_state["df_haeng"] = df_haeng
    st.session_state["df_chang"] = df_chang

# -----------------------------
# 3️⃣ 명렬 표시
# -----------------------------
if "students_table" in st.session_state:

    edited = st.data_editor(
        st.session_state["students_table"],
        hide_index=True
    )
    st.session_state["students_table"] = edited

    selected = edited[edited["선택"]]

    if st.button("🧠 선택 학생 보고서 생성"):

        sid = selected.iloc[0]["학번"]
        sname = selected.iloc[0]["성명"]

        report = generate_sh_insight_report(
            student_id=sid,
            masked_name=sname,
            year_count=3,
            seteuk_text="",
            haengteuk_text="",
            changche_text=""
        )

        st.session_state["active_report"] = report

# -----------------------------
# 🔥 보고서 새 창 (모달)
# -----------------------------
if "active_report" in st.session_state:

    @st.dialog("📊 SH-Insight 심층 분석 보고서", width="large")
    def show_report():

        r = st.session_state["active_report"]

        st.markdown("### 종합 평가")
        st.markdown(f"<div class='card'>{r['종합 평가']}</div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("<div class='card good'><b>핵심 강점</b>", unsafe_allow_html=True)
            for item in r["핵심 강점"]:
                st.markdown(f"- {item}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='card bad'><b>보완 영역</b>", unsafe_allow_html=True)
            for item in r["보완 영역"]:
                st.markdown(f"- {item}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 평가 항목별 분석")
        for k, v in r["평가 항목"].items():
            st.markdown(f"<div class='card'><b>{k}</b><br>{v}</div>", unsafe_allow_html=True)

    show_report()
