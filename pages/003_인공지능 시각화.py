import streamlit as st
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.cluster import KMeans
import numpy as np
import pandas as pd

st.set_page_config(page_title="AI 시각화 학습기", layout="wide")
st.title("🧠 인공지능 분류 · 예측 · 군집화 체험 웹")

# 기본 데이터
if "points" not in st.session_state:
    st.session_state.points = []

st.write("👆 아래 그래프를 클릭해서 점을 추가하세요!")

# 캔버스 설정
fig, ax = plt.subplots()
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_title("클릭하여 데이터를 추가하세요 (x, y)")
ax.set_xlabel("X")
ax.set_ylabel("Y")

# 기존 포인트 표시
points = np.array(st.session_state.points)
if len(points) > 0:
    ax.scatter(points[:, 0], points[:, 1], c="blue", label="입력 데이터")

# 클릭 이벤트 처리
click = st.plotly_chart(
    {
        "data": [],
        "layout": {
            "clickmode": "event+select",
            "xaxis": {"range": [0, 10]},
            "yaxis": {"range": [0, 10]},
            "title": "그래프 클릭 시 포인트가 추가됩니다"
        }
    },
    use_container_width=True
)

# Streamlit에서 matplotlib 그래프 출력
st.pyplot(fig)

# 점 추가
x = st.number_input("X 좌표", 0.0, 10.0, step=0.1)
y = st.number_input("Y 좌표", 0.0, 10.0, step=0.1)
if st.button("➕ 점 추가"):
    st.session_state.points.append((x, y))
    st.experimental_rerun()

# 데이터가 충분한 경우 모델 시각화
if len(st.session_state.points) >= 5:
    data = np.array(st.session_state.points)
    X = data[:, 0].reshape(-1, 1)
    y = data[:, 1]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🎯 분류 (Classification)")
        y_class = (y > np.median(y)).astype(int)  # 임시 라벨링
        clf = LogisticRegression().fit(X, y_class)
        x_range = np.linspace(0, 10, 300).reshape(-1, 1)
        y_pred = clf.predict_proba(x_range)[:, 1]
        fig1, ax1 = plt.subplots()
        ax1.scatter(X, y_class, c="blue")
        ax1.plot(x_range, y_pred, color="red")
        ax1.set_title("로지스틱 회귀")
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
                    c='red', marker='X', s=200, label='Centroids')
        ax3.set_title("K-Means 군집화")
        st.pyplot(fig3)
else:
    st.info("👆 5개 이상의 데이터를 입력하면 AI 분석 결과가 나타납니다!")

