import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import io
import shutil

# 1. 사이드바 함수 가져오기
from utils.sidebar import render_sidebar

# 2. 페이지 설정
st.set_page_config(
    page_title="회의록 서명",
    layout="wide",
    initial_sidebar_state="expanded"
)

render_sidebar()

# --- 설정 및 데이터 ---
BASE_DIR = os.getcwd()
ORIG_DIR = os.path.join(BASE_DIR, "Original_PDFs")
SIGNED_DIR = os.path.join(BASE_DIR, "Signed_Images") # 서명 이미지가 저장될 폴더

# 폴더 생성
for d in [ORIG_DIR, SIGNED_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# 교사 명단 (가나다 순 정렬)
TEACHER_LIST = sorted([
    "권지연", "김지환", "김하은", "박현태", "황승순", 
    "임진경", "조상현", "이규호", "황순영", "이주영", "김영옥"
])

# 엑셀 생성 함수 (이미지 포함)
def generate_excel_with_images(doc_name, signature_folder):
    output = io.BytesIO()
    # 데이터프레임 생성
    df = pd.DataFrame({"성명": TEACHER_LIST})
    
    # Pandas XlsxWriter 엔진 사용
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='서명부', index=False)
        workbook = writer.book
        worksheet = writer.sheets['서명부']
        
        # 서식 설정
        worksheet.set_column('A:A', 15) # 성명 컬럼 너비
        worksheet.set_column('B:B', 20) # 서명 컬럼 너비
        worksheet.set_default_row(50)   # 행 높이
        
        # 헤더 쓰기
        worksheet.write('B1', '전자서명')
        
        # 이미지 삽입 Loop
        for i, name in enumerate(TEACHER_LIST):
            img_path = os.path.join(signature_folder, f"{name}.png")
            if os.path.exists(img_path):
                # 이미지가 있으면 엑셀 B열에 삽입
                worksheet.insert_image(i+1, 1, img_path, {'x_scale': 0.3, 'y_scale': 0.3, 'object_position': 1})
            else:
                worksheet.write(i+1, 1, "(미서명)")
                
    output.seek(0)
    return output

# --- 메인 화면 ---
st.title("✒️ 예체능생활교양과 전자서명")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 사용자 (서명하기)", "⚙️ 관리자 (문서관리)"])

# ==========================================
# 탭 1: 사용자 (서명하기)
# ==========================================
with tab1:
    st.header("📋 회의록 서명")
    
    # 등록된 PDF 목록
    try:
        pdf_files = [f for f in os.listdir(ORIG_DIR) if f.endswith(".pdf")]
    except:
        pdf_files = []
    
    if not pdf_files:
        st.info("현재 서명할 문서가 없습니다.")
    else:
        # 1. 문서 선택
        selected_doc = st.selectbox("서명할 문서를 선택하세요", pdf_files)
        
        if selected_doc:
            # 해당 문서의 서명 저장 폴더 경로
            current_doc_sign_dir = os.path.join(SIGNED_DIR, selected_doc.replace(".pdf", ""))
            if not os.path.exists(current_doc_sign_dir):
                os.makedirs(current_doc_sign_dir)

            st.markdown("---")
            
            # 레이아웃: 왼쪽(현황판/서명) | 오른쪽(문서뷰어)
            col_left, col_right = st.columns([1, 1.2])
            
            with col_left:
                st.subheader("1. 서명 현황")
                
                # 서명 상태 확인
                status_data = []
                signed_count = 0
                for name in TEACHER_LIST:
                    sign_path = os.path.join(current_doc_sign_dir, f"{name}.png")
                    if os.path.exists(sign_path):
                        status_data.append({"성명": name, "상태": "✅ 서명완료"})
                        signed_count += 1
                    else:
                        status_data.append({"성명": name, "상태": "⬜ 미서명"})
                
                # 진행률 표시
                progress = signed_count / len(TEACHER_LIST)
                st.progress(progress, text=f"서명 진행률: {signed_count}/{len(TEACHER_LIST)}명")
                
                # 현황 테이블 (데이터프레임)
                st.dataframe(
                    pd.DataFrame(status_data), 
                    use_container_width=True, 
                    hide_index=True,
                    height=200
                )
                
                st.markdown("---")
                st.subheader("2. 서명 하기")
                
                # 본인 이름 선택
                selected_name = st.selectbox("본인의 성함을 선택해주세요", TEACHER_LIST)
                
                # 이미 서명했는지 확인
                user_sign_path = os.path.join(current_doc_sign_dir, f"{selected_name}.png")
                already_signed = os.path.exists(user_sign_path)
                
                if already_signed:
                    st.success(f"{selected_name}님은 이미 서명을 완료하셨습니다. (다시 하면 덮어씌워집니다)")
                
                st.caption("아래 박스에 서명 후 '제출하기'를 눌러주세요.")
                
                # 캔버스 (서명판)
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0)",
                    stroke_width=2,
                    stroke_color="#000000",
                    background_color="#f0f2f6",
                    height=150,
                    width=400,
                    drawing_mode="freedraw",
                    key=f"canvas_{selected_doc}_{selected_name}", # 키를 다르게 줘서 캔버스 초기화
                )

                if st.button("✅ 서명 제출하기", type="primary", use_container_width=True):
                    if canvas_result.image_data is not None:
                        # 이미지 저장 (PNG)
                        img_data = canvas_result.image_data
                        img = Image.fromarray(img_data.astype('uint8'), 'RGBA')
                        img.save(user_sign_path, "PNG")
                        
                        st.toast(f"{selected_name}님의 서명이 저장되었습니다!", icon="🎉")
                        st.rerun() # 화면 갱신
                    else:
                        st.warning("서명을 그려주세요.")

            # 오른쪽: 문서 뷰어
            with col_right:
                st.subheader("📄 문서 확인")
                doc_full_path = os.path.join(ORIG_DIR, selected_doc)
                try:
                    doc = fitz.open(doc_full_path)
                    # 첫 페이지만 미리보기 (필요시 페이지 넘김 구현 가능)
                    page = doc[0] 
                    pix = page.get_pixmap(dpi=120)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.image(img, caption=f"{selected_doc} (1페이지)", use_container_width=True)
                except Exception as e:
                    st.error("문서 로딩 실패")

# ==========================================
# 탭 2: 관리자 (문서 관리)
# ==========================================
with tab_admin:
    st.header("📂 문서 관리 및 결과 다운로드")
    
    # 1. 새 문서 등록
    with st.expander("➕ 새 문서 등록하기", expanded=True):
        uploaded_file = st.file_uploader("PDF 파일 업로드", type="pdf")
        doc_title_input = st.text_input("문서 제목 (예: 3월_교과협의회)", placeholder="파일명을 입력하세요")
        
        if st.button("💾 문서 저장"):
            if uploaded_file and doc_title_input:
                safe_title = doc_title_input.replace("/", "_").replace("\\", "_")
                save_path = os.path.join(ORIG_DIR, f"{safe_title}.pdf")
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # 서명 저장용 폴더도 미리 생성
                os.makedirs(os.path.join(SIGNED_DIR, safe_title), exist_ok=True)
                
                st.success(f"등록 완료: {safe_title}.pdf")
                st.rerun()
            else:
                st.warning("파일과 제목을 모두 입력해주세요.")

    st.markdown("---")
    
    # 2. 등록된 문서 목록 및 관리 (삭제/엑셀다운)
    st.subheader("📑 등록된 문서 목록")
    
    if not pdf_files:
        st.write("등록된 문 서가 없습니다.")
    else:
        for pfile in pdf_files:
            col_doc, col_down, col_del_pw, col_del_btn = st.columns([2, 1.5, 1.5, 1])
            
            doc_name_only = pfile.replace(".pdf", "")
            sign_folder = os.path.join(SIGNED_DIR, doc_name_only)
            
            # 문서 이름
            with col_doc:
                st.write(f"📄 **{doc_name_only}**")

            # 엑셀 다운로드 버튼
            with col_down:
                if os.path.exists(sign_folder):
                    excel_data = generate_excel_with_images(doc_name_only, sign_folder)
                    st.download_button(
                        label="📥 엑셀 다운로드",
                        data=excel_data,
                        file_name=f"{doc_name_only}_서명부.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"down_{pfile}"
                    )
                else:
                    st.caption("서명 데이터 없음")

            # 삭제 (비밀번호)
            with col_del_pw:
                del_pw = st.text_input("비번", type="password", key=f"pw_{pfile}", label_visibility="collapsed", placeholder="삭제비번")
            
            with col_del_btn:
                if st.button("삭제", key=f"del_{pfile}"):
                    if del_pw == "9835":
                        # 원본 PDF 삭제
                        os.remove(os.path.join(ORIG_DIR, pfile))
                        # 서명 폴더 삭제
                        if os.path.exists(sign_folder):
                            shutil.rmtree(sign_folder)
                        st.success("삭제됨")
                        st.rerun()
                    else:
                        st.error("비번 오류")
            
            st.divider()
