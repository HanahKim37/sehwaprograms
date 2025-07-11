import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import math
import io

st.set_page_config(page_title="토너먼트 대진표", layout="centered")
st.title("토너먼트 대진표 생성기")

def create_first_round_pairs(num_teams, bye_teams):
    """
    1라운드에서 '부전승 팀'은 제외하고,
    나머지 팀들을 순서대로 2개씩 짝지어 (A vs B) 매치를 만든다.
    예) num_teams=12, bye_teams=[3,6,9,12] 이면
       => 1라운드 후보 = [1,2,4,5,7,8,10,11]
       => pairs = [(1,2), (4,5), (7,8), (10,11)]
    """
    teams = [i for i in range(1, num_teams+1) if i not in bye_teams]
    pairs = []
    # 2개씩 끊어서 매치업 구성
    for i in range(0, len(teams), 2):
        # 혹시 팀 수가 홀수라 마지막이 튀면 적절히 처리 필요
        if i+1 < len(teams):
            pairs.append( (teams[i], teams[i+1]) )
        else:
            # 마지막 한 팀만 남았다면, 강제로 부전승 처리하거나 로직 보강
            # 여기서는 단순히 pass
            pass
    return pairs

def create_second_round_pairs(first_round_pairs, bye_teams):
    """
    1라운드를 통과한 '승자들'을 순서대로 추상 객체로 보고,
    bye_teams 목록과 순서대로 vs 매치업을 만든다.

    예) (1,2), (4,5), (7,8), (10,11) → 승자가 각각 M1, M2, M3, M4 라고 본 뒤
        bye_teams = [3,6,9,12] 이라면
        round2 = [(M1, 3), (M2, 6), (M3, 9), (M4, 12)]
    """
    # ex) first_round_pairs = [(1,2), (4,5), (7,8), (10,11)]
    # => 승자를 M1,M2,M3,M4라 명명 (문자열)
    winners = []
    for i in range(len(first_round_pairs)):
        winners.append(f"M{i+1}")  # M1, M2, M3 ...

    # 부전승 팀 수 == winners 수 라고 가정(동일 개수)
    second_pairs = []
    for i, w in enumerate(winners):
        second_pairs.append( (w, bye_teams[i]) )
    return second_pairs

def create_subsequent_rounds(pairs):
    """
    2라운드를 생성한 뒤에는, 그 승자들끼리 다음 라운드를 또 매치업 생성해야 합니다.
    pairs = [(M1, 3), (M2, 6), (M3, 9), (M4, 12)] 라고 하면,
    승자는 N1, N2, N3, N4 같은 식으로 선언 후 다시 2개씩 짝지어 최종 결승까지 반복.
    """
    round_list = []
    current_pairs = pairs
    round_index = 1

    while len(current_pairs) >= 2:
        round_list.append(current_pairs)
        # 이번 라운드 승자들: Nx...
        winners = []
        for i in range(len(current_pairs)):
            winners.append(f"N{round_index}_{i+1}")  # 예: N1_1, N1_2 ...
        # 다음 라운드 pairs 만들기
        next_pairs = []
        for i in range(0, len(winners), 2):
            if i+1 < len(winners):
                next_pairs.append( (winners[i], winners[i+1]) )
            else:
                # 홀수라 한 승자가 남으면 pass (또는 부전승 처리)
                pass
        round_index += 1
        current_pairs = next_pairs

    # 마지막 round도 추가
    if current_pairs:
        round_list.append(current_pairs)
    return round_list

def draw_bracket_image(num_teams, bye_teams):
    """
    1) 1라운드: (1,2), (3,4), ...
    2) 2라운드: (1,2)승자 vs bye_team, ...
    3) 3라운드~: 승자들끼리 매치
    => 모든 라운드를 순차적으로 세로 방향으로 그려 준다.
    => 반환값: 그림 파일의 바이너리(bytes)
    """
    # 1) 1라운드 매치업
    first_round = create_first_round_pairs(num_teams, bye_teams)
    # 2) 2라운드 = 1라운드 승자 vs bye_teams
    second_round = create_second_round_pairs(first_round, bye_teams)
    # 3) 이후 라운드들
    round_list = []
    round_list.append(first_round)
    round_list.append(second_round)
    round_list.extend(create_subsequent_rounds(second_round))
    # round_list 는 2D 구조: [ [ (1,2), (3,4), ... ], [ ('M1',3), ... ], [ ('N1_1','N1_2'), ... ], ...]

    fig, ax = plt.subplots(figsize=(10, 1.5 * num_teams))

    box_width = 1.2
    box_height = 0.6
    h_gap = 2.5  # 라운드 간 가로간격
    v_gap = 0.3  # 매치 간 세로 간격

    # 라운드 수
    total_rounds = len(round_list)
    # 각 라운드 별 (match i -> (center_x, center_y)) 저장
    center_positions = {}

    for r_idx, matches in enumerate(round_list):
        x_left = r_idx * (box_width + h_gap)  # 라운드별 x 위치
        # 세로 길이 = (box_height + v_gap) * 매치 수
        for m_idx, match in enumerate(matches):
            # match = (A, B)
            y_top = (box_height + v_gap) * (m_idx * 2)  # 매치 수만큼 세로로 늘리기
            # 그 매치 박스 그리기 (가운데에 그릴 수도 있지만 단순화해서 그냥 y_top)
            rect = Rectangle((x_left, y_top),
                             box_width, box_height,
                             fill=False, edgecolor='black')
            ax.add_patch(rect)
            cx = x_left + box_width/2
            cy = y_top + box_height/2
            center_positions[(r_idx, m_idx)] = (cx, cy)

    # 연결선 그리기:
    # 라운드 r_idx의 m_idx 매치 vs 다음 라운드 r_idx+1의 어떤 매치 ?
    # 여기선 매치업을 실제로 "누가 승자인지" 추적하여 다음 라운드에 연결해야 하지만,
    # 단순히 "위에서부터 순서대로 연결"하는 로직으로 표현.
    for r_idx in range(len(round_list)-1):
        curr_round = round_list[r_idx]
        next_round = round_list[r_idx+1]
        for m_idx, match in enumerate(curr_round):
            # 현재 매치 박스 중심
            cx1, cy1 = center_positions[(r_idx, m_idx)]

            # 승자가 next_round의 어느 매치로 가는지 알아야 함.
            # 여기서는 "m_idx//2" 매치의 위쪽/아래쪽 참가자 라고 단순 가정
            next_m_idx = m_idx // 2
            if next_m_idx < len(next_round):
                cx2, cy2 = center_positions[(r_idx+1, next_m_idx)]
                # 위아래 중에서 위 참가자/아래 참가자 결정
                # m_idx가 짝수면 위, 홀수면 아래 라고 해서 약간 y를 조정
                offset = (box_height/4) if (m_idx % 2 == 0) else -(box_height/4)
                ax.plot([cx1, cx2, cx2],
                        [cy1, cy1, cy2 + offset],
                        color='black')

    ax.set_xlim(-1, total_rounds*(box_width + h_gap) + 2)
    ax.set_ylim(-1, (box_height + v_gap)*2*max(len(r) for r in round_list) + 1)
    # 좌표 뒤집으면 우승자가 위로 보이는 형태
    ax.invert_yaxis()
    ax.axis("off")
    plt.tight_layout()

    # 그림을 메모리에 저장 후 반환
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# ─────────────────────────────────────────────────────
# 메인 Streamlit 로직
# ─────────────────────────────────────────────────────

def main():
    st.write("1) 전체 팀 수, 2) 부전승 팀 수, 3) 부전승 팀 번호들을 기입해 주세요.")
    num_teams = st.number_input("전체 팀 수", min_value=2, value=12, step=1)
    bye_teams_count = st.number_input("부전승 팀 수", min_value=0, max_value=num_teams, value=4, step=1)

    placeholder_text = ", ".join(str(x) for x in range(1, 1+bye_teams_count))
    bye_input = st.text_input("부전승 팀 번호(콤마로 구분)", value=placeholder_text)

    # 부전승 팀 목록 파싱
    if bye_input.strip():
        try:
            bye_teams = [int(x.strip()) for x in bye_input.split(",")]
        except:
            st.error("부전승 팀 번호 입력이 올바르지 않습니다.")
            bye_teams = []
    else:
        bye_teams = []

    # 입력 검증
    if len(bye_teams) != bye_teams_count:
        st.warning("입력한 부전승 팀 수와 실제 목록 개수가 일치하지 않습니다.")

    # 대진표 생성 버튼
    if st.button("대진표 생성"):
        # 빈 박스가 많은 그림이므로, 너무 큰 팀 수면 곤란할 수 있음
        if (num_teams - bye_teams_count) < 2:
            st.warning("부전승 제외 후 최소 2팀 이상이어야 대진이 가능합니다.")
            return

        # 이미지 생성
        bracket_png = draw_bracket_image(num_teams, bye_teams)

        # 스트림릿으로 이미지 표시
        st.image(bracket_png, caption="토너먼트 대진표 (빈 박스)", use_column_width=True)

        # 다운로드 버튼
        st.download_button(
            label="이미지 다운로드",
            data=bracket_png,
            file_name="tournament_bracket.png",
            mime="image/png"
        )

if __name__ == "__main__":
    main()
