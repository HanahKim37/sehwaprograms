import streamlit as st
import pandas as pd

st.set_page_config(page_title="학생 결과물 보기", layout="centered")

st.title("📝 학생 결과물 정리")

# 파일 업로드
uploaded_file = st.file_uploader("📁 학생 결과물이 담긴 엑셀 파일을 업로드하세요", type=["xlsx"])

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        # 필수 컬럼 존재 확인
        required_columns = ["학년", "반", "번호", "이름", "과제명", "제출일", "내용"]
        if not all(col in df.columns for col in required_columns):
            st.error("❗ 엑셀 파일에 다음과 같은 컬럼이 모두 포함되어야 합니다: " + ", ".join(required_columns))
        else:
            st.success("✅ 파일이 성공적으로 업로드되었습니다.")

            # 선택박스 생성
            grade = st.selectbox("학년", sorted(df["학년"].unique()))
            classroom = st.selectbox("반", sorted(df[df["학년"] == grade]["반"].unique()))
            number = st.selectbox("번호", sorted(df[(df["학년"] == grade) & (df["반"] == classroom)]["번호"].unique()))
            name = st.selectbox("이름", sorted(df[(df["학년"] == grade) & (df["반"] == classroom) & (df["번호"] == number)]["이름"].unique()))

            # 해당 학생의 결과물 필터링
            filtered_df = df[
                (df["학년"] == grade) &
                (df["반"] == classroom) &
                (df["번호"] == number) &
                (df["이름"] == name)
            ]

            st.subheader(f"📄 {grade}학년 {classroom}반 {number}번 {name} 학생의 제출 결과물")

            if filtered_df.empty:
                st.info("해당 학생의 결과물이 없습니다.")
            else:
                st.dataframe(filtered_df[["과제명", "제출일", "내용"]].sort_values(by="제출일"))

                # 다운로드 옵션
                csv = filtered_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 결과물 다운로드 (CSV)",
                    data=csv,
                    file_name=f"{grade}_{classroom}_{number}_{name}_결과물.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"❗ 파일을 읽는 중 오류가 발생했습니다: {e}")
else:
    st.info("먼저 엑셀 파일을 업로드해주세요.")

