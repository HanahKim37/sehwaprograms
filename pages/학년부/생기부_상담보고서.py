import streamlit as st
import pandas as pd
from utils.parser_changche import load_changche
from utils.parser_haengteuk import load_haengteuk
from utils.parser_seteuk import load_seteuk
from utils.report_generator import generate_report_pdf, generate_report_text

st.set_page_config(page_title="생기부 상담 보고서", layout="wide")

st.title("📘 생기부 기반 상담 보고서 생성기")

st.markdown("""
학생의 **세특·행특·창체**를 기반으로  
자동으로 상담 보고서를 생성하는 시스템입니다.
---
""")

# -----------------------------
# 1. 파일 업로드 영역
# -----------------------------
st.header("1️⃣ 파일 업로드")

col1, col2, col3 = st.columns(3)

with col1:
    file_seteuk = st.file_uploader("세특 파일 업로드", type=["xlsx"])

with col2:
    file_haeng = st.file_uploader("행동특성 파일 업로드", type=["xlsx"])

with col3:
    file_chang = st.file_uploader("창체 파일 업로드", type=["xlsx"])


# -----------------------------
# 2. 파일 분석 버튼
# -----------------------------
if st.button("📊 데이터 분석 시작"):

    if not file_seteuk or not file_haeng or not file_chang:
        st.error("세특·행특·창체 파일을 모두 업로드해주세요.")
        st.stop()

    with st.spinner("데이터 분석 중입니다…"):

        df_seteuk = load_seteuk(file_seteuk)
        df_haeng = load_haengteuk(file_haeng)
        df_chang = load_changche(file_chang)

        # 학생 리스트 생성
        df_students = (
            df_seteuk[["번호", "성명"]]
            .drop_duplicates()
            .reset_index(drop=True)
        )

        # 이름 마스킹
        df_students["마스킹이름"] = df_students["성명"].apply(
            lambda x: x[0] + "ㅇ" + x[-1] if len(x) >= 3 else x
        )

        st.success("데이터 분석이 완료되었습니다!")

        st.subheader("📋 학생 명단")

        # 표시할 테이블
        st.dataframe(df_students[["번호", "마스킹이름"]])


        # 학생 선택
        selected_no = st.selectbox(
            "보고서를 생성할 학생 번호를 선택하세요.",
            df_students["번호"].unique()
        )

        student_name = df_students[df_students["번호"] == selected_no]["성명"].iloc[0]
        masked_name = df_students[df_students["번호"] == selected_no]["마스킹이름"].iloc[0]

        # 학생 데이터 필터링
        stu_seteuk = df_seteuk[df_seteuk["번호"] == selected_no]
        stu_haeng = df_haeng[df_haeng["번호"] == selected_no]
        stu_chang = df_chang[df_chang["번호"] == selected_no]


        # -----------------------------
        # 3. 1개년 이상 여부 확인
        # -----------------------------
        years = set()

        if "학년" in stu_seteuk:
            years.update(stu_seteuk["학년"].dropna().unique())

        if "학년" in stu_haeng:
            years.update(stu_haeng["학년"].dropna().unique())

        if "학년" in stu_chang:
            years.update(stu_chang["학년"].dropna().unique())

        if len(years) < 2:
            st.error("⚠️ 1개년 이상의 기록이 없어 보고서를 생성할 수 없습니다.")
            st.stop()


        # -----------------------------
        # 4. 보고서 생성
        # -----------------------------
        st.header("📄 보고서 생성")

        if st.button("🧠 AI 상담 보고서 만들기"):

            with st.spinner("보고서를 생성하고 있습니다…"):

                report_text = generate_report_text(
                    name=masked_name,
                    number=selected_no,
                    df_seteuk=stu_seteuk,
                    df_haeng=stu_haeng,
                    df_chang=stu_chang
                )

                pdf_bytes = generate_report_pdf(report_text)

            st.success("보고서가 생성되었습니다!")

            st.download_button(
                label="📥 PDF 다운로드",
                data=pdf_bytes,
                file_name=f"{selected_no}_{masked_name}_상담보고서.pdf",
                mime="application/pdf"
            )

            st.text_area("생성된 보고서 미리보기", report_text, height=400)
