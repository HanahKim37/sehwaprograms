# utils/report_ui.py
from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List, Optional

import streamlit as st

from utils.report_chart import build_radar_png
from utils.report_pdf import build_pdf_bytes


# -----------------------------
# HTML/CSS (사진 레이아웃 최대한 유사)
# -----------------------------
UI_CSS = """
<style>
/* 전체 폭 정리 */
.report-wrap {max-width: 980px; margin: 0 auto;}

/* 상단 제목 */
.report-title{
  text-align:center;
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin: 8px 0 6px 0;
}
.report-sub{
  text-align:right;
  font-size: 18px;
  color:#111827;
  margin: 0 0 8px 0;
}
.hr-line{
  height:2px;
  background:#111827;
  border-radius: 1px;
  margin: 8px 0 18px 0;
}

/* 섹션 타이틀(왼쪽 바) */
.sec-title{
  display:flex;
  align-items:center;
  gap:10px;
  margin: 20px 0 10px 0;
}
.sec-bar{
  width:6px;
  height:22px;
  background:#9CA3AF;
  border-radius: 3px;
}
.sec-text{
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.3px;
}
.sec-note{
  font-size: 20px;
  font-weight: 700;
  color:#111827;
  margin-left: 6px;
}

/* 카드 */
.card{
  background:#ffffff;
  border:1px solid #E5E7EB;
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.card p{margin:0; line-height:1.65;}
.muted{color:#6B7280;}

/* 2열 박스 */
.grid2{
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.pill{
  border-radius: 16px;
  padding: 16px;
  border: 1px solid;
}
.pill h4{
  margin:0 0 10px 0;
  font-size: 18px;
  font-weight: 800;
}
.pill ul{margin:0; padding-left: 18px;}
.pill li{margin: 6px 0; line-height: 1.55;}
.pill.good{background:#ECFDF5; border-color:#A7F3D0;}
.pill.bad{background:#FEF2F2; border-color:#FECACA;}

/* 레이더 차트 영역 */
.chart-box{
  display:flex;
  justify-content:center;
  padding: 10px 0 0 0;
}

/* 평가 섹션 */
.eval-card{
  background:#fff;
  border:1px solid #E5E7EB;
  border-radius: 16px;
  padding: 18px;
  margin: 10px 0 14px 0;
}
.eval-head{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom: 10px;
}
.eval-head .name{
  font-size: 22px;
  font-weight: 800;
}
.eval-head .stars{
  font-size: 18px;
  color:#F59E0B;
  font-weight: 700;
}
.evidence{
  background:#F9FAFB;
  border:1px solid #E5E7EB;
  border-radius: 12px;
  padding: 12px 14px;
  margin: 10px 0 12px 0;
}
.evidence .ev-title{
  font-weight: 800;
  margin-bottom: 6px;
}
.evidence ul{margin:0; padding-left: 18px;}
.evidence li{margin: 5px 0; color:#111827;}

/* 성장 제안 */
.grid2b{
  display:grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.soft{
  background:#F9FAFB;
}

/* 심화탐구(하늘배경) */
.topic-card{
  background:#EFF6FF;
  border:1px solid #BFDBFE;
  border-radius: 16px;
  padding: 18px;
}
.topic-item{
  padding: 14px 0;
  border-top:1px dashed #CBD5E1;
}
.topic-item:first-child{
  border-top:none;
  padding-top: 6px;
}
.topic-item .k{
  font-weight: 900;
  font-size: 18px;
}
.topic-item .v{
  margin-top: 4px;
  color:#334155;
  line-height: 1.6;
}

/* 추천학과 3카드 */
.grid3{
  display:grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 14px;
}
.major-card{
  background:#fff;
  border:1px solid #E5E7EB;
  border-radius: 16px;
  padding: 16px;
}
.major-card .m-title{
  font-size: 20px;
  font-weight: 900;
  margin-bottom: 10px;
}
.major-card .m-body{
  color:#334155;
  line-height: 1.6;
}
</style>
"""


def _stars(score: int, max_score: int = 10) -> str:
    s = max(0, min(int(score), max_score))
    return "★" * s + "☆" * (max_score - s)


def _safe_list(x) -> List[str]:
    if isinstance(x, list):
        return [str(v) for v in x if str(v).strip()]
    return []


def _guess_major(report: Dict[str, Any]) -> str:
    majors = report.get("역량 기반 추천 학과", [])
    if isinstance(majors, list) and majors:
        m0 = majors[0]
        if isinstance(m0, dict):
            return str(m0.get("학과", "") or "")
        return str(m0)
    return ""


def render_report_dialog(report: Dict[str, Any], sid: str, sname: str) -> None:
    """
    결과창(대화상자) UI 전담.
    - 사진 레이아웃 최대한 유사
    - PDF 저장 버튼 포함
    """

    @st.dialog(f"📊 SH-Insight 심층 분석 보고서 · {sid} / {sname}", width="large")
    def show():
        st.markdown(UI_CSS, unsafe_allow_html=True)
        major = _guess_major(report)

        # 점수(레이더)
        detail = report.get("3대 평가 항목별 상세 분석", {})
        scores = {}
        if isinstance(detail, dict):
            for k in ["학업역량", "학업 외 소양", "학업태도"]:
                v = detail.get(k, {})
                if isinstance(v, dict):
                    scores[k] = v.get("점수", 0)

        radar_png = build_radar_png(scores, size_inches=(3.0, 2.7), dpi=220)

        # 상단(제목/학생정보/라인)
        st.markdown(
            f"""
            <div class="report-wrap">
              <div class="report-title">DK-Insight 심층 분석 보고서</div>
              <div class="report-sub">{sid} / {sname}</div>
              <div class="hr-line"></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 종합평가 섹션
        overall = str(report.get("종합 평가", "") or "")
        st.markdown(
            f"""
            <div class="report-wrap">
              <div class="sec-title">
                <div class="sec-bar"></div>
                <div class="sec-text">종합 평가</div>
                <div class="sec-note muted">(예상 희망 진로: {major})</div>
              </div>
              <div class="card">{overall}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 핵심역량 + 레이더
        st.markdown(
            """
            <div class="report-wrap">
              <div class="sec-title">
                <div class="sec-bar"></div>
                <div class="sec-text">핵심 역량 분석</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.markdown("<div class='report-wrap'><div class='card'><div class='chart-box'>", unsafe_allow_html=True)
        st.image(radar_png, width=340)  # ✅ 작게 고정
        st.markdown("</div></div></div>", unsafe_allow_html=True)

        # 강점/보완 2박스(색 박스 안에 문구)
        strengths = _safe_list(report.get("핵심 강점", []))
        needs = _safe_list(report.get("보완 추천 영역", []))

        left_li = "".join([f"<li>{st.html.escape(x) if hasattr(st, 'html') else x}</li>" for x in strengths]) if strengths else "<li>-</li>"
        right_li = "".join([f"<li>{st.html.escape(x) if hasattr(st, 'html') else x}</li>" for x in needs]) if needs else "<li>-</li>"

        st.markdown(
            f"""
            <div class="report-wrap">
              <div class="grid2">
                <div class="pill good">
                  <h4>핵심 강점 (Core Strengths)</h4>
                  <ul>{left_li}</ul>
                </div>
                <div class="pill bad">
                  <h4>보완 추천 영역 (Needs Improvement)</h4>
                  <ul>{right_li}</ul>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 3대 평가 항목별 상세 분석 + 별점 + 근거박스
        st.markdown(
            """
            <div class="report-wrap">
              <div class="sec-title">
                <div class="sec-bar"></div>
                <div class="sec-text">3대 평가 항목별 상세 분석</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if isinstance(detail, dict):
            for k in ["학업역량", "학업태도", "학업 외 소양"]:
                v = detail.get(k, {})
                if not isinstance(v, dict):
                    continue

                score = int(v.get("점수", 0) or 0)
                stars = _stars(score, 10)
                ev = _safe_list(v.get("평가 근거 문장", []))
                ev_li = "".join([f"<li>{e}</li>" for e in ev[:6]]) if ev else "<li>-</li>"
                analysis = str(v.get("분석", "") or "")

                st.markdown(
                    f"""
                    <div class="report-wrap">
                      <div class="eval-card">
                        <div class="eval-head">
                          <div class="name">{k}</div>
                          <div class="stars">{stars} ({score}/10)</div>
                        </div>
                        <div class="evidence">
                          <div class="ev-title">평가 근거 문장</div>
                          <ul>{ev_li}</ul>
                        </div>
                        <div class="muted" style="font-weight:800; margin-bottom:6px;">분석</div>
                        <div>{analysis}</div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # 맞춤형 성장 제안(좌) + 추천도서(우)
        growth = report.get("맞춤형 성장 제안", {})
        books = report.get("추천 도서", [])

        left_html = ""
        if isinstance(growth, dict):
            strategy = str(growth.get("생활기록부 중점 보완 전략", "") or "-")
            events = growth.get("추천 학교 행사", [])
            events_li = "".join([f"<li>{x}</li>" for x in events[:8]]) if isinstance(events, list) and events else "<li>-</li>"
            left_html = f"""
              <div class="card">
                <div style="font-size:20px; font-weight:900; margin-bottom:10px;">생활기록부 중점 보완 전략</div>
                <div style="line-height:1.7;">{strategy}</div>
                <div style="height:12px;"></div>
                <div style="font-size:20px; font-weight:900; margin-bottom:10px;">추천 학교 행사</div>
                <ul style="margin:0; padding-left:18px;">{events_li}</ul>
              </div>
            """

        right_html = ""
        if isinstance(books, list) and books:
            parts = []
            for b in books[:8]:
                if isinstance(b, dict):
                    cat = b.get("분류", "")
                    title = b.get("도서", "")
                    author = b.get("저자", "")
                    why = b.get("추천 이유", "")
                    parts.append(f"""
                      <div class="card soft" style="margin-bottom:10px;">
                        <div style="font-weight:900;">{cat}</div>
                        <div style="font-size:18px; font-weight:900; margin-top:6px;">{title} <span class="muted" style="font-weight:700;">({author})</span></div>
                        <div class="muted" style="margin-top:8px; line-height:1.6;">{why}</div>
                      </div>
                    """)
            right_html = "".join(parts)
        else:
            right_html = "<div class='card soft'>-</div>"

        st.markdown(
            f"""
            <div class="report-wrap">
              <div class="sec-title">
                <div class="sec-bar"></div>
                <div class="sec-text">맞춤형 성장 제안 (Growth Suggestions)</div>
              </div>
              <div class="grid2b">
                <div>{left_html}</div>
                <div>{right_html}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 영역별 심화 탐구 주제 제안(하늘배경, 자율/진로/동아리)
        topics = report.get("영역별 심화 탐구 주제 제안", {})
        def _topic(k: str) -> str:
            if isinstance(topics, dict):
                return str(topics.get(k, "") or "")
            return ""

        st.markdown(
            f"""
            <div class="report-wrap">
              <div class="sec-title">
                <div class="sec-bar"></div>
                <div class="sec-text">영역별 심화 탐구 주제 제안</div>
              </div>
              <div class="topic-card">
                <div class="topic-item">
                  <div class="k">[자율] {_topic("자율")}</div>
                </div>
                <div class="topic-item">
                  <div class="k">[진로] {_topic("진로")}</div>
                </div>
                <div class="topic-item">
                  <div class="k">[동아리] {_topic("동아리")}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 역량 기반 추천 학과(3박스)
        majors = report.get("역량 기반 추천 학과", [])
        cards = []
        if isinstance(majors, list) and majors:
            for m in majors[:3]:
                if isinstance(m, dict):
                    dept = str(m.get("학과", "") or "")
                    reason = str(m.get("근거", "") or "")
                else:
                    dept = str(m)
                    reason = ""
                cards.append((dept, reason))

        while len(cards) < 3:
            cards.append(("-", "-"))

        st.markdown(
            f"""
            <div class="report-wrap">
              <div class="sec-title">
                <div class="sec-bar"></div>
                <div class="sec-text">역량 기반 추천 학과</div>
              </div>
              <div class="grid3">
                <div class="major-card">
                  <div class="m-title">{cards[0][0]}</div>
                  <div class="m-body">{cards[0][1]}</div>
                </div>
                <div class="major-card">
                  <div class="m-title">{cards[1][0]}</div>
                  <div class="m-body">{cards[1][1]}</div>
                </div>
                <div class="major-card">
                  <div class="m-title">{cards[2][0]}</div>
                  <div class="m-body">{cards[2][1]}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # PDF 다운로드(레이아웃 동일 기준)
        pdf_bytes = build_pdf_bytes(report, radar_png, sid, sname)
        st.download_button(
            label="📄 PDF로 저장",
            data=pdf_bytes,
            file_name=f"SH-Insight_{sid}_{sname}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    show()
