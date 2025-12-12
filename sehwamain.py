import streamlit as st

st.set_page_config(
    page_title="세화고 프로그램 모음",
    layout="wide",
)

# ----- 페이지 이동 함수 -----
def go(page_name):
    st.switch_page(page_name)

# ----- 사이드바 고급 디자인 적용 -----
sidebar_style = """
<style>
/* 사이드바 전체 배경 */
[data-testid="stSidebar"] {
    background-color: #f8f9fa;
    padding: 20px;
}

/* 메뉴 제목 */
.sidebar-title {
    font-size: 20px; 
    font-weight: 700;
    margin-bottom: 15px;
    color: #333;
}

/* 링크 스타일 */
.sidebar-item {
    font-size: 16px;
    padding: 6px 4px;
    border-radius: 6px;
}

.sidebar-item:hover {
    background-color: #e6e6e6;
    cursor: pointer;
}

</style>
"""

st.markdown(sidebar_style, unsafe_allow_html=True)

# -----------------------------
# 📁 사이드바 메뉴 구성
# -----------------------------
st.sidebar.markdown('<div class="sidebar-title">📂 부서별 메뉴</div>', unsafe_allow_html=True)

menu = {
    "교무부": {
        "시간표 관리": "pages/01_교무부_시간표관리.py",
        "출결 확인": "pages/02_교무부_출결확인.py",
        "성적 처리": "pages/03_교무부_성적처리.py",
    },
    "진로진학부": {
        "진학 자료 열람": "pages/04_진로진학부_진학자료열람.py",
        "상담 기록 관리": "pages/05_진로진학부_상담기록관리.py",
        "진로 설문 분석": "pages/06_진로진학부_설문분석.py",
    },
    "창의인성부": {
        "봉사활동 관리": "pages/07_창의인성부_봉사관리.py",
        "프로젝트 관리": "pages/08_창의인성부_프로젝트관리.py",
        "창의탐구페스티벌": "pages/09_창의인성부_탐구페스티벌.py",
    },
    "연구부": {
        "연구 과제 관리": "pages/10_연구부_과제관리.py",
        "자료 업로드": "pages/11_연구부_자료업로드.py",
        "세미나 기록": "pages/12_연구부_세미나기록.py",
    },
    "생활안전부": {
        "생활지도 기록": "pages/13_생활안전부_생활지도기록.py",
        "상벌점 관리": "pages/14_생활안전부_상벌점관리.py",
        "안전 점검표": "pages/15_생활안전부_점검표.py",
    },
    "학년부": {
        "생기부_상담보고서": "pages/학년부/생기부_상담보고서.py",
        "학생 정보 조회": "pages/17_학년부_학생조회.py",
        "학부모 상담 관리": "pages/18_학년부_상담관리.py",
    }
}


icons = {
    "교무부": "🏫",
    "진로진학부": "🎓",
    "창의인성부": "🌱",
    "연구부": "🔬",
    "생활안전부": "🛡️",
    "학년부": "📘",
}

# ----- 토글 메뉴 생성 -----
for dept, items in menu.items():
    with st.sidebar.expander(f"{icons.get(dept, '')} {dept}", expanded=False):
        for name, page in items.items():
            if st.button(f"• {name}", key=name):
                go(page)

# -----------------------------
# 🏠 메인 페이지 본문
# -----------------------------
st.markdown("""
# 🌟 세화고 프로그램 통합 페이지
## 업무 효율을 위한 도구를 한곳에 모았습니다.

---

### 🔎 제공 기능 안내
- 📋 학생 제출물 정리 도구  
- 🔍 창의탐구페스티벌 타임별 명단 비교  
- 🧮 학급 관리 도구  
- 📊 보고서 자동 생성기  
- ➕ 신규 기능이 지속적으로 업데이트됩니다.

---

### 💬 문의 및 요청
필요한 프로그램이 있다면 언제든지 말씀해주세요.  
빠르게 반영하겠습니다.

---
""")
