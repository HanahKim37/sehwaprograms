import streamlit as st

# -----------------------------
# 공통 사이드바 (1회 호출)
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

# -----------------------------
# 📘 페이지 본문
# -----------------------------
st.title("📘 생기부 기반 상담 보고서")

st.markdown("""
세특·행특·창체 파일을 업로드하면  
학생별 상담 보고서를 자동으로 생성합니다.
""")

# -----------------------------
# 1. 파일 업로드 (한꺼번에)
# -----------------------------
st.header("1️⃣ 파일 업로드")

uploaded_files = st.file_uploader(
    "세특·행특·창체 파일 3개를 모두 선택하세요",
    type=["xlsx"],
    accept_multiple_files=True
)

file_seteuk = None
file_haeng = None
file_chang = None

if uploaded_files:
    for f in uploaded_files:
        fname = f.name
        if "세특" in fname:
            file_seteuk = f
        elif "행특" in fname:
            file_haeng = f
        elif "창체" in fname:
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

        # 번호 컬럼 타입 통일 (⭐ 중요)
        for df in [df_seteuk, df_haeng, df_chang]:
            if "번호" in df.columns:
                df["번호"] = df["번호"].astype(str).str.strip()

        # -----------------------------
        # 학생 명렬 생성
        # -----------------------------
        df_students = (
            df_seteuk[["번호", "성명"]]
            .dropna()
            .drop_duplicates()
            .reset_index(drop=True)
        )

        df_students["마스킹이름"] = df_students["성명"].apply(
            lambda x: x[0] + "ㅇ" + x[-1] if isinstance(x, str) and len(x) >= 3 else x
        )

    st.success("명렬을 불러왔습니다.")

    st.subheader("📋 학생 명렬")
    st.dataframe(
        df_students[["번호", "마스킹이름"]],
        use_container_width=True
    )

    # -----------------------------
    # 학생 선택
    # -----------------------------
    selected_no = st.selectbox(
        "보고서를 생성할 학생 번호를 선택하세요.",
        df_students["번호"].tolist()
    )

    selected_row = df_students[df_students["번호"] == selected_no]

    if selected_row.empty:
        st.error("선택한 학생 정보를 찾을 수 없습니다. 데이터 구조를 확인해주세요.")
        st.stop()

    student_name = selected_row["성명"].iloc[0]
    masked_name = selected_row["마스킹이름"].iloc[0]

    # -----------------------------
    # 학생별 데이터 필터링
    # -----------------------------
    stu_seteuk = df_seteuk[df_seteuk["번호"] == selected_no]
    stu_haeng = df_haeng[df_haeng["번호"] == selected_no]
    stu_chang = df_chang[df_chang["번호"] == selected_no]

    # -----------------------------
    # 3. 1개년 이상 여부 확인
    # -----------------------------
    years = set()

    for df in [stu_seteuk, stu_haeng, stu_chang]:
        if "학년" in df.columns:
            years.update(df["학년"].dropna().unique())

    if len(years) < 2:
        st.error("⚠️ 1개년 이상의 기록이 없어 보고서를 생성할 수 없습니다.")
        st.stop()

    # -----------------------------
    # 4. 보고서 생성 (다음 단계)
    # -----------------------------
    st.info("다음 단계: AI 상담 보고서 생성")
