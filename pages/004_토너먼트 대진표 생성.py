import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math

st.set_page_config(page_title="토너먼트 대진표", layout="centered")
st.title("🏆 토너먼트 대진표 생성기 (빈 칸용)")

# ✅ 사용자 입력
num_teams = st.number_input("전체 팀 수 (2의 제곱수 권장)", min_value=2, value=8, step=1)
bye_teams = st.number_input("부전승 팀 수", min_value=0, max_value=num_teams-1, value=0, step=1)

# 입력 검증
if (num_teams - bye_teams) < 2:
    st.warning("⚠️ 부전승을 제외한 팀 수가 2 이상이어야 합니다.")
    st.stop()

# 2의 거듭제곱으로 조정
adjusted_teams = 2 ** math.ceil(math.log2(num_teams))
if adjusted_teams != num_teams:
    st.info(f"⚠️ {num_teams} → {adjusted_teams} 팀으로 자동 보정됩니다.")
    num_teams = adjusted_teams

# ✅ 대진표 그리기 함수 (우승자가 위로, 부전승 고려)
def draw_vertical_bracket(total_teams, bye_teams, filename="vertical_bracket.png"):
    fig, ax = plt.subplots(figsize=(10, 0.6 * total_teams + 3))

    box_width = 1.2
    box_height = 0.6
    h_spacing = 2
    v_spacing = 1

    rounds = int(math.log2(total_teams))
    x_positions = {}
    box_centers = {}

    # 1라운드 (맨 아래)
    match_index = 0
    for i in range(total_teams):
        y = 0
        x = i * (box_height + v_spacing)
        ax.add_patch(Rectangle((y, x), box_width, box_height, fill=False))
        center_x = y + box_width / 2
        center_y = x + box_height / 2
        x_positions[(0, i)] = (center_x, center_y)

    # 위로 올라가며 그리기
    for r in range(1, rounds + 1):
        num_matches = total_teams // (2 ** (r))
        for m in range(num_matches):
            prev1 = x_positions[(r - 1, m * 2)]
            prev2 = x_positions[(r - 1, m * 2 + 1)]
            y = r * (box_width + h_spacing)
            x = (prev1[1] + prev2[1]) / 2

            # 박스
            ax.add_patch(Rectangle((y, x - box_height / 2), box_width, box_height, fill=False))
            curr_center = (y + box_width / 2, x)
            x_positions[(r, m)] = curr_center

            # 선 (직각 연결)
            for prev in [prev1, prev2]:
                ax.plot([prev[0], y, y], [prev[1], prev[1], x], color='black')

    # 부전승 박스 표시 (하단에 따로)
    if bye_teams > 0:
        st.markdown("✅ **부전승 팀 수:** {}명 → 2라운드 자동 진출".format(bye_teams))
        for i in range(bye_teams):
            y = box_width + h_spacing
            x = (total_teams + i) * (box_height + v_spacing)
            ax.add_patch(Rectangle((y, x), box_width, box_height, fill=False, linestyle='dashed'))
            ax.text(y + box_width/2, x + box_height/2, "□", ha="center", va="center")

    ax.axis("off")
    ax.set_xlim(-1, (rounds + 1) * (box_width + h_spacing))
    ax.set_ylim(-2, total_teams * (box_height + v_spacing))
    plt.gca().invert_yaxis()  # ← 우승자가 위로 올라가도록
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename

# ✅ 버튼 클릭 시 실행
if st.button("🎯 대진표 생성"):
    file = draw_vertical_bracket(num_teams, bye_teams)
    st.image(file, caption="📄 우승자가 맨 위에 있는 빈칸용 대진표", use_column_width=True)
    with open(file, "rb") as f:
        st.download_button("📥 이미지 다운로드", f, file_name="tournament_bracket.png")
