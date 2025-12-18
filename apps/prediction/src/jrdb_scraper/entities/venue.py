"""JRDB競馬場エンティティ
競馬場名とJRDB場コードのマッピング
"""

# 競馬場名とJRDB場コードのマッピング
# JRDB仕様書に基づく正しいマッピング
# 参考: .cursor/rules/JRDB_SPECIFICATIONS.mdc
JRDB_VENUE_CODE_MAP: dict[str, str] = {
    '札幌': '01',
    '函館': '02',
    '福島': '03',
    '新潟': '04',
    '東京': '05',
    '中山': '06',
    '中京': '07',
    '京都': '08',
    '阪神': '09',
    '小倉': '10',
    '門別': '12',
    '盛岡': '13',
    '水沢': '14',
    '金沢': '15',
    '川崎': '16',
    '船橋': '17',
    '大井': '18',
    '浦和': '19',
    '名古屋': '20',
    '園田': '22',
    '姫路': '23',
    '高知': '24',
    '佐賀': '25',
    '荒尾': '26',
    '中津': '27',
    '北九州': '28',
}


def convert_racecourse_to_jrdb_venue_code(racecourse: str) -> str:
    """競馬場名をJRDB場コードに変換
    
    Args:
        racecourse: 競馬場名（例: "東京"）
    
    Returns:
        JRDB場コード（例: "01"）
    
    Raises:
        ValueError: 競馬場名が見つからない場合
    """
    venueCode = JRDB_VENUE_CODE_MAP.get(racecourse)
    if not venueCode:
        valid_racecourses = ', '.join(JRDB_VENUE_CODE_MAP.keys())
        raise ValueError(f'Unknown racecourse: {racecourse}. Valid racecourses: {valid_racecourses}')
    return venueCode

