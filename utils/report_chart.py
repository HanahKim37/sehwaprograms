import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import matplotlib.font_manager as fm

def setup_matplotlib_korean_font():
    # 폰트 설정 (기존과 동일)
    system_fonts = [f.name for f in fm.fontManager.ttflist]
    if 'NanumGothic' in system_fonts: plt.rc('font', family='NanumGothic')
    elif 'NanumBarunGothic' in system_fonts: plt.rc('font', family='NanumBarunGothic')
    elif 'Malgun Gothic' in system_fonts: plt.rc('font', family='Malgun Gothic')
    elif 'AppleGothic' in system_fonts: plt.rc('font', family='AppleGothic')
    else: plt.rc('font', family='sans-serif')
    plt.rcParams['axes.unicode_minus'] = False

def build_radar_png(scores: dict):
    if not scores: return None

    categories = list(scores.keys())
    # 점수 데이터 정규화 (10점 만점 기준)
    values = []
    for v in scores.values():
        try:
            val = float(v)
            if val > 10: val = val / 10 # 100점이면 10으로 나눔
            values.append(val)
        except:
            values.append(0)
            
    N = len(categories)
    
    # 1. 각도 계산 (3개면 삼각형, 5개면 오각형)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1] # 끝점을 첫점과 연결 (폐곡선 만들기)
    
    # 2. 값도 첫 값을 끝에 추가
    values += values[:1]

    # 3. 그래프 그리기
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    
    # 12시 방향 시작, 시계 방향
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # X축 라벨
    plt.xticks(angles[:-1], categories, size=11, weight='bold')

    # Y축 라벨 (0~10점)
    ax.set_rlabel_position(0)
    plt.yticks([2,4,6,8,10], ["2","4","6","8","10"], color="grey", size=8)
    plt.ylim(0, 10)

    # 데이터 그리기 (선 + 채우기)
    ax.plot(angles, values, linewidth=2, linestyle='solid', color='#3b82f6')
    ax.fill(angles, values, '#3b82f6', alpha=0.2)

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    plt.close(fig)
    return buf
