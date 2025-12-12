import pandas as pd
from openpyxl import load_workbook

import re

def load_haengteuk(file):
    """행동특성 파일을 분석하여 학생별 학년·행특 내용으로 구성된 DF 반환."""

    raw = pd.read_excel(file, header=None)

    # 1) 헤더 탐지
    header_row = None
    for i, row in raw.iterrows():
        line = " ".join(row.astype(str).tolist())
        if ("번 호" in line) and ("성" in line) and ("학 년" in line) and ("행 동" in line):
            header_row = i
            break

    if header_row is None:
        raise ValueError("행특 헤더를 찾지 못했습니다.")

    # 2) 헤더 지정 후 데이터 읽기
    header = raw.iloc[header_row].fillna("")
    df = raw.iloc[header_row + 1:].copy()
    df.columns = header

    # 3) 컬럼 정규화
    def norm(c):
        return str(c).replace(" ", "")

    rename_map = {}
    for col in df.columns:
        nc = norm(col)
        if "번호" in nc or "번호" in nc:
            rename_map[col] = "번호"
        elif "성명" in nc or "성명" in col:
            rename_map[col] = "성명"
        elif "학년" in nc:
            rename_map[col] = "학년"
        elif "행동특성" in nc or "종합의견" in nc:
            rename_map[col] = "행특내용"

    df = df.rename(columns=rename_map)

    # 4) 필요 없는 행 제거 (헤더 반복 제거)
    df = df[~df["번호"].astype(str).str.contains("번", na=False)]

    # 5) 값 보완
    for c in ["번호", "성명", "학년"]:
        if c in df.columns:
            df[c] = df[c].ffill()

    df["행특내용"] = df["행특내용"].astype(str).str.strip()
    df = df[df["행특내용"] != ""]

    df["학년"] = pd.to_numeric(df["학년"], errors="coerce")

    return df.reset_index(drop=True)
