import pandas as pd
import re

def load_changche(file):
    """창체 파일을 분석하여 학생별 활동 데이터프레임을 반환합니다."""
    
    df_raw = pd.read_excel(file, header=None)

    # 1) 헤더 탐색 (번 호, 성명, 창의적체험활동 등이 들어 있는 1차 헤더)
    header_row1 = None
    for i, row in df_raw.iterrows():
        line = " ".join(row.astype(str).tolist())
        if ("번 호" in line) and ("성" in line) and ("창의적체험활동" in line):
            header_row1 = i
            break

    if header_row1 is None:
        raise ValueError("창체 헤더를 찾지 못했습니다.")

    header_row2 = header_row1 + 1  # 영역/시간 등이 있는 2차 헤더

    header1 = df_raw.iloc[header_row1].fillna("")
    header2 = df_raw.iloc[header_row2].fillna("")

    # 2) 멀티 헤더 결합
    combined = header1.astype(str) + "_" + header2.astype(str)
    combined = combined.str.replace("_nan", "", regex=False).str.replace("_$", "", regex=True)

    df = df_raw.iloc[header_row2 + 1:].copy()
    df.columns = combined

    # 3) 핵심 컬럼 이름 정규화
    def normalize(c):
        return str(c).replace(" ", "")

    rename_map = {}
    for col in df.columns:
        nc = normalize(col)
        if "번호" in nc or "번호" in nc:
            rename_map[col] = "번호"
        elif "성명" in nc or "성명" in col or "성명" in nc:
            rename_map[col] = "성명"
        elif "학년" in nc:
            rename_map[col] = "학년"
        elif "창의적체험활동_영역" in nc:
            rename_map[col] = "영역"
        elif "시간" in nc:
            rename_map[col] = "시간"

    df = df.rename(columns=rename_map)

    keep_cols = [c for c in ["번호", "성명", "학년", "영역", "시간"] if c in df.columns]
    df = df[keep_cols]

    # 4) 빈값 보완
    for c in ["번호", "성명", "학년"]:
        if c in df.columns:
            df[c] = df[c].ffill()

    df = df.dropna(how="all")

    return df.reset_index(drop=True)
