import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from io import BytesIO

def draw_bracket(total_teams, byes_count, byes_teams):
    fig, ax = plt.subplots(figsize=(max(8, total_teams//2), 6))
    ax.set_xlim(0, total_teams + 2)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # 1. 아래쪽에 팀 수만큼 빈 박스 일렬로
    box_width = 0.8
    box_height = 0.8
    y_base = 1

    team_positions = []  # 각 팀 박스 좌표 (x, y) 저장
    
    for i in range(total_teams):
        x = i + 1
        rect = patches.Rectangle((x - box_width/2, y_base), box_width, box_height,
                                 linewidth=1, edgecolor='black', facecolor='white')
        ax.add_patch(rect)
        team_positions.append((x, y_base + box_height / 2))

    # 2. 부전승 팀과 인접 승자 팀 연결
    # 부전승팀 번호는 1부터 total_teams 기준, 입력값은 리스트로 받음
    # 예) total_teams=12, byes_count=4, byes_teams=[3,6,9,12]
    # 1,2 우승자가 3과 붙는다 -> (1,2) 연결선을 그리고 3과 붙는 모양
    
    # 승자팀은 부전승팀 앞에 있는 2팀씩 묶음 (1,2) (4,5) (7,8) (10,11) 등
    # 부전승팀 번호는 홀수 or 짝수 여부와 관계없이 그냥 부전승팀 번호 기준
    
    y_bye = y_base + box_height + 1.5

    for bye in byes_teams:
        # 부전승팀 위치
        bx, by = team_positions[bye - 1]
        # 앞에 붙을 승자 2팀 위치 (bye-2, bye-3)
        # 예: bye=3 → 승자팀 = 1,2 
        # bye가 3,6,9,12...일 경우 승자팀 번호는 bye-2, bye-1
        winner1_idx = bye - 2
        winner2_idx = bye - 3
        # 승자팀 좌표 (위에서 찾기)
        if winner1_idx < 0 or winner2_idx < 0:
            # 예외처리 (처음에 인덱스 음수일 수 있음)
            continue
        w1x, w1y = team_positions[winner1_idx]
        w2x, w2y = team_positions[winner2_idx]

        # 승자팀 사이 연결선 (가로선)
        mid_y = y_base + box_height + 0.7
        ax.plot([w2x, w1x], [mid_y, mid_y], color='black')

        # 승자팀 각 박스에서 위로 선 연결
        ax.plot([w2x, w2x], [w2y, mid_y], color='black')
        ax.plot([w1x, w1x], [w1y, mid_y], color='black')

        # 승자팀 사이선 중간에서 부전승팀으로 가는 선 (세로선)
        ax.plot([ (w2x + w1x)/2, (w2x + w1x)/2], [mid_y, y_bye], color='black')

        # 부전승팀 박스에서 위로 선 연결
        ax.plot([bx, (w2x + w1x)/2], [by, y_bye], color='black')

    return fig

def main():
    st.title("토너먼트 대진표 생성기")

    total_teams = st.number_input("전체 팀 수", min_value=2, step=1, value=12)
    byes_count = st.number_input("부전승 팀 수", min_value=0, max_value=total_teams, step=1, value=4)
    
    byes_input = st.text_input("부전승으로 올라가는 팀 번호 (콤마로 구분, 예: 3,6,9,12)", "3,6,9,12")
    
    if st.button("대진표 생성"):
        try:
            byes_teams = [int(x.strip()) for x in byes_input.split(",") if x.strip()]
            # 기본 검증
            if len(byes_teams) != byes_count:
                st.error("부전승 팀 수와 입력한 팀 번호 개수가 일치하지 않습니다.")
                return
            if max(byes_teams) > total_teams or min(byes_teams) < 1:
                st.error("부전승 팀 번호는 1부터 전체 팀 수 사이여야 합니다.")
                return

            fig = draw_bracket(total_teams, byes_count, byes_teams)
            st.pyplot(fig)

            # 이미지 다운로드
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
            st.error(f"입력값 처리 중 오류: {e}")

if __name__ == "__main__":
    main()
