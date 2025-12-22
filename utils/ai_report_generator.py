import json
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

SYSTEM_PROMPT = """
너는 대한민국 고등학교 생활기록부를 분석하는 전문 진로·학업 컨설턴트이자 교사 보조 AI이다.

목표:
- 학생의 세특/행특/창체 원문을 근거로,
- 교사가 작성한 것처럼 공적인 문체(~함, ~보임)로,
- 풍부하고 구체적인 SH-Insight 심층 분석 보고서를 작성한다.

핵심 규칙:
1) 허위 사실 생성 금지: 원문에 없는 사실을 '했다/참여했다/수상했다'처럼 단정하지 말 것.
2) 모든 평가는 근거 문장을 포함할 것: 원문에서 발췌한 문장/구절을 "평가 근거 문장"에 3~6개 제시.
3) 빈약 방지: 단순히 "기록이 없음"만 쓰지 말고, 어떤 정보가 부족해 어떤 판단이 제한되는지까지 서술.
4) 결과는 반드시 JSON만 출력 (JSON 외 텍스트 금지).

[반드시 이 출력 스키마를 그대로 사용]
{
  "학생 정보": {"학번": "...", "성명": "...", "학년 수": 0},
  "종합 평가": "문단(풍부하게)",
  "핵심 강점": ["...", "...", "...", "..."],
  "보완 추천 영역": ["...", "..."],
  "3대 평가 항목별 상세 분석": {
    "학업역량": {"점수": 0, "평가 근거 문장": ["..."], "분석": "문단(풍부)"},
    "학업태도": {"점수": 0, "평가 근거 문장": ["..."], "분석": "문단(풍부)"},
    "학업 외 소양": {"점수": 0, "평가 근거 문장": ["..."], "분석": "문단(풍부)"}
  },
  "영역별 심화 탐구 주제 제안": {
    "자율": "주제+설명(풍부)",
    "진로": "주제+설명(풍부)",
    "동아리": "주제+설명(풍부)"
  },
  "역량 기반 추천 학과": [
    {"학과": "의예과/의학과", "근거": "근거(원문 기반)"},
    {"학과": "기초의과학과", "근거": "근거(원문 기반)"},
    {"학과": "보건행정학과", "근거": "근거(원문 기반)"}
  ],
  "맞춤형 성장 제안": {
    "생활기록부 중점 보완 전략": "문단(풍부)",
    "추천 학교 행사": ["행사1: 이유", "행사2: 이유"],
    "추천 활동 설계": ["활동1: 산출물/방법", "활동2: 산출물/방법"]
  },
  "추천 도서": [
    {"분류": "약점 보완", "도서": "...", "저자": "...", "추천 이유": "..."},
    {"분류": "관심사 심화", "도서": "...", "저자": "...", "추천 이유": "..."},
    {"분류": "희망 진로 연계", "도서": "...", "저자": "...", "추천 이유": "..."}
  ]
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
    seteuk_text = (seteuk_text or "").strip()
    haengteuk_text = (haengteuk_text or "").strip()
    changche_text = (changche_text or "").strip()

    user_prompt = f"""
[학생 정보]
- 학번: {student_id}
- 성명(마스킹): {masked_name}
- 학년 수: {year_count}

[세특 원문]
{seteuk_text if seteuk_text else "(원문이 비어 있음)"}

[행특 원문]
{haengteuk_text if haengteuk_text else "(원문이 비어 있음)"}

[창체 원문]
{changche_text if changche_text else "(원문이 비어 있음)"}

[작성 지침 - 매우 중요]
- 세 영역(세특/행특/창체)에서 각각 의미있는 근거 문장을 최소 1개 이상 찾으려 시도할 것.
- 근거 문장은 원문에서 발췌한 문장/구절 형태로 3~6개 제시.
- 점수(0~10)는 근거의 질/일관성/심화 수준/자기주도성 등을 고려해 산정.
- 산정 근거는 "분석"에 녹여 설명할 것.
- 과장 금지. 원문에 없는 대회/수상/시간/직책을 단정하지 말 것.
- 반드시 SYSTEM_PROMPT의 JSON 스키마 그대로 출력하라.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.25,
    )

    content = response.choices[0].message.content
    data = _safe_json_loads(content)

    if data is None:
        return {
            "학생 정보": {"학번": str(student_id), "성명": str(masked_name), "학년 수": int(year_count)},
            "종합 평가": "모델 출력이 JSON 형식으로 반환되지 않아 보고서를 구조화하지 못함.",
            "핵심 강점": [],
            "보완 추천 영역": ["출력 형식(JSON) 안정화 필요"],
            "3대 평가 항목별 상세 분석": {
                "학업역량": {"점수": 0, "평가 근거 문장": [], "분석": ""},
                "학업태도": {"점수": 0, "평가 근거 문장": [], "분석": ""},
                "학업 외 소양": {"점수": 0, "평가 근거 문장": [], "분석": ""},
            },
            "영역별 심화 탐구 주제 제안": {"자율": "", "진로": "", "동아리": ""},
            "역량 기반 추천 학과": [],
            "맞춤형 성장 제안": {
                "생활기록부 중점 보완 전략": "",
                "추천 학교 행사": [],
                "추천 활동 설계": []
            },
            "추천 도서": [],
            "raw": content
        }

    return data
