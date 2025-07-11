import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math
import os

st.set_page_config(page_title="토너먼트 대진표", layout="centered")
st.title("🏆 토너먼트 대진표 생성기")

# ✅ 입력 받기
num_teams = st.number_input("총 팀 수 (예: 12)", min_value=2, value=12, step=1)
bye_teams = st.number_input("부전승 팀 수 (다음 라운드 자동 진출)", min_value=0, max_value=num_teams-1, value=4, step=1)

# ✅ 그리기 함수
def draw_bracket(num_teams, bye_teams, filename="tournament_bracket.png"):
    total_teams = 2 ** math.ceil(math.log2(num_teams))
    rounds = int(math.log2(total_teams))

    fig, ax = plt.subplots(figsize=(total_teams * 0.9, rounds * 2))
    box_width = 1.2
    box_height = 0.6
    h_spacing = 2.2
    v_spacing = 1.5

    positions = {}

    # 1라운드
    for i in range(total_teams):
        x = i * (box_width + h_spacing)
        y = 0
        ax.add_patch(Rectangle((x - box_width/2, y - box_height/2), box_width, box_height, fill=False))
        ax.text(x, y, "□", ha="center", va="center", fontsize=10)
        positions[(0, i)] = (x, y)

    # 라운드 반복
    for r in range(1, rounds + 1):
        matches = total_teams // (2 ** r)
        for m in range(matches):
            left = positions[(r - 1, m * 2)]
            right = positions[(r - 1, m * 2 + 1)]
            x = (left[0] + right[0]) / 2
            y = r * (box_height + v_spacing)
            ax.add_patch(Rectangle((x - box_width/2, y - box_height/2), box_width, box_height, fill=False))
            ax.text(x, y, "□", ha="center", va="center", fontsize=10)
            positions[(r, m)] = (x, y)

            # 직각 연결선
            mid_y = (left[1] + right[1]) / 2
            for px, py in [left, right]:
                ax.plot([px[0], px[0]], [py[1] + box_height/2, mid_y], color="black")
                ax.plot([px[0], x], [mid_y, mid_y], color="black")
                ax.plot([x, x], [mid_y, y - box_height/2], color="black")

    # 부전승 표시 (점선 사각형)
    actual_matches = num_teams - bye_teams
    auto_advance = total_teams - actual_matches
    for i in range(auto_advance):
        x, y = positions[(0, total_teams - 1 - i)]
        ax.add_patch(Rectangle(
            (x - box_width / 2, y - box_height / 2),
            box_width, box_height,
            fill=False, linestyle="dashed", edgecolor="gray"
        ))

    # 마무리
    ax.axis("off")
    ax.set_xlim(-1, total_teams * (box_width + h_spacing))
    ax.set_ylim(-1, rounds * (box_height + v_spacing) + 1)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename

# ✅ 실행 버튼
if st.button("🎯 대진표 생성"):
    file = draw_bracket(num_teams, bye_teams)
    st.image(file, caption="📄 대진표 (빈 칸)", use_column_width=True)
    with open(file, "rb") as f:
        st.download_button("📥 이미지 다운로드", f, file_name="tournament_bracket.png")
