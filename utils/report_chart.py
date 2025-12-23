import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import matplotlib.font_manager as fm
import os

def setup_matplotlib_korean_font():
    """
    한글 폰트 설정 (Streamlit Cloud 등 리눅스 환경 고려)
    """
    system_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 1. 나눔고딕/나눔바른고딕 (리눅스/서버 환경)
    if 'NanumGothic' in system_fonts:
        plt.rc('font', family='NanumGothic')
    elif 'NanumBarunGothic' in system_fonts:
        plt.rc('font', family='NanumBarunGothic')
    # 2. 맑은 고딕 (윈도우)
    elif 'Malgun Gothic' in system_fonts:
        plt.rc('font', family='Malgun Gothic')
    # 3. 애플고딕 (맥)
    elif 'AppleGothic' in system_fonts:
        plt.rc('font', family='AppleGothic')
    else:
        # 폰트가 없을 경우 기본값 (한글 깨질 수 있음)
        plt.rc('font', family='sans-serif')

    plt.rcParams['axes.unicode_minus'] = False

def build_radar_png(scores: dict):
    """
    점수 딕셔너리({'학업역량': 8, ...})를 받아 
    삼각형(또는 다각형) 레이더 차트 이미지를 BytesIO로 반환
    """
    if not scores:
        return None

    # 데이터 준비
    categories = list(scores.keys())
    # 점수 정규화 (100점 만점으로 오면 10으로 나눔)
    values = []
    for v in scores.values():
        try:
            val = float(v)
            if val > 10: val = val / 10  # 100점 만점 대응
            values.append(val)
        except:
            values.append(0)
            
    N = len(categories)

    # 각 축의 각도 계산 (마지막 점을 첫 점과 연결하기 위해 2pi까지)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1] # 닫힌 도형을 위해 첫 각도 추가
    
    # 값도 닫힌 도형을 위해 첫 값 추가
    values += values[:1]

    # 그래프 그리기
    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw=dict(polar=True))
    
    # 축(Spines) 설정 - 여기가 원형/다각형 결정
    # 0도(12시 방향)부터 시작
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # X축 라벨(카테고리) 설정
    plt.xticks(angles[:-1], categories, size=11, weight='bold')

    # Y축 라벨(점수) 설정
    ax.set_rlabel_position(0)
    plt.yticks([2, 4, 6, 8, 10], ["2", "4", "6", "8", "10"], color="grey", size=8)
    plt.ylim(0, 10)

    # 데이터 플롯 (선 그리기)
    ax.plot(angles, values, linewidth=2, linestyle='solid', color='#3b82f6')
    
    # 내부 채우기
    ax.fill(angles, values, '#3b82f6', alpha=0.2)

    # 이미지 저장
    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
    buf.seek(0)
    plt.close(fig)
    
    return buf
