"""Parquetファイルの読み込み処理"""

from pathlib import Path
from typing import Dict, List

import pandas as pd
from tqdm import tqdm


class ParquetLoader:
    """Parquetファイルを読み込むクラス"""

    def __init__(self, base_path: Path):
        """初期化。base_path: データファイルのベースパス"""
        self._base_path = Path(base_path)

    def load(self, data_types: List[str], year: int) -> Dict[str, pd.DataFrame]:
        """各データタイプのParquetファイルを読み込む。data_types: データタイプのリスト、year: 年度。data_dict: データタイプをキー、DataFrameを値とする辞書を返す"""
        data_dict = {}
        for data_type in tqdm(data_types, desc="データタイプ読み込み"):
            try:
                data_dict[data_type] = self._load_annual_pack_parquet(data_type, year)
            except FileNotFoundError:
                if data_type == "SEC" and "SED" in data_types:
                    continue
                raise ValueError(f"データタイプ '{data_type}' の読み込みに失敗しました")
        
        missing_types = [dt for dt in data_types if dt not in data_dict and (dt != "SEC" or "SED" not in data_dict)]
        if missing_types:
            raise ValueError(f"指定されたデータタイプが存在しません: {missing_types}")
        
        return data_dict

    def _load_annual_pack_parquet(self, data_type: str, year: int) -> pd.DataFrame:
        """年度パックParquetファイルを読み込む。DataFrameを返す。"""
        # ファイル名形式: {data_type}_{year}.parquet (例: BAC_2024.parquet)
        file_name = f"{data_type}_{year}.parquet"
        file_path = self._base_path / file_name
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"年度パックファイルが見つかりません: {file_path}\n"
                f"データタイプ: {data_type}, 年度: {year}"
            )
        
        return pd.read_parquet(file_path)

