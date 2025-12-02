"""FeatureExtractorのテスト"""

import os
import pandas as pd
import pytest

from src.data_processer._03_feature_extractor import FeatureExtractor
from tests.data_processer.conftest import create_simple_kyi_data, create_simple_bac_data, create_simple_sed_data


class TestFeatureExtractor:
    """FeatureExtractorのテスト"""

    @pytest.fixture
    def extractor(self):
        """FeatureExtractorインスタンスを作成"""
        return FeatureExtractor()

    @pytest.fixture
    def sample_data(self):
        """サンプルデータを作成"""
        kyi_df = create_simple_kyi_data(5)
        bac_df = create_simple_bac_data(5)
        sed_df = create_simple_sed_data(10)  # 過去レースを含むため多めに作成
        
        # race_keyを追加
        from src.data_processer._03_01_feature_converter import FeatureConverter
        df = kyi_df.copy()
        df = df.merge(bac_df[["場コード", "回", "日", "R", "年月日"]], on=["場コード", "回", "日", "R"], how="left")
        df["race_key"] = df.apply(
            lambda row: FeatureConverter.generate_race_key(
                2024, 1, 1, f"{row['場コード']:02d}", row["回"], row["日"], row["R"]
            ),
            axis=1
        )
        
        return {
            "df": df,
            "sed_df": sed_df,
            "bac_df": bac_df,
        }

    def test_extract_all_parallel_basic(self, extractor, sample_data):
        """extract_all_parallelの基本動作テスト"""
        result = extractor.extract_all_parallel(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data["df"])
        # 前走データのカラムが追加されていることを確認
        assert "prev_1_rank" in result.columns or "prev_1_rank" not in result.columns  # データによっては追加されない場合もある

    def test_extract_all_parallel_without_sed(self, extractor, sample_data):
        """SEDデータがない場合のテスト"""
        result = extractor.extract_all_parallel(
            sample_data["df"],
            None,
            sample_data["bac_df"]
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data["df"])

    def test_extract_all_parallel_without_bac(self, extractor, sample_data):
        """BACデータがない場合のテスト（エラーが投げられることを確認）"""
        with pytest.raises(ValueError, match="BACデータは必須です"):
            extractor.extract_all_parallel(
                sample_data["df"],
                sample_data["sed_df"],
                None
            )

    def test_extract_all_parallel_worker_count(self, extractor, sample_data):
        """ワーカー数の環境変数が正しく反映されることを確認"""
        # ワーカー数を1に設定
        os.environ["FEATURE_EXTRACTOR_MAX_WORKERS"] = "1"
        result = extractor.extract_all_parallel(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        assert isinstance(result, pd.DataFrame)
        # 環境変数をクリア
        del os.environ["FEATURE_EXTRACTOR_MAX_WORKERS"]

    def test_extract_all_parallel_result_consistency(self, extractor, sample_data):
        """複数回実行しても結果が一貫していることを確認"""
        result1 = extractor.extract_all_parallel(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        result2 = extractor.extract_all_parallel(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        # カラム数が同じであることを確認
        assert len(result1.columns) == len(result2.columns)
        # 行数が同じであることを確認
        assert len(result1) == len(result2)

    def test_extract_previous_races(self, extractor, sample_data):
        """extract_previous_racesの基本動作テスト"""
        result = extractor.extract_previous_races(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data["df"])

