import streamlit as st

def render_sidebar():
    """
    사이드바를 렌더링하는 함수입니다.
    부서별 메뉴와 교과별 메뉴로 구성됩니다.
    """
    
    # ---------------------------------------------------------
    # 1. 부서별 메뉴 섹션
    # ---------------------------------------------------------
    st.sidebar.markdown("## 📂 부서별 메뉴")
    
    # 교무부
    with st.sidebar.expander("🏫 교무부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # 진로진학부
    with st.sidebar.expander("🎓 진로진학부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # 창의인성부
    with st.sidebar.expander("🌱 창의인성부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # 연구부
    with st.sidebar.expander("🔬 연구부", expanded=False):
       if st.button("🎲 추첨 프로그램", use_container_width=True):
            # pages 폴더 안에 '추첨_프로그램.py' 파일이 있어야 합니다.
            st.switch_page("pages/추첨_프로그램.py")

    # 생활안전부
    with st.sidebar.expander("🛡️ 생활안전부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # 학년부 (기존 기능 유지)
    with st.sidebar.expander("📘 학년부", expanded=False):
        if st.button("📄 생기부 기반 상담보고서", use_container_width=True):
            st.switch_page("pages/생기부_상담보고서.py")

    
    st.sidebar.markdown("---")


    # ---------------------------------------------------------
    # 2. 교과별 메뉴 섹션
    # ---------------------------------------------------------
    st.sidebar.markdown("## 📚 교과별 메뉴")

    # 국어과
    with st.sidebar.expander("🇰🇷 국어과", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # 영어과
    with st.sidebar.expander("🇺🇸 영어과", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # 수학과
    with st.sidebar.expander("📐 수학과", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # 사회과
    with st.sidebar.expander("🌏 사회과", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # 과학과
    with st.sidebar.expander("🧪 과학과", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # 예체능생활교양과 (기능 추가)
    with st.sidebar.expander("🎨 예체능생활교양과", expanded=True):
        if st.button("📝 회의록 서명 수합", use_container_width=True):
            # 주의: pages 폴더 안에 '회의록_서명_수합.py' 파일이 실제로 존재해야 합니다.
            st.switch_page("pages/회의록_서명_수합.py")


    # ---------------------------------------------------------
    # 하단 푸터
    # ---------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.caption("ⓒ 세화고 업무 지원 시스템")
