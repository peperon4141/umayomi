"""共通フィクスチャとヘルパー関数"""

import pandas as pd
import pytest
from typing import Dict


def _generate_race_key(year: int, month: int, day: int, place_code: int, kaisai_round: int, kaisai_day: str, race_number: int) -> str:
    """race_keyを生成（LZH→Parquet変換時と同じロジック）"""
    date_str = f"{year:04d}{month:02d}{day:02d}"
    place_code_str = f"{place_code:02d}"
    round_str = f"{kaisai_round:02d}"
    day_str = str(kaisai_day).lower()
    race_str = f"{race_number:02d}"
    return f"{date_str}_{place_code_str}_{round_str}_{day_str}_{race_str}"


def create_simple_kyi_data(n_records: int = 3) -> pd.DataFrame:
    """簡易KYIデータを作成（race_keyを含む）"""
    place_code = 1
    kaisai_round = 1
    kaisai_day = "1"
    race_number = 1
    year = 2024
    month = 1
    day = 1
    
    race_key = _generate_race_key(year, month, day, place_code, kaisai_round, kaisai_day, race_number)
    
    return pd.DataFrame({
        "場コード": [place_code] * n_records,
        "回": [kaisai_round] * n_records,
        "日": [kaisai_day] * n_records,
        "R": [race_number] * n_records,
        "馬番": list(range(1, n_records + 1)),
        "血統登録番号": [f"{i:08d}" for i in range(12345678, 12345678 + n_records)],
        "騎手コード": [f"J{i:03d}" for i in range(1, n_records + 1)],
        "調教師コード": [f"T{i:03d}" for i in range(1, n_records + 1)],
        "race_key": [race_key] * n_records,  # 事前定義済みのキー
    })


def create_simple_bac_data(n_records: int = 3) -> pd.DataFrame:
    """簡易BACデータを作成（race_keyを含む）"""
    place_code = 1
    kaisai_round = 1
    kaisai_day = "1"
    race_number = 1
    year = 2024
    month = 1
    day = 1
    
    race_key = _generate_race_key(year, month, day, place_code, kaisai_round, kaisai_day, race_number)
    
    return pd.DataFrame({
        "場コード": [place_code] * n_records,
        "回": [kaisai_round] * n_records,
        "日": [kaisai_day] * n_records,
        "R": [race_number] * n_records,
        "年月日": [year * 10000 + month * 100 + day] * n_records,
        "発走時刻": [1200] * n_records,
        "race_key": [race_key] * n_records,  # 事前定義済みのキー
    })


def create_simple_sed_data(n_records: int = 3) -> pd.DataFrame:
    """簡易SEDデータを作成（race_keyを含む）"""
    place_code = 1
    kaisai_round = 1
    kaisai_day = "1"
    race_number = 1
    year = 2024
    month = 1
    day = 1
    
    race_key = _generate_race_key(year, month, day, place_code, kaisai_round, kaisai_day, race_number)
    
    return pd.DataFrame({
        "場コード": [place_code] * n_records,
        "回": [kaisai_round] * n_records,
        "日": [kaisai_day] * n_records,
        "R": [race_number] * n_records,
        "馬番": list(range(1, n_records + 1)),
        "血統登録番号": [f"{i:08d}" for i in range(12345678, 12345678 + n_records)],
        "騎手コード": [f"J{i:03d}" for i in range(1, n_records + 1)],
        "調教師コード": [f"T{i:03d}" for i in range(1, n_records + 1)],
        "着順": list(range(1, n_records + 1)),
        "タイム": [120.5 + i * 0.5 for i in range(n_records)],
        "距離": [1600] * n_records,
        "芝ダ障害コード": [1] * n_records,
        "馬場状態": [1] * n_records,
        "頭数": [n_records] * n_records,
        "年月日": [year * 10000 + month * 100 + day] * n_records,
        "確定単勝オッズ": [f"{2.5 + i * 0.5:.1f}" for i in range(n_records)],  # 評価用に追加
        "race_key": [race_key] * n_records,  # 事前定義済みのキー
    })


@pytest.fixture
def simple_data_dict() -> Dict[str, pd.DataFrame]:
    """簡易テストデータ辞書"""
    return {
        "KYI": create_simple_kyi_data(),
        "BAC": create_simple_bac_data(),
        "SED": create_simple_sed_data(),
    }
