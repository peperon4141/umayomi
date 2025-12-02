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


def _add_race_key_to_dataframe(df: pd.DataFrame, use_ymd_column: bool = True) -> pd.DataFrame:
    """DataFrameにrace_keyを追加（年月日カラムまたは年・月・日カラムがある場合のみ）
    
    Args:
        df: DataFrame
        use_ymd_column: 年月日カラムを使用するかどうか（True: 年月日カラム、False: 年・月・日カラム）
    
    Returns:
        race_keyが追加されたDataFrame（追加できない場合はそのまま返す）
    """
    # 必須カラムを確認
    base_required_columns = ["場コード", "回", "日", "R"]
    
    if use_ymd_column:
        # 年月日カラムを使用する場合
        required_columns = base_required_columns + ["年月日"]
        if not all(col in df.columns for col in required_columns):
            logger.debug("race_key生成に必要なカラム（年月日）が不足しています。race_keyは追加しません。")
            return df
        
        df = df.copy()
        # 年月日から年、月、日を抽出
        year = pd.to_numeric(df["年月日"].astype(str).str[:4], errors="coerce")
        month = pd.to_numeric(df["年月日"].astype(str).str[4:6], errors="coerce")
        day = pd.to_numeric(df["年月日"].astype(str).str[6:8], errors="coerce")
    else:
        # 年・月・日カラムを使用する場合
        required_columns = base_required_columns + ["年"]
        if not all(col in df.columns for col in required_columns):
            logger.debug("race_key生成に必要なカラム（年）が不足しています。race_keyは追加しません。")
            return df
        
        df = df.copy()
        # 年・月・日カラムから取得（月・日は別途計算が必要な場合がある）
        year = pd.to_numeric(df["年"].fillna(0).astype(int), errors="coerce")
        # 年が2桁の場合は2000年を加算
        year = year.apply(lambda y: 2000 + y if y < 100 else y)
        
        # 月・日は年月日カラムがない場合は取得できない
        if "年月日" in df.columns:
            month = pd.to_numeric(df["年月日"].astype(str).str[4:6], errors="coerce")
            day = pd.to_numeric(df["年月日"].astype(str).str[6:8], errors="coerce")
        else:
            # 年月日カラムがない場合（KYI, TYBなど）
            # 月・日の情報がないため、完全なrace_keyは生成できない
            # 後でBACデータとマージする際にrace_keyを取得する必要がある
            logger.debug("月・日の情報が不足しています。race_keyは後でBACデータとマージする際に取得します。")
            return df
    
    # 場コード、回、日、Rを文字列に変換（ゼロパディング）
    place_code_str = df["場コード"].fillna(0).astype(int).astype(str).str.zfill(2)
    round_str = df["回"].fillna(1).astype(int).astype(str).str.zfill(2)
    day_str = df["日"].fillna("1").astype(str).str.lower()
    race_str = df["R"].fillna(1).astype(int).astype(str).str.zfill(2)
    
    # race_keyを生成: YYYYMMDD_場コード_回_日_R
    date_str = year.astype(str).str.zfill(4) + month.astype(str).str.zfill(2) + day.astype(str).str.zfill(2)
    df["race_key"] = date_str + "_" + place_code_str + "_" + round_str + "_" + day_str + "_" + race_str
    
    logger.info(f"race_keyを追加しました: {len(df)}件")
    return df


def convert_to_parquet(
    records: List[Dict[str, Union[int, str, None]]],
    outputFilePath: Union[str, Path],
    dataType: Optional[Union[JRDBDataType, str]] = None
) -> None:
    """レコード配列をParquet形式で保存
    
    Args:
        records: レコード配列
        outputFilePath: 出力Parquetファイルパス
        dataType: データタイプ（race_key生成に使用、オプション）
    
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
    
    # データタイプに応じて結合キーを追加
    if dataType is not None:
        data_type_str = dataType.value if isinstance(dataType, JRDBDataType) else str(dataType)
        
        # race_keyが必要なデータタイプ（年月日カラムがある場合のみ生成）
        # BAC, SED: 年月日カラムがあるので生成可能
        # KYI, TYB: 年月日カラムがないため、race_keyは生成しない（後でBACデータとマージする際に取得）
        if data_type_str in ["BAC", "SED"]:
            df = _add_race_key_to_dataframe(df, use_ymd_column=True)
        
        # UKCは血統登録番号が既に含まれているので追加処理不要
    
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
    convert_to_parquet(records, outputFilePath, dataType=actualDataType)
    return (actualDataType, records)

