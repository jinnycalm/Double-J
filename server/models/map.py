from typing import TypedDict, Literal, NotRequired

class MapInfo(TypedDict):
    '''카카오 API로 받아온 결과
    id: 매장 고유 ID, place_name: 매장 이름, 
    category_group_code: 카테고리 그룹 코드, category_group_name: 카테고리 그룹 이름,
    phone: 전화번호, address_name: 전체 지번 주소, road_address_name: 전체 도로명 주소,
    x: X 좌표값, y: Y 좌표값, place_url: 장소 상세페이지 URL
    '''
    id: str
    place_name: str
    category_group_code: Literal['FD6', 'CE7', 'CS2', 'HP8','PM9', 'MT1', 'AC5', 'PK6', 'OL7']
    category_group_name: Literal['음식점', '카페', '편의점', '병원', '약국', '대형마트', '학원', '주차장', '주유소/충전소']
    phone: NotRequired[str]
    address_name: NotRequired[str]
    road_address_name: NotRequired[str]
    x: str
    y: str
    place_url: NotRequired[str]