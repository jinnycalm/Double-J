from fastapi import APIRouter, Depends
from models.map import MapInfo
from database.connection import get_db_conn

router = APIRouter()

@router.post("/analyze")
async def analyze_benefit(place: MapInfo, db_conn = Depends(get_db_conn)):
    print(f"프론트에서 수신한 매장 이름: {place['place_name']}, 카테고리: {place['category_group_name']}")
    
    # 처리 완료 후 결과 반환
    return {
        "status": "success",
        "message": f"'{place['place_name']}' 매장에 대한 분석이 완료되었습니다.",
        "best_card": "예시: 토스 뱅크 체크카드",
        "details": "스타벅스 10% 캐시백 적용"
    }
