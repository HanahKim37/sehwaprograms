import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# 1. 사이드바 함수 가져오기 (필수)
from utils.sidebar import render_sidebar

# 2. 페이지 설정
st.set_page_config(
    page_title="회의록 서명",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 3. 공통 사이드바 렌더링 (이게 있어야 왼쪽 메뉴가 사라지지 않습니다!)
render_sidebar()

# --- 폴더 생성 및 설정 (오류 방지) ---
# 현재 파일이 있는 위치가 아니라, 실행되는 루트 경로 기준으로 폴더를 만듭니다.
BASE_DIR = os.getcwd()
ORIG_DIR = os.path.join(BASE_DIR, "Original_PDFs")
SIGNED_DIR = os.path.join(BASE_DIR, "Signed_PDFs")

# 폴더가 없으면 생성 (FileNotFoundError 방지)
if not os.path.exists(ORIG_DIR):
    os.makedirs(ORIG_DIR)
if not os.path.exists(SIGNED_DIR):
    os.makedirs(SIGNED_DIR)

# --- 메인 화면 ---
st.title("✒️ 온라인 회의록 서명 시스템")
st.markdown("---")

# 4. 관리자/사용자 모드를 '탭'으로 분리 (사이드바 X, 메인 화면 O)
tab1, tab2 = st.tabs(["📝 사용자 (서명하기)", "⚙️ 관리자 (문서등록)"])

# ==========================================
# 탭 1: 사용자 (서명하기)
# ==========================================
with tab1:
    st.header("📋 서명할 문서 선택")
    
    # PDF 파일 목록 불러오기
    try:
        pdf_files = [f for f in os.listdir(ORIG_DIR) if f.endswith(".pdf")]
    except Exception:
        pdf_files = []
    
    if not pdf_files:
        st.info("현재 등록된 회의록이 없습니다. 관리자 탭에서 먼저 등록해주세요.")
    else:
        selected_doc = st.selectbox("서명할 회의록을 선택하세요", pdf_files)
        
        if selected_doc:
            st.markdown("---")
            col1, col2 = st.columns([1.2, 1])
            
            # 왼쪽: 문서 미리보기
            with col1:
                st.subheader("📄 문서 확인")
                doc_path = os.path.join(ORIG_DIR, selected_doc)
                try:
                    doc = fitz.open(doc_path)
                    page = doc[0]  # 첫 페이지만 미리보기
                    pix = page.get_pixmap(dpi=150)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.image(img, caption="문서 미리보기 (1페이지)", use_container_width=True)
                except Exception as e:
                    st.error(f"문서를 불러올 수 없습니다: {e}")

            # 오른쪽: 서명 패드
            with col2:
                st.subheader("✍️ 전자 서명")
                st.caption("아래 영역에 마우스나 터치로 서명하세요.")
                
                # 캔버스 (서명판)
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0)",  # 배경 투명
                    stroke_width=2,
                    stroke_color="#000000",
                    background_color="#f0f2f6",
                    height=200,
                    width=400,
                    drawing_mode="freedraw",
                    key="signature_canvas",
                )

                if st.button("✅ 서명 제출하기", type="primary", use_container_width=True):
                    if canvas_result.image_data is not None:
                        # [TODO] 여기에 실제 PDF 합성 및 저장 로직 추가
                        # 현재는 UI 동작만 확인
                        st.success(f"'{selected_doc}' 문서에 서명이 정상적으로 제출되었습니다!")
                        st.balloons()
                    else:
                        st.warning("서명란이 비어있습니다. 서명을 먼저 그려주세요.")

# ==========================================
# 탭 2: 관리자 (문서 업로드)
# ==========================================
with tab2:
    st.header("📂 새 회의록 등록")
    st.caption("PDF 파일을 업로드하면 사용자 탭에 즉시 표시됩니다.")
    
    uploaded_file = st.file_uploader("PDF 파일 선택", type="pdf")
    doc_title_input = st.text_input("문서 제목 (예: 3월_교과협의회)", placeholder="파일명을 입력하세요")
    
    if st.button("💾 문서 저장"):
        if uploaded_file and doc_title_input:
            # 파일명 안전하게 처리 (특수문자 / 제거)
            safe_title = doc_title_input.replace("/", "_").replace("\\", "_")
            save_path = os.path.join(ORIG_DIR, f"{safe_title}.pdf")
            
            try:
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"문서가 성공적으로 등록되었습니다: {safe_title}.pdf")
                st.rerun()  # 화면 새로고침하여 사용자 탭 목록 갱신
            except Exception as e:
                st.error(f"파일 저장 중 오류가 발생했습니다: {e}")
        else:
            st.warning("파일을 첨부하고 제목을 입력해주세요.")
