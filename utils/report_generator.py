import openai
from fpdf import FPDF

def generate_report_text(name, number, df_seteuk, df_haeng, df_chang):
    """ChatGPT API를 이용하여 상담 보고서를 텍스트로 생성"""

    prompt = f"""
    아래 학생의 생기부 데이터를 분석하여 전문적인 상담 보고서를 작성하시오.

    학생 이름(마스킹): {name}
    학번: {number}

    [세특]
    {df_seteuk.to_string()}

    [행동특성 및 종합의견]
    {df_haeng.to_string()}

    [창체 활동]
    {df_chang.to_string()}

    반드시 아래 구조로 보고서를 작성하시오.

    1. 제목 + 학생 기본 정보(이름 마스킹 유지)
    2. 종합 평가 (희망 진로 포함)
    3. 핵심 역량 분석
       - 삼각형 그래프 설명
       - 핵심 강점 3개
       - 보완 추천 영역 3개
    4. 3대 평가 항목별 상세 분석
       - 학업 역량 (평가 근거 문항 포함)
       - 학업 태도 (평가 근거 문항 포함)
       - 학업 외 소양 (평가 근거 문항 포함)
    5. 맞춤형 성장 제안 (생활기록부 기반)

    전문적이며 교사의 상담 문체로 작성할 것.
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


def generate_report_pdf(text):
    """텍스트 기반 PDF 생성"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for line in text.split("\n"):
        pdf.multi_cell(0, 7, line)

    return pdf.output(dest="S").encode("latin1")
