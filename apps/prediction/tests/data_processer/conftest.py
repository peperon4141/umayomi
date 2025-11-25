"""共通フィクスチャとヘルパー関数"""

import pandas as pd
import pytest
from typing import Dict


def create_simple_kyi_data(n_records: int = 3) -> pd.DataFrame:
    """簡易KYIデータを作成"""
    return pd.DataFrame({
        "場コード": [1] * n_records,
        "回": [1] * n_records,
        "日": ["1"] * n_records,
        "R": [1] * n_records,
        "馬番": list(range(1, n_records + 1)),
        "血統登録番号": [f"{i:08d}" for i in range(12345678, 12345678 + n_records)],
        "騎手コード": [f"J{i:03d}" for i in range(1, n_records + 1)],
        "調教師コード": [f"T{i:03d}" for i in range(1, n_records + 1)],
    })


def create_simple_bac_data(n_records: int = 3) -> pd.DataFrame:
    """簡易BACデータを作成"""
    return pd.DataFrame({
        "場コード": [1] * n_records,
        "回": [1] * n_records,
        "日": ["1"] * n_records,
        "R": [1] * n_records,
        "年月日": [20240101] * n_records,
        "発走時刻": [1200] * n_records,
    })


def create_simple_sed_data(n_records: int = 3) -> pd.DataFrame:
    """簡易SEDデータを作成"""
    return pd.DataFrame({
        "場コード": [1] * n_records,
        "回": [1] * n_records,
        "日": ["1"] * n_records,
        "R": [1] * n_records,
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
        "年月日": [20240101] * n_records,
        "確定単勝オッズ": [f"{2.5 + i * 0.5:.1f}" for i in range(n_records)],  # 評価用に追加
    })


@pytest.fixture
def simple_data_dict() -> Dict[str, pd.DataFrame]:
    """簡易テストデータ辞書"""
    return {
        "KYI": create_simple_kyi_data(),
        "BAC": create_simple_bac_data(),
        "SED": create_simple_sed_data(),
    }

