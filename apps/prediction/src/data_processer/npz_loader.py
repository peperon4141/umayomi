"""NPZファイルの読み込み処理"""

from pathlib import Path
from typing import Dict, List

import pandas as pd
from tqdm import tqdm

from ..data_loader import load_annual_pack_npz


class NpzLoader:
    """NPZファイルを読み込むクラス"""

    def __init__(self, base_path: Path):
        """初期化。base_path: データファイルのベースパス"""
        self._base_path = Path(base_path)

    def load(self, data_types: List[str], year: int) -> Dict[str, pd.DataFrame]:
        """各データタイプのNPZファイルを読み込む。data_types: データタイプのリスト、year: 年度。data_dict: データタイプをキー、DataFrameを値とする辞書を返す"""
        data_dict = {}
        for data_type in tqdm(data_types, desc="データタイプ読み込み"):
            try:
                data_dict[data_type] = load_annual_pack_npz(self._base_path, data_type, year)
            except FileNotFoundError:
                if data_type == "SEC" and "SED" in data_types:
                    continue
                raise ValueError(f"データタイプ '{data_type}' の読み込みに失敗しました")
        
        missing_types = [dt for dt in data_types if dt not in data_dict and (dt != "SEC" or "SED" not in data_dict)]
        if missing_types:
            raise ValueError(f"指定されたデータタイプが存在しません: {missing_types}")
        
        return data_dict

