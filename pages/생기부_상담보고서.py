import streamlit as st
import pandas as pd

from utils.sidebar import render_sidebar
from utils.parser_seteuk import load_seteuk
from utils.parser_haengteuk import load_haengteuk
from utils.parser_changche import load_changche
from utils.ai_report_generator import generate_sh_insight_report

# --- PDF / Chart deps (추가) ---
from io import BytesIO
from datetime import datetime

import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib import colors


st.set_page_config(page_title="SH-Insight 상담보고서", layout="wide")
render_sidebar()

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
# 유틸: 원문 텍스트 추출 (빈약/기록없음 방지의 핵심)
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
# 레이더 차트 (추가)
# -----------------------------
def render_radar_chart(scores: dict):
    """
    scores 예: {"학업역량": 9, "학업태도": 10, "학업 외 소양": 9}
    """
    labels = ["학업역량", "학업태도", "학업 외 소양"]
    values = [float(scores.get(k, 0)) for k in labels]

    # 닫힌 폴리곤
    values += values[:1]
    angles = [n / float(len(labels)) * 2 * 3.1415926535 for n in range(len(labels))]
    angles += angles[:1]

    fig = plt.figure(figsize=(4.8, 4.2))
    ax = fig.add_subplot(111, polar=True)

    ax.set_theta_offset(3.1415926535 / 2)
    ax.set_theta_direction(-1)

    ax.set_thetagrids([a * 180 / 3.1415926535 for a in angles[:-1]], labels, fontsize=10)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=8)

    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.15)

    st.pyplot(fig, clear_figure=True)

    # PDF용 이미지 바이트도 함께 반환
    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", dpi=200, bbox_inches="tight")
    img_buf.seek(0)
    plt.close(fig)
    return img_buf

# -----------------------------
# PDF 생성 (추가)
# -----------------------------
def build_pdf_bytes(report: dict, radar_png: BytesIO, sid: str, sname: str) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    story = []

    title = f"SH-Insight 심층 분석 보고서"
    subtitle = f"{sid} / {sname}   |   생성: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    story.append(Paragraph(f"<b>{title}</b>", styles["Title"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(subtitle, styles["Normal"]))
    story.append(Spacer(1, 14))

    # 종합 평가
    story.append(Paragraph("<b>종합 평가</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(str(report.get("종합 평가", "")), styles["BodyText"]))
    story.append(Spacer(1, 12))

    # 레이더
    story.append(Paragraph("<b>핵심 역량 레이더</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    if radar_png is not None:
        img = RLImage(radar_png, width=140*mm, height=120*mm)
        story.append(img)
        story.append(Spacer(1, 10))

    # 강점/보완
    def _list_to_paras(title_txt, items):
        story.append(Paragraph(f"<b>{title_txt}</b>", styles["Heading2"]))
        story.append(Spacer(1, 6))
        if isinstance(items, list) and items:
            for it in items:
                story.append(Paragraph(f"• {str(it)}", styles["BodyText"]))
        else:
            story.append(Paragraph("-", styles["BodyText"]))
        story.append(Spacer(1, 12))

    _list_to_paras("핵심 강점", report.get("핵심 강점", []))
    _list_to_paras("보완 추천 영역", report.get("보완 추천 영역", []))

    # 3대 평가 항목
    story.append(Paragraph("<b>3대 평가 항목별 상세 분석</b>", styles["Heading2"]))
    story.append(Spacer(1, 6))
    items = report.get("3대 평가 항목별 상세 분석", {})
    if isinstance(items, dict) and items:
        for k, v in items.items():
            story.append(Paragraph(f"<b>{k}</b>", styles["Heading3"]))
            if isinstance(v, dict):
                score = v.get("점수", "")
                story.append(Paragraph(f"점수: {score}/10", styles["BodyText"]))
                ev = v.get("평가 근거 문장", [])
                if isinstance(ev, list) and ev:
                    story.append(Paragraph("근거 문장:", styles["BodyText"]))
                    for e in ev[:6]:
                        story.append(Paragraph(f" - {str(e)}", styles["BodyText"]))
                story.append(Spacer(1, 4))
                story.append(Paragraph(str(v.get("분석", "")), styles["BodyText"]))
            else:
                story.append(Paragraph(str(v), styles["BodyText"]))
            story.append(Spacer(1, 10))
    else:
        story.append(Paragraph("-", styles["BodyText"]))
        story.append(Spacer(1, 12))

    # 탐구 주제/추천 학과/성장 제안/도서
    def _section(title_txt, content):
        story.append(Paragraph(f"<b>{title_txt}</b>", styles["Heading2"]))
        story.append(Spacer(1, 6))
        if isinstance(content, dict):
            for k, v in content.items():
                story.append(Paragraph(f"<b>{k}</b>: {str(v)}", styles["BodyText"]))
        elif isinstance(content, list):
            for it in content:
                story.append(Paragraph(f"• {str(it)}", styles["BodyText"]))
        else:
            story.append(Paragraph(str(content), styles["BodyText"]))
        story.append(Spacer(1, 12))

    _section("영역별 심화 탐구 주제 제안", report.get("영역별 심화 탐구 주제 제안", {}))
    _section("역량 기반 추천 학과", report.get("역량 기반 추천 학과", []))
    _section("맞춤형 성장 제안", report.get("맞춤형 성장 제안", {}))

    # 추천 도서 표(있으면)
    books = report.get("추천 도서", [])
    if isinstance(books, list) and books:
        story.append(Paragraph("<b>추천 도서</b>", styles["Heading2"]))
        story.append(Spacer(1, 6))
        data = [["분류", "도서", "저자", "추천 이유"]]
        for b in books[:10]:
            if isinstance(b, dict):
                data.append([str(b.get("분류","")), str(b.get("도서","")), str(b.get("저자","")), str(b.get("추천 이유",""))])
            else:
                data.append(["", str(b), "", ""])
        tbl = Table(data, colWidths=[22*mm, 55*mm, 30*mm, 65*mm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
            ("GRID", (0,0), (-1,-1), 0.5, colors.lightgrey),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("PADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 12))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

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
            overall = report.get("종합 평가", "")
            strengths = report.get("핵심 강점", [])
            needs = report.get("보완 추천 영역", [])
            detail = report.get("3대 평가 항목별 상세 분석", {})
            growth = report.get("맞춤형 성장 제안", {})
            majors = report.get("역량 기반 추천 학과", [])
            topics = report.get("영역별 심화 탐구 주제 제안", {})
            books = report.get("추천 도서", [])

            # 점수 추출
            scores = {}
            if isinstance(detail, dict):
                for key in ["학업역량", "학업태도", "학업 외 소양"]:
                    v = detail.get(key, {})
                    if isinstance(v, dict):
                        scores[key] = v.get("점수", 0)

            st.markdown(f"<div class='card'><div class='card-title'>종합 평가</div>{overall}</div>", unsafe_allow_html=True)

            # 레이더 차트
            st.markdown("<div class='card'><div class='card-title'>핵심 역량 레이더</div>", unsafe_allow_html=True)
            radar_png = render_radar_chart(scores)
            st.markdown("</div>", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<div class='card'><div class='card-title'>핵심 강점</div><div class='pill-good'>", unsafe_allow_html=True)
                for x in strengths:
                    st.markdown(f"- {x}")
                st.markdown("</div></div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='card'><div class='card-title'>보완 추천 영역</div><div class='pill-bad'>", unsafe_allow_html=True)
                for x in needs:
                    st.markdown(f"- {x}")
                st.markdown("</div></div>", unsafe_allow_html=True)

            st.markdown("<div class='card'><div class='card-title'>3대 평가 항목별 상세 분석</div></div>", unsafe_allow_html=True)
            if isinstance(detail, dict):
                for k, v in detail.items():
                    if isinstance(v, dict):
                        st.markdown(f"<div class='card'><div class='card-title'>{k}  ({v.get('점수','')}/10)</div>", unsafe_allow_html=True)
                        ev = v.get("평가 근거 문장", [])
                        if isinstance(ev, list) and ev:
                            st.markdown("**평가 근거 문장**")
                            for e in ev[:6]:
                                st.markdown(f"- {e}")
                        st.markdown("**분석**")
                        st.write(v.get("분석",""))
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='card'><div class='card-title'>{k}</div>{v}</div>", unsafe_allow_html=True)

            st.markdown("<div class='card'><div class='card-title'>영역별 심화 탐구 주제 제안</div></div>", unsafe_allow_html=True)
            if isinstance(topics, dict):
                for k, v in topics.items():
                    st.markdown(f"<div class='card'><div class='card-title'>[{k}]</div>{v}</div>", unsafe_allow_html=True)

            st.markdown("<div class='card'><div class='card-title'>역량 기반 추천 학과</div></div>", unsafe_allow_html=True)
            if isinstance(majors, list):
                for m in majors:
                    if isinstance(m, dict):
                        st.markdown(f"<div class='card'><div class='card-title'>{m.get('학과','')}</div>{m.get('근거','')}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"- {m}")

            st.markdown("<div class='card'><div class='card-title'>맞춤형 성장 제안</div></div>", unsafe_allow_html=True)
            if isinstance(growth, dict):
                for k, v in growth.items():
                    if isinstance(v, list):
                        st.markdown(f"<div class='card'><div class='card-title'>{k}</div>", unsafe_allow_html=True)
                        for it in v:
                            st.markdown(f"- {it}")
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='card'><div class='card-title'>{k}</div>{v}</div>", unsafe_allow_html=True)

            if isinstance(books, list) and books:
                st.markdown("<div class='card'><div class='card-title'>추천 도서</div></div>", unsafe_allow_html=True)
                for b in books:
                    if isinstance(b, dict):
                        st.markdown(
                            f"<div class='card'><div class='card-title'>[{b.get('분류','')}] {b.get('도서','')} ({b.get('저자','')})</div>{b.get('추천 이유','')}</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(f"- {b}")

            # --- PDF 저장 버튼 (요구사항 1) ---
            pdf_bytes = build_pdf_bytes(report, radar_png, sid, sname)
            st.download_button(
                label="📄 PDF로 저장",
                data=pdf_bytes,
                file_name=f"SH-Insight_{sid}_{sname}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        _show()

    if st.button("🧠 선택 학생 보고서 생성"):
        if selected.empty:
            st.warning("보고서를 생성할 학생을 선택하세요.")
            st.stop()

        results = []
        first_report = None
        first_meta = None

        for _, row in selected.reset_index(drop=True).iterrows():
            sid = str(row["학번"]).strip()
            sname = row["성명"]

            set_col = get_id_col(df_seteuk)
            hae_col = get_id_col(df_haeng)
            cha_col = get_id_col(df_chang)

            stu_seteuk = df_seteuk[normalize_id_series(df_seteuk[set_col]) == sid] if set_col in df_seteuk.columns else df_seteuk.iloc[0:0]
            stu_haeng = df_haeng[normalize_id_series(df_haeng[hae_col]) == sid] if hae_col in df_haeng.columns else df_haeng.iloc[0:0]
            stu_chang = df_chang[normalize_id_series(df_chang[cha_col]) == sid] if cha_col in df_chang.columns else df_chang.iloc[0:0]

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

            if first_report is None and isinstance(report, dict):
                first_report = report
                first_meta = (sid, sname)

        st.session_state["reports"] = results
        st.success("보고서 생성이 완료되었습니다.")

        # 자동 모달
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
