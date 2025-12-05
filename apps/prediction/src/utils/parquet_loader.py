"""Parquetファイルの読み込み処理"""

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from tqdm import tqdm


class ParquetLoader:
    """Parquetファイルの読み込みを担当するクラス"""

    def __init__(self, base_path: Path):
        """
        初期化
        
        Args:
            base_path: Parquetファイルのベースパス
        """
        self._base_path = Path(base_path)

    def check_parquet_files(self, year: int, max_display: int = 5) -> None:
        """
        Parquetファイルの存在確認と表示
        
        Args:
            year: 年度
            max_display: 表示するファイル数の上限（デフォルト: 5）
        """
        print(f"Parquetファイルパス: {self._base_path.absolute()}")
        if self._base_path.exists():
            parquet_files = list(self._base_path.glob(f'*_{year}.parquet'))
            print(f"見つかった{year}年度のParquetファイル: {len(parquet_files)}件")
            for parquet_file in parquet_files[:max_display]:
                print(f"  - {parquet_file.name}")
        else:
            print(f"警告: {self._base_path} が存在しません")

    def load_parquet_files(self, data_types: List[str], year: int) -> Dict[str, pd.DataFrame]:
        """
        各データタイプのParquetファイルを読み込む
        
        Args:
            data_types: データタイプのリスト
            year: 年度
        
        Returns:
            データタイプをキー、DataFrameを値とする辞書
        """
        data_dict = {}
        for data_type in tqdm(data_types, desc="データタイプ読み込み"):
            try:
                data_dict[data_type] = self.load_annual_pack_parquet(data_type, year)
            except FileNotFoundError:
                if data_type == "SEC" and "SED" in data_types:
                    continue
                raise ValueError(f"データタイプ '{data_type}' の読み込みに失敗しました")
        
        missing_types = [dt for dt in data_types if dt not in data_dict and (dt != "SEC" or "SED" not in data_dict)]
        if missing_types:
            raise ValueError(f"指定されたデータタイプが存在しません: {missing_types}")
        
        return data_dict

    def load_annual_pack_parquet(self, data_type: str, year: int, raise_on_not_found: bool = True) -> Optional[pd.DataFrame]:
        """
        年度パックParquetファイルを読み込む
        
        Args:
            data_type: データタイプ
            year: 年度
            raise_on_not_found: ファイルが見つからない場合にエラーを投げるかどうか（デフォルト: True）
        
        Returns:
            DataFrame（ファイルが存在しない場合でraise_on_not_found=Falseの場合はNone）
        
        Raises:
            FileNotFoundError: ファイルが見つからず、raise_on_not_found=Trueの場合
        """
        file_name = f"{data_type}_{year}.parquet"
        file_path = self._base_path / file_name
        
        if not file_path.exists():
            if raise_on_not_found:
                raise FileNotFoundError(
                    f"年度パックファイルが見つかりません: {file_path}\n"
                    f"データタイプ: {data_type}, 年度: {year}"
                )
            return None
        
        return pd.read_parquet(file_path)

