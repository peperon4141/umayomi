"""年度パック取得
指定年度の年度パックを取得してParquet保存
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from .converter import convert_lzh_to_parquet
from .downloader import download_jrdb_file
from .entities.jrdb import (
    JRDBDataType,
    generate_annual_pack_url,
    get_annual_pack_supported_data_types,
    get_all_data_types,
    get_jrdb_data_type_info
)

logger = logging.getLogger(__name__)


def fetch_single_annual_data_type(
    year: int,
    dataType: JRDBDataType,
    outputDir: Union[str, Path]
) -> Dict[str, Union[str, int, bool, Optional[str]]]:
    """単一のデータタイプの年度パックを取得してParquetに保存（内部関数）
    
    Args:
        year: 年度（例: 2024）
        dataType: データタイプ
        outputDir: 出力ディレクトリ
    
    Returns:
        結果辞書
    """
    logger.info('年度パックデータ取得開始', extra={'year': year, 'dataType': dataType.value})
    
    outputPath = Path(outputDir)
    outputPath.mkdir(parents=True, exist_ok=True)
    
    try:
        info = get_jrdb_data_type_info(dataType)
        if not info['hasAnnualPack']:
            raise ValueError(f'データタイプ {dataType.value} には年度パックが提供されていません')
        
        actualDataType = dataType.value
        sourceUrl = generate_annual_pack_url(dataType, year)
        logger.info('年度パックURLを生成しました', extra={
            'dataType': actualDataType,
            'year': year,
            'sourceUrl': sourceUrl
        })
        
        lzhBuffer = download_jrdb_file(sourceUrl)
        logger.info('年度パックLZHファイルをダウンロードしました', extra={
            'dataType': actualDataType,
            'year': year,
            'url': sourceUrl,
            'fileSize': len(lzhBuffer)
        })
        
        fileName = f'{actualDataType}_{year}'
        parquetFilePath = outputPath / f'{fileName}.parquet'
        
        _, records = convert_lzh_to_parquet(lzhBuffer, actualDataType, year, parquetFilePath)
        
        if len(records) == 0:
            raise ValueError('パースされたレコードが0件です')
        
        logger.info('年度パックデータ取得完了', extra={
            'dataType': actualDataType,
            'year': year,
            'recordCount': len(records),
            'outputPath': str(parquetFilePath)
        })
        
        return {
            'year': year,
            'dataType': actualDataType,
            'success': True,
            'recordCount': len(records),
            'outputPath': str(parquetFilePath),
            'fileName': fileName
        }
    except Exception as error:
        errorMessage = str(error)
        logger.error('年度パックデータ取得エラー', extra={
            'year': year,
            'dataType': dataType.value,
            'error': errorMessage
        })
        
        return {
            'year': year,
            'dataType': dataType.value,
            'success': False,
            'recordCount': 0,
            'error': errorMessage
        }


def fetch_annual_data(
    year: int,
    dataTypes: List[JRDBDataType],
    outputDir: Union[str, Path] = 'cache/jrdb/parquet'
) -> List[Dict[str, Union[str, int, bool, Optional[str]]]]:
    """年度単位で指定されたデータタイプの年度パックを取得してParquetに保存
    
    Args:
        year: 年度（例: 2024）
        dataTypes: データタイプの配列（年度パックをサポートしているもののみ処理される）
        outputDir: 出力ディレクトリ（デフォルト: 'cache/jrdb/parquet'）
    
    Returns:
        結果のリスト
    """
    logger.info('年度パックデータ取得開始（複数データタイプ）', extra={
        'year': year,
        'dataTypes': [dt.value for dt in dataTypes]
    })
    
    # 年度パックをサポートしているデータタイプのみをフィルタリング
    supportedDataTypes = get_annual_pack_supported_data_types(dataTypes)
    
    if not supportedDataTypes:
        logger.warning('年度パックをサポートしているデータタイプがありません', extra={
            'requestedDataTypes': [dt.value for dt in dataTypes],
            'supportedDataTypes': [dt.value for dt in get_annual_pack_supported_data_types(get_all_data_types())]
        })
        return []
    
    if len(supportedDataTypes) < len(dataTypes):
        unsupportedDataTypes = [dt for dt in dataTypes if dt not in supportedDataTypes]
        logger.warning('一部のデータタイプは年度パックをサポートしていません', extra={
            'unsupportedDataTypes': [dt.value for dt in unsupportedDataTypes],
            'supportedDataTypes': [dt.value for dt in supportedDataTypes]
        })
    
    results: List[Dict[str, Union[str, int, bool, Optional[str]]]] = []
    
    for dataType in supportedDataTypes:
        try:
            result = fetch_single_annual_data_type(year, dataType, outputDir)
            results.append(result)
        except Exception as error:
            errorMessage = str(error)
            logger.error('データタイプ取得エラー', extra={
                'year': year,
                'dataType': dataType.value,
                'error': errorMessage
            })
            results.append({
                'year': year,
                'dataType': dataType.value,
                'success': False,
                'recordCount': 0,
                'error': errorMessage
            })
    
    successCount = sum(1 for r in results if r.get('success', False))
    logger.info('年度パックデータ取得完了', extra={
        'year': year,
        'totalDataTypes': len(supportedDataTypes),
        'successCount': successCount
    })
    
    return results

