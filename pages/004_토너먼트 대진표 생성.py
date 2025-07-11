import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO
import math

def draw_bracket(total_teams, byes_teams):
    fig, ax = plt.subplots(figsize=(max(12, total_teams/1.5), 8))
    ax.set_xlim(0, total_teams * 1.2)
    ax.set_ylim(0, 12)
    ax.axis('off')

    box_w = 0.8
    box_h = 0.8
    base_y = 1

    # 라운드 수 계산 (전체 팀 수가 2의 제곱이 아닐 경우를 위해)
    rounds = math.ceil(math.log2(total_teams))
    # 각 라운드별 박스 수
    round_counts = [math.ceil(total_teams / (2 ** r)) for r in range(rounds)]

    # 각 라운드 박스 좌표 저장 (라운드 번호 → 리스트 of (x,y))
    round_positions = {}

    # 1라운드: 전체 팀 박스 가로 배치
    x_start = 1
    spacing_x = 1.2  # 박스 사이 가로 간격
    round_positions[0] = []
    for i in range(total_teams):
        x = x_start + i * spacing_x
        y = base_y
        rect = patches.Rectangle((x - box_w/2, y), box_w, box_h, linewidth=1, edgecolor='black', facecolor='white')
        ax.add_patch(rect)
        round_positions[0].append((x, y + box_h/2))

    # 부전승팀 표시용 높이
    bye_y = base_y + box_h + 2

    # 부전승팀: 위쪽에 빈 박스 그리기 (same x좌표)
    for bye in byes_teams:
        if bye < 1 or bye > total_teams:
            continue
        x, _ = round_positions[0][bye - 1]
        rect = patches.Rectangle((x - box_w/2, bye_y), box_w, box_h, linewidth=1, edgecolor='black', facecolor='white')
        ax.add_patch(rect)

    # 2라운드 이상 박스 위치 그리기
    for r in range(1, rounds):
        round_positions[r] = []
        num_boxes = round_counts[r]
        for i in range(num_boxes):
            # x 위치: 1라운드 시작점 + i*spacing*2^r (간격이 2배씩 늘어남)
            x = x_start + (i * spacing_x * (2 ** r))
            # y 위치는 1라운드보다 위로 올라감, 간격도 라운드마다 다름
            y = base_y + r * (box_h + 1.8)
            rect = patches.Rectangle((x - box_w/2, y), box_w, box_h, linewidth=1, edgecolor='black', facecolor='white')
            ax.add_patch(rect)
            round_positions[r].append((x, y + box_h/2))

    # 연결선 그리기 (라운드별 박스와 다음 라운드 박스 연결)
    # 1라운드 -> 2라운드
    for i in range(round_counts[1]):
        # 2라운드 박스 위치
        x2, y2 = round_positions[1][i]

        # 1라운드 박스 2개 좌표 (2i, 2i+1)
        idx1 = i * 2
        idx2 = idx1 + 1
        if idx2 >= total_teams:
            # 홀수개 팀일 경우 마지막 하나만 연결
            idx2 = idx1

        x1_1, y1_1 = round_positions[0][idx1]
        x1_2, y1_2 = round_positions[0][idx2]

        # 왼쪽 박스에서 위로 선
        ax.plot([x1_1, x1_1], [y1_1, y2 - box_h/2], color='black')
        # 오른쪽 박스에서 위로 선
        ax.plot([x1_2, x1_2], [y1_2, y2 - box_h/2], color='black')
        # 두 선을 연결하는 가로선 (직각 꺾임)
        ax.plot([x1_1, x1_2], [y2 - box_h/2, y2 - box_h/2], color='black')

        # 위 가로선에서 2라운드 박스로 세로선
        ax.plot([x2, (x1_1 + x1_2)/2], [y2 + box_h/2, y2 - box_h/2], color='black')

    # 2라운드 이상 연결 (r -> r+1)
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

    # 부전승팀과 연결선 (부전승팀 박스 위쪽 위치 bye_y → 1라운드 박스)
    for bye in byes_teams:
        if bye < 1 or bye > total_teams:
            continue
        x, y1 = round_positions[0][bye - 1]
        # 부전승팀 박스 위치
        y_bye = bye_y + box_h/2
        # 1라운드 박스 y 좌표
        y_1 = y1

        # 직각 꺾임 선으로 연결 (부전승팀 박스 아래 → 1라운드 박스 위)
        ax.plot([x, x], [y_bye, bye_y], color='black')  # 세로선
        ax.plot([x, x], [bye_y, y_1 + box_h/2], color='black')  # 세로선
        # 실제 연결선 (두 직각 꺾임이지만 시각적으로 연결됨)

    return fig


def main():
    st.title("확장된 토너먼트 대진표 생성기")

    total_teams = st.number_input("전체 팀 수 (2 이상, 2의 배수 권장)", min_value=2, step=1, value=12)
    byes_input = st.text_input("부전승 팀 번호 (콤마 구분, 예: 3,6,9,12)", "3,6,9,12")

    if st.button("대진표 생성"):
        try:
            byes_teams = [int(x.strip()) for x in byes_input.split(",") if x.strip()]
            # 기본 검증
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
