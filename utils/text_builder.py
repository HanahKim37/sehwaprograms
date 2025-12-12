def build_text(df, content_col="내용"):
    """
    한 학생의 여러 행 기록을 하나의 텍스트로 합침
    """
    if df.empty:
        return ""

    texts = (
        df[content_col]
        .dropna()
        .astype(str)
        .tolist()
    )

    return "\n".join(texts)
