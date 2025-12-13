"""日単位データ取得
指定日付のデータタイプを取得してParquet保存
"""

import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Union

from .converter import convert_lzh_to_parquet
from .downloader import download_jrdb_file
from .entities.jrdb import JRDBDataType
from .race_key_generator import generate_jrdb_data_file_url
from .utils.date_formatter import create_date_from_ymd, format_date_iso, format_date_jrdb

logger = logging.getLogger(__name__)


def fetch_single_data_type(
    year: int,
    month: int,
    day: int,
    dataType: JRDBDataType,
    outputDir: Union[str, Path],
    dateStr: str
) -> Dict[str, Union[str, int, bool, Optional[str]]]:
    """単一のデータタイプのデータを取得してParquetに保存（内部関数）
    
    Args:
        year: 年
        month: 月
        day: 日
        dataType: データタイプ
        outputDir: 出力ディレクトリ
        dateStr: 日付文字列（ISO形式）
    
    Returns:
        結果辞書
    """
    logger.info('日単位データ取得開始', extra={'date': dateStr, 'dataType': dataType.value})
    
    outputPath = Path(outputDir)
    outputPath.mkdir(parents=True, exist_ok=True)
    
    try:
        actualDataType = dataType.value
        dateObj = create_date_from_ymd(year, month, day)
        dateStrJRDB = format_date_jrdb(year, month, day)
        sourceUrl = generate_jrdb_data_file_url(actualDataType, dateObj)
        lzhBuffer = download_jrdb_file(sourceUrl)
        fileName = f'{actualDataType}{dateStrJRDB}'
        
        # LZHファイルも保存（PredictionExecutorで使用するため）
        lzhFilePath = outputPath / f'{fileName}.lzh'
        with open(lzhFilePath, 'wb') as f:
            f.write(lzhBuffer)
        
        # Parquetファイルも保存
        parquetFilePath = outputPath / f'{fileName}.parquet'
        _, records = convert_lzh_to_parquet(lzhBuffer, actualDataType, year, parquetFilePath)
        
        if len(records) == 0:
            raise ValueError('パースされたレコードが0件です')
        
        logger.info('日単位データ取得完了', extra={
            'dataType': actualDataType,
            'date': dateStr,
            'recordCount': len(records),
            'lzhPath': str(lzhFilePath),
            'parquetPath': str(parquetFilePath)
        })
        
        return {
            'date': dateStr,
            'dataType': actualDataType,
            'success': True,
            'recordCount': len(records),
            'outputPath': str(parquetFilePath),
            'lzhPath': str(lzhFilePath),
            'fileName': fileName
        }
    except Exception as error:
        errorMessage = str(error)
        logger.error('日単位データ取得エラー', extra={
            'date': dateStr,
            'dataType': dataType.value,
            'error': errorMessage
        })
        
        return {
            'date': dateStr,
            'dataType': dataType.value,
            'success': False,
            'recordCount': 0,
            'error': errorMessage
        }


def fetch_daily_data(
    year: int,
    month: int,
    day: int,
    dataTypes: List[JRDBDataType],
    outputDir: Union[str, Path] = 'cache/jrdb/parquet'
) -> List[Dict[str, Union[str, int, bool, Optional[str]]]]:
    """日単位で指定されたデータタイプのデータを取得してParquetに保存
    
    Args:
        year: 年
        month: 月
        day: 日
        dataTypes: データタイプの配列
        outputDir: 出力ディレクトリ（デフォルト: 'cache/jrdb/parquet'）
    
    Returns:
        結果のリスト
    """
    dateStr = format_date_iso(year, month, day)
    
    logger.info('日単位データ取得開始（複数データタイプ）', extra={
        'date': dateStr,
        'dataTypes': [dt.value for dt in dataTypes]
    })
    
    results: List[Dict[str, Union[str, int, bool, Optional[str]]]] = []
    
    for dataType in dataTypes:
        try:
            result = fetch_single_data_type(year, month, day, dataType, outputDir, dateStr)
            results.append(result)
        except Exception as error:
            errorMessage = str(error)
            logger.error('データタイプ取得エラー', extra={
                'date': dateStr,
                'dataType': dataType.value,
                'error': errorMessage
            })
            results.append({
                'date': dateStr,
                'dataType': dataType.value,
                'success': False,
                'recordCount': 0,
                'error': errorMessage
            })
    
    successCount = sum(1 for r in results if r.get('success', False))
    logger.info('日単位データ取得完了', extra={
        'date': dateStr,
        'totalDataTypes': len(dataTypes),
        'successCount': successCount
    })
    
    return results

