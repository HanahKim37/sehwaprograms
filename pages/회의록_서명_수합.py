import streamlit as st
import os
import fitz  # PyMuPDF
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import pandas as pd
import io
import shutil

# --- 라이브러리 체크 ---
try:
    import xlsxwriter
except ImportError:
    st.error("🚨 'XlsxWriter' 라이브러리가 설치되지 않았습니다. requirements.txt 파일에 'XlsxWriter'를 추가하고 앱을 재부팅(Reboot)해주세요.")
    st.stop()

# 1. 사이드바 함수 로드
try:
    from utils.sidebar import render_sidebar
    render_sidebar()
except:
    # utils가 없거나 로딩 실패시에도 앱이 죽지 않도록 방어
    st.sidebar.warning("사이드바 로딩 실패 (utils 경로 확인 필요)")

# 2. 페이지 설정 (필요시 import 직후로 이동 가능)
# st.set_page_config(page_title="회의록 서명", layout="wide", initial_sidebar_state="expanded")

# --- 설정 및 데이터 ---
BASE_DIR = os.getcwd()
ORIG_DIR = os.path.join(BASE_DIR, "Original_PDFs")
SIGNED_DIR = os.path.join(BASE_DIR, "Signed_Images")

# 폴더 자동 생성
for d in [ORIG_DIR, SIGNED_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# ✅ 선생님 명단 (가나다순)
TEACHER_LIST = sorted([
    "권지연", "김지환", "김하은", "박현태", "황승순", 
    "임진경", "조상현", "이규호", "황순영", "이주영", "김영옥"
])

# 엑셀 생성 함수
def generate_excel_with_images(doc_name, signature_folder):
    output = io.BytesIO()
    df = pd.DataFrame({"성명": TEACHER_LIST})
    
    # XlsxWriter 엔진 사용
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='서명부', index=False)
        workbook = writer.book
        worksheet = writer.sheets['서명부']
        
        # 스타일 설정
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 20)
        worksheet.set_default_row(50)
        
        # 헤더
        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#D7E4BC'})
        worksheet.write('A1', '성명', header_format)
        worksheet.write('B1', '전자서명', header_format)
        
        # 이미지 삽입
        for i, name in enumerate(TEACHER_LIST):
            img_path = os.path.join(signature_folder, f"{name}.png")
            if os.path.exists(img_path):
                worksheet.insert_image(i+1, 1, img_path, {'x_scale': 0.3, 'y_scale': 0.3, 'object_position': 1})
            else:
                worksheet.write(i+1, 1, "(미서명)")
                
    output.seek(0)
    return output

# --- 메인 화면 ---
st.title("✒️ 예체능생활교양과 전자서명")
st.markdown("---")

# ✅ 여기서 변수명을 명확하게 정의합니다 (tab_user, tab_admin)
tab_user, tab_admin = st.tabs(["📝 사용자 (서명하기)", "⚙️ 관리자 (문서관리/삭제/다운로드)"])

# ==========================================
# 탭 1: 사용자 (서명하기)
# ==========================================
with tab_user:
    st.header("📋 서명 진행")
    
    # PDF 목록 로드
    try:
        pdf_files = [f for f in os.listdir(ORIG_DIR) if f.endswith(".pdf")]
    except:
        pdf_files = []
    
    if not pdf_files:
        st.info("현재 등록된 회의록이 없습니다. (관리자 탭에서 등록)")
    else:
        selected_doc = st.selectbox("서명할 문서를 선택하세요", pdf_files)
        
        if selected_doc:
            # 서명 저장 경로 설정
            current_doc_sign_dir = os.path.join(SIGNED_DIR, selected_doc.replace(".pdf", ""))
            if not os.path.exists(current_doc_sign_dir):
                os.makedirs(current_doc_sign_dir)

            st.markdown("---")
            col_left, col_right = st.columns([1, 1.2])
            
            # 왼쪽: 현황판 및 서명 입력
            with col_left:
                st.subheader("1. 서명 현황표")
                
                # 현황 데이터 생성
                status_data = []
                signed_count = 0
                for name in TEACHER_LIST:
                    sign_path = os.path.join(current_doc_sign_dir, f"{name}.png")
                    if os.path.exists(sign_path):
                        status_data.append({"성명": name, "상태": "✅ 서명완료"})
                        signed_count += 1
                    else:
                        status_data.append({"성명": name, "상태": "⬜ 미서명"})
                
                # 진행률 바
                st.progress(signed_count / len(TEACHER_LIST), text=f"완료: {signed_count}명 / 전체: {len(TEACHER_LIST)}명")
                st.dataframe(pd.DataFrame(status_data), use_container_width=True, hide_index=True, height=300)
                
                st.markdown("---")
                st.subheader("2. 내 이름 찾기")
                my_name = st.selectbox("성함을 선택하세요", TEACHER_LIST)
                
                # 서명 여부 체크
                my_sign_path = os.path.join(current_doc_sign_dir, f"{my_name}.png")
                if os.path.exists(my_sign_path):
                    st.success(f"✅ {my_name}님은 이미 서명을 완료하셨습니다.")
                
                # 서명 패드
                st.caption(f"아래 영역에 서명 후 [제출] 버튼을 눌러주세요.")
                canvas = st_canvas(
                    fill_color="rgba(255, 255, 255, 0)", # 투명 배경
                    stroke_width=2,
                    stroke_color="#000",
                    background_color="#f0f2f6",
                    height=150,
                    width=400,
                    drawing_mode="freedraw",
                    key=f"canvas_{selected_doc}_{my_name}" # 캔버스 리셋을 위한 키
                )
                
                if st.button("✅ 서명 제출", use_container_width=True):
                    if canvas.image_data is not None:
                        # 이미지 저장
                        img = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA')
                        img.save(my_sign_path, "PNG")
                        st.toast(f"{my_name}님 서명이 저장되었습니다!", icon="🎉")
                        st.rerun()
                    else:
                        st.warning("서명을 먼저 그려주세요.")

            # 오른쪽: 문서 미리보기
            with col_right:
                st.subheader("📄 회의록 내용")
                doc_path = os.path.join(ORIG_DIR, selected_doc)
                try:
                    doc = fitz.open(doc_path)
                    page = doc[0] # 첫 페이지만
                    pix = page.get_pixmap(dpi=120)
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    st.image(img, caption="문서 미리보기 (1페이지)", use_container_width=True)
                except Exception as e:
                    st.error(f"문서 로딩 실패: {e}")

# ==========================================
# 탭 2: 관리자 (문서 관리)
# ==========================================
with tab_admin:
    st.header("⚙️ 관리자 모드")
    
    # 1. 문서 등록
    with st.expander("➕ 새 문서 등록하기", expanded=True):
        up_file = st.file_uploader("PDF 회의록 업로드", type="pdf")
        up_title = st.text_input("문서 제목 입력 (예: 3월_교과협의회)")
        
        if st.button("문서 저장"):
            if up_file and up_title:
                # 특수문자 제거
                s_title = up_title.replace("/", "_").replace("\\", "_").strip()
                save_path = os.path.join(ORIG_DIR, f"{s_title}.pdf")
                
                try:
                    with open(save_path, "wb") as f:
                        f.write(up_file.getbuffer())
                    
                    # 서명 폴더도 미리 생성
                    os.makedirs(os.path.join(SIGNED_DIR, s_title), exist_ok=True)
                    
                    st.success(f"'{s_title}' 등록 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"저장 실패: {e}")
            else:
                st.warning("파일과 제목을 모두 입력해주세요.")

    st.divider()
    
    # 2. 문서 목록 및 관리
    st.subheader("🗑️ 문서 관리 및 📥 결과 다운로드")
    
    # 파일 목록 다시 읽기
    try:
        admin_pdf_files = [f for f in os.listdir(ORIG_DIR) if f.endswith(".pdf")]
    except:
        admin_pdf_files = []

    if not admin_pdf_files:
        st.caption("등록된 문서가 없습니다.")
    else:
        for p in admin_pdf_files:
            # 4단 컬럼 레이아웃
            c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
            
            d_name = p.replace(".pdf", "") # 확장자 뺀 이름
            
            # 컬럼 1: 문서명
            with c1: 
                st.write(f"📄 **{d_name}**")
            
            # 컬럼 2: 엑셀 다운로드
            with c2:
                s_folder = os.path.join(SIGNED_DIR, d_name)
                # 서명 폴더가 있으면 엑셀 생성
                if os.path.exists(s_folder):
                    try:
                        excel_data = generate_excel_with_images(d_name, s_folder)
                        st.download_button(
                            label="📥 엑셀다운",
                            data=excel_data,
                            file_name=f"{d_name}_서명부.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"down_{p}"
                        )
                    except Exception as e:
                        st.error("생성 오류")
                else:
                    st.caption("데이터 없음")
            
            # 컬럼 3: 비번 입력
            with c3:
                pw = st.text_input("삭제비번", type="password", key=f"pw_{p}", label_visibility="collapsed", placeholder="비번(9835)")
            
            # 컬럼 4: 삭제 버튼
            with c4:
                if st.button("삭제", key=f"del_{p}"):
                    if pw == "9835":
                        try:
                            # PDF 원본 삭제
                            os.remove(os.path.join(ORIG_DIR, p))
                            # 서명 폴더 삭제
                            if os.path.exists(s_folder):
                                shutil.rmtree(s_folder)
                            st.success("삭제됨")
                            st.rerun()
                        except Exception as e:
                            st.error(f"오류: {e}")
                    else:
                        st.error("암호 틀림")
            
            st.divider()
