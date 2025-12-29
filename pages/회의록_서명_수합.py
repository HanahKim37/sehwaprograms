import streamlit as st
import os
from PIL import Image
import fitz  # PyMuPDF
from streamlit_drawable_canvas import st_canvas

# 1. 사이드바 함수 가져오기 (필수)
from utils.sidebar import render_sidebar

# 2. 페이지 설정
st.set_page_config(
    page_title="회의록 서명",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3. 공통 사이드바 렌더링 (이게 있어야 메뉴가 보입니다!)
render_sidebar()

# --- 여기서부터 페이지 고유 기능 ---

# 폴더 생성
os.makedirs("Original_PDFs", exist_ok=True)
os.makedirs("Signed_PDFs", exist_ok=True)

st.title("✒️ 온라인 전자서명 시스템")

# 4. 기능 선택을 사이드바가 아닌 '탭'으로 변경 (더 깔끔함)
tab_user, tab_admin = st.tabs(["📝 사용자 (서명하기)", "⚙️ 관리자 (문서등록)"])

# ==========================================
# 탭 1: 사용자 (서명하기)
# ==========================================
with tab_user:
    st.subheader("문서 서명하기")
    
    # PDF 목록 가져오기 (확장자 제거하고 이름만)
    pdf_files = [f for f in os.listdir("Original_PDFs") if f.endswith(".pdf")]
    
    if not pdf_files:
        st.warning("등록된 문서가 없습니다. 관리자 탭에서 문서를 먼저 등록해주세요.")
    else:
        selected_doc = st.selectbox("서명할 문서를 선택하세요", pdf_files)
        
        if selected_doc:
            col1, col2 = st.columns([1, 1])
            
            # 왼쪽: 문서 미리보기
            with col1:
                st.markdown("##### 📄 문서 미리보기 (1페이지)")
                doc_path = os.path.join("Original_PDFs", selected_doc)
                try:
                    doc = fitz.open(doc_path)
                    page = doc[0]  # 첫 페이지만
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.image(img, use_container_width=True)
                except Exception as e:
                    st.error(f"문서를 불러오는 중 오류 발생: {e}")

            # 오른쪽: 서명 패드
            with col2:
                st.markdown("##### ✍️ 여기에 서명하세요")
                # 캔버스 설정
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0)",  # 투명 배경
                    stroke_width=2,
                    stroke_color="#000000",
                    background_color="#f0f2f6",
                    height=200,
                    width=400,
                    drawing_mode="freedraw",
                    key="signature_canvas",
                )

                if st.button("✅ 서명 제출 완료", type="primary"):
                    if canvas_result.image_data is not None:
                        # TODO: 여기에 실제 PDF 합성 로직 추가 (필요시 구현해 드림)
                        st.success(f"'{selected_doc}' 문서에 서명이 완료되었습니다! (현재는 UI만 동작)")
                        st.balloons()
                    else:
                        st.warning("먼저 서명을 그려주세요.")

# ==========================================
# 탭 2: 관리자 (문서 업로드)
# ==========================================
with tab_admin:
    st.subheader("📂 새 회의록 등록")
    
    uploaded_file = st.file_uploader("PDF 회의록 파일을 업로드하세요", type="pdf")
    doc_title = st.text_input("문서 제목 (저장될 파일명)", placeholder="예: 2024_03_10_교과협의회")
    
    if st.button("💾 문서 저장"):
        if uploaded_file and doc_title:
            save_path = os.path.join("Original_PDFs", f"{doc_title}.pdf")
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"'{doc_title}.pdf' 등록이 완료되었습니다!")
            st.rerun()  # 새로고침해서 사용자 탭 리스트 갱신
        else:
            st.error("파일과 제목을 모두 입력해주세요.")
