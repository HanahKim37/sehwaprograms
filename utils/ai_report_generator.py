import json
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SYSTEM_PROMPT = """
너는 대한민국 고등학교 생활기록부를 분석하는 전문 진로·학업 컨설턴트이자 교사 보조 AI이다.

역할:
- 학생의 세특, 행특, 창체 기록을 종합 분석하여
- 교사가 작성한 것처럼 공적인 문체(~함, ~보임)로
- SH-Insight 심층 분석 보고서를 작성한다.

[작성 원칙]
1. 허위 사실 생성 금지 (근거 없는 단정 금지)
2. 생활기록부 문체 유지 (~함, ~보임)
3. 과장 표현 금지
4. 모든 평가는 근거를 함께 제시
5. 결과는 반드시 JSON 형식
6. JSON 외 텍스트 출력 금지

[출력 스키마 - 반드시 이 키를 포함]
{
  "학생 정보": {"학번": "...", "성명": "...", "학년 수": 0},
  "종합 평가": "문장",
  "핵심 강점": ["...", "...", "..."],
  "보완 추천 영역": ["...", "..."],
  "3대 평가 항목별 상세 분석": {
    "학업역량": "문장",
    "학업태도": "문장",
    "학업 외 소양": "문장"
  }
}
"""

def _safe_json_loads(text: str):
    if not text:
        return None
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end+1])
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
    # 원문이 비어있으면 모델이 “기록이 없음”으로 갈 확률이 매우 높음 → 여기서 최소 보정
    seteuk_text = seteuk_text.strip() if seteuk_text else ""
    haengteuk_text = haengteuk_text.strip() if haengteuk_text else ""
    changche_text = changche_text.strip() if changche_text else ""

    user_prompt = f"""
[학생 정보]
- 학번: {student_id}
- 성명(마스킹): {masked_name}
- 학년 수: {year_count}

[세부능력 및 특기사항 원문]
{seteuk_text if seteuk_text else "(비어있음)"}

[행동특성 및 종합의견 원문]
{haengteuk_text if haengteuk_text else "(비어있음)"}

[창의적 체험활동 원문]
{changche_text if changche_text else "(비어있음)"}

[요청]
- 위 원문에 근거하여 분석하라.
- 원문이 비어 있으면 "기록이 없음"이라고만 하지 말고,
  어떤 정보가 부족해서 어떤 판단이 제한되는지 '근거형'으로 작성하라.
- 반드시 시스템 프롬프트의 출력 스키마대로 JSON만 출력하라.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    data = _safe_json_loads(content)

    if data is None:
        # JSON 파싱 실패 시에도 앱이 죽지 않도록 최소 반환
        return {
            "학생 정보": {"학번": str(student_id), "성명": str(masked_name), "학년 수": int(year_count)},
            "종합 평가": "모델 출력이 JSON 형식으로 반환되지 않아 분석 결과를 구조화하지 못함.",
            "핵심 강점": [],
            "보완 추천 영역": ["출력 형식(JSON) 안정화 필요"],
            "3대 평가 항목별 상세 분석": {
                "학업역량": "",
                "학업태도": "",
                "학업 외 소양": ""
            },
            "raw": content
        }

    return data
