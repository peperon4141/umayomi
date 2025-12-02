"""日付フォーマットユーティリティ"""

from datetime import date


def create_date_from_ymd(year: int, month: int, day: int) -> date:
    """年、月、日からDateオブジェクトを作成
    
    Args:
        year: 年
        month: 月
        day: 日
    
    Returns:
        dateオブジェクト
    """
    return date(year, month, day)


def format_date_iso(year: int, month: int, day: int) -> str:
    """年、月、日からISO形式の日付文字列を作成（YYYY-MM-DD）
    
    Args:
        year: 年
        month: 月
        day: 日
    
    Returns:
        ISO形式の日付文字列（YYYY-MM-DD）
    """
    return f'{year}-{month:02d}-{day:02d}'


def format_date_jrdb(year: int, month: int, day: int) -> str:
    """年、月、日からJRDB形式の日付文字列を作成（YYMMDD）
    
    Args:
        year: 年
        month: 月
        day: 日
    
    Returns:
        JRDB形式の日付文字列（YYMMDD）
    """
    year2Digit = str(year)[-2:]
    return f'{year2Digit}{month:02d}{day:02d}'


def format_year_2digit(year: int) -> str:
    """年から2桁の年文字列を作成（YY）
    
    Args:
        year: 年
    
    Returns:
        2桁の年文字列（YY）
    """
    return str(year)[-2:]

