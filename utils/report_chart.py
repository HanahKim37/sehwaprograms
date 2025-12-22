import os
from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib import font_manager as fm


def _candidate_font_paths():
    here = os.path.dirname(os.path.abspath(__file__))
    proj_root = os.path.abspath(os.path.join(here, ".."))
    return [
        os.path.join(proj_root, "assets", "NanumGothic.ttf"),
        os.path.join(proj_root, "assets", "NotoSansKR-Regular.ttf"),
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]


def setup_matplotlib_korean_font() -> bool:
    for fp in _candidate_font_paths():
        if fp and os.path.exists(fp):
            try:
                fm.fontManager.addfont(fp)
                font_name = fm.FontProperties(fname=fp).get_name()
                plt.rcParams["font.family"] = font_name
                plt.rcParams["axes.unicode_minus"] = False
                return True
            except Exception:
                continue
    return False


def render_radar_chart_to_streamlit(st, scores: dict) -> BytesIO:
    """
    Streamlit에 레이더 차트를 '작게' 출력하고, PDF용 PNG BytesIO도 반환.
    labels는 사진 요구사항대로 한글로 고정.
    """
    labels = ["학업역량", "학업 외 소양", "학업태도"]
    values = [float(scores.get(k, 0) or 0) for k in labels]

    # closed polygon
    values += values[:1]
    N = len(labels)
    angles = [n / float(N) * 2 * 3.1415926535 for n in range(N)]
    angles += angles[:1]

    fig = plt.figure(figsize=(3.3, 3.0), dpi=160)
    ax = fig.add_subplot(111, polar=True)
    ax.set_theta_offset(3.1415926535 / 2)
    ax.set_theta_direction(-1)

    ax.set_thetagrids([a * 180 / 3.1415926535 for a in angles[:-1]], labels, fontsize=9)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=7)

    ax.plot(angles, values, linewidth=2)
    ax.fill(angles, values, alpha=0.15)

    st.pyplot(fig, clear_figure=True)

    img_buf = BytesIO()
    fig.savefig(img_buf, format="png", dpi=220, bbox_inches="tight")
    img_buf.seek(0)
    plt.close(fig)
    return img_buf
