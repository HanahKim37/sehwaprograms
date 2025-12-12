import streamlit as st
import pandas as pd

from utils.sidebar import render_sidebar
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche
from utils.text_builder import build_text
from utils.ai_report_generator import generate_sh_insight_report

st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")
render_sidebar()

st.title("📘 SH-Insight 생기부 기반 상담 보고서")

# -----------------------------
# 파일 업로드
# -----------------------------
uploaded_files = st.file_uploader(
    "세특·행특·창체 파일 3개 업로드",
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
# 명렬 보기
# -----------------------------
if st.button("📋 명렬 보기"):
    if not all([file_seteuk, file_haeng, file_chang]):
        st.error("세특·행특·창체 파일을 모두 업로드하세요.")
        st.stop()

    df_seteuk = load_seteuk(file_seteuk)
    df_haeng = load_haengteuk(file_haeng)
    df_chang = load_changche(file_chang)

    frames = []
    for df in [df_seteuk, df_haeng, df_chang]:
        if {"번호", "성명"}.issubset(df.columns):
            df["번호"] = df["번호"].astype(str).str.strip()
            frames.append(df[["번호", "성명"]])

    df_students = (
        pd.concat(frames)
        .drop_duplicates()
        .query("번호.str.isdigit()", engine="python")
    )

    df_students["성명"] = df_students["성명"].apply(
        lambda x: x[0] + "ㅇ" + x[-1] if len(x) >= 3 else x
    )

    st.session_state["students"] = df_students

# -----------------------------
# 명렬 출력 (가운데 정렬)
# -----------------------------
if "students" in st.session_state:

    styled = (
        st.session_state["students"]
        .style
        .set_properties(**{"text-align": "center"})
    )

    st.dataframe(styled, width=600)

    selected_id = st.selectbox(
        "보고서 생성 학생 선택",
        st.session_state["students"]["번호"]
    )

    if st.button("🧠 보고서 생성"):

        stu_seteuk = df_seteuk[df_seteuk["번호"] == selected_id]
        stu_haeng = df_haeng[df_haeng["번호"] == selected_id]
        stu_chang = df_chang[df_chang["번호"] == selected_id]

        seteuk_text = build_text(stu_seteuk)
        haeng_text = build_text(stu_haeng)
        chang_text = build_text(stu_chang)

        report = generate_sh_insight_report(
            student_id=selected_id,
            masked_name=st.session_state["students"]
                .query("번호 == @selected_id")["성명"].iloc[0],
            year_count=3,
            seteuk_text=seteuk_text,
            haengteuk_text=haeng_text,
            changche_text=chang_text,
        )

        st.session_state["report"] = report
        st.success("SH-Insight 보고서 생성 완료")

# -----------------------------
# 보고서 출력 (다음 단계)
# -----------------------------
if "report" in st.session_state:
    st.subheader("📄 생성된 SH-Insight 보고서 (JSON)")
    st.json(st.session_state["report"])
