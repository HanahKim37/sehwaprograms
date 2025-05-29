import streamlit as st
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd
from streamlit_drawable_canvas import st_canvas

# 페이지 설정
st.set_page_config(page_title="AI 시각화 체험기", layout="wide")
st.title("🧠 인공지능 분류 · 예측 · 군집화 체험 웹")

# 점 데이터 초기화
if "points" not in st.session_state:
    st.session_state.points = []

st.markdown("### 👇 아래 캔버스를 클릭해서 점을 찍어보세요!")

# 캔버스 생성
canvas_result = st_canvas(
    fill_color="rgba(0, 0, 255, 0.3)",  # 점 색상
    stroke_width=15,
    background_color="#FFFFFF",
    height=500,
    width=500,
    drawing_mode="point",
    key="canvas"
)

# 클릭한 점을 세션에 저장
if canvas_result.json_data is not None:
    for obj in canvas_result.json_data["objects"]:
        if obj["type"] == "circle":
            x = round(obj["left"] / 50, 2)   # 0~10 범위로 정규화
            y = round(obj["top"] / 50, 2)
            if (x, y) not in st.session_state.points:
                st.session_state.points.append((x, y))

# 점 출력
data = np.array(st.session_state.points)
if len(data) > 0:
    df = pd.DataFrame(data, columns=["X", "Y"])
    st.dataframe(df)

# 데이터 삭제 버튼
if st.button("🗑️ 데이터 초기화"):
    st.session_state.points = []
    st.experimental_rerun()

# 충분한 데이터가 있으면 시각화 시작
if len(st.session_state.points) >= 5:
    X = data[:, 0].reshape(-1, 1)
    y = data[:, 1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🎯 분류 (Classification)")
        y_class = (y > np.median(y)).astype(int)
        clf = LogisticRegression().fit(X, y_class)
        x_range = np.linspace(0, 10, 300).reshape(-1, 1)
        y_pred = clf.predict_proba(x_range)[:, 1]
        fig1, ax1 = plt.subplots()
        ax1.scatter(X, y_class, c="blue")
        ax1.plot(x_range, y_pred, color="red")
        ax1.set_title("로지스틱 회귀 분류")
        st.pyplot(fig1)

    with col2:
        st.subheader("📈 예측 (Regression)")
        reg = LinearRegression().fit(X, y)
        y_line = reg.predict(x_range)
        fig2, ax2 = plt.subplots()
        ax2.scatter(X, y, c="green")
        ax2.plot(x_range, y_line, color="black")
        ax2.set_title("선형 회귀 예측")
        st.pyplot(fig2)

    with col3:
        st.subheader("🧩 군집화 (Clustering)")
        kmeans = KMeans(n_clusters=2, random_state=0).fit(data)
        fig3, ax3 = plt.subplots()
        ax3.scatter(data[:, 0], data[:, 1], c=kmeans.labels_, cmap='cool')
        ax3.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1],
                    c='red', marker='X', s=200, label='중심')
        ax3.set_title("K-Means 군집화")
        st.pyplot(fig3)
else:
    st.info("📌 분석을 시작하려면 5개 이상의 점을 찍어주세요.")
