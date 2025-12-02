"""ColumnFilterのテスト - インデックスの保持を確認"""

import pandas as pd
import pytest

from pathlib import Path
from src.data_processer._06_01_column_filter import ColumnFilter


class TestColumnFilter:
    """ColumnFilterのテスト - インデックスの保持を確認"""

    @pytest.fixture
    def column_filter(self):
        """ColumnFilterインスタンスを作成"""
        base_path = Path(__file__).parent.parent.parent.parent.parent
        return ColumnFilter(base_path)

    @pytest.fixture
    def sample_df_with_race_key_index(self):
        """race_keyをインデックスとして持つDataFrameを作成"""
        data = {
            "horse_win_rate": [0.1, 0.2, 0.3],
            "rank": [1, 2, 3],
        }
        df = pd.DataFrame(data)
        df.index = pd.Index([f"2024010{i}_01_1_a_0{i}" for i in range(1, 4)], name="race_key")
        return df

    def test_filter_training_columns_preserves_index(self, column_filter, sample_df_with_race_key_index):
        """filter_training_columns()がインデックスを保持することを確認"""
        result_df = column_filter.filter_training_columns(sample_df_with_race_key_index)
        
        # インデックスが保持されていることを確認
        assert result_df.index.name == "race_key", "filter_training_columns()後もインデックスがrace_keyである必要があります"
        assert len(result_df.index) == len(sample_df_with_race_key_index.index), "インデックスの行数が一致する必要があります"
        assert list(result_df.index) == list(sample_df_with_race_key_index.index), "インデックスの値が一致する必要があります"

    def test_filter_training_columns_with_race_key_column(self, column_filter):
        """race_keyがカラムとして存在する場合のテスト"""
        data = {
            "race_key": [f"2024010{i}_01_1_a_0{i}" for i in range(1, 4)],
            "horse_win_rate": [0.1, 0.2, 0.3],
            "rank": [1, 2, 3],
        }
        df = pd.DataFrame(data)
        # インデックスはデフォルト（0, 1, 2）
        
        result_df = column_filter.filter_training_columns(df)
        
        # race_keyがカラムとして含まれていない場合（学習用スキーマに含まれていない場合）、
        # インデックスは保持されるが、race_keyカラムは削除される可能性がある
        # これは正常な動作（学習用スキーマに含まれていないカラムは削除される）
        assert len(result_df) == len(df), "行数が一致する必要があります"

