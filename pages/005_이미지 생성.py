# streamlit_app.py
import io
import os
import time
import json
import base64
import requests
import streamlit as st
from PIL import Image
from openai import OpenAI

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="Sora2 · GPT-Image-1 Demo", page_icon="🎬", layout="centered")

# 안전한 키 로딩
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY", "")
st.title("Sora2 · GPT-Image-1 생성 스튜디오")
st.caption("프롬프트로 이미지/영상 생성 · 이미지 업로드 변환/편집 | OpenAI API 사용")

with st.sidebar:
    st.header("설정")
    api_key_input = st.text_input("OpenAI API Key (선택 입력)", value="", type="password", help="secrets에 저장되어 있다면 비워두세요")
    if api_key_input.strip():
        OPENAI_API_KEY = api_key_input.strip()
    st.info("키는 세션 메모리에서만 사용됩니다.")
    st.markdown("---")
    st.write("**모델 참고**")
    st.write("• 이미지: `gpt-image-1`")
    st.write("• 영상: `sora-2` (계정 활성 필요)")

if not OPENAI_API_KEY:
    st.warning("OpenAI API 키가 필요합니다. 사이드바에서 입력하거나 secrets.toml에 설정하세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# -----------------------------
# 유틸
# -----------------------------
def _display_image_from_b64(b64_data: str, filename: str = "image.png"):
    image_bytes = base64.b64decode(b64_data)
    st.download_button("이미지 다운로드", data=image_bytes, file_name=filename, mime="image/png")
    st.image(Image.open(io.BytesIO(image_bytes)))

def _bytes_from_uploaded(file):
    # Streamlit UploadedFile -> bytes
    return file.read()

def _safe_int(v, default):
    try:
        return int(v)
    except Exception:
        return default

# -----------------------------
# 탭 구성
# -----------------------------
tab1, tab2, tab3 = st.tabs(["① 프롬프트→이미지", "② 이미지→이미지(편집/변환)", "③ 프롬프트→짧은 영상"])

# -----------------------------
# ① 프롬프트 → 이미지
# -----------------------------
with tab1:
    st.subheader("프롬프트로 고품질 이미지 생성 (GPT-Image-1)")
    prompt = st.text_area("프롬프트*", height=120, placeholder="예) 초여름 아침의 서귀포 수국 정원, 자연광, 잡지 화보 느낌, 타이포그래피 '세화'")
    size = st.selectbox("출력 크기", ["512x512", "768x768", "1024x1024", "1024x1536", "1536x1024"], index=2)
    n_images = st.slider("생성 수", 1, 4, 1)
    transparent = st.checkbox("배경 투명(PNG)", value=False, help="로고/스티커 등 투명 배경이 필요한 경우")
    go = st.button("이미지 생성", type="primary", use_container_width=True)

    if go:
        if not prompt.strip():
            st.error("프롬프트를 입력해 주세요.")
        else:
            with st.spinner("이미지 생성 중…"):
                try:
                    # OpenAI Images API (gpt-image-1)
                    # 공식 가이드: images.generate / edits. (2025-04 공개) 
                    # https://platform.openai.com/docs/guides/image-generation
                    resp = client.images.generate(
                        model="gpt-image-1",
                        prompt=prompt,
                        size=size,
                        quality="high",
                        background="transparent" if transparent else "solid",
                        n=n_images,
                    )
                    for i, datum in enumerate(resp.data, start=1):
                        st.markdown(f"**결과 {i}**")
                        _display_image_from_b64(datum.b64_json, filename=f"gen_{i}.png")
                except Exception as e:
                    st.error(f"이미지 생성 실패: {e}")

# -----------------------------
# ② 이미지 → 이미지 (편집/변환)
# -----------------------------
with tab2:
    st.subheader("업로드 이미지 기반 변환 · 부분편집(마스크)")
    base_img = st.file_uploader("기준 이미지 업로드*", type=["png", "jpg", "jpeg", "webp"])
    mask_img = st.file_uploader("마스크 이미지(선택, PNG 투명영역=보존)", type=["png"], help="마스크 투명 부분은 변경 안 함")
    edit_prompt = st.text_area("지시 프롬프트*", height=100, placeholder="예) 배경을 수국 정원으로 바꾸고, 상단에 '세화 AI 페스티벌' 타이틀 추가")
    size2 = st.selectbox("출력 크기", ["512x512", "768x768", "1024x1024"], index=2, key="edit_size")
    n_variants = st.slider("변형 수", 1, 3, 1, key="edit_n")
    go2 = st.button("이미지 변환/편집 실행", type="primary", use_container_width=True)

    if go2:
        if not base_img or not edit_prompt.strip():
            st.error("기준 이미지와 프롬프트를 모두 입력해 주세요.")
        else:
            try:
                with st.spinner("이미지 편집 중…"):
                    files = {
                        "image": (_bytes_from_uploaded(base_img),),
                    }
                    # openai-python SDK의 images.edits는 파일 경로 또는 파일 객체를 받습니다.
                    # Streamlit 업로드 바이트를 io.BytesIO로 감싸 전달:
                    kwargs = {
                        "model": "gpt-image-1",
                        "prompt": edit_prompt,
                        "size": size2,
                        "n": n_variants,
                    }
                    # mask가 있으면 포함
                    if mask_img is not None:
                        kwargs["mask"] = io.BytesIO(_bytes_from_uploaded(mask_img))
                        kwargs["mask"].name = "mask.png"
                    # 기준 이미지
                    base_bytes = io.BytesIO(_bytes_from_uploaded(base_img))
                    base_bytes.name = "input.png"
                    resp = client.images.edits(
                        image=base_bytes,
                        **kwargs
                    )
                    for i, datum in enumerate(resp.data, start=1):
                        st.markdown(f"**결과 {i}**")
                        _display_image_from_b64(datum.b64_json, filename=f"edit_{i}.png")
            except Exception as e:
                st.error(f"이미지 편집 실패: {e}")

# -----------------------------
# ③ 프롬프트 → 짧은 영상 (Sora 2)
# -----------------------------
with tab3:
    st.subheader("프롬프트로 짧은 영상 생성 (Sora 2)")
    v_prompt = st.text_area("프롬프트*", height=120, placeholder="예) 푸른 수국이 바람에 흔들리는 서귀포 정원, 부드러운 카메라 패닝, 새소리")
    colA, colB = st.columns(2)
    with colA:
        seconds = _safe_int(st.number_input("길이(초)", min_value=3, max_value=25, value=8), 8)
    with colB:
        aspect = st.selectbox("종횡비", ["1:1", "16:9", "9:16", "4:3"], index=1)
    go3 = st.button("영상 생성", type="primary", use_container_width=True)

    # 참고: 공식 문서는 '비디오 생성 작업 생성 → 상태 폴링 → 컨텐츠 다운로드' 플로우를 안내합니다.
    # 일부 계정은 아직 Sora 2 API가 활성화되지 않았을 수 있어 권한/존재 오류를 안내합니다.
    if go3:
        if not v_prompt.strip():
            st.error("프롬프트를 입력해 주세요.")
        else:
            with st.spinner("영상 생성 작업을 시작합니다… (작업 큐/처리 상황을 폴링)"):
                try:
                    # 가능하면 SDK의 videos API를 사용하고, 없으면 REST로 폴백
                    # 여기서는 REST 예시(/v1/video/generations/jobs)를 사용합니다.
                    # (Azure 문서의 Job 패턴과 동일한 개념: 생성→폴링→컨텐츠 조회)
                    # OpenAI 순정 API에서도 유사한 Job 엔드포인트가 순차 도입되고 있습니다.
                    # 참고: https://platform.openai.com/docs/models/sora-2  (모델)
                    headers = {
                        "Authorization": f"Bearer {OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    }

                    w, h = {"1:1": (768, 768), "16:9": (1280, 720), "9:16": (720, 1280), "4:3": (1024, 768)}[aspect]

                    create_url = "https://api.openai.com/v1/video/generations/jobs"
                    body = {
                        "model": "sora-2",
                        "prompt": v_prompt,
                        "n_seconds": int(seconds),
                        "width": w,
                        "height": h,
                        "n_variants": 1
                    }
                    create_res = requests.post(create_url, headers=headers, json=body, timeout=60)
                    if create_res.status_code >= 400:
                        # 권한/알파 비활성 계정의 경우 403/404가 나올 수 있음
                        st.error(f"작업 생성 실패: {create_res.status_code} {create_res.text}")
                    else:
                        job_id = create_res.json().get("id")
                        st.write(f"작업 생성: `{job_id}`")
                        status_url = f"https://api.openai.com/v1/video/generations/jobs/{job_id}"
                        status = None
                        start = time.time()
                        while status not in ("succeeded", "failed", "cancelled"):
                            time.sleep(5)
                            poll = requests.get(status_url, headers=headers, timeout=60)
                            poll_json = poll.json()
                            status = poll_json.get("status")
                            st.write(f"현재 상태: **{status}**")
                            # 3분 타임아웃(적절히 조정)
                            if time.time() - start > 180:
                                st.warning("대기 시간이 길어 중단했습니다. 작업은 백엔드에서 계속될 수 있습니다.")
                                break

                        if status == "succeeded":
                            gens = poll_json.get("generations", [])
                            if not gens:
                                st.error("생성 결과가 비어 있습니다.")
                            else:
                                gen_id = gens[0].get("id")
                                content_url = f"https://api.openai.com/v1/video/generations/{gen_id}/content/video"
                                vid = requests.get(content_url, headers=headers, timeout=120)
                                if vid.ok:
                                    st.success("영상 생성 완료")
                                    st.video(vid.content)
                                    st.download_button("MP4 다운로드", data=vid.content, file_name="sora2_output.mp4", mime="video/mp4")
                                else:
                                    st.error(f"영상 다운로드 실패: {vid.status_code} {vid.text}")
                        elif status in ("failed", "cancelled"):
                            st.error(f"작업이 {status} 상태로 종료되었습니다.")
                        else:
                            st.info("현재 계정에서 API 접근이 제한되어 있을 수 있습니다. Sora 앱/플랜 상태를 확인해 주세요.")
                except Exception as e:
                    st.error(f"영상 생성 중 오류: {e}")

# 푸터
st.markdown("---")
st.caption("ⓒ 2025 • OpenAI API (gpt-image-1, sora-2) • Streamlit 데모")

