import streamlit as st
import pandas as pd

from utils.sidebar import render_sidebar
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche

# ✅ AI 분석 엔진(유지)
from utils.ai_report_generator import generate_sh_insight_report

# ✅ PDF 전용(권장 구조)
from utils.report_generator import build_pdf_from_report

from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
from pathlib import Path

# -----------------------------
# Page config (가장 먼저)
# -----------------------------
st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")

# -----------------------------
# Sidebar
# -----------------------------
render_sidebar()

# -----------------------------
# 스타일 (기존 + 결과창 카드 UI만 개선)
# -----------------------------
st.markdown(
    """
    <style>
    div[data-testid="stDataEditor"]{
        margin-left:auto;
        margin-right:auto;
        max-width:900px;
    }

    .r-wrap{background:#f6f7f9;padding:14px;border-radius:18px;}
    .r-card{
        background:#ffffff;
        border:1px solid #e5e7eb;
        border-radius:16px;
        padding:18px;
        margin:12px 0;
        box-shadow:0 1px 2px rgba(0,0,0,0.04);
    }
    .r-title{
        font-size:18px;
        font-weight:800;
        margin:0 0 10px 0;
        color:#111827;
    }
    .r-sub{
        font-size:14px;
        font-weight:800;
        margin:16px 0 8px 0;
        color:#111827;
    }
    .r-text{
        font-size:14px;
        line-height:1.75;
        color:#374151;
        white-space:pre-wrap;
    }
    .pill-good{
        background:#f0fdf4;
        border:1px solid #bbf7d0;
        border-radius:12px;
        padding:12px;
    }
    .pill-bad{
        background:#fef2f2;
        border:1px solid #fecaca;
        border-radius:12px;
        padding:12px;
    }
    .badge{
        display:inline-block;
        padding:3px 10px;
        border-radius:999px;
        font-size:12px;
        border:1px solid #e5e7eb;
        background:#fafafa;
        color:#111827;
        margin-right:6px;
    }
    .stars{
        font-size:18px;
        letter-spacing:2px;
        margin:4px 0 10px 0;
        color:#f59e0b;
    }
    .evi{
        background:#f9fafb;
        border-left:4px solid #9ca3af;
        border-radius:10px;
        padding:10px 12px;
        margin:6px 0;
        color:#374151;
        font-size:13px;
        white-space:pre-wrap;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
# 유틸: 원문 텍스트 추출 (빈약 방지)
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
# 폰트: Matplotlib 한글 폴백
# -----------------------------
def _set_mpl_korean_font():
    """
    Streamlit Cloud 환경에서 폰트가 없을 수 있으므로:
    1) 프로젝트 내 assets/NanumGothic.ttf
    2) 시스템 NanumGothic
    없으면 기본 폰트로 진행 (라벨은 영문 병기)
    """
    candidates = [
        Path("assets/NanumGothic.ttf"),
        Path("NanumGothic.ttf"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
        Path("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),
    ]
    for p in candidates:
        try:
            if p.exists():
                font_manager.fontManager.addfont(str(p))
                rcParams["font.family"] = "NanumGothic"
                rcParams["axes.unicode_minus"] = False
                return True
        except Exception:
            continue
    rcParams["axes.unicode_minus"] = False
    return False

# -----------------------------
# 별점
# -----------------------------
def render_stars(score_10) -> str:
    try:
        s = int(round(float(score_10)))
    except Exception:
        s = 0
    s = max(0, min(10, s))
    stars = int(round(s / 2))
    return "⭐" * stars + "☆" * (5 - stars)

# -----------------------------
# 레이더 차트 (크기 확실히 축소 + use_container_width=False)
# -----------------------------
def render_radar_chart(scores: dict):
    has_korean_font = _set_mpl_korean_font()

    # 한글 깨짐 방지: 라벨 영문 병기(폰트 없을 때도 안전)
    labels_kr = ["학업역량", "학업태도", "학업 외 소양"]
    labels = labels_kr if has_korean_font else ["Academic", "Attitude", "Character"]

    vals = [float(scores.get(k, 0) or 0) for k in labels_kr]
    vals = [max(0.0, min(10.0, v)) for v in vals]

    vals += vals[:1]
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(2.6, 2.6), dpi=140)  # ✅ 더 작게
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=9)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=8)

    ax.plot(angles, vals, linewidth=2)
    ax.fill(angles, vals, alpha=0.15)

    # ✅ 화면 표시 크기 고정
    st.pyplot(fig, use_container_width=False, clear_figure=True)

    # PDF용 PNG bytes
    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", dpi=160, bbox_inches="tight")
    img_buf.seek(0)
    plt.close(fig)
    return img_buf

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
            id_col = get_id_col(df)
            if id_col in df.columns:
                df[id_col] = normalize_id_series(df[id_col])

        # 학생 명렬 생성(기존 로직 유지)
        frames = []
        for df in (df_seteuk, df_haeng, df_chang):
            id_col = get_id_col(df)
            if {id_col, "성명"}.issubset(df.columns):
                tmp = df[[id_col, "성명"]].copy()
                tmp.columns = ["번호", "성명"]  # 통합 표준
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

    def render_report_modal(report: dict, sid: str, sname: str):
        @st.dialog(f"📊 SH-Insight 심층 분석 보고서 · {sid} / {sname}", width="large")
        def _show():
            overall = report.get("종합 평가") or report.get("종합의견") or ""
            strengths = report.get("핵심 강점") or []
            needs = report.get("보완 추천 영역") or report.get("보완 영역") or []
            detail = report.get("3대 평가 항목별 상세 분석") or {}

            topics = report.get("영역별 심화 탐구 주제 제안") or {}
            majors = report.get("역량 기반 추천 학과") or []
            growth = report.get("맞춤형 성장 제안") or {}
            books = report.get("추천 도서") or []

            # 점수 추출(레이더 전용)
            scores = {}
            if isinstance(detail, dict):
                for key in ["학업역량", "학업태도", "학업 외 소양"]:
                    v = detail.get(key, {})
                    if isinstance(v, dict):
                        scores[key] = v.get("점수", 0)

            st.markdown("<div class='r-wrap'>", unsafe_allow_html=True)

            # 요약 카드
            st.markdown(
                f"""
                <div class='r-card'>
                  <div class='r-title'>보고서 요약</div>
                  <span class='badge'>학번 {sid}</span>
                  <span class='badge'>성명 {sname}</span>
                  <div class='r-text' style='margin-top:10px;'>{overall}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # 레이더 + 강점/보완
            c_left, c_right = st.columns([1.1, 1.3], gap="large")

            with c_left:
                st.markdown("<div class='r-card'><div class='r-title'>핵심 역량</div>", unsafe_allow_html=True)
                radar_png = render_radar_chart(scores)
                st.markdown("</div>", unsafe_allow_html=True)

            with c_right:
                st.markdown("<div class='r-card'><div class='r-title'>핵심 강점</div><div class='pill-good'>", unsafe_allow_html=True)
                if isinstance(strengths, list) and strengths:
                    for x in strengths[:6]:
                        st.markdown(f"- {x}")
                else:
                    st.markdown("- (내용 없음)")
                st.markdown("</div></div>", unsafe_allow_html=True)

                st.markdown("<div class='r-card'><div class='r-title'>보완 추천 영역</div><div class='pill-bad'>", unsafe_allow_html=True)
                if isinstance(needs, list) and needs:
                    for x in needs[:6]:
                        st.markdown(f"- {x}")
                else:
                    st.markdown("- (내용 없음)")
                st.markdown("</div></div>", unsafe_allow_html=True)

            # 3대 평가 항목
            if isinstance(detail, dict) and detail:
                st.markdown("<div class='r-card'><div class='r-title'>3대 평가 항목별 상세 분석</div></div>", unsafe_allow_html=True)

                for k, v in detail.items():
                    if not isinstance(v, dict):
                        continue
                    score = v.get("점수", 0)
                    stars = render_stars(score)
                    analysis = v.get("분석", "")
                    evidence = v.get("평가 근거 문장", []) or []

                    st.markdown(
                        f"""
                        <div class='r-card'>
                          <div class='r-title'>{k}</div>
                          <div class='stars'>{stars} <span class='badge'>{score}/10</span></div>
                          <div class='r-text'>{analysis}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if isinstance(evidence, list) and evidence:
                        st.markdown("<div class='r-card'><div class='r-title'>평가 근거</div>", unsafe_allow_html=True)
                        for e in evidence[:8]:
                            st.markdown(f"<div class='evi'>{e}</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)

            # 탐구 주제/학과/성장/도서 (있으면 표시)
            if isinstance(topics, dict) and any(str(v).strip() for v in topics.values()):
                st.markdown("<div class='r-card'><div class='r-title'>영역별 심화 탐구 주제 제안</div>", unsafe_allow_html=True)
                for k, v in topics.items():
                    if str(v).strip():
                        st.markdown(f"<div class='r-sub'>[{k}]</div><div class='r-text'>{v}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            if isinstance(majors, list) and majors:
                st.markdown("<div class='r-card'><div class='r-title'>역량 기반 추천 학과</div>", unsafe_allow_html=True)
                for m in majors[:8]:
                    if isinstance(m, dict):
                        st.markdown(f"<div class='r-sub'>{m.get('학과','')}</div><div class='r-text'>{m.get('근거','')}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='r-text'>- {m}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            if isinstance(growth, dict) and growth:
                st.markdown("<div class='r-card'><div class='r-title'>맞춤형 성장 제안</div>", unsafe_allow_html=True)
                for kk, vv in growth.items():
                    st.markdown(f"<div class='r-sub'>{kk}</div>", unsafe_allow_html=True)
                    if isinstance(vv, list):
                        for it in vv[:10]:
                            st.markdown(f"<div class='r-text'>- {it}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='r-text'>{vv}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            if isinstance(books, list) and books:
                st.markdown("<div class='r-card'><div class='r-title'>추천 도서</div>", unsafe_allow_html=True)
                for b in books[:10]:
                    if isinstance(b, dict):
                        line = f"[{b.get('분류','')}] {b.get('도서','')} / {b.get('저자','')}"
                        why = b.get("추천 이유", "")
                        st.markdown(f"<div class='r-sub'>{line}</div><div class='r-text'>{why}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='r-text'>- {b}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # ✅ PDF 저장 (TTF 경로 의존 제거: report_generator에서 처리)
            pdf_bytes = build_pdf_from_report(report, radar_png, sid, sname)
            st.download_button(
                label="📄 PDF로 저장",
                data=pdf_bytes,
                file_name=f"SH-Insight_{sid}_{sname}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            st.markdown("</div>", unsafe_allow_html=True)

        _show()

    if st.button("🧠 선택 학생 보고서 생성"):
        if selected.empty:
            st.warning("보고서를 생성할 학생을 선택하세요.")
            st.stop()

        results = []
        first_report = None
        first_meta = None

        total = len(selected)
        progress = st.progress(0)
        status = st.empty()

        for i, (_, row) in enumerate(selected.reset_index(drop=True).iterrows(), start=1):
            sid = str(row["학번"]).strip()
            sname = row["성명"]

            status.info(f"보고서 생성 중… ({i}/{total}) · {sid} {sname}")

            set_col = get_id_col(df_seteuk)
            hae_col = get_id_col(df_haeng)
            cha_col = get_id_col(df_chang)

            stu_seteuk = df_seteuk[normalize_id_series(df_seteuk[set_col]) == sid] if set_col in df_seteuk.columns else df_seteuk.iloc[0:0]
            stu_haeng = df_haeng[normalize_id_series(df_haeng[hae_col]) == sid] if hae_col in df_haeng.columns else df_haeng.iloc[0:0]
            stu_chang = df_chang[normalize_id_series(df_chang[cha_col]) == sid] if cha_col in df_chang.columns else df_chang.iloc[0:0]

            year_count = calc_year_count(stu_seteuk, stu_haeng, stu_chang)
            if year_count < 2:
                results.append((sid, sname, "❌ 1개년 이상 자료 없음"))
                progress.progress(int(i / total * 100))
                continue

            seteuk_text = extract_text(stu_seteuk)
            haeng_text = extract_text(stu_haeng)
            chang_text = extract_text(stu_chang)

            with st.spinner(f"{sid} {sname} 분석 중…"):
                report = generate_sh_insight_report(
                    student_id=sid,
                    masked_name=sname,
                    year_count=year_count,
                    seteuk_text=seteuk_text,
                    haengteuk_text=haeng_text,
                    changche_text=chang_text,
                )

            results.append((sid, sname, report))

            if first_report is None and isinstance(report, dict):
                first_report = report
                first_meta = (sid, sname)

            progress.progress(int(i / total * 100))

        status.success("보고서 생성이 완료되었습니다.")
        progress.empty()

        st.session_state["reports"] = results
        st.success("보고서 생성이 완료되었습니다.")

        # ✅ 자동 모달 (첫 번째 학생)
        if first_report is not None and first_meta is not None:
            render_report_modal(first_report, first_meta[0], first_meta[1])

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
