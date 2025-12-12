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
세특·행특·창체 파일을 업로드한 뒤  
학생을 선택하여 상담 보고서를 생성합니다.
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
# 2. 명렬 불러오기
# -----------------------------
if st.button("📋 명렬 보기"):

    if not file_seteuk or not file_haeng or not file_chang:
        st.error("❗ 파일명에 '세특 / 행특 / 창체'가 포함된 파일 3개를 모두 업로드해주세요.")
        st.stop()

    with st.spinner("데이터 분석 중입니다…"):
        df_seteuk = load_seteuk(file_seteuk)
        df_haeng = load_haengteuk(file_haeng)
        df_chang = load_changche(file_chang)

        # 번호 문자열 통일
        for df in [df_seteuk, df_haeng, df_chang]:
            if "번호" in df.columns:
                df["번호"] = df["번호"].astype(str).str.strip()

        # 학생 명렬 통합
        frames = []
        for df in [df_seteuk, df_haeng, df_chang]:
            if {"번호", "성명"}.issubset(df.columns):
                frames.append(df[["번호", "성명"]])

        df_students = (
            pd.concat(frames)
            .dropna()
            .drop_duplicates()
        )

        # 헤더/가짜 행 제거
        df_students = df_students[df_students["번호"].str.isdigit()]

        if df_students.empty:
            st.error("학생 명렬을 생성할 수 없습니다.")
            st.stop()

        # 이름 마스킹
        df_students["성명"] = df_students["성명"].apply(
            lambda x: x[0] + "ㅇ" + x[-1] if isinstance(x, str) and len(x) >= 3 else x
        )

        # 화면용 테이블 (No 열 제거)
        df_view = pd.DataFrame({
            "선택": False,
            "학번": df_students["번호"].values,
            "성명": df_students["성명"].values,
        })

        st.session_state["students_table"] = df_view

    st.success("명렬을 불러왔습니다.")

# -----------------------------
# 3. 명렬 표시 (가운데 정렬 + 폭 제한)
# -----------------------------
if "students_table" in st.session_state:

    st.subheader("📋 학생 명렬")

    # 전체 선택 버튼
    col_btn, _ = st.columns([1, 6])
    with col_btn:
        if st.button("✅ 전체 선택"):
            st.session_state["students_table"]["선택"] = True

    # 좌우 여백 컬럼으로 가운데 배치
    left, center, right = st.columns([2, 6, 2])

    with center:
        edited_df = st.data_editor(
            st.session_state["students_table"],
            hide_index=True,
            use_container_width=True,
            column_config={
                "선택": st.column_config.CheckboxColumn("선택", width="small"),
                "학번": st.column_config.TextColumn(
                    "학번", width="medium", disabled=True, align="center"
                ),
                "성명": st.column_config.TextColumn(
                    "성명", width="medium", disabled=True, align="center"
                ),
            },
            disabled=["학번", "성명"]
        )

    # 상태 유지
    st.session_state["students_table"] = edited_df

    # -----------------------------
    # 4. 보고서 생성
    # -----------------------------
    st.divider()
    st.header("📄 보고서 생성")

    selected_students = edited_df[edited_df["선택"] == True]

    st.write(f"선택된 학생 수: **{len(selected_students)}명**")

    if st.button("🧠 선택 학생 보고서 생성"):

        if selected_students.empty:
            st.warning("보고서를 생성할 학생을 한 명 이상 선택하세요.")
            st.stop()

        # 🔹 임시 보고서 생성 로직 (동작 확인용)
        for _, row in selected_students.iterrows():
            st.success(f"📄 {row['학번']} / {row['성명']} 상담 보고서 생성 완료 (예시)")

        st.info("※ 다음 단계에서 AI 상담 보고서 실제 생성 로직이 연결됩니다.")
