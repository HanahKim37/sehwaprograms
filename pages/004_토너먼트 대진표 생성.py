import streamlit as st
import matplotlib.pyplot as plt
import networkx as nx
from PIL import Image
import os

# ===== 기능 함수 =====

def generate_team_names(total):
    return [f'Team {i+1}' for i in range(total)]

def create_bracket(teams, byes):
    rounds = []
    current = teams[byes:]
    bye_teams = teams[:byes]
    if len(current) >= 2:
        rounds.append([(current[i], current[i+1]) for i in range(0, len(current)-1, 2)])
        next_round = [f"Winner({a} vs {b})" for a, b in rounds[0]]
    else:
        next_round = []

    next_round += bye_teams

    while len(next_round) > 1:
        round_match = [(next_round[i], next_round[i+1]) for i in range(0, len(next_round)-1, 2)]
        rounds.append(round_match)
        next_round = [f"Winner({a} vs {b})" for a, b in round_match]

    return rounds

def build_tree_graph(bracket):
    G = nx.DiGraph()
    pos = {}
    labels = {}

    def add_match(match, level, x):
        if isinstance(match, str):
            G.add_node(match)
            pos[match] = (x, -level)
            labels[match] = match
            return x

        team1, team2 = match
        center1 = add_match(team1, level+1, x)
        center2 = add_match(team2, level+1, x+1)
        name = f"Winner({team1} vs {team2})"
        G.add_node(name)
        pos[name] = ((center1 + center2) / 2, -level)
        labels[name] = name
        G.add_edge(team1, name)
        G.add_edge(team2, name)
        return (center1 + center2) / 2

    final = bracket[-1][0]
    add_match(final, 0, 0)
    return G, pos, labels

def draw_bracket(G, pos, labels, filename="bracket.png"):
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, labels=labels, with_labels=True, node_size=3000,
            node_color='lightgreen', font_size=8, font_weight='bold', arrows=False)
    plt.title("Tournament Bracket")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    return filename

# ===== Streamlit 페이지 =====

st.header("🏆 토너먼트 대진표 생성기")
st.markdown("팀 수와 부전승 팀 수를 입력하면 트리 형태의 대진표를 이미지로 만들어 보여줍니다.")

# 입력부
col1, col2 = st.columns(2)
with col1:
    total_teams = st.number_input("전체 팀 수", min_value=2, step=1, value=8)
with col2:
    bye_teams = st.number_input("부전승 팀 수", min_value=0, max_value=total_teams-1, step=1, value=0)

if st.button("🖼 대진표 생성"):
    teams = generate_team_names(total_teams)

    if total_teams - bye_teams < 2:
        st.warning("⚠️ 부전승을 제외한 팀 수가 2 이상이어야 합니다.")
    else:
        bracket = create_bracket(teams, bye_teams)
        G, pos, labels = build_tree_graph(bracket)
        filename = "bracket.png"
        draw_bracket(G, pos, labels, filename)

        st.image(Image.open(filename), caption="🎯 생성된 대진표", use_column_width=True)
        with open(filename, "rb") as f:
            st.download_button("📥 대진표 이미지 다운로드", f, file_name="bracket.png")
