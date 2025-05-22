import streamlit as st
import pandas as pd

st.set_page_config(page_title="창탐페 신청 검사", layout="centered")
st.title("🔍 창의탐구페스티벌 타임별 명단 비교")

st.write("두 엑셀 파일을 업로드하세요. 각 파일에는 학년, 반, 번호, 이름, 신청강좌 컬럼이 포함되어야 합니다.")

a_file = st.file_uploader("📁 A타임 신청 명단 업로드", type=["xlsx"])
b_file = st.file_uploader("📁 B타임 신청 명단 업로드", type=["xlsx"])

if a_file and b_file:
    try:
        df_a = pd.read_excel(a_file)
        df_b = pd.read_excel(b_file)

        required_columns = ["학년", "반", "번호", "이름", "신청강좌"]
        if not all(col in df_a.columns for col in required_columns) or not all(col in df_b.columns for col in required_columns):
            st.error("❗ 두 파일 모두에 다음 컬럼이 있어야 합니다: " + ", ".join(required_columns))
        else:
            # 학생 고유 식별자 열 추가 (학년-반-번호-이름)
            df_a["식별자"] = df_a["학년"].astype(str) + "-" + df_a["반"].astype(str) + "-" + df_a["번호"].astype(str) + "-" + df_a["이름"]
            df_b["식별자"] = df_b["학년"].astype(str) + "-" + df_b["반"].astype(str) + "-" + df_b["번호"].astype(str) + "-" + df_b["이름"]

            # 같은 강좌를 신청한 학생 (A, B 둘 다 같은 강좌 신청)
            merged = pd.merge(df_a, df_b, on="식별자", suffixes=("_A", "_B"))
            same_course = merged[merged["신청강좌_A"] == merged["신청강좌_B"]]

            st.subheader("⚠️ A타임과 B타임에 동일한 강좌를 신청한 학생")
            if same_course.empty:
                st.success("A타임과 B타임에 같은 강좌를 신청한 학생이 없습니다.")
            else:
                st.dataframe(same_course[["학년_A", "반_A", "번호_A", "이름_A", "신청강좌_A"]].rename(columns={
                    "학년_A": "학년", "반_A": "반", "번호_A": "번호", "이름_A": "이름", "신청강좌_A": "신청강좌"
                }))

            # B타임에만 있고 A타임에 없는 학생
            only_b = df_b[~df_b["식별자"].isin(df_a["식별자"])]

            st.subheader("🚫 A타임에는 없는데 B타임에만 신청한 학생")
            if only_b.empty:
                st.success("모든 B타임 신청자는 A타임에도 존재합니다.")
            else:
                st.dataframe(only_b[["학년", "반", "번호", "이름", "신청강좌"]])

    except Exception as e:
        st.error(f"❗ 파일 처리 중 오류가 발생했습니다: {e}")
