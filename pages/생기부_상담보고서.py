# pages/생기부_상담보고서.py
import streamlit as st
import pandas as pd

from utils.sidebar import render_sidebar
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche
from utils.ai_report_generator import generate_sh_insight_report

# ✅ UI/PDF/Chart
from utils.report_ui import inject_report_css, render_report_modal
from utils.report_chart import setup_matplotlib_korean_font, build_radar_png
from utils.report_pdf import build_pdf_bytes


st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")
render_sidebar()

# ✅ 차트 한글 폰트
setup_matplotlib_korean_font()

# ✅ 결과창 CSS (인자 없이 호출되도록 report_ui에서 방어 처리함)
inject_report_css()

st.title("📘 생기부 기반 상담 보고서 (SH-Insight)")
st.markdown("세특·행특·창체 파일을 업로드하고 학생을 선택해 상담 보고서를 생성합니다.")

# -----------------------------
# 유틸: ID 컬럼 자동 감지
# -----------------------------
def get_id_col(df: pd.DataFrame) -> str:
    for c in ["번호", "학번", "학생번호", "student_id", "ID"]:
        if c in df.columns:
            return c
    return "번호"

def normalize_id_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()

# -----------------------------
# 유틸: 원문 텍스트 추출 (빈약/기록없음 방지)
# -----------------------------
def extract_text(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return ""

    drop_cols = {"번호", "학번", "학생번호", "성명", "이름", "학년", "반", "담임", "과목", "영역", "구분"}
    cols = [c for c in df.columns if str(c).strip() and str(c) not in drop_cols]
    if not cols:
        return ""

    preferred_kw = ["세부", "특기", "행동", "종합", "의견", "창체", "체험", "활동", "기록", "내용", "서술", "요약"]
    preferred = [c for c in cols if any(k in str(c) for k in preferred_kw)]
    target_cols = preferred if preferred else cols

    parts = []
    for c in target_cols:
        s = df[c]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
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

# -----------------------------
# 1️⃣ 파일 업로드 (아이콘 변경 요청 반영)
# -----------------------------
st.header("📁 파일 업로드")  # ✅ (3) 아이콘 변경

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
            id_col = get_id_col(df)
            if id_col in df.columns:
                df[id_col] = normalize_id_series(df[id_col])

        # 학생 명렬 생성(기존 로직 유지)
        frames = []
        for df in (df_seteuk, df_haeng, df_chang):
            id_col = get_id_col(df)
            if {id_col, "성명"}.issubset(df.columns):
                tmp = df[[id_col, "성명"]].copy()
                tmp.columns = ["번호", "성명"]  # 표준
                frames.append(tmp)

        df_students = (
            pd.concat(frames, ignore_index=True)
            .dropna()
            .drop_duplicates()
        )

        df_students["번호"] = df_students["번호"].astype(str).str.strip()
        df_students = df_students[df_students["번호"].str.isdigit()]

        if df_students.empty:
            st.error("학생 명렬을 생성할 수 없습니다.")
            st.stop()

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

# -----------------------------
# 3️⃣ 명렬 표 표시 + 보고서 생성
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

    st.divider()
    st.header("📄 보고서 생성")

    selected = edited_df[edited_df["선택"] == True]
    st.write(f"선택된 학생 수: **{len(selected)}명**")

    for k in ["df_seteuk", "df_haeng", "df_chang"]:
        if k not in st.session_state:
            st.error("먼저 '명렬 보기'를 눌러 데이터를 불러와 주세요.")
            st.stop()

    df_seteuk = st.session_state["df_seteuk"]
    df_haeng = st.session_state["df_haeng"]
    df_chang = st.session_state["df_chang"]

    if st.button("🧠 선택 학생 보고서 생성"):

        if selected.empty:
            st.warning("보고서를 생성할 학생을 선택하세요.")
            st.stop()

        results = []
        first_report = None
        first_meta = None
        first_radar_png = None
        first_pdf_bytes = None

        # ✅ (4) 진행률 UI
        progress_wrap = st.container()
        with progress_wrap:
            st.markdown("#### ⏳ 보고서 생성 진행 상황")
            progress_bar = st.progress(0)
            progress_text = st.empty()

        # 처리 대상 수(필터링 후 실제 생성 대상 기준으로도 가능하지만, 일단 선택 수 기준)
        total = int(len(selected))
        done = 0

        set_col = get_id_col(df_seteuk)
        hae_col = get_id_col(df_haeng)
        cha_col = get_id_col(df_chang)

        for idx, row in selected.reset_index(drop=True).iterrows():
            sid = str(row["학번"]).strip()
            sname = row["성명"]

            stu_seteuk = df_seteuk[normalize_id_series(df_seteuk[set_col]) == sid] if set_col in df_seteuk.columns else df_seteuk.iloc[0:0]
            stu_haeng = df_haeng[normalize_id_series(df_haeng[hae_col]) == sid] if hae_col in df_haeng.columns else df_haeng.iloc[0:0]
            stu_chang = df_chang[normalize_id_series(df_chang[cha_col]) == sid] if cha_col in df_chang.columns else df_chang.iloc[0:0]

            year_count = calc_year_count(stu_seteuk, stu_haeng, stu_chang)
            if year_count < 2:
                results.append((sid, sname, "❌ 1개년 이상 자료 없음"))
                done += 1
                pct = int(done / total * 100)
                progress_bar.progress(min(pct, 100))
                progress_text.markdown(f"**{pct}%** 완료 · {done}/{total} (자료 부족 건은 제외됨)")
                continue

            seteuk_text = extract_text(stu_seteuk)
            haeng_text = extract_text(stu_haeng)
            chang_text = extract_text(stu_chang)

            with st.spinner(f"{sid} {sname} 보고서 생성 중…"):
                report = generate_sh_insight_report(
                    student_id=sid,
                    masked_name=sname,
                    year_count=year_count,
                    seteuk_text=seteuk_text,
                    haengteuk_text=haeng_text,
                    changche_text=chang_text,
                )

            results.append((sid, sname, report))

            # ✅ (5) 레이더 그래프가 반드시 나오게: 보고서 점수 → PNG 생성
            if isinstance(report, dict) and (first_report is None):
                detail = report.get("3대 평가 항목별 상세 분석", {}) or {}
                scores = {}
                if isinstance(detail, dict):
                    for kname in ["학업역량", "학업태도", "학업 외 소양"]:
                        v = detail.get(kname, {})
                        if isinstance(v, dict):
                            scores[kname] = v.get("점수", 0)

                first_report = report
                first_meta = (sid, sname)
                first_radar_png = build_radar_png(scores)  # ✅ 그래프 생성(실패하면 None)

                # PDF도 “첫 리포트” 기준으로 즉시 생성
                try:
                    first_pdf_bytes = build_pdf_bytes(first_report, first_radar_png, sid, sname)
                except Exception:
                    first_pdf_bytes = None

            done += 1
            pct = int(done / total * 100)
            progress_bar.progress(min(pct, 100))
            progress_text.markdown(f"**{pct}%** 완료 · {done}/{total}")

        st.session_state["reports"] = results
        st.success("보고서 생성이 완료되었습니다.")

        # 완료 후 진행 UI 정리(원하시면 지울 수도 있음)
        progress_text.markdown("✅ 완료되었습니다.")

        # 첫 학생 자동 모달
        if first_report is not None and first_meta is not None:
            render_report_modal(
                st,
                first_report,
                first_meta[0],
                first_meta[1],
                radar_png=first_radar_png,
                pdf_bytes=first_pdf_bytes
            )

# -----------------------------
# 결과 목록(기존 유지)
# -----------------------------
if "reports" in st.session_state:
    st.subheader("📌 생성 결과")
    for sid, sname, content in st.session_state["reports"]:
        st.markdown(f"### {sid} / {sname}")
        if isinstance(content, str):
            st.error(content)
        else:
            st.json(content)
        st.divider()
