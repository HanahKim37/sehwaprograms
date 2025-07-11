import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math

def generate_matchups(num_teams, bye_teams):
    """
    예: 12팀, 부전승 4팀이면, 
    1라운드: 8팀만 경기, 4팀 부전승 -> 4승 + 4부전승 = 8
    2라운드: 8 -> 4
    3라운드: 4 -> 2
    4라운드: 2 -> 1
    이런 식으로 매치업 자료구조 만들기
    """
    # 여기서 원하시는 로직(예: 1,2 승자가 3이랑 붙도록)대로 
    # matchups를 구성해 주세요.
    # 여기서는 개념만 간략히 표현합니다.
    matchups = {
        1: [
            ("A", [1, 2]),
            ("B", [4, 5])
            # 나머지도 비슷하게...
        ],
        2: [
            ("C", ["A", 3]),
            ("D", ["B", 6])
            # ...
        ],
        3: [
            ("E", ["C", "D"])
        ]
    }
    return matchups

def draw_bracket(matchups):
    fig, ax = plt.subplots()
    # 라운드별 박스 위치를 저장할 dict: { "A": (x,y), "B": (x,y), 1:(x,y), 2:(x,y), ... }
    centers = {}

    # 라운드별로 x 좌표를 달리 부여
    for round_i, round_info in matchups.items():
        x_coord = round_i * 3  # round 별 x간격
        for match_id, participants in round_info:
            # match_id에 해당하는 박스 하나 그리기
            y_coord = ... # 라운드 안에서 몇 번째 매치인지에 따라 y 계산
            # 박스 그리기
            box_width, box_height = 1, 0.5
            ax.add_patch(Rectangle((x_coord, y_coord), box_width, box_height, fill=False))
            # 박스의 중심 연결
            center_x = x_coord + box_width / 2
            center_y = y_coord + box_height / 2
            centers[match_id] = (center_x, center_y)

            # 참가자 각각에 대해 선을 그리기
            for p in participants:
                if isinstance(p, int):
                    # p가 팀 번호라면, 따로 팀 박스 혹은 표시
                    # 혹은 1라운드면 (p, int)에 대해 별도 박스 그릴 수도 있음
                    # 여기서는 간략히 '~' 처리
                    px, py = x_coord - 2, y_coord  # 그냥 옆에 그린다고 가정
                    # ...
                    ax.plot([px, center_x], [py, center_y], color='black')
                else:
                    # p가 "A", "B" 같은 이전 match 승자면
                    prev_cx, prev_cy = centers[p]
                    ax.plot([prev_cx, center_x], [prev_cy, center_y], color='black')

    ax.invert_yaxis()
    ax.axis("off")
    st.pyplot(fig)

def main():
    st.title("토너먼트 (커스텀 대진표)")
    num_teams = st.number_input("전체 팀 수", min_value=2, value=12)
    bye_teams = st.number_input("부전승 팀 수", min_value=0, value=4)

    # '생성' 버튼 클릭하면, matchups 만들고 그리기
    if st.button("대진표 생성"):
        matchups = generate_matchups(num_teams, bye_teams)
        draw_bracket(matchups)

if __name__ == "__main__":
    main()
