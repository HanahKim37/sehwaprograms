# utils/report_chart.py
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib import font_manager as fm


# -----------------------------
# 한글 폰트 자동 탐색 (matplotlib)
# -----------------------------
def _try_set_korean_font() -> Optional[str]:
    """
    가능한 한 '한글이 깨지지 않도록' matplotlib 폰트를 자동 설정한다.
    - Windows: Malgun Gothic
    - macOS: AppleGothic
    - Linux: NanumGothic / NotoSansCJK / etc.
    성공 시 font family name 반환, 실패 시 None
    """
    candidates = []

    # 1) OS별 대표 폰트 패밀리 이름 우선 시도
    for fam in ["Malgun Gothic", "AppleGothic", "NanumGothic", "Noto Sans CJK KR", "Noto Sans KR"]:
        candidates.append(("family", fam))

    # 2) 파일 경로 탐색 (자주 쓰는 경로)
    font_paths = [
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKkr-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansKR-Regular.otf",
        "/System/Library/Fonts/AppleGothic.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/malgunbd.ttf",
    ]

    # 프로젝트 내 fonts 폴더도 탐색(권장)
    here = Path(__file__).resolve().parent
    local_fonts = list((here / "fonts").glob("*.ttf")) + list((here / "fonts").glob("*.otf")) + list((here / "fonts").glob("*.ttc"))
    for p in local_fonts:
        font_paths.append(str(p))

    for fp in font_paths:
        if Path(fp).exists():
            candidates.append(("file", fp))

    # 적용 시도
    for kind, val in candidates:
        try:
            if kind == "family":
                plt.rcParams["font.family"] = val
                # 테스트: 폰트 매칭이 가능한지 확인
                _ = fm.findfont(val, fallback_to_default=False)
                plt.rcParams["axes.unicode_minus"] = False
                return val
            else:
                fm.fontManager.addfont(val)
                prop = fm.FontProperties(fname=val)
                fam = prop.get_name()
                plt.rcParams["font.family"] = fam
                plt.rcParams["axes.unicode_minus"] = False
                return fam
        except Exception:
            continue

    return None


# -----------------------------
# 레이더 차트 생성 (작게/가운데)
# -----------------------------
def build_radar_png(
    scores: Dict[str, float],
    size_inches: Tuple[float, float] = (3.0, 2.7),
    dpi: int = 220,
) -> BytesIO:
    """
    scores 예:
      {"학업역량": 9, "학업태도": 10, "학업 외 소양": 8}

    반환: PNG BytesIO (UI/PDF 공용)
    """
    _try_set_korean_font()

    labels = ["학업역량", "학업 외 소양", "학업태도"]  # 사진과 동일 순서/표기
    vals = [float(scores.get(k, 0) or 0) for k in labels]

    # 닫힌 다각형
    vals += vals[:1]
    n = len(labels)
    angles = [i / float(n) * 2 * 3.1415926535 for i in range(n)]
    angles += angles[:1]

    fig = plt.figure(figsize=size_inches)
    ax = fig.add_subplot(111, polar=True)

    # 위쪽 시작 + 시계방향
    ax.set_theta_offset(3.1415926535 / 2)
    ax.set_theta_direction(-1)

    # 라벨
    ax.set_thetagrids([a * 180 / 3.1415926535 for a in angles[:-1]], labels, fontsize=9)

    # 축 범위
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], fontsize=7)

    # 선/채움
    ax.plot(angles, vals, linewidth=2)
    ax.fill(angles, vals, alpha=0.15)

    # 여백 최소화
    fig.tight_layout(pad=0.6)

    out = BytesIO()
    fig.savefig(out, format="png", dpi=dpi, bbox_inches="tight", transparent=True)
    out.seek(0)
    plt.close(fig)
    return out
