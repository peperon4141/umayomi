"""ローカルフォルダ内のLZHファイルをParquetに変換
指定フォルダ内のLZHファイルを読み込んでParquet形式で保存
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from .converter import convert_lzh_to_parquet
from .entities.jrdb import (
    JRDBDataType,
    get_annual_pack_supported_data_types,
    get_all_data_types,
    get_jrdb_data_type_info
)

logger = logging.getLogger(__name__)


def convert_single_local_file(
    lzhFilePath: Union[str, Path],
    dataType: JRDBDataType,
    year: int,
    outputDir: Union[str, Path],
    bac_df: Optional[pd.DataFrame] = None
) -> Dict[str, Union[str, int, bool, Optional[str]]]:
    """単一のLZHファイルをParquetに変換（内部関数）
    
    Args:
        lzhFilePath: LZHファイルのパス
        dataType: データタイプ
        year: 年度（例: 2024）
        outputDir: 出力ディレクトリ
    
    Returns:
        結果辞書
    """
    logger.info('ローカルLZHファイル変換開始', extra={'year': year, 'dataType': dataType.value, 'filePath': str(lzhFilePath)})
    
    outputPath = Path(outputDir)
    outputPath.mkdir(parents=True, exist_ok=True)
    
    try:
        info = get_jrdb_data_type_info(dataType)
        actualDataType = dataType.value
        
        # ローカルファイルを読み込む
        lzhFilePathObj = Path(lzhFilePath)
        if not lzhFilePathObj.exists():
            raise FileNotFoundError(f'LZHファイルが見つかりません: {lzhFilePath}')
        
        with open(lzhFilePathObj, 'rb') as f:
            lzhBuffer = f.read()
        
        logger.info('ローカルLZHファイルを読み込みました', extra={
            'dataType': actualDataType,
            'year': year,
            'filePath': str(lzhFilePath),
            'fileSize': len(lzhBuffer)
        })
        
        fileName = f'{actualDataType}_{year}'
        parquetFilePath = outputPath / f'{fileName}.parquet'
        
        _, records = convert_lzh_to_parquet(lzhBuffer, actualDataType, year, parquetFilePath, bac_df=bac_df)
        
        if len(records) == 0:
            raise ValueError('パースされたレコードが0件です')
        
        logger.info('ローカルLZHファイル変換完了', extra={
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
        logger.error('ローカルLZHファイル変換エラー', extra={
            'year': year,
            'dataType': dataType.value,
            'filePath': str(lzhFilePath),
            'error': errorMessage
        })
        
        return {
            'year': year,
            'dataType': dataType.value,
            'success': False,
            'recordCount': 0,
            'error': errorMessage
        }


def find_lzh_files_in_folder(
    folderPath: Union[str, Path],
    dataType: Optional[JRDBDataType] = None
) -> List[Path]:
    """フォルダ内のLZHファイルを検索
    
    Args:
        folderPath: 検索対象フォルダ
        dataType: データタイプ（指定時は該当ファイルのみ検索）
    
    Returns:
        LZHファイルのパスリスト
    """
    folder = Path(folderPath)
    if not folder.exists():
        logger.warning('フォルダが存在しません', extra={'folderPath': str(folderPath)})
        return []
    
    lzhFiles = []
    if dataType is not None:
        # データタイプが指定されている場合、ファイル名にデータタイプが含まれるものを検索
        pattern = f'*{dataType.value}*.lzh'
        lzhFiles = list(folder.glob(pattern))
        # 大文字小文字を区別しない検索も試行
        if not lzhFiles:
            for file in folder.glob('*.lzh'):
                if dataType.value.lower() in file.name.lower():
                    lzhFiles.append(file)
    else:
        # データタイプが指定されていない場合、全てのLZHファイルを検索
        lzhFiles = list(folder.glob('*.lzh'))
    
    logger.info('LZHファイル検索完了', extra={
        'folderPath': str(folderPath),
        'dataType': dataType.value if dataType else None,
        'fileCount': len(lzhFiles)
    })
    
    return lzhFiles


def convert_local_folder_to_parquet(
    folderPath: Union[str, Path],
    year: int,
    dataTypes: List[JRDBDataType],
    outputDir: Union[str, Path] = 'cache/jrdb/parquet'
) -> List[Dict[str, Union[str, int, bool, Optional[str]]]]:
    """ローカルフォルダ内のLZHファイルをParquetに変換
    
    Args:
        folderPath: LZHファイルが格納されているフォルダパス
        year: 年度（例: 2024）
        dataTypes: データタイプの配列（年度パックをサポートしているもののみ処理される）
        outputDir: 出力ディレクトリ（デフォルト: 'cache/jrdb/parquet'）
    
    Returns:
        結果のリスト
    """
    logger.info('ローカルフォルダ変換開始（複数データタイプ）', extra={
        'folderPath': str(folderPath),
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
    
    # KYI等の年月日がないデータタイプのrace_key生成用に、BACデータを事前に読み込む
    bac_df = None
    if JRDBDataType.BAC in supportedDataTypes:
        try:
            bac_files = find_lzh_files_in_folder(folderPath, JRDBDataType.BAC)
            if bac_files:
                from .converter import extract_and_parse_lzh_data
                with open(bac_files[0], 'rb') as f:
                    bac_buffer = f.read()
                _, bac_records = extract_and_parse_lzh_data(bac_buffer, JRDBDataType.BAC)
                if bac_records:
                    bac_df = pd.DataFrame(bac_records)
                logger.info('BACデータを読み込みました（KYI等のrace_key生成用）', extra={'year': year, 'recordCount': len(bac_records) if bac_records else 0})
        except Exception as e:
            logger.warning('BACデータの読み込みに失敗しました（KYI等のrace_key生成に影響する可能性があります）', extra={'year': year, 'error': str(e)})
    
    for dataType in supportedDataTypes:
        try:
            # フォルダ内から該当データタイプのLZHファイルを検索
            lzhFiles = find_lzh_files_in_folder(folderPath, dataType)
            
            if not lzhFiles:
                logger.warning('該当データタイプのLZHファイルが見つかりません', extra={
                    'year': year,
                    'dataType': dataType.value,
                    'folderPath': str(folderPath)
                })
                results.append({
                    'year': year,
                    'dataType': dataType.value,
                    'success': False,
                    'recordCount': 0,
                    'error': f'LZHファイルが見つかりません: {folderPath}'
                })
                continue
            
            # 最初に見つかったファイルを使用（複数ファイルがある場合は最初の1つ）
            lzhFile = lzhFiles[0]
            if len(lzhFiles) > 1:
                logger.warning('複数のLZHファイルが見つかりました。最初のファイルを使用します', extra={
                    'dataType': dataType.value,
                    'fileCount': len(lzhFiles),
                    'selectedFile': str(lzhFile)
                })
            
            # KYI等の年月日がないデータタイプの場合は、BACデータを渡す
            result = convert_single_local_file(lzhFile, dataType, year, outputDir, bac_df=bac_df if dataType != JRDBDataType.BAC else None)
            results.append(result)
        except Exception as error:
            errorMessage = str(error)
            logger.error('データタイプ変換エラー', extra={
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
    logger.info('ローカルフォルダ変換完了', extra={
        'folderPath': str(folderPath),
        'year': year,
        'totalDataTypes': len(supportedDataTypes),
        'successCount': successCount
    })
    
    return results

