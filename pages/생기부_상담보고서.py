import streamlit as st
import pandas as pd

# -----------------------------
# 공통 사이드바
# -----------------------------
from utils.sidebar import render_sidebar
render_sidebar()

# -----------------------------
# 데이터 파서
# -----------------------------
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche


st.set_page_config(
    page_title="생기부 기반 상담보고서",
    layout="wide",
)

st.title("📘 생기부 기반 상담 보고서")

st.markdown("""
세특·행특·창체 파일을 업로드하면  
학생별 상담 보고서를 자동으로 생성합니다.
""")

# -----------------------------
# 1. 파일 업로드
# -----------------------------
st.header("1️⃣ 파일 업로드")

uploaded_files = st.file_uploader(
    "세특·행특·창체 파일 3개를 모두 선택하세요",
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
# 2. 명렬 보기
# -----------------------------
if st.button("📋 명렬 보기"):

    if not file_seteuk or not file_haeng or not file_chang:
        st.error("❗ 파일명에 '세특 / 행특 / 창체'가 포함된 파일 3개를 모두 업로드해주세요.")
        st.stop()

    with st.spinner("데이터 분석 중입니다…"):
        df_seteuk = load_seteuk(file_seteuk)
        df_haeng = load_haengteuk(file_haeng)
        df_chang = load_changche(file_chang)

        # 번호 컬럼 문자열 통일
        for df in [df_seteuk, df_haeng, df_chang]:
            if "번호" in df.columns:
                df["번호"] = df["번호"].astype(str).str.strip()

        # -----------------------------
        # 학생 명렬 생성 (세 파일 통합)
        # -----------------------------
        student_frames = []

        for df in [df_seteuk, df_haeng, df_chang]:
            if {"번호", "성명"}.issubset(df.columns):
                student_frames.append(df[["번호", "성명"]])

        df_students = (
            pd.concat(student_frames)
            .dropna()
            .drop_duplicates()
            .reset_index(drop=True)
        )

        if df_students.empty:
            st.error("학생 명렬을 생성할 수 없습니다.")
            st.stop()

        # 이름 마스킹
        df_students["성명"] = df_students["성명"].apply(
            lambda x: x[0] + "ㅇ" + x[-1] if isinstance(x, str) and len(x) >= 3 else x
        )

        # -----------------------------
        # 화면용 컬럼 구성
        # -----------------------------
        df_view = pd.DataFrame({
            "선택": [False] * len(df_students),
            "No": range(1, len(df_students) + 1),
            "학번": df_students["번호"],
            "성명": df_students["성명"],
        })

    st.success("명렬을 불러왔습니다.")

    st.subheader("📋 학생 명렬")

    # -----------------------------
    # 전체 선택 버튼
    # -----------------------------
    col_btn, _ = st.columns([1, 5])
    with col_btn:
        if st.button("✅ 전체 선택"):
            df_view["선택"] = True

    # -----------------------------
    # 체크박스 테이블
    # -----------------------------
    edited_df = st.data_editor(
        df_view,
        hide_index=True,
        use_container_width=True,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택"),
            "No": st.column_config.NumberColumn("No", disabled=True),
            "학번": st.column_config.TextColumn("학번", disabled=True),
            "성명": st.column_config.TextColumn("성명", disabled=True),
        },
        disabled=["No", "학번", "성명"]
    )

    # -----------------------------
    # 선택된 학생 추출
    # -----------------------------
    selected_students = edited_df[edited_df["선택"] == True]

    if not selected_students.empty:
        st.markdown("### ✅ 선택된 학생")
        st.dataframe(
            selected_students[["학번", "성명"]],
            hide_index=True,
            use_container_width=True
        )
