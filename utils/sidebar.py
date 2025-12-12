import streamlit as st

def render_sidebar():
    st.sidebar.markdown("## 📂 부서별 메뉴")
    st.sidebar.markdown("---")

    # ===== 학년부 (실제 이동 가능) =====
    with st.sidebar.expander("📘 학년부", expanded=True):
        if st.button("📄 생기부 상담보고서", use_container_width=True):
            st.switch_page("pages/생기부_상담보고서.py")

    # ===== 아래 부서들은 '준비중' =====
    with st.sidebar.expander("🎓 진로진학부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    with st.sidebar.expander("🌱 창의인성부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    with st.sidebar.expander("🔬 연구부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    with st.sidebar.expander("🛡️ 생활안전부", expanded=False):
        st.caption("⏳ 준비 중입니다")

    st.sidebar.markdown("---")
    st.sidebar.caption("ⓒ 세화고 업무 지원 시스템")
