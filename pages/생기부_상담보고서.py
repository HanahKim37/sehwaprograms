import streamlit as st
import pandas as pd

# -----------------------------
# 공통 사이드바
# -----------------------------
from utils.sidebar import render_sidebar
render_sidebar()

# -----------------------------
# 파서 / AI
# -----------------------------
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche
from utils.ai_report_generator import generate_sh_insight_report

st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")

# -----------------------------
# 스타일 (표 폭 + 인덱스 문제 방지)
# -----------------------------
st.markdown(
    """
    <style>
    div[data-testid="stDataEditor"]{
        margin-left:auto;
        margin-right:auto;
        max-width:900px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📘 생기부 기반 상담 보고서 (SH-Insight)")
st.markdown("세특·행특·창체 파일을 업로드하고 학생을 선택해 상담 보고서를 생성합니다.")

# -----------------------------
# 1️⃣ 파일 업로드
# -----------------------------
st.header("1️⃣ 파일 업로드")

uploaded_files = st.file_uploader(
    "세특·행특·창체 파일 3개 업로드 (파일명에 세특/행특/창체 포함)",
    type=["xlsx"],
    accept_multiple_files=True,
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
# 2️⃣ 명렬 불러오기
# -----------------------------
if st.button("📋 명렬 보기"):

    if not file_seteuk or not file_haeng or not file_chang:
        st.error("세특·행특·창체 파일을 모두 업로드하세요.")
        st.stop()

    with st.spinner("데이터 분석 중입니다…"):
        df_seteuk = load_seteuk(file_seteuk)
        df_haeng = load_haengteuk(file_haeng)
        df_chang = load_changche(file_chang)

        # 번호 통일
        for df in (df_seteuk, df_haeng, df_chang):
            if "번호" in df.columns:
                df["번호"] = df["번호"].astype(str).str.strip()

        # 학생 명렬 생성
        frames = []
        for df in (df_seteuk, df_haeng, df_chang):
            if {"번호", "성명"}.issubset(df.columns):
                frames.append(df[["번호", "성명"]])

        df_students = (
            pd.concat(frames, ignore_index=True)
            .dropna()
            .drop_duplicates()
        )

        # 숫자 아닌 행 제거 (헤더 제거)
        df_students = df_students[df_students["번호"].astype(str).str.isdigit()]

        if df_students.empty:
            st.error("학생 명렬을 생성할 수 없습니다.")
            st.stop()

        # 이름 마스킹
        def mask_name(x):
            x = str(x)
            return x[0] + "ㅇ" + x[-1] if len(x) >= 3 else x

        df_students["성명"] = df_students["성명"].apply(mask_name)

        # 체크박스 포함 화면용 테이블
        st.session_state["students_table"] = pd.DataFrame({
            "선택": [False] * len(df_students),
            "학번": df_students["번호"].astype(str).tolist(),
            "성명": df_students["성명"].tolist(),
        })

        # ★ 반드시 세션에 저장 (KeyError 방지)
        st.session_state["df_seteuk"] = df_seteuk
        st.session_state["df_haeng"] = df_haeng
        st.session_state["df_chang"] = df_chang

    st.success("명렬을 불러왔습니다.")

# -----------------------------
# 3️⃣ 명렬 표 표시
# -----------------------------
if "students_table" in st.session_state:

    st.subheader("📋 학생 명렬")

    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("✅ 전체 선택"):
            st.session_state["students_table"]["선택"] = True

    edited_df = st.data_editor(
        st.session_state["students_table"],
        hide_index=True,
        use_container_width=True,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", width="small"),
            "학번": st.column_config.TextColumn("학번", disabled=True),
            "성명": st.column_config.TextColumn("성명", disabled=True),
        },
        disabled=["학번", "성명"],
    )

    st.session_state["students_table"] = edited_df

    # -----------------------------
    # 4️⃣ 보고서 생성
    # -----------------------------
    st.divider()
    st.header("📄 보고서 생성")

    selected = edited_df[edited_df["선택"] == True]
    st.write(f"선택된 학생 수: **{len(selected)}명**")

    # session_state 안전 체크
    required_keys = ["df_seteuk", "df_haeng", "df_chang"]
    for k in required_keys:
        if k not in st.session_state:
            st.error("먼저 '명렬 보기'를 눌러 데이터를 불러와 주세요.")
            st.stop()

    df_seteuk = st.session_state["df_seteuk"]
    df_haeng = st.session_state["df_haeng"]
    df_chang = st.session_state["df_chang"]

    # -----------------------------
    # 텍스트 컬럼 자동 탐색 (중복 컬럼명 방어)
    # -----------------------------
    def pick_text_column(df: pd.DataFrame):
        for c in df.columns:
            s = df[c]

            # ✅ 중복 컬럼명으로 df[c]가 DataFrame이 되는 경우 방어
            if isinstance(s, pd.DataFrame):
                s = s.iloc[:, 0]

            if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
                return c
        return None

    def build_text(df: pd.DataFrame) -> str:
        if df is None or df.empty:
            return ""

        col = pick_text_column(df)
        if col is None:
            return ""

        s = df[col]
        # ✅ 여기서도 한 번 더 방어
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]

        return "\n".join(s.dropna().astype(str).tolist())

    def calc_year_count(*dfs):
        years = set()
        for df in dfs:
            if "학년" in df.columns:
                years.update(df["학년"].dropna().astype(str).tolist())
        return len(years)

    if st.button("🧠 선택 학생 보고서 생성"):

        if selected.empty:
            st.warning("보고서를 생성할 학생을 선택하세요.")
            st.stop()

        results = []

        for _, row in selected.iterrows():
            sid = str(row["학번"]).strip()
            sname = row["성명"]

            # 번호 컬럼이 문자열로 통일되어 있다고 가정
            stu_seteuk = df_seteuk[df_seteuk["번호"].astype(str).str.strip() == sid]
            stu_haeng = df_haeng[df_haeng["번호"].astype(str).str.strip() == sid]
            stu_chang = df_chang[df_chang["번호"].astype(str).str.strip() == sid]

            year_count = calc_year_count(stu_seteuk, stu_haeng, stu_chang)

            if year_count < 2:
                results.append((sid, sname, "❌ 1개년 이상 자료 없음"))
                continue

            with st.spinner(f"{sid} {sname} 보고서 생성 중…"):
                report = generate_sh_insight_report(
                    student_id=sid,
                    masked_name=sname,
                    year_count=year_count,
                    seteuk_text=build_text(stu_seteuk),
                    haengteuk_text=build_text(stu_haeng),
                    changche_text=build_text(stu_chang),
                )

            results.append((sid, sname, report))

        st.session_state["reports"] = results
        st.success("보고서 생성이 완료되었습니다.")

# -----------------------------
# 5️⃣ 결과 출력
# -----------------------------
if "reports" in st.session_state:

    st.subheader("📌 생성 결과")

    for item in st.session_state["reports"]:
        sid, sname, content = item
        st.markdown(f"### {sid} / {sname}")

        if isinstance(content, str):
            st.error(content)
        else:
            st.json(content)

        st.divider()
