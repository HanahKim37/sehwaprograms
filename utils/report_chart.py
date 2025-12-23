from __future__ import annotations

from io import BytesIO
from pathlib import Path
import math

import matplotlib.pyplot as plt
from matplotlib import font_manager


# -------------------------------------------------
# 한글 폰트 설정
# -------------------------------------------------
def setup_matplotlib_korean_font(_st=None):
    """
    기존 호출 호환을 위해 _st 인자를 받지만 사용하지 않습니다.
    """
    fonts_dir = Path(__file__).resolve().parent / "fonts"
    font_files = []

    if fonts_dir.exists():
        font_files += list(fonts_dir.glob("*.ttf"))
        font_files += list(fonts_dir.glob("*.otf"))
        font_files += list(fonts_dir.glob("*.ttc"))

    chosen_family = None

    # 폰트 등록
    for fp in font_files:
        try:
            font_manager.fontManager.addfont(str(fp))
        except Exception:
            pass

    # 나눔/노토 우선 선택
    for fp in font_files:
        name = fp.stem.lower()
        if "nanum" in name or "noto" in name:
            try:
                prop = font_manager.FontProperties(fname=str(fp))
                chosen_family = prop.get_name()
                break
            except Exception:
                continue

    # 못 찾으면 첫 폰트라도 사용
    if chosen_family is None and font_files:
        try:
            prop = font_manager.FontProperties(fname=str(font_files[0]))
            chosen_family = prop.get_name()
        except Exception:
            pass

    if chosen_family:
        plt.rcParams["font.family"] = chosen_family

    plt.rcParams["axes.unicode_minus"] = False


# -------------------------------------------------
# 내부 공통 레이더 생성
# -------------------------------------------------
def _make_radar_figure(scores: dict, size=(3.2, 3.0)):
    labels = ["학업역량", "학업태도", "학업 외 소양"]
    values = [float(scores.get(k, 0) or 0) for k in labels]

    values += values[:1]
    angles = [n / float(len(labels)) * 2 * math.pi for n in range(len(labels))]
    angles += angles[:1]

    fig = plt.figure(figsize=size)
    ax = fig.add_subplot(111, polar=True)

    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_thetagrids(
        [a * 180 / math.pi for a in angles[:-1]],
        labels,
        fontsize=9,
    )
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=8)

    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.15)

    return fig


# -------------------------------------------------
# Streamlit 표시 + PNG 반환 (호환 시그니처)
# -------------------------------------------------
def render_radar_chart_to_streamlit(*args, **kwargs) -> BytesIO:
    """
    ✅ 기존 메인 호출: render_radar_chart_to_streamlit(st, scores)
    ✅ 신규 호출: render_radar_chart_to_streamlit(scores)

    둘 다 지원합니다.
    반환: PNG(BytesIO) - PDF 삽입용
    """
    # args 파싱
    if len(args) == 2:
        st_obj, scores = args
    elif len(args) == 1:
        st_obj, scores = None, args[0]
    else:
        st_obj = kwargs.get("st")
        scores = kwargs.get("scores", {})

    # figure size (그래프 작게)
    size = kwargs.get("size", (3.2, 3.0))
    dpi = int(kwargs.get("dpi", 180))

    fig = _make_radar_figure(scores or {}, size=size)

    # Streamlit 표시 (st 전달된 경우만)
    if st_obj is not None:
        st_obj.pyplot(fig, clear_figure=True)

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf


# -------------------------------------------------
# UI/PDF 공용 PNG 생성 (report_ui에서 import)
# -------------------------------------------------
def build_radar_png(scores: dict, size=(3.2, 3.0), dpi=180) -> BytesIO:
    fig = _make_radar_figure(scores or {}, size=size)
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=int(dpi), bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    return buf
