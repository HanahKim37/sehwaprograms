# utils/text_builder.py
from __future__ import annotations

from typing import Iterable, Optional, Set
import pandas as pd


def get_id_col(df: pd.DataFrame) -> str:
    for c in ["번호", "학번", "학생번호", "student_id", "ID"]:
        if c in df.columns:
            return c
    return "번호"


def normalize_id_series(s: pd.Series) -> pd.Series:
    return s.astype(str).str.strip()


def calc_year_count(*dfs: pd.DataFrame) -> int:
    years: Set[str] = set()
    for df in dfs:
        if df is None or df.empty:
            continue
        if "학년" in df.columns:
            years.update(df["학년"].dropna().astype(str).str.strip().tolist())
    return len(years)


def extract_text(df: Optional[pd.DataFrame]) -> str:
    """
    원문이 '기록이 없음'으로 나오는 빈약 현상을 줄이기 위해,
    텍스트 후보 컬럼을 폭넓게 찾아 결합한다.
    """
    if df is None or df.empty:
        return ""

    drop_cols = {
        "번호", "학번", "학생번호", "성명", "이름", "학년", "반", "담임",
        "과목", "영역", "구분", "학기", "연도", "학년도"
    }

    cols = [c for c in df.columns if str(c).strip() and str(c) not in drop_cols]
    if not cols:
        return ""

    preferred_kw = ["세부", "특기", "행동", "종합", "의견", "창체", "체험", "활동", "기록", "내용", "서술", "요약"]
    preferred = [c for c in cols if any(k in str(c) for k in preferred_kw)]
    target_cols = preferred if preferred else cols

    blocks = []
    for c in target_cols:
        s = df[c]
        if isinstance(s, pd.DataFrame):  # 중복 컬럼명 방어
            s = s.iloc[:, 0]

        if pd.api.types.is_object_dtype(s) or pd.api.types.is_string_dtype(s):
            vals = (
                s.dropna()
                 .astype(str)
                 .map(lambda x: x.strip())
                 .tolist()
            )
            vals = [v for v in vals if v and v.lower() != "nan"]
            if vals:
                blocks.append(f"[{c}]\n" + "\n".join(vals))

    return "\n\n".join(blocks).strip()
