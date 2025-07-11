import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

st.set_page_config(page_title="토너먼트 대진표", layout="centered")
st.header("🏆 토너먼트 대진표 생성기")

# 입력
num_teams = st.number_input("총 팀 수 (2의 제곱수)", min_value=2, value=8, step=1)

# 2의 거듭제곱 확인
import math
if math.log2(num_teams) % 1 != 0:
    st.error("⚠️ 팀 수는 2, 4, 8, 16, 32 같은 2의 거듭제곱이어야 합니다.")
    st.stop()

# 대진표 생성 함수
def draw_tournament_bracket(num_teams, filename='tournament.png'):
    fig, ax = plt.subplots(figsize=(12, 8))

    box_width = 1
    box_height = 0.5
    h_spacing = 2  # 가로 간격
    v_spacing = 1  # 세로 간격

    rounds = int(math.log2(num_teams))
    y_positions = {}

    # 1라운드 박스 그리기 (왼쪽에서 시작)
    for i in range(num_teams):
        x = 0
        y = i * (box_height + v_spacing)
        ax.add_patch(Rectangle((x, y), box_width, box_height, fill=False))
        y_positions[(0, i)] = y + box_height / 2  # 가운데 y 저장

    # 상위 라운드 박스 및 선 그리기
    for r in range(1, rounds + 1):
        num_matches = num_teams // (2 ** r)
        for m in range(num_matches):
            x = r * h_spacing
            left_idx = m * 2
            right_idx = m * 2 + 1

            y1 = y_positions[(r - 1, left_idx)]
            y2 = y_positions[(r - 1, right_idx)]
            y = (y1 + y2) / 2
            y_positions[(r, m)] = y

            # 박스
            ax.add_patch(Rectangle((x, y - box_height / 2), box_width, box_height, fill=False))

            # 선: 왼쪽 팀 → 현재 박스
            ax.plot([x - h_spacing + box_width, x, x], [y1, y1, y], color="black")
            ax.plot([x - h_spacing + box_width, x, x], [y2, y2, y], color="black")

    ax.set_xlim(-1, (rounds + 1) * h_spacing)
    ax.set_ylim(-1, y + 2)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename

# 버튼 누르면 실행
if st.button("🎯 대진표 생성"):
    file = draw_tournament_bracket(num_teams)
    st.image(file, caption="📄 토너먼트 대진표 (빈 칸)", use_column_width=True)
    with open(file, "rb") as f:
        st.download_button("📥 이미지 다운로드", f, file_name="tournament_bracket.png")
