import streamlit as st
from streamlit_drawable_canvas import st_canvas
import fitz  # PyMuPDF
from PIL import Image
import os

# 폴더 생성
os.makedirs("Original_PDFs", exist_ok=True)
os.makedirs("Signed_PDFs", exist_ok=True)

st.title("✒️ 온라인 전자서명 시스템")

# 사이드바에서 모드 선택
menu = st.sidebar.selectbox("메뉴", ["사용자(서명하기)", "관리자(문서업로드)"])

if menu == "관리자(문서업로드)":
    st.header("📂 새 문서 등록")
    uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
    doc_title = st.text_input("문서 제목 입력", placeholder="예: 3/10 1차 회의록")
    
    if st.button("문서 등록"):
        if uploaded_file and doc_title:
            with open(f"Original_PDFs/{doc_title}.pdf", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"'{doc_title}' 등록 완료!")

elif menu == "사용자(서명하기)":
    st.header("📝 문서 서명")
    pdf_list = [f.replace(".pdf", "") for f in os.listdir("Original_PDFs")]
    selected_doc = st.selectbox("서명할 문서를 선택하세요", pdf_list)
    
    if selected_doc:
        # 1. PDF 보여주기 (첫 페이지만 예시로)
        doc_path = f"Original_PDFs/{selected_doc}.pdf"
        doc = fitz.open(doc_path)
        page = doc[0]
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        st.image(img, caption="문서 미리보기", use_column_width=True)
        
        # 2. 서명 패드
        st.subheader("서명란")
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=3,
            stroke_color="#000000",
            background_color="#eee",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="canvas",
        )
        
        if st.button("서명 완료 및 제출"):
            if canvas_result.image_data is not None:
                # 여기에 PDF와 서명 이미지를 합성하는 로직 추가
                st.success("서명이 완료된 PDF가 저장되었습니다!")
