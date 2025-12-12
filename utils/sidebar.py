import streamlit as st

def render_sidebar():
    st.sidebar.markdown("## 📂 부서별 메뉴")
    st.sidebar.markdown("---")

    # =========================
    # 교무부
    # =========================
    with st.sidebar.expander("🏫 교무부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # =========================
    # 진로진학부
    # =========================
    with st.sidebar.expander("🎓 진로진학부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # =========================
    # 창의인성부
    # =========================
    with st.sidebar.expander("🌱 창의인성부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # =========================
    # 연구부
    # =========================
    with st.sidebar.expander("🔬 연구부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # =========================
    # 생활안전부
    # =========================
    with st.sidebar.expander("🛡️ 생활안전부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    # =========================
    # 학년부 (실제 동작)
    # =========================
    with st.sidebar.expander("📘 학년부", expanded=True):
        if st.button("📄 생기부 기반 상담보고서", use_container_width=True):
            st.switch_page("pages/생기부_상담보고서.py")

    st.sidebar.markdown("---")
    st.sidebar.caption("ⓒ 세화고 업무 지원 시스템")
