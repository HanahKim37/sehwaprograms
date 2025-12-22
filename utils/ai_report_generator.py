import json
import streamlit as st
import openai

openai.api_key = st.secrets["OPENAI_API_KEY"]

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
"""

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message["content"]

    return json.loads(content)
