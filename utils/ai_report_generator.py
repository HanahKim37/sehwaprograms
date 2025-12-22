import json
import os
import streamlit as st
from openai import OpenAI

# Streamlit Secrets에서 키 로드
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SYSTEM_PROMPT = """
너는 대한민국 고등학교 생활기록부를 분석하는
전문 진로·학업 컨설턴트이자 교사 보조 AI이다.

너의 역할은 학생의 세특, 행특, 창체 기록을 종합 분석하여
교사가 작성한 것처럼 공적인 문체(~함, ~보임)로
SH-Insight 심층 분석 보고서를 작성하는 것이다.

[작성 원칙]
1. 허위 사실 생성 금지
2. 생활기록부 문체 유지
3. 과장 표현 금지
4. 모든 평가는 근거 포함
5. 결과는 반드시 JSON 형식
6. JSON 외 텍스트 출력 금지
"""

def _safe_json_loads(text: str):
    """모델 출력이 JSON 앞뒤로 문구를 붙였을 때를 대비한 최소 방어."""
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None

def generate_sh_insight_report(
    student_id: str,
    masked_name: str,
    year_count: int,
    seteuk_text: str,
    haengteuk_text: str,
    changche_text: str,
):
    user_prompt = f"""
[학생 정보]
- 학번: {student_id}
- 성명: {masked_name}
- 학년 수: {year_count}

[세부능력 및 특기사항]
{seteuk_text}

[행동특성 및 종합의견]
{haengteuk_text}

[창의적 체험활동]
{changche_text}

[요청]
지정된 JSON 스키마를 정확히 따르는
SH-Insight 심층 분석 보고서를 작성하라.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content  # ✅ v1 방식

    data = _safe_json_loads(content)
    if data is None:
        # 운영 중 장애를 줄이기 위한 최소 fallback
        return {"error": "MODEL_OUTPUT_NOT_JSON", "raw": content}

    return data
