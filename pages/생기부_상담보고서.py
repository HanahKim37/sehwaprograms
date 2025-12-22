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
    .card{
        background:#ffffff;
        border:1px solid #e5e7eb;
        border-radius:14px;
        padding:18px 18px;
        margin:10px 0 16px 0;
        box-shadow:0 1px 2px rgba(0,0,0,0.04);
    }
    .card h3{
        margin:0 0 10px 0;
        font-size:18px;
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
        df_students = df_students[df_students["번호"].str.isdigit()]

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
            "학번": df_students["번호"].tolist(),
            "성명": df_students["성명"].tolist(),
        })

        # 세션 저장
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

    required_keys = ["df_seteuk", "df_haeng", "df_chang"]
    for k in required_keys:
        if k not in st.session_state:
            st.error("먼저 '명렬 보기'를 눌러 데이터를 불러와 주세요.")
            st.stop()

    df_seteuk = st.session_state["df_seteuk"]
    df_haeng = st.session_state["df_haeng"]
    df_chang = st.session_state["df_chang"]

    # -----------------------------
    # 텍스트 컬럼 자동 탐색 (중복 컬럼 방어)
    # -----------------------------
    def pick_text_column(df: pd.DataFrame):
        for c in df.columns:
            s = df[c]
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
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        return "\n".join(s.dropna().astype(str).tolist())

    def calc_year_count(*dfs):
        years = set()
        for df in dfs:
            if "학년" in df.columns:
                years.update(df["학년"].dropna().astype(str).tolist())
        return len(years)

    # -----------------------------
    # ✅ (추가) 보고서 모달 렌더링 유틸
    # -----------------------------
    def _get_first(d: dict, keys: list, default=""):
        for k in keys:
            if isinstance(d, dict) and k in d and d[k]:
                return d[k]
        return default

    def _as_list(x):
        if x is None:
            return []
        if isinstance(x, list):
            return x
        if isinstance(x, dict):
            # {"0":"...", "1":"..."} 같은 케이스
            # key 정렬해 list로
            try:
                return [x[k] for k in sorted(x.keys(), key=lambda z: int(str(z)))]
            except Exception:
                return list(x.values())
        if isinstance(x, str):
            return [x]
        return [str(x)]

    def render_report_modal(report: dict, sid: str, sname: str):
        @st.dialog(f"📊 SH-Insight 심층 분석 보고서 · {sid} / {sname}", width="large")
        def _show():
            # 1) UI용 키가 있으면 우선 사용
            overall = _get_first(report, ["종합 평가", "종합평가", "총평", "요약"], "")
            strengths = _get_first(report, ["핵심 강점", "핵심강점", "강점"], [])
            needs = _get_first(report, ["보완 영역", "보완영역", "보완점", "개선점"], [])
            items = _get_first(report, ["평가 항목", "평가항목", "세부 평가", "세부평가"], {})

            # 2) 없으면 현재처럼 원자료 키(세특/행특/창체)를 “임시 보고서”로 표시
            if not overall:
                # 최소한 “학생 정보”는 표시
                student_info = report.get("학생 정보", {})
                st.markdown("<div class='card'><h3>학생 정보</h3></div>", unsafe_allow_html=True)
                st.json(student_info)

                st.markdown("<div class='card'><h3>원문 요약 입력(세특/행특/창체)</h3></div>", unsafe_allow_html=True)
                st.markdown("현재 모델 출력이 ‘보고서 스키마(종합평가/강점/보완/평가항목)’ 형태가 아니라, 원자료 형태로 반환되고 있습니다. 아래는 수집된 원문 영역입니다.")
                st.markdown("<div class='card'><h3>세특</h3></div>", unsafe_allow_html=True)
                st.json(report.get("세부능력 및 특기사항", []))
                st.markdown("<div class='card'><h3>행특</h3></div>", unsafe_allow_html=True)
                st.json(report.get("행동특성 및 종합의견", []))
                st.markdown("<div class='card'><h3>창체</h3></div>", unsafe_allow_html=True)
                st.json(report.get("창의적 체험활동", []))

                st.divider()
                st.info("다음 단계: AI 출력 스키마를 ‘보고서 전용 스키마’로 강제하면, 사진처럼 카드 형태의 결과가 생성됩니다.")
                return

            # --- 사진 같은 카드 UI (키가 있을 때만) ---
            st.markdown(f"<div class='card'><h3>종합 평가</h3>{overall}</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='card'><h3>핵심 강점</h3><div class='pill-good'>", unsafe_allow_html=True)
                for s in _as_list(strengths):
                    st.markdown(f"- {s}")
                st.markdown("</div></div>", unsafe_allow_html=True)

            with c2:
                st.markdown("<div class='card'><h3>보완 추천 영역</h3><div class='pill-bad'>", unsafe_allow_html=True)
                for s in _as_list(needs):
                    st.markdown(f"- {s}")
                st.markdown("</div></div>", unsafe_allow_html=True)

            st.markdown("<div class='card'><h3>평가 항목별 상세 분석</h3></div>", unsafe_allow_html=True)
            if isinstance(items, dict) and items:
                for k, v in items.items():
                    st.markdown(f"<div class='card'><h3>{k}</h3>{v}</div>", unsafe_allow_html=True)
            else:
                st.write("평가 항목 데이터가 없습니다.")
                st.json(items)

        _show()

    # -----------------------------
    # 보고서 생성 버튼
    # -----------------------------
    if st.button("🧠 선택 학생 보고서 생성"):

        if selected.empty:
            st.warning("보고서를 생성할 학생을 선택하세요.")
            st.stop()

        results = []

        for _, row in selected.iterrows():
            sid = str(row["학번"]).strip()
            sname = row["성명"]

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
# 5️⃣ 결과 출력 + (추가) 모달 보기 버튼
# -----------------------------
if "reports" in st.session_state:

    st.subheader("📌 생성 결과")

    for item in st.session_state["reports"]:
        sid, sname, content = item
        st.markdown(f"### {sid} / {sname}")

        if isinstance(content, str):
            st.error(content)
        else:
            # ✅ 기존 JSON 출력 유지 (원하면 주석 처리 가능)
            st.json(content)

            # ✅ (추가) 사진처럼 “새 창에서 보기”
            if st.button(f"🪟 보고서 창으로 보기 · {sid}", key=f"open_{sid}"):
                render_report_modal(content, sid, sname)

        st.divider()
