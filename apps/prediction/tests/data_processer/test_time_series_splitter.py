"""TimeSeriesSplitterのテスト - race_keyのインデックス保持を確認"""

import pandas as pd
import pytest

from src.data_processer._05_time_series_splitter import TimeSeriesSplitter
from src.data_processer._06_column_selector import ColumnSelector
from tests.data_processer.conftest import create_simple_kyi_data, create_simple_bac_data


class TestTimeSeriesSplitter:
    """TimeSeriesSplitterのテスト - race_keyのインデックス保持を確認"""

    @pytest.fixture
    def splitter(self):
        """TimeSeriesSplitterインスタンスを作成"""
        return TimeSeriesSplitter()

    @pytest.fixture
    def sample_converted_df(self):
        """サンプルのconverted_dfを作成（race_keyをインデックスとして設定）"""
        # 簡易データを作成
        data = {
            "race_key": [f"2024010{i}_01_1_a_0{i}" for i in range(1, 11)],
            "start_datetime": [202401010000 + i * 10000 for i in range(1, 11)],
            "horse_win_rate": [0.1 * i for i in range(1, 11)],
            "rank": list(range(1, 11)),
        }
        df = pd.DataFrame(data)
        # race_keyをインデックスとして設定（main.pyと同じ処理）
        df.set_index("race_key", inplace=True)
        return df

    def test_split_preserves_race_key_index(self, splitter, sample_converted_df):
        """時系列分割後もrace_keyがインデックスとして保持されることを確認"""
        split_date = "2024-01-05"
        train_df, test_df = splitter.split(sample_converted_df, split_date)
        
        # インデックスがrace_keyであることを確認
        assert train_df.index.name == "race_key", "train_dfのインデックスがrace_keyである必要があります"
        assert test_df.index.name == "race_key", "test_dfのインデックスがrace_keyである必要があります"
        
        # インデックスの値が正しいことを確認
        assert all("2024010" in str(idx) for idx in train_df.index), "train_dfのインデックスがrace_key形式である必要があります"
        assert all("2024010" in str(idx) for idx in test_df.index), "test_dfのインデックスがrace_key形式である必要があります"

    def test_select_training_preserves_race_key_index(self, splitter, sample_converted_df):
        """select_training()後もrace_keyがインデックスとして保持されることを確認"""
        from pathlib import Path
        base_path = Path(__file__).parent.parent.parent.parent.parent
        
        split_date = "2024-01-05"
        train_df, test_df = splitter.split(sample_converted_df, split_date)
        
        # カラム選択器で学習用カラムを選択
        column_selector = ColumnSelector(base_path)
        train_df_selected = column_selector.select_training(train_df)
        test_df_selected = column_selector.select_training(test_df)
        
        # インデックスがrace_keyのままであることを確認
        assert train_df_selected.index.name == "race_key", "select_training()後もtrain_dfのインデックスがrace_keyである必要があります"
        assert test_df_selected.index.name == "race_key", "select_training()後もtest_dfのインデックスがrace_keyである必要があります"
        
        # インデックスの値が保持されていることを確認
        assert len(train_df_selected.index) == len(train_df.index), "インデックスの行数が一致する必要があります"
        assert len(test_df_selected.index) == len(test_df.index), "インデックスの行数が一致する必要があります"

    def test_race_key_available_for_feature_enhancement(self, splitter, sample_converted_df):
        """特徴量強化時にrace_keyがインデックスとして利用可能であることを確認"""
        from pathlib import Path
        base_path = Path(__file__).parent.parent.parent.parent.parent
        
        split_date = "2024-01-05"
        train_df, test_df = splitter.split(sample_converted_df, split_date)
        
        # カラム選択器で学習用カラムを選択
        column_selector = ColumnSelector(base_path)
        train_df_selected = column_selector.select_training(train_df)
        
        # 特徴量強化でrace_keyが利用可能であることを確認
        # race_keyがインデックスまたはカラムとして存在することを確認
        has_race_key = (
            train_df_selected.index.name == "race_key" or 
            "race_key" in train_df_selected.columns
        )
        assert has_race_key, "特徴量強化時にrace_keyがインデックスまたはカラムとして存在する必要があります"
        
        # インデックスがrace_keyの場合、reset_index()でカラムとして取得できることを確認
        if train_df_selected.index.name == "race_key":
            df_for_enhance = train_df_selected.reset_index()
            assert "race_key" in df_for_enhance.columns, "reset_index()でrace_keyがカラムとして取得できる必要があります"

