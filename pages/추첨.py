import streamlit as st
import pandas as pd
import io

# 🔹 페이지 기본 설정
st.set_page_config(
    page_title="엑셀 추첨기",
    page_icon="🎲",
    layout="centered",
)

st.title("🎲 엑셀 기반 랜덤 추첨기")
st.write(
    """
업로드한 엑셀 파일에서 **'학번'** 과 **'이름'** 열을 자동으로 찾아  
설정한 인원 수만큼 무작위로 추첨하는 프로그램입니다.
"""
)

# 🔹 엑셀 파일 업로드
uploaded_file = st.file_uploader(
    "엑셀 파일을 업로드하세요 (.xlsx, .xls)",
    type=["xlsx", "xls"],
)

# 🔹 추첨 인원 입력
num_winners = st.number_input(
    "추첨 인원 수를 입력하세요",
    min_value=1,
    step=1,
)

# 결과 저장용 변수 초기화
result_df = None

if uploaded_file is not None:
    try:
        # 엑셀 파일 읽기 (첫 번째 시트 기준)
        df = pd.read_excel(uploaded_file)

    except Exception as e:
        st.error("엑셀 파일을 읽는 중 오류가 발생했습니다. 파일 형식을 다시 확인해주세요.")
        st.stop()

    required_cols = ["학번", "이름"]

    # 🔹 필수 열 존재 여부 확인
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

    if num_winners > total_count:
        st.warning(f"추첨 인원({int(num_winners)}명)이 전체 인원({total_count}명)보다 많습니다. 인원 수를 줄여주세요.")
    else:
        # 🔹 추첨 실행 버튼
        if st.button("✅ 추첨 시작"):
            # 무작위 샘플링
            result_df = df[required_cols].sample(
                n=int(num_winners),
                replace=False,   # 중복 없이 추첨
                random_state=None,  # 실행할 때마다 다른 결과
            ).reset_index(drop=True)

            # 보기 좋게 번호 컬럼 추가
            result_df.index = result_df.index + 1
            result_df.index.name = "번호"

            st.success("추첨이 완료되었습니다.")
            st.subheader("추첨 결과")
            st.dataframe(result_df)

            # 🔹 엑셀로 다운로드할 수 있도록 버퍼에 저장
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

# 추첨 버튼 누르기 전에 다운로드 버튼이 보이지 않도록 처리
elif uploaded_file is None:
    st.info("먼저 엑셀 파일을 업로드해주세요.")
