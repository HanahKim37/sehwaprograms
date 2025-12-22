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
# 스타일
# -----------------------------
st.markdown(
    """
    <style>
    div[data-testid="stDataEditor"]{
        margin-left:auto;
        margin-right:auto;
        max-width:900px;
    }
    .card{
        background:#ffffff;
        border:1px solid #e5e7eb;
        border-radius:14px;
        padding:18px;
        margin:10px 0 16px 0;
        box-shadow:0 1px 2px rgba(0,0,0,0.04);
    }
    .card-title{
        font-size:18px;
        font-weight:700;
        margin:0 0 10px 0;
    }
    .pill-good{
        background:#dcfce7;
        border:1px solid #86efac;
        padding:10px 12px;
        border-radius:12px;
    }
    .pill-bad{
        background:#fee2e2;
        border:1px solid #fca5a5;
        padding:10px 12px;
        border-radius:12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📘 생기부 기반 상담 보고서 (SH-Insight)")
st.markdown("세특·행특·창체 파일을 업로드하고 학생을 선택해 상담 보고서를 생성합니다.")

# -----------------------------
# 유틸: ID 컬럼 자동 감지 (최소 추가)
# -----------------------------
def get_id_col(df: pd.DataFrame) -> str:
    for c in ["번호", "학번", "학생번호", "student_id", "ID"]:
        if c in df.columns:
            return c
    return "번호"  # fallback

def normalize_id_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()

# -----------------------------
# 유틸: 텍스트 추출 (원문 못 읽는 문제 해결의 핵심)
# -----------------------------
def extract_text(df: pd.DataFrame) -> str:
    """
    - 숫자/메타 컬럼(번호/성명/학년 등) 제외
    - 문자열 컬럼들에서 '내용/특기/의견/활동/기록' 등 키워드 우선
    - 여러 컬럼이면 모두 합쳐서 반환
    - 중복 컬럼명(df[c]가 DataFrame) 방어
    """
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
        # 문자열/객체형만 추출
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

        # 번호 통일(각 df별 ID 컬럼 감지 후 normalize)
        for df in (df_seteuk, df_haeng, df_chang):
            id_col = get_id_col(df)
            if id_col in df.columns:
                df[id_col] = normalize_id_series(df[id_col])

        # 학생 명렬 생성(기존 로직 유지 + ID 컬럼 대응)
        frames = []
        for df in (df_seteuk, df_haeng, df_chang):
            id_col = get_id_col(df)
            if {id_col, "성명"}.issubset(df.columns):
                tmp = df[[id_col, "성명"]].copy()
                tmp.columns = ["번호", "성명"]  # 명렬 통합용 표준화
                frames.append(tmp)

        df_students = (
            pd.concat(frames, ignore_index=True)
            .dropna()
            .drop_duplicates()
        )

        # 숫자 아닌 행 제거 (헤더 제거)
        df_students["번호"] = df_students["번호"].astype(str).str.strip()
        df_students = df_students[df_students["번호"].str.isdigit()]

        if df_students.empty:
            st.error("학생 명렬을 생성할 수 없습니다.")
            st.stop()

        # 이름 마스킹(기존 유지)
        def mask_name(x):
            x = str(x)
            return x[0] + "ㅇ" + x[-1] if len(x) >= 3 else x

        df_students["성명"] = df_students["성명"].apply(mask_name)

        # 체크박스 포함 화면용 테이블(기존 유지)
        st.session_state["students_table"] = pd.DataFrame({
            "선택": [False] * len(df_students),
            "학번": df_students["번호"].tolist(),
            "성명": df_students["성명"].tolist(),
        })

        # 세션 저장(기존 유지)
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

    # session_state 안전 체크(기존 유지)
    required_keys = ["df_seteuk", "df_haeng", "df_chang"]
    for k in required_keys:
        if k not in st.session_state:
            st.error("먼저 '명렬 보기'를 눌러 데이터를 불러와 주세요.")
            st.stop()

    df_seteuk = st.session_state["df_seteuk"]
    df_haeng = st.session_state["df_haeng"]
    df_chang = st.session_state["df_chang"]

    # -----------------------------
    # 모달 렌더러: 버튼 없이 자동으로 뜨게(요구사항 1)
    # -----------------------------
    def render_report_modal(report: dict, sid: str, sname: str):
        @st.dialog(f"📊 SH-Insight 심층 분석 보고서 · {sid} / {sname}", width="large")
        def _show():
            # 모델이 주는 키 변형을 모두 허용 (KeyError 방지)
            overall = report.get("종합 평가") or report.get("종합평가") or report.get("종합의견") or report.get("총평") or ""
            strengths = report.get("핵심 강점") or report.get("핵심강점") or report.get("강점") or []
            needs = report.get("보완 추천 영역") or report.get("보완 영역") or report.get("보완영역") or report.get("개선점") or []
            items = report.get("3대 평가 항목별 상세 분석") or report.get("평가 항목") or report.get("평가항목") or report.get("세부 평가") or {}

            st.markdown(f"<div class='card'><div class='card-title'>종합 평가</div>{overall}</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='card'><div class='card-title'>핵심 강점</div><div class='pill-good'>", unsafe_allow_html=True)
                if isinstance(strengths, list):
                    for x in strengths:
                        st.markdown(f"- {x}")
                else:
                    st.write(strengths)
                st.markdown("</div></div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='card'><div class='card-title'>보완 추천 영역</div><div class='pill-bad'>", unsafe_allow_html=True)
                if isinstance(needs, list):
                    for x in needs:
                        st.markdown(f"- {x}")
                else:
                    st.write(needs)
                st.markdown("</div></div>", unsafe_allow_html=True)

            st.markdown("<div class='card'><div class='card-title'>평가 항목별 상세 분석</div></div>", unsafe_allow_html=True)
            if isinstance(items, dict) and items:
                for k, v in items.items():
                    st.markdown(f"<div class='card'><div class='card-title'>{k}</div>{v}</div>", unsafe_allow_html=True)
            else:
                st.json(items)

        _show()

    # -----------------------------
    # 보고서 생성 버튼
    # -----------------------------
    if st.button("🧠 선택 학생 보고서 생성"):

        if selected.empty:
            st.warning("보고서를 생성할 학생을 선택하세요.")
            st.stop()

        # 여러 명 선택 가능하나, “자동으로 창 뜨기”는 한 명 기준이 현실적입니다.
        # 선택이 여러 명이면: 일단 첫 번째 학생 결과를 모달로 즉시 띄우고,
        # 나머지는 아래 결과 목록(JSON)에서 확인하게 두는 방식(최소 변경).
        results = []
        first_report_for_modal = None
        first_meta = None

        for idx, row in selected.reset_index(drop=True).iterrows():
            sid = str(row["학번"]).strip()
            sname = row["성명"]

            # 학생 데이터 필터링(각 DF의 ID 컬럼 자동 감지)
            sid_seteuk_col = get_id_col(df_seteuk)
            sid_haeng_col = get_id_col(df_haeng)
            sid_chang_col = get_id_col(df_chang)

            stu_seteuk = df_seteuk[normalize_id_series(df_seteuk[sid_seteuk_col]) == sid] if sid_seteuk_col in df_seteuk.columns else df_seteuk.iloc[0:0]
            stu_haeng = df_haeng[normalize_id_series(df_haeng[sid_haeng_col]) == sid] if sid_haeng_col in df_haeng.columns else df_haeng.iloc[0:0]
            stu_chang = df_chang[normalize_id_series(df_chang[sid_chang_col]) == sid] if sid_chang_col in df_chang.columns else df_chang.iloc[0:0]

            year_count = calc_year_count(stu_seteuk, stu_haeng, stu_chang)
            if year_count < 2:
                results.append((sid, sname, "❌ 1개년 이상 자료 없음"))
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

            if first_report_for_modal is None and isinstance(report, dict):
                first_report_for_modal = report
                first_meta = (sid, sname)

        st.session_state["reports"] = results
        st.success("보고서 생성이 완료되었습니다.")

        # ✅ 요구사항 1: 묻지 말고 바로 모달 띄우기
        if first_report_for_modal is not None and first_meta is not None:
            sid, sname = first_meta
            render_report_modal(first_report_for_modal, sid, sname)

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
