"""JRDBデータファイルURL生成ユーティリティ"""

from datetime import date

from .entities.jrdb import JRDBDataType, get_jrdb_data_type_info


def generate_jrdb_data_file_url(dataType: str, date_obj: date) -> str:
    """JRDBデータファイルURLを生成
    
    Args:
        dataType: データ種別（例: 'KYI', 'KYH', 'KYG', 'KKA'）
        date_obj: 日付（date型）
    
    Returns:
        JRDBメンバーページのURL
    
    Raises:
        ValueError: 未定義のデータタイプの場合
    
    Note:
        すべてのデータタイプ: `{dataType}{YYMMDD}.lzh` 形式（例: `KYI251102.lzh`, `KZA251108.lzh`, `MZA251108.lzh`）
    """
    try:
        enumDataType = JRDBDataType(dataType.upper())
    except ValueError:
        raise ValueError(f'未定義のデータタイプ: {dataType}. jrdb.pyに定義を追加してください。')
    
    info = get_jrdb_data_type_info(enumDataType)
    
    # すべてのデータタイプは日付を含める
    year2Digit = str(date_obj.year)[-2:]
    month = f'{date_obj.month:02d}'
    day = f'{date_obj.day:02d}'
    dateStr = f'{year2Digit}{month}{day}'
    fileName = f'{dataType}{dateStr}.lzh'
    
    return f"{info['dataFileBaseUrl']}/{fileName}"

