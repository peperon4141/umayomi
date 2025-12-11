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
from src.utils.feature_converter import FeatureConverter

logger = logging.getLogger(__name__)


def convert_to_parquet(
    records: List[Dict[str, Union[int, str, None]]],
    outputFilePath: Union[str, Path],
    dataType: Optional[Union[JRDBDataType, str]] = None,
    bac_df: Optional[pd.DataFrame] = None
) -> None:
    """レコード配列をParquet形式で保存
    
    Args:
        records: レコード配列
        outputFilePath: 出力Parquetファイルパス
        dataType: データタイプ（race_key生成に使用、オプション）
        bac_df: BACデータ（KYI等の年月日がないデータタイプのrace_key生成に使用、オプション）
    
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
    
    # race_key生成に必要なカラムをチェック（データタイプに関係なく）
    required_columns = FeatureConverter.RACE_KEY_REQUIRED_COLUMNS
    has_required_columns = all(col in df.columns for col in required_columns)
    
    if has_required_columns:
        # 必要なカラムが全て存在する場合は、race_keyを追加
        data_type_str = dataType.value if isinstance(dataType, JRDBDataType) else str(dataType) if dataType is not None else "unknown"
        logger.info(f"データタイプ '{data_type_str}' にrace_keyを追加中... (必要なカラムが揃っています)")
        
        # 年月日カラムがないデータタイプ（KYI等）の場合は、BACデータから日付を取得
        use_bac_date = bac_df is not None and "年月日" not in df.columns
        df = FeatureConverter.add_race_key_to_df(df, bac_df=bac_df, use_bac_date=use_bac_date)
        
        if "race_key" not in df.columns:
            logger.error(f"データタイプ '{data_type_str}' にrace_keyの追加に失敗しました。利用可能なカラム: {list(df.columns)[:10]}")
            raise ValueError(f"データタイプ '{data_type_str}' にrace_keyの追加に失敗しました。")
        
        race_key_count = df['race_key'].notna().sum()
        logger.info(f"データタイプ '{data_type_str}' にrace_keyを追加しました。race_keyの行数: {race_key_count}/{len(df)}")
    else:
        # 必要なカラムが揃っていない場合は、race_keyを追加しない
        missing_columns = [col for col in required_columns if col not in df.columns]
        data_type_str = dataType.value if isinstance(dataType, JRDBDataType) else str(dataType) if dataType is not None else "unknown"
        logger.info(f"データタイプ '{data_type_str}' にrace_keyを追加しません。必要なカラムが不足しています: {missing_columns}")
    
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
    outputFilePath: Union[str, Path],
    bac_df: Optional[pd.DataFrame] = None
) -> tuple[Union[JRDBDataType, str], List[Dict[str, Union[int, str, None]]]]:
    """lzhファイルからParquetファイルへの変換処理
    
    Args:
        lzhBuffer: LZHファイルのバイト列
        dataType: データタイプ（オプション）
        year: 年
        outputFilePath: 出力Parquetファイルパス
        bac_df: BACデータ（KYI等の年月日がないデータタイプのrace_key生成に使用、オプション）
    
    Returns:
        (実際のデータタイプ, レコード配列)
    """
    actualDataType, records = extract_and_parse_lzh_data(lzhBuffer, dataType)
    convert_to_parquet(records, outputFilePath, dataType=actualDataType, bac_df=bac_df)
    return (actualDataType, records)

