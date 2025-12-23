# utils/report_chart.py
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Dict, Optional

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm


def setup_matplotlib_korean_font():
    """
    프로젝트 내부 폰트(utils/fonts/*.ttf|*.otf)를 우선 사용하여
    matplotlib 한글 깨짐을 방지합니다.
    """
    try:
        matplotlib.rcParams["axes.unicode_minus"] = False
        here = Path(__file__).resolve().parent
        fonts_dir = here / "fonts"

        # 우선순위: NanumGothic 계열 → NotoSansKR 계열 → 기타 ttf/otf
        candidates = []
        if fonts_dir.exists():
            for name in [
                "NanumGothic-Regular.ttf",
                "NanumGothic.ttf",
                "NanumGothicBold.ttf",
                "NotoSansKR-Regular.otf",
                "NotoSansCJK-Regular.ttc",
            ]:
                p = fonts_dir / name
                if p.exists():
                    candidates.append(p)

            # 혹시 다른 폰트 파일이 들어있으면 그것도 후보에 추가
            for p in list(fonts_dir.glob("*.ttf")) + list(fonts_dir.glob("*.otf")):
                if p not in candidates:
                    candidates.append(p)

        for p in candidates:
            try:
                fm.fontManager.addfont(str(p))
                prop = fm.FontProperties(fname=str(p))
                matplotlib.rcParams["font.family"] = prop.get_name()
                return
            except Exception:
                continue
    except Exception:
        # 폰트 셋업 실패해도 앱이 죽지 않게
        return


def build_radar_png(scores: Dict[str, float], size_px: int = 300) -> Optional[BytesIO]:
    """
    scores 예:
      {"학업역량": 7, "학업태도": 8, "학업 외 소양": 6}
    반환: PNG BytesIO
    """
    labels = ["학업역량", "학업 외 소양", "학업태도"]  # 요청 순서 반영(사진 느낌)
    vals = [float(scores.get(k, 0) or 0) for k in labels]

    # 레이더 폐곡선
    vals_closed = vals + vals[:1]
    n = len(labels)
    angles = [i / float(n) * 2.0 * 3.1415926535 for i in range(n)]
    angles_closed = angles + angles[:1]

    # 작게 보이도록 (size_px 기준으로 적절히)
    fig = plt.figure(figsize=(size_px / 100, size_px / 100), dpi=200)
    ax = fig.add_subplot(111, polar=True)

    ax.set_theta_offset(3.1415926535 / 2)
    ax.set_theta_direction(-1)

    ax.set_thetagrids([a * 180 / 3.1415926535 for a in angles], labels, fontsize=9)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=7)

    ax.plot(angles_closed, vals_closed, linewidth=2)
    ax.fill(angles_closed, vals_closed, alpha=0.12)

    # 여백 최소화
    fig.tight_layout(pad=0.6)

    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.15)
    buf.seek(0)
    plt.close(fig)
    return buf


def render_radar_chart_to_streamlit(st, scores: Dict[str, float]) -> Optional[BytesIO]:
    """
    Streamlit에 표시 + PDF용 PNG(BytesIO)도 반환
    """
    png = build_radar_png(scores, size_px=320)
    if png is None:
        return None
    st.image(png, width=260)  # ✅ 그래프 크기: 강제로 작게
    return png
