import json

from langchain_openai import ChatOpenAI

from server.langgraph.models import AnalysisState, FinalRanking

# LLM 모델을 초기화합니다.
llm = ChatOpenAI(model="gpt-4.1-mini")

def generate_final_ranking(state: AnalysisState) -> dict:
    """통합된 정보를 바탕으로 LLM이 최종 순위 생성"""
    print("\n--- LLM 최종 순위 생성 중 ---")
    
    structured_llm = llm.with_structured_output(FinalRanking)
    
    prompt = f"""
    당신은 대한민국 최고의 카드 혜택 분석 전문가입니다. 사용자의 현재 상황(시간, 날짜, 장소)과 보유한 카드/이벤트 정보를 결합하여 가장 이득이 큰 결제 수단을 추천합니다.(최대 3개)
    만약 조건에 맞는 카드가 1개뿐이라면 1순위만 출력하고 응답을 종료합니다. 절대 2, 3순위를 억지로 만들지 마세요.
    조건에 맞는 카드가 아예 없다면 "현재 조건에서 혜택을 받을 수 있는 카드가 없습니다."라고만 답변하세요.
    결제 금액이 정해져 있지 않으므로, 할인율과 고정 할인 금액을 비교하여 조건부 추천을 할 수 있습니다. (예: '2만원 이상 결제 시 A카드가 유리, 미만 시 B카드가 유리')
    
    **규칙:**
    1. 최종 요약(summary)을 제외한 모든 필드는 문장(~합니다. ~임)으로 끝내지 말고 명사나 키워드로 끝내세요. (ex. 네이버 페이 결제 시 최고 할인율 적용)
    2. 다음의 경우에 해당하는 항목은 추천 리스트에서 반드시 제외하세요.
     - 매장명/지점명이 데이터와 명백히 다르고 연관성이 없는 경우.
     - 해당 카테고리(예: 편의점)와 무관한 혜택인 경우.
    3. 각 추천 항목에 대해 '비판적 검토(critical_review)'를 반드시 포함해야 합니다. 예상되는 단점이나 주의사항(예: 실적 제외, 다른 혜택과 중복 불가 등)을 명확히 지적해주세요. 단점이 없다면 '특별한 단점 없음'으로 표기하세요.
    4. 최종 요약(summary)을 통해 왜 이 순위가 최선인지 사용자에게 친절하게 설명해주세요.(2줄 이내)
    5. `benefit_description` 필드에는 구체적인 할인율이나 금액 대신, 사용자에게 가장 와닿는 형태의 혜택 설명을 요약해서 제공해주세요.
    6. 모든 추천은 반드시 다음 4단계를 거쳐 논리적으로 판단하세요.
    
    1단계: 장소 및 카테고리 매칭
     - 매장명에 지점명(ex. 강남점)이 있다면 지점 전용 혜택을 우선 확인하고, 없으면 본사(순수 매장명) 기준으로 판단하세요.
     - 제공된 카테고리 코드(store_category)를 다음 키워드 그룹으로 치환하여 분석에 활용하세요:
        - 'FD6': FOOD ("음식점", "식당", "외식", "패밀리레스토랑"), 
        - 'CE7': CAFE_BAKERY ("카페", "스타벅스", "베이커리", "커피", "디저트", "투썸", "이디야", "파리바게뜨", "뚜레쥬르"),
        - 'CS2': CONVENIENCE ("편의점", "CU", "GS25", "세븐일레븐", "이마트24", "다이소", "올리브영"),
        - 'HP8', 'PM9': MEDICAL ("병원", "약국", "치과", "한의원", "의료", "건강검진"),
        - 'MT1': SHOPPING ("마트", "이마트", "홈플러스", "롯데마트", "백화점", "아울렛", "쇼핑"),
        - 'AC5': EDUCATION ("학원", "교육", "학습지", "강의", "서점", "도서", "유치원"),
        - 'PK6': PARKING_LOT ("주차장", "주차", "발레파킹"),
        - 'OL7': OIL ("주유", "GSCALTEX", "S-OIL", "현대오일뱅크", "SK에너지", "충전소"), 
        - 'SW8': TRANSPORTATION ("대중교통", "버스", "지하철", "택시", "철도", "KTX", "SRT", "K-패스"),
        - 'CT1': CULTURE_ENTERTAINMENT ("영화", "CGV", "메가박스", "롯데시네마", "문화", "공연", "전시", "테마파크", "놀이공원"),
        - "EX1": OTHER (기타시설)

    2단계: 시간 가용성 체크
     - 현재 시간(current_datetime)을 기준으로 현장 결제 이벤트, 카드 혜택의 [혜택 적용 요일 : 평일/주말] 및 [혜택 적용 시간]을 대조하세요.
     - 시간 조건이 맞지 않는 혜택은 즉시 제외하거나 최하단으로 배치하세요.(요일, 시간 조건이 없는 혜택이면 시간 가용성 체크할 필요 없음)

    3단계: 월초/월말 전략 적용
     - 월초 (1일~15일): 실적 제외 여부보다 **'당장 받는 혜택 금액(할인/적립)'**이 큰 것을 우선순위로 둡니다.
     - 월말 (16일~말일): 혜택이 조금 적더라도 **'카드 실적에 포함되는 결제'**를 우선순위로 둡니다.
     - 예외: 혜택 금액 차이가 2배 이상 압도적이라면 날짜와 상관없이 혜택이 큰 쪽을 추천하고 사유를 명시하세요.

    4단계: 조건부 비교
     - 결제 금액에 따라 유리한 카드가 다르다면(예: 2만원 이상 시 A가 유리), 이를 명확히 구분하여 추천하세요.

    **입력 정보:**
    - 사용자 ID: {state['user_id']}
    - 결제 장소: {state['store_name']}
    - 혜택 적용 카테고리: {state['store_category']} 
    - 현재 시간: {state['current_datetime']}
    - 분석된 카드 혜택: {json.dumps(state['analyzed_cards'], indent=2, ensure_ascii=False)}
    - 현장 결제 이벤트: {json.dumps(state.get('offline_events', []), indent=2, ensure_ascii=False)} 
    """
    # llm이 이해하기 쉽게 json 형식으로 변환(indent로 사람이 보기 쉽게 표현, ensure_ascii로 한글 깨짐 방지)
    
    response = structured_llm.invoke(prompt) 
    
    print(f"✅ LLM이 추천하는 혜택 순위 생성 완료")
    return {"final_ranking": response.model_dump()}


def format_briefing(state: AnalysisState) -> dict:
    """구조화된 순위 결과를 사용자가 보기 좋은 문자열로 변환"""
    print("\n--- 최종 브리핑 포맷팅 중 ---")
    ranking_data = state["final_ranking"]
    briefing = f"✨ **'{state['store_name']}' 최적 결제 플랜** ✨\n\n"
    
    recommendations = ranking_data.get('recommendations', [])
    rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}

    if not recommendations:
        briefing += "🤔 아쉽게도 현재 조건에 맞는 특별한 혜택을 찾지 못했어요."
    else:
        for rec in recommendations:
            rank = rec.get('rank')
            emoji = rank_emojis.get(rank, '🏅')
            
            briefing += f"---\n"
            briefing += f"### {emoji} {rank}순위: {rec['payment_method']}\n"
            briefing += f"- **혜택**: **{rec['benefit_description']}**\n"
            briefing += f"- **👍 장점**: {rec['positive_reason']}\n"
            briefing += f"- **⚠️ 단점**: {rec['critical_review']}\n"
            briefing += f"- **🔍 근거**: {rec['evidence']}\n\n"
    
    if recommendations:
        briefing += f"---\n**💡 최종 요약**\n{ranking_data['summary']}"
    
    print(briefing)
    return {"final_briefing": briefing}