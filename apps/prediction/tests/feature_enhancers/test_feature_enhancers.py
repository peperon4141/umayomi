"""feature_enhancersモジュールのテスト"""

import numpy as np
import pandas as pd
import pytest

from src.feature_enhancers import (
    add_relative_features,
    add_interaction_features,
    enhance_features,
)


class TestAddRelativeFeatures:
    """add_relative_features関数のテスト"""

    def test_add_relative_features_with_index(self):
        """インデックスがrace_keyの場合のテスト"""
        # テストデータ作成（2レース、各3頭）
        data = {
            "race_key": ["20240101_01_01_1_01", "20240101_01_01_1_01", "20240101_01_01_1_01",
                        "20240101_01_01_1_02", "20240101_01_01_1_02", "20240101_01_01_1_02"],
            "horse_place_rate": [0.5, 0.3, 0.7, 0.6, 0.4, 0.2],
            "horse_avg_rank": [3.0, 5.0, 2.0, 2.5, 4.0, 6.0],
            "horse_weight": [450, 440, 460, 455, 445, 435],
        }
        df = pd.DataFrame(data)
        df.set_index("race_key", inplace=True)

        result = add_relative_features(df, race_key_col="race_key")

        # 相対特徴量が追加されていることを確認
        assert "horse_place_rate_rank" in result.columns
        assert "horse_avg_rank_rank" in result.columns
        assert "horse_weight_rank" in result.columns

        # レース1の順位を確認（horse_place_rateが大きい順）
        race1 = result.loc["20240101_01_01_1_01"]
        # 順位は1から始まる（最大値は頭数）
        assert race1["horse_place_rate_rank"].min() >= 1.0
        assert race1["horse_place_rate_rank"].max() <= len(race1)
        # 順位が正しく計算されていることを確認（すべて異なる値を持つ）
        rank_values = race1["horse_place_rate_rank"].values
        assert len(set(rank_values)) == len(rank_values)  # すべて異なる値

        # インデックスが保持されていることを確認
        assert result.index.name == "race_key"

    def test_add_relative_features_with_column(self):
        """race_keyがカラムの場合のテスト"""
        data = {
            "race_key": ["20240101_01_01_1_01", "20240101_01_01_1_01", "20240101_01_01_1_01"],
            "horse_place_rate": [0.5, 0.3, 0.7],
            "horse_avg_rank": [3.0, 5.0, 2.0],
        }
        df = pd.DataFrame(data)

        result = add_relative_features(df, race_key_col="race_key")

        # 相対特徴量が追加されていることを確認
        assert "horse_place_rate_rank" in result.columns
        assert "horse_avg_rank_rank" in result.columns

        # race_keyカラムが保持されていることを確認
        assert "race_key" in result.columns

    def test_add_relative_features_missing_race_key(self):
        """race_keyが存在しない場合のエラーテスト"""
        data = {
            "horse_place_rate": [0.5, 0.3, 0.7],
        }
        df = pd.DataFrame(data)

        with pytest.raises(ValueError, match="race_key"):
            add_relative_features(df, race_key_col="race_key")

    def test_add_relative_features_with_nan(self):
        """NaN値が含まれる場合のテスト"""
        data = {
            "race_key": ["20240101_01_01_1_01", "20240101_01_01_1_01", "20240101_01_01_1_01"],
            "horse_place_rate": [0.5, np.nan, 0.7],
        }
        df = pd.DataFrame(data)

        result = add_relative_features(df, race_key_col="race_key")

        # NaN値は0に置換されていることを確認
        assert "horse_place_rate_rank" in result.columns
        nan_rank = result.loc[result["horse_place_rate"].isna(), "horse_place_rate_rank"].values[0]
        assert nan_rank == 0.0


class TestAddInteractionFeatures:
    """add_interaction_features関数のテスト"""

    def test_add_interaction_features_numeric(self):
        """数値型特徴量のインタラクション"""
        data = {
            "horse_place_rate": [0.5, 0.3, 0.7],
            "course_length": [1600, 1800, 2000],
            "frame": [1, 2, 3],
            "num_horses": [10, 12, 14],
        }
        df = pd.DataFrame(data)

        result = add_interaction_features(df)

        # インタラクション特徴量が追加されていることを確認
        assert "horse_place_rate_x_distance" in result.columns
        assert "frame_x_num_horses" in result.columns

        # 値が正しく計算されていることを確認
        expected = df["horse_place_rate"] * df["course_length"]
        pd.testing.assert_series_equal(
            result["horse_place_rate_x_distance"],
            expected,
            check_names=False
        )

    def test_add_interaction_features_missing_columns(self):
        """必要なカラムが存在しない場合のテスト"""
        data = {
            "horse_place_rate": [0.5, 0.3, 0.7],
        }
        df = pd.DataFrame(data)

        result = add_interaction_features(df)

        # 存在しないカラムの組み合わせは追加されない
        assert "horse_place_rate_x_course_type" not in result.columns

    def test_add_interaction_features_categorical(self):
        """カテゴリカル型特徴量のインタラクション"""
        data = {
            "course_type": ["芝", "ダ", "芝"],
            "ground_condition": ["良", "良", "重"],
        }
        df = pd.DataFrame(data)

        result = add_interaction_features(df)

        # カテゴリカル型も処理されることを確認（エラーが発生しない）
        assert isinstance(result, pd.DataFrame)


class TestEnhanceFeatures:
    """enhance_features関数のテスト"""

    def test_enhance_features_complete(self):
        """特徴量強化の統合テスト"""
        # テストデータ作成
        data = {
            "race_key": ["20240101_01_01_1_01", "20240101_01_01_1_01", "20240101_01_01_1_01",
                        "20240101_01_01_1_02", "20240101_01_01_1_02", "20240101_01_01_1_02"],
            "horse_place_rate": [0.5, 0.3, 0.7, 0.6, 0.4, 0.2],
            "horse_avg_rank": [3.0, 5.0, 2.0, 2.5, 4.0, 6.0],
            "course_length": [1600, 1600, 1600, 1800, 1800, 1800],
            "frame": [1, 2, 3, 1, 2, 3],
            "num_horses": [3, 3, 3, 3, 3, 3],
        }
        df = pd.DataFrame(data)

        original_cols = len(df.columns)
        result = enhance_features(df, race_key_col="race_key")

        # 特徴量が追加されていることを確認
        assert len(result.columns) > original_cols

        # 相対特徴量が追加されていることを確認
        assert "horse_place_rate_rank" in result.columns
        assert "horse_avg_rank_rank" in result.columns

        # インタラクション特徴量が追加されていることを確認
        assert "horse_place_rate_x_distance" in result.columns
        assert "frame_x_num_horses" in result.columns

    def test_enhance_features_with_index(self):
        """インデックスがrace_keyの場合のテスト"""
        data = {
            "race_key": ["20240101_01_01_1_01", "20240101_01_01_1_01", "20240101_01_01_1_01"],
            "horse_place_rate": [0.5, 0.3, 0.7],
            "course_length": [1600, 1600, 1600],
        }
        df = pd.DataFrame(data)
        df.set_index("race_key", inplace=True)

        result = enhance_features(df, race_key_col="race_key")

        # インデックスが保持されていることを確認
        assert result.index.name == "race_key"
        assert len(result) == len(df)

        # 特徴量が追加されていることを確認
        assert "horse_place_rate_rank" in result.columns

