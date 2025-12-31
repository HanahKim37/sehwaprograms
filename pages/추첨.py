import os
import sys
import streamlit as st
import pandas as pd
import io

# === [공통 사이드바 import 설정] ======================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))   # .../sehwaprograms/pages
PARENT_DIR = os.path.dirname(CURRENT_DIR)                  # .../sehwaprograms

if PARENT_DIR not in sys.path:
    sys.path.append(PARENT_DIR)

# ✅ utils 폴더 안의 sidebar.py 사용
from utils.sidebar import render_sidebar
# =====================================================================

# ✅ 모든 페이지에서 사이드바 렌더링
render_sidebar()

st.title("🎲 추첨 프로그램")
st.write(
    """
업로드한 엑셀 파일에서 **'학번'** 과 **'이름'** 열을 찾아  
설정한 인원 수만큼 무작위로 추첨하는 페이지입니다.
"""
)

# 🔹 1. 엑셀 파일 업로드
uploaded_file = st.file_uploader(
    "엑셀 파일을 업로드하세요 (.xlsx, .xls)",
    type=["xlsx", "xls"],
)

# 🔹 2. 추첨 인원 입력
num_winners = st.number_input(
    "추첨 인원 수를 입력하세요",
    min_value=1,
    step=1,
)

if uploaded_file is None:
    st.info("먼저 엑셀 파일을 업로드해주세요.")
    st.stop()

try:
    df = pd.read_excel(uploaded_file)
except Exception:
    st.error("엑셀 파일을 읽는 중 오류가 발생했습니다. 파일 형식을 다시 확인해주세요.")
    st.stop()

required_cols = ["학번", "이름"]

if not all(col in df.columns for col in required_cols):
    st.error("엑셀에 **'학번'**, **'이름'** 열이 모두 존재해야 합니다.")
    st.write("현재 엑셀에 있는 열 목록:", list(df.columns))
    st.stop()

st.subheader("업로드된 데이터 미리보기")
st.dataframe(df[required_cols].head())

total_count = len(df)

if total_count == 0:
    st.warning("데이터가 한 행도 없습니다. 엑셀 파일 내용을 확인해주세요.")
    st.stop()

if int(num_winners) > total_count:
    st.warning(f"추첨 인원({int(num_winners)}명)이 전체 인원({total_count}명)보다 많습니다. 인원 수를 줄여주세요.")
    st.stop()

if st.button("✅ 추첨 시작"):
    result_df = df[required_cols].sample(
        n=int(num_winners),
        replace=False,
        random_state=None,
    ).reset_index(drop=True)

    result_df.index = result_df.index + 1
    result_df.index.name = "번호"

    st.success("추첨이 완료되었습니다.")
    st.subheader("추첨 결과")
    st.dataframe(result_df)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        result_df.to_excel(writer, sheet_name="추첨결과")
    output.seek(0)

    st.download_button(
        label="📥 추첨 결과 엑셀 다운로드",
        data=output,
        file_name="추첨결과.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
