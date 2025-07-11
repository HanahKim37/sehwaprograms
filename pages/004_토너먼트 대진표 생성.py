import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import math

def draw_bracket(total_teams, byes_teams):
    fig, ax = plt.subplots(figsize=(max(12, total_teams/1.5), 8))
    ax.set_xlim(0, total_teams * 1.3)
    ax.set_ylim(0, 14)
    ax.axis('off')

    box_w = 0.8
    box_h = 0.8
    base_y = 1

    rounds = math.ceil(math.log2(total_teams))
    round_counts = [math.ceil(total_teams / (2 ** r)) for r in range(rounds)]

    round_positions = {}

    # 1라운드 박스 (전체 팀 박스, 제일 아래)
    x_start = 1
    spacing_x = 1.2
    round_positions[0] = []
    for i in range(total_teams):
        x = x_start + i * spacing_x
        y = base_y
        rect = patches.Rectangle((x - box_w/2, y), box_w, box_h,
                                 linewidth=1, edgecolor='black', facecolor='white')
        ax.add_patch(rect)
        round_positions[0].append((x, y + box_h/2))

    # 부전승팀 박스 (1라운드 위쪽, 따로 띄움)
    bye_y = base_y + box_h + 3
    bye_positions = []
    for bye in byes_teams:
        if 1 <= bye <= total_teams:
            x, _ = round_positions[0][bye - 1]
            rect = patches.Rectangle((x - box_w/2, bye_y), box_w, box_h,
                                     linewidth=1, edgecolor='black', facecolor='white')
            ax.add_patch(rect)
            bye_positions.append((x, bye_y + box_h/2))

            # 부전승팀 박스 → 1라운드 박스 직각 꺾임 연결선
            # 1. 부전승 박스 아래로 세로선
            ax.plot([x, x], [bye_y + box_h/2, base_y + box_h], color='black')
            # 2. 1라운드 박스 위쪽까지 직각 꺾임(같은 x축선 유지)
            # (위에서 바로 세로선 연결했으므로 별도 꺾임 선 불필요)

    # 2라운드부터 마지막 라운드 박스 위치 생성
    for r in range(1, rounds):
        round_positions[r] = []
        num_boxes = round_counts[r]
        for i in range(num_boxes):
            x = x_start + i * spacing_x * (2 ** r)
            y = base_y + r * (box_h + 1.8)
            rect = patches.Rectangle((x - box_w/2, y), box_w, box_h,
                                     linewidth=1, edgecolor='black', facecolor='white')
            ax.add_patch(rect)
            round_positions[r].append((x, y + box_h/2))

    # 1라운드 → 2라운드 연결선 (2개씩 묶어서 1개 박스와 연결)
    for i in range(round_counts[1]):
        x2, y2 = round_positions[1][i]

        idx1 = i * 2
        idx2 = idx1 + 1
        if idx2 >= total_teams:
            idx2 = idx1

        x1_1, y1_1 = round_positions[0][idx1]
        x1_2, y1_2 = round_positions[0][idx2]

        # 각 1라운드 박스에서 위로 직선 연결
        ax.plot([x1_1, x1_1], [y1_1, y2 - box_h/2], color='black')
        ax.plot([x1_2, x1_2], [y1_2, y2 - box_h/2], color='black')

        # 두 선 연결하는 가로선 (직각 꺾임)
        ax.plot([x1_1, x1_2], [y2 - box_h/2, y2 - box_h/2], color='black')

        # 가로선 중간에서 2라운드 박스 세로선 연결
        ax.plot([(x1_1 + x1_2) / 2, x2], [y2 - box_h/2, y2 + box_h/2], color='black')

    # 2라운드 이상 연결선 (r → r+1)
    for r in range(1, rounds - 1):
        for i in range(round_counts[r + 1]):
            x_next, y_next = round_positions[r + 1][i]

            idx1 = i * 2
            idx2 = idx1 + 1
            if idx2 >= round_counts[r]:
                idx2 = idx1

            x1_1, y1_1 = round_positions[r][idx1]
            x1_2, y1_2 = round_positions[r][idx2]

            ax.plot([x1_1, x1_1], [y1_1, y_next - box_h/2], color='black')
            ax.plot([x1_2, x1_2], [y1_2, y_next - box_h/2], color='black')
            ax.plot([x1_1, x1_2], [y_next - box_h/2, y_next - box_h/2], color='black')
            ax.plot([x_next, (x1_1 + x1_2)/2], [y_next + box_h/2, y_next - box_h/2], color='black')

    return fig


def main():
    st.title("토너먼트 대진표 (부전승 포함)")

    total_teams = st.number_input("전체 팀 수 (2 이상)", min_value=2, step=1, value=12)
    byes_input = st.text_input("부전승 팀 번호 (콤마 구분, 예: 3,6,9,12)", "3,6,9,12")

    if st.button("대진표 생성"):
        try:
            byes_teams = [int(x.strip()) for x in byes_input.split(",") if x.strip()]
            if any(t < 1 or t > total_teams for t in byes_teams):
                st.error("부전승 팀 번호는 1부터 전체 팀 수 사이여야 합니다.")
                return

            fig = draw_bracket(total_teams, byes_teams)
            st.pyplot(fig)

            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight')
            buf.seek(0)
            st.download_button(
                label="대진표 이미지 다운로드",
                data=buf,
                file_name="bracket.png",
                mime="image/png"
            )

        except Exception as e:
            st.error(f"오류 발생: {e}")

if __name__ == "__main__":
    main()
