"""JRDBデータのNPZファイル読み込み処理（年度パック・日次データ対応）"""

from pathlib import Path
from typing import Dict, List, Union, Optional

import numpy as np
import pandas as pd

# 公開API（外部で使用される関数）
__all__ = [
    "load_annual_pack_npz",
    "load_multiple_npz_files",
]

def load_jrdb_npz_to_dataframe(file_path: Union[str, Path]) -> pd.DataFrame:
    """NPZファイルからデータを読み込んでDataFrameに変換。各フィールドが列として格納される。"""
    file_path = Path(file_path)
    if not file_path.exists(): raise FileNotFoundError(f"NPZファイルが見つかりません: {file_path}")

    data = {}
    with np.load(file_path, allow_pickle=True) as npz_file:
        for field_name in npz_file.files: data[field_name] = npz_file[field_name]

    # すべての配列の長さが同じか確認
    lengths = [len(arr) for arr in data.values()]
    if len(set(lengths)) > 1: raise ValueError(f"フィールド間でレコード数が一致しません: {lengths}")

    df = pd.DataFrame(data)
    
    # INTEGER_ZERO_BLANK型のフィールド（空文字列をNaNに変換）
    # WIN5フラグなど、数値型のフィールドで空文字列の場合はNaNに変換
    # 数値に変換可能なフィールドを特定（空文字列が含まれている場合）
    for col in df.columns:
        # 空文字列が含まれている列を確認
        if df[col].dtype == 'object':
            # 空文字列をNaNに変換してから数値変換を試行
            # まず空文字列をNaNに変換
            col_series = df[col].copy()
            col_series = col_series.replace('', np.nan)
            # FutureWarningを回避するため、infer_objectsを使用
            col_series = col_series.infer_objects(copy=False)
            # 数値に変換可能な場合は数値型に変換、できない場合は文字列のまま
            numeric_series = pd.to_numeric(col_series, errors='coerce')
            # 数値に変換できた行が存在する場合、その列は数値型として扱う
            if numeric_series.notna().any():
                df[col] = numeric_series
            else:
                # すべてNaNの場合でも、数値型として扱う（空文字列をNaNに変換済み）
                df[col] = numeric_series
    
    return df

def load_multiple_npz_files(
    file_paths: List[Union[str, Path]], data_type: Optional[str] = None
) -> pd.DataFrame:
    """複数のNPZファイルを読み込んで結合。結合されたDataFrameを返す。"""
    if not file_paths: raise ValueError("ファイルパスが空です")

    dataframes = []
    for file_path in file_paths:
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"警告: ファイルが見つかりません: {file_path}")
            continue

        try:
            df = load_jrdb_npz_to_dataframe(file_path)
            if data_type: print(f"読み込み完了: {data_type} - {file_path.name} ({len(df)}件)")
            dataframes.append(df)
        except Exception as e:
            print(f"エラー: {file_path} の読み込みに失敗しました: {e}")
            continue

    if not dataframes: raise ValueError("読み込めるファイルがありませんでした")

    # すべてのDataFrameを結合
    combined_df = pd.concat(dataframes, ignore_index=True)

    if data_type: print(f"結合完了: {data_type} - 合計 {len(combined_df)}件")

    return combined_df


def load_annual_pack_npz(base_path: Union[str, Path], data_type: str, year: int) -> pd.DataFrame:
    """年度パックNPZファイルを読み込む。DataFrameを返す。"""
    base_path = Path(base_path)

    # 複数のファイル名形式を試す
    possible_file_names = [
        f"{data_type}_{year}.npz",  # BAC_2024.npz
        f"jrdb_npz_{data_type}_{year}.npz",  # jrdb_npz_BAC_2024.npz
    ]

    for file_name in possible_file_names:
        file_path = base_path / file_name
        if file_path.exists(): return load_jrdb_npz_to_dataframe(file_path)

    # ファイルが見つからない場合
    raise FileNotFoundError(
        f"年度パックファイルが見つかりません: {base_path}\n試したファイル名: {possible_file_names}"
    )
