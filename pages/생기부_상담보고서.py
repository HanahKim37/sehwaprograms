import streamlit as st
import pandas as pd

from utils.sidebar import render_sidebar
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche
from utils.ai_report_generator import generate_sh_insight_report

from utils.report_chart import setup_matplotlib_korean_font, render_radar_chart_to_streamlit
from utils.report_pdf import build_pdf_bytes
from utils.report_ui import inject_report_css, render_report_modal

st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")
render_sidebar()
inject_report_css(st)
setup_matplotlib_korean_font()

st.title("📘 생기부 기반 상담 보고서 (SH-Insight)")
st.markdown("세특·행특·창체 파일을 업로드하고 학생을 선택해 상담 보고서를 생성합니다.")


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
    drop_cols = {"번호", "학번", "학생번호", "성명", "이름", "학년", "반", "담임", "과목", "영역", "구분"}
    cols = [c for c in df.columns if str(c).strip() and str(c) not in drop_cols]
    if not cols:
        return ""
    parts = []
    for c in cols:
        s = df[c]
        if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            vals = s.dropna().astype(str).map(lambda x: x.strip()).tolist()
            vals = [v for v in vals if v and v.lower() != "nan"]
            if vals:
                parts.append(f"[{c}]\n" + "\n".join(vals))
    return "\n\n".join(parts).strip()


def calc_year_count(*dfs):
    years = set()
    for df in dfs:
        if df is not None and "학년" in df.columns:
            years.update(df["학년"].dropna().astype(str).str.strip().tolist())
    return len(years)


# 1) 업로드
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

# 2) 명렬
if st.button("📋 명렬 보기"):
    if not file_seteuk or not file_haeng or not file_chang:
        st.error("세특·행특·창체 파일을 모두 업로드하세요.")
        st.stop()

    with st.spinner("데이터 분석 중입니다…"):
        df_seteuk = load_seteuk(file_seteuk)
        df_haeng = load_haengteuk(file_haeng)
        df_chang = load_changche(file_chang)

        for df in (df_seteuk, df_haeng, df_chang):
            id_col = get_id_col(df)
            if id_col in df.columns:
                df[id_col] = normalize_id_series(df[id_col])

        frames = []
        for df in (df_seteuk, df_haeng, df_chang):
            id_col = get_id_col(df)
            if {id_col, "성명"}.issubset(df.columns):
                tmp = df[[id_col, "성명"]].copy()
                tmp.columns = ["번호", "성명"]
                frames.append(tmp)

        df_students = pd.concat(frames, ignore_index=True).dropna().drop_duplicates()
        df_students["번호"] = df_students["번호"].astype(str).str.strip()
        df_students = df_students[df_students["번호"].str.isdigit()]

        def mask_name(x):
            x = str(x)
            return x[0] + "ㅇ" + x[-1] if len(x) >= 3 else x

        df_students["성명"] = df_students["성명"].apply(mask_name)

        st.session_state["students_table"] = pd.DataFrame({
            "선택": [False] * len(df_students),
            "학번": df_students["번호"].tolist(),
            "성명": df_students["성명"].tolist(),
        })
        st.session_state["df_seteuk"] = df_seteuk
        st.session_state["df_haeng"] = df_haeng
        st.session_state["df_chang"] = df_chang

    st.success("명렬을 불러왔습니다.")

# 3) 표 + 생성
if "students_table" in st.session_state:
    st.subheader("📋 학생 명렬")
    edited_df = st.data_editor(
        st.session_state["students_table"],
        hide_index=True,
        use_container_width=True,
        disabled=["학번", "성명"],
    )
    st.session_state["students_table"] = edited_df

    selected = edited_df[edited_df["선택"] == True]
    st.write(f"선택된 학생 수: **{len(selected)}명**")

    if st.button("🧠 선택 학생 보고서 생성"):
        if selected.empty:
            st.warning("보고서를 생성할 학생을 선택하세요.")
            st.stop()

        df_seteuk = st.session_state["df_seteuk"]
        df_haeng = st.session_state["df_haeng"]
        df_chang = st.session_state["df_chang"]

        total = len(selected)
        prog = st.progress(0, text="보고서 생성 준비 중…")

        first_report = None
        first_meta = None

        for idx, row in enumerate(selected.reset_index(drop=True).itertuples(index=False), start=1):
            sid = str(getattr(row, "학번")).strip()
            sname = getattr(row, "성명")

            set_col = get_id_col(df_seteuk)
            hae_col = get_id_col(df_haeng)
            cha_col = get_id_col(df_chang)

            stu_seteuk = df_seteuk[normalize_id_series(df_seteuk[set_col]) == sid] if set_col in df_seteuk.columns else df_seteuk.iloc[0:0]
            stu_haeng = df_haeng[normalize_id_series(df_haeng[hae_col]) == sid] if hae_col in df_haeng.columns else df_haeng.iloc[0:0]
            stu_chang = df_chang[normalize_id_series(df_chang[cha_col]) == sid] if cha_col in df_chang.columns else df_chang.iloc[0:0]

            year_count = calc_year_count(stu_seteuk, stu_haeng, stu_chang)
            seteuk_text = extract_text(stu_seteuk)
            haeng_text = extract_text(stu_haeng)
            chang_text = extract_text(stu_chang)

            report = generate_sh_insight_report(
                student_id=sid,
                masked_name=sname,
                year_count=year_count,
                seteuk_text=seteuk_text,
                haengteuk_text=haeng_text,
                changche_text=chang_text,
            )

            if first_report is None and isinstance(report, dict):
                first_report = report
                first_meta = (sid, sname)

            prog.progress(int(idx / total * 100), text=f"진행률: {int(idx/total*100)}%")

        prog.empty()
        st.success("보고서 생성이 완료되었습니다.")

        # 첫 학생 결과창 오픈
        if first_report and first_meta:
            detail = first_report.get("3대 평가 항목별 상세 분석", {}) or {}
            scores = {}
            if isinstance(detail, dict):
                for key in ["학업역량", "학업태도", "학업 외 소양"]:
                    v = detail.get(key, {})
                    if isinstance(v, dict):
                        scores[key] = v.get("점수", 0)

            # 차트 먼저 생성(이미지 buf 반환)
            radar_png = render_radar_chart_to_streamlit(st, scores)

            # PDF 생성
            pdf_bytes = build_pdf_bytes(first_report, radar_png, first_meta[0], first_meta[1])

            # 모달 렌더
            render_report_modal(st, first_report, first_meta[0], first_meta[1], radar_png, pdf_bytes)
