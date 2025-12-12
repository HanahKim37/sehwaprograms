import streamlit as st
import pandas as pd

# 사이드바
from utils.sidebar import render_sidebar
render_sidebar()

# 파서
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche

# AI 생성기 (이미 만들어둔 파일 사용)
from utils.ai_report_generator import generate_sh_insight_report

st.set_page_config(page_title="생기부 기반 상담보고서", layout="wide")

# ---- (가능한 범위 내) 표 가운데 정렬 CSS 시도 ----
# Streamlit data_editor는 정렬 제어가 제한적이지만, 보이는 범위에서 최대한 맞춥니다.
st.markdown(
    """
    <style>
    /* 표 자체 폭을 너무 넓지 않게 (가운데 배치) */
    div[data-testid="stDataEditor"]{
        margin-left:auto;
        margin-right:auto;
        max-width: 900px;
    }
    /* 셀 텍스트 가운데 정렬 "시도" */
    div[data-testid="stDataEditor"] div[role="gridcell"]{
        justify-content: center !important;
        text-align: center !important;
    }
    div[data-testid="stDataEditor"] div[role="columnheader"]{
        justify-content: center !important;
        text-align: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📘 생기부 기반 상담 보고서")
st.markdown("세특·행특·창체 파일을 업로드한 뒤 학생을 선택하여 **SH-Insight** 보고서를 생성합니다.")

# -----------------------------
# 1) 파일 업로드 (3개 한 번에)
# -----------------------------
st.header("1️⃣ 파일 업로드")

uploaded_files = st.file_uploader(
    "세특·행특·창체 파일 3개를 모두 선택하세요 (파일명에 세특/행특/창체 포함)",
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
# 2) 명렬 보기
# -----------------------------
if st.button("📋 명렬 보기"):
    if not file_seteuk or not file_haeng or not file_chang:
        st.error("세특·행특·창체 파일 3개를 모두 업로드해주세요. (파일명에 '세특/행특/창체' 포함)")
        st.stop()

    with st.spinner("데이터 분석 중입니다…"):
        df_seteuk = load_seteuk(file_seteuk)
        df_haeng = load_haengteuk(file_haeng)
        df_chang = load_changche(file_chang)

        # 번호 문자열 통일(비교 안정화)
        for df in (df_seteuk, df_haeng, df_chang):
            if "번호" in df.columns:
                df["번호"] = df["번호"].astype(str).str.strip()

        # 학생 명렬(3파일 통합)
        frames = []
        for df in (df_seteuk, df_haeng, df_chang):
            if {"번호", "성명"}.issubset(df.columns):
                frames.append(df[["번호", "성명"]])

        if not frames:
            st.error("파일에서 '번호'/'성명' 컬럼을 찾지 못했습니다. 파서 결과를 확인해주세요.")
            st.stop()

        df_students = (
            pd.concat(frames, ignore_index=True)
            .dropna(subset=["번호", "성명"])
            .drop_duplicates()
        )

        # '학번/성명' 같은 헤더가 데이터로 섞인 행 제거 (학번은 숫자만 허용)
        df_students = df_students[df_students["번호"].str.isdigit()]

        if df_students.empty:
            st.error("학생 명렬이 비었습니다. 업로드 파일 내용/형식을 확인해주세요.")
            st.stop()

        # 이름 마스킹
        def mask_name(x: str) -> str:
            x = str(x)
            return x[0] + "ㅇ" + x[-1] if len(x) >= 3 else x

        df_students["성명"] = df_students["성명"].apply(mask_name)

        # 화면용 테이블(체크박스 포함)
        df_view = pd.DataFrame({
            "선택": [False] * len(df_students),
            "학번": df_students["번호"].tolist(),
            "성명": df_students["성명"].tolist(),
        })

        # session_state에 고정 저장 (명렬이 사라지지 않게)
        st.session_state["students_table"] = df_view
        st.session_state["df_seteuk"] = df_seteuk
        st.session_state["df_haeng"] = df_haeng
        st.session_state["df_chang"] = df_chang

    st.success("명렬을 불러왔습니다.")

# -----------------------------
# 3) 명렬 표 표시 (체크박스 유지)
# -----------------------------
if "students_table" in st.session_state:
    st.subheader("📋 학생 명렬")

    col_a, col_b = st.columns([1, 6])
    with col_a:
        if st.button("✅ 전체 선택"):
            st.session_state["students_table"]["선택"] = True

    edited_df = st.data_editor(
        st.session_state["students_table"],
        hide_index=True,                 # ← 이상한 행번호 안 보이게
        use_container_width=True,
        column_config={
            "선택": st.column_config.CheckboxColumn("선택", width="small"),
            "학번": st.column_config.TextColumn("학번", disabled=True, width="medium"),
            "성명": st.column_config.TextColumn("성명", disabled=True, width="medium"),
        },
        disabled=["학번", "성명"],
    )

    # 변경사항 유지
    st.session_state["students_table"] = edited_df

    # -----------------------------
    # 4) 보고서 생성
    # -----------------------------
    st.divider()
    st.header("📄 보고서 생성")

    selected = edited_df[edited_df["선택"] == True].copy()
    st.write(f"선택된 학생 수: **{len(selected)}명**")

    # 학생 기록 텍스트 만들기(컬럼명은 파서마다 다를 수 있어 안전하게 찾습니다)
    def pick_text_column(df: pd.DataFrame) -> str | None:
        candidates = ["내용", "기록", "텍스트", "서술", "세특", "행특", "창체"]
        for c in candidates:
            if c in df.columns:
                return c
        # 마지막: 문자열 컬럼 중 가장 긴 평균 길이 컬럼 하나 선택
        text_cols = [c for c in df.columns if df[c].dtype == "object"]
        if not text_cols:
            return None
        best = max(text_cols, key=lambda c: df[c].astype(str).str.len().mean())
        return best

    def build_text(df: pd.DataFrame) -> str:
        col = pick_text_column(df)
        if col is None or df.empty:
            return ""
        return "\n".join(df[col].dropna().astype(str).tolist())

    def calc_year_count(*dfs: pd.DataFrame) -> int:
        years = set()
        for df in dfs:
            if "학년" in df.columns:
                years.update(df["학년"].dropna().astype(str).str.strip().tolist())
        # 숫자만 추출되는 경우가 많아 최소 0 제거
        years = {y for y in years if y}
        return len(years) if years else 0

    if st.button("🧠 선택 학생 보고서 생성"):
        if selected.empty:
            st.warning("보고서를 생성할 학생을 한 명 이상 선택하세요.")
            st.stop()

        df_seteuk = st.session_state["df_seteuk"]
        df_haeng = st.session_state["df_haeng"]
        df_chang = st.session_state["df_chang"]

        # 여러 명 선택 가능: 우선 “선택된 학생별로 순차 생성” (안정형)
        results = []

        for _, row in selected.iterrows():
            sid = str(row["학번"]).strip()
            sname = str(row["성명"]).strip()

            stu_seteuk = df_seteuk[df_seteuk["번호"].astype(str).str.strip() == sid] if "번호" in df_seteuk.columns else df_seteuk.iloc[0:0]
            stu_haeng  = df_haeng[df_haeng["번호"].astype(str).str.strip() == sid] if "번호" in df_haeng.columns else df_haeng.iloc[0:0]
            stu_chang  = df_chang[df_chang["번호"].astype(str).str.strip() == sid] if "번호" in df_chang.columns else df_chang.iloc[0:0]

            year_count = calc_year_count(stu_seteuk, stu_haeng, stu_chang)

            # 1개년 미만이면 생성 불가(요구사항)
            if year_count < 2:
                results.append({
                    "학번": sid,
                    "성명": sname,
                    "status": "fail",
                    "message": "1개년 이상의 내용이 없어서 보고서 생성이 불가합니다."
                })
                continue

            seteuk_text = build_text(stu_seteuk)
            haeng_text = build_text(stu_haeng)
            chang_text = build_text(stu_chang)

            with st.spinner(f"{sid} {sname} 보고서 생성 중…"):
                try:
                    report = generate_sh_insight_report(
                        student_id=sid,
                        masked_name=sname,
                        year_count=year_count,
                        seteuk_text=seteuk_text,
                        haengteuk_text=haeng_text,
                        changche_text=chang_text,
                    )
                    results.append({
                        "학번": sid,
                        "성명": sname,
                        "status": "ok",
                        "report": report
                    })
                except Exception as e:
                    results.append({
                        "학번": sid,
                        "성명": sname,
                        "status": "fail",
                        "message": f"AI 생성 중 오류: {e}"
                    })

        st.session_state["reports"] = results
        st.success("보고서 생성 요청이 처리되었습니다.")

# -----------------------------
# 5) 결과 출력(일단 화면에 표시)
# -----------------------------
if "reports" in st.session_state:
    st.subheader("📌 생성 결과")

    for item in st.session_state["reports"]:
        st.markdown(f"### {item['학번']} / {item['성명']}")
        if item["status"] == "fail":
            st.error(item["message"])
        else:
            # 우선 JSON 그대로 보여주기 (다음 단계에서 이미지처럼 카드 UI로 렌더링)
            st.json(item["report"])
        st.divider()
