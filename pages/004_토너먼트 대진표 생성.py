import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def generate_matchups(num_teams, bye_teams):
    """
    팀 수와 부전승 등을 고려해 원하는 대로 대진표 정보를 구성하시면 됩니다.
    여기서는 예시로 (1,2) 승자는 3과 붙고, (4,5) 승자는 6과 붙는 식으로만 구조화.
    """
    # 라운드 1: A=(1 vs 2), B=(4 vs 5)  /  3, 6번은 부전승(1R 생략)
    # 라운드 2: C=(A 승자 vs 3), D=(B 승자 vs 6)
    # 라운드 3: E=(C 승자 vs D 승자)

    matchups = {
        1: [
            ("A", [1, 2]),
            ("B", [4, 5]),
        ],
        2: [
            ("C", ["A", 3]),
            ("D", ["B", 6]),
        ],
        3: [
            ("E", ["C", "D"]),
        ]
    }
    return matchups

def draw_bracket(matchups):
    fig, ax = plt.subplots(figsize=(8, 6))
    centers = {}  # match_id나 팀 번호 → (center_x, center_y) 저장

    box_width = 1.0
    box_height = 0.5
    x_gap = 3.0
    y_gap = 1.0  # 매치끼리 세로 간격

    # 팀을 박스로 그리고 싶으면 0라운드를 따로 구성해도 되지만,
    # 여기서는 matchups를 라운드별로 돌면서 필요한 순간에 그립니다.

    for round_i, round_info in matchups.items():
        x_coord = (round_i - 1) * x_gap  # 라운드별 x 위치
        for match_index, (match_id, participants) in enumerate(round_info):
            # y 좌표는 match_index 순서에 따라 중첩 없이 띄우기
            y_coord = match_index * (box_height + y_gap)

            # 현재 매치 “박스” 그리기
            ax.add_patch(Rectangle((x_coord, y_coord), 
                                   box_width, 
                                   box_height, 
                                   fill=False))
            # 박스 가운데 좌표
            center_x = x_coord + box_width/2
            center_y = y_coord + box_height/2
            centers[match_id] = (center_x, center_y)

            # 참가자 두 명(혹은 승자)마다 라인 연결하기
            # p가 int면 “팀 번호”, str이면 “이전 매치 승자”라고 가정
            for p_idx, p in enumerate(participants):
                # 참가자를 그릴 x, y
                # “첫 라운드”에서 팀 번호가 있으면 따로 표시, 혹은
                # 그냥 이 함수를 재귀적으로 부르거나, 미리 0라운드에 팀을 박스화하기도 함.

                if isinstance(p, int):
                    # 간단히 말해, 팀 번호는 x_coord-1 쯤에 표시
                    px = x_coord - 1.0
                    # 참가자 2명이면 하나는 위쪽, 하나는 아래쪽에 두기
                    # p_idx=0이면 약간 더 위쪽, p_idx=1이면 아래쪽
                    py = y_coord + p_idx*(box_height/2)

                    # 팀 번호 텍스트 표시를 위한 박스나 텍스트:
                    ax.text(px, py, str(p), ha='right', va='center')

                    # 라인 연결
                    ax.plot([px, center_x], [py, center_y], color='black')

                else:
                    # str(“A”, “B”…)인 경우 이전 매치 승자의 위치
                    if p not in centers:
                        # 아직 이전 매치가 안 그려졌다면, matchups 선언 순서를 정리하거나
                        # 한 번 더 돌면서 그려야 함. 
                        # 여기선 전 라운드부터 순서대로 있기 때문에 괜찮다는 가정.
                        continue
                    prev_cx, prev_cy = centers[p]
                    ax.plot([prev_cx, center_x], [prev_cy, center_y], color='black')

    ax.invert_yaxis()
    ax.axis("off")
    st.pyplot(fig)

def main():
    st.title("토너먼트 (커스텀 대진표)")
    num_teams = st.number_input("전체 팀 수", min_value=2, value=12)
    bye_teams = st.number_input("부전승 팀 수", min_value=0, value=4)

    if st.button("대진표 생성"):
        matchups = generate_matchups(num_teams, bye_teams)
        draw_bracket(matchups)

if __name__ == "__main__":
    main()
