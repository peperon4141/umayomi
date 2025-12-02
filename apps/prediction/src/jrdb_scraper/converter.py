"""コンバーター
パース済みデータをParquet形式に変換
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from .entities.jrdb import JRDBDataType
from .lzh_extractor import extract_data_type_from_file_name, extract_lzh_file
from .parsers.jrdb_parser import parse_jrdb_data_from_buffer

logger = logging.getLogger(__name__)


def convert_to_parquet(
    records: List[Dict[str, Union[int, str, None]]],
    outputFilePath: Union[str, Path]
) -> None:
    """レコード配列をParquet形式で保存
    
    Args:
        records: レコード配列
        outputFilePath: 出力Parquetファイルパス
    
    Raises:
        ValueError: レコードが0件の場合
    """
    if len(records) == 0:
        raise ValueError('cannot write parquet file with zero rows')
    
    # 出力ディレクトリを作成
    outputPath = Path(outputFilePath)
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    
    # DataFrameに変換
    df = pd.DataFrame(records)
    
    # Parquet形式で保存
    df.to_parquet(
        outputPath,
        index=False,
        compression='snappy',
        engine='pyarrow'
    )
    
    logger.info(f'Parquetファイルを保存しました: {outputPath}', extra={
        'rows': len(df),
        'columns': len(df.columns)
    })


def extract_and_parse_lzh_data(
    lzhBuffer: bytes,
    dataType: Optional[Union[JRDBDataType, str]]
) -> tuple[Union[JRDBDataType, str], List[Dict[str, Union[int, str, None]]]]:
    """LZHファイルからデータを抽出・パースする共通処理
    年度パック（複数ファイルを含む）にも対応
    
    Args:
        lzhBuffer: LZHファイルのバイト列
        dataType: データタイプ（オプション）
    
    Returns:
        (実際のデータタイプ, レコード配列)
    
    Raises:
        ValueError: 展開やパースに失敗した場合
    """
    extractedFiles = extract_lzh_file(lzhBuffer)
    if not extractedFiles:
        raise ValueError('展開されたファイルが見つかりません')
    
    # データタイプを決定（最初のファイルから推測、または引数で指定）
    if dataType is not None:
        actualDataType = dataType
    else:
        extractedDataType = extract_data_type_from_file_name(extractedFiles[0][1])
        if not extractedDataType:
            raise ValueError(f'データ種別の推測に失敗しました。ファイル名: {extractedFiles[0][1]}')
        actualDataType = extractedDataType
    
    # すべてのファイルをパースしてレコードを結合
    allRecords: List[Dict[str, Union[int, str, None]]] = []
    for extractedBuffer, _ in extractedFiles:
        fileRecords = parse_jrdb_data_from_buffer(extractedBuffer, actualDataType)
        allRecords.extend(fileRecords)
    
    if len(allRecords) == 0:
        raise ValueError('パースされたレコードが0件です')
    
    return (actualDataType, allRecords)


def convert_lzh_to_parquet(
    lzhBuffer: bytes,
    dataType: Optional[Union[JRDBDataType, str]],
    year: int,
    outputFilePath: Union[str, Path]
) -> tuple[Union[JRDBDataType, str], List[Dict[str, Union[int, str, None]]]]:
    """lzhファイルからParquetファイルへの変換処理
    
    Args:
        lzhBuffer: LZHファイルのバイト列
        dataType: データタイプ（オプション）
        year: 年
        outputFilePath: 出力Parquetファイルパス
    
    Returns:
        (実際のデータタイプ, レコード配列)
    """
    actualDataType, records = extract_and_parse_lzh_data(lzhBuffer, dataType)
    convert_to_parquet(records, outputFilePath)
    return (actualDataType, records)

