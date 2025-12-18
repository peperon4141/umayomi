"""日単位データ取得
指定日付のデータタイプを取得してParquet保存
"""

import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

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
    dateStr: str,
    bac_df: Optional[pd.DataFrame] = None
) -> Dict[str, Union[str, int, bool, Optional[str]]]:
    """単一のデータタイプのデータを取得してParquetに保存（内部関数）
    
    Args:
        year: 年
        month: 月
        day: 日
        dataType: データタイプ
        outputDir: 出力ディレクトリ
        dateStr: 日付文字列（ISO形式）
        bac_df: BACデータ（KYI等の年月日がないデータタイプのrace_key生成に使用、オプション）
    
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
        _, records = convert_lzh_to_parquet(lzhBuffer, actualDataType, year, parquetFilePath, bac_df=bac_df)
        
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
        error_type = type(error).__name__
        errorMessage = f"{error_type}: {error}"
        # extra はフォーマッタによって表示されないことがあるため、メッセージ本体に含める
        # スタックトレースも必ず出す（原因調査のため）
        logger.exception(f"日単位データ取得エラー date={dateStr} dataType={dataType.value}")
        
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
    
    # KYI等の年月日がないデータタイプのrace_key生成用に、BACデータを事前に読み込む
    bac_df: Optional[pd.DataFrame] = None
    bac_result: Optional[Dict[str, Union[str, int, bool, Optional[str]]]] = None
    
    # BACが含まれている場合は、先に処理する
    if JRDBDataType.BAC in dataTypes:
        try:
            bac_result = fetch_single_data_type(year, month, day, JRDBDataType.BAC, outputDir, dateStr)
            if bac_result.get('success', False) and bac_result.get('outputPath'):
                bac_parquet_path = Path(bac_result['outputPath'])
                if bac_parquet_path.exists():
                    bac_df = pd.read_parquet(bac_parquet_path)
                    logger.info('BACデータを読み込みました（KYI等のrace_key生成用）', extra={
                        'date': dateStr,
                        'recordCount': len(bac_df) if bac_df is not None else 0
                    })
        except Exception as e:
            logger.warning('BACデータの読み込みに失敗しました（KYI等のrace_key生成に影響する可能性があります）', extra={
                'date': dateStr,
                'error': str(e)
            })
    
    results: List[Dict[str, Union[str, int, bool, Optional[str]]]] = []
    
    # BACの結果を先に追加（既に取得済みの場合）
    if bac_result is not None:
        results.append(bac_result)
    
    for dataType in dataTypes:
        # BACは既に処理済みなのでスキップ
        if dataType == JRDBDataType.BAC:
            continue
        
        try:
            # KYI等の年月日がないデータタイプの場合は、BACデータを渡す
            result = fetch_single_data_type(
                year, month, day, dataType, outputDir, dateStr,
                bac_df=bac_df
            )
            results.append(result)
        except Exception as error:
            error_type = type(error).__name__
            errorMessage = f"{error_type}: {error}"
            logger.exception(f"データタイプ取得エラー date={dateStr} dataType={dataType.value}")
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

