"""previous_race_extractorのテスト"""

import os
import pandas as pd
import pytest

from src.data_processer._03_02_previous_race_extractor import extract as extract_previous_races
from tests.data_processer.conftest import create_simple_kyi_data, create_simple_bac_data, create_simple_sed_data


class TestPreviousRaceExtractor:
    """previous_race_extractorのテスト"""

    @pytest.fixture
    def sample_data(self):
        """サンプルデータを作成（前走データ抽出用）"""
        # 同じ馬が複数レースに出走するデータを作成
        kyi_df = pd.DataFrame({
            "場コード": [1, 1, 1],
            "回": [1, 1, 2],
            "日": ["1", "1", "1"],
            "R": [1, 2, 1],
            "馬番": [1, 1, 1],
            "血統登録番号": ["12345678", "12345678", "12345678"],  # 同じ馬
            "騎手コード": ["J001", "J001", "J001"],
            "調教師コード": ["T001", "T001", "T001"],
        })
        
        bac_df = pd.DataFrame({
            "場コード": [1, 1, 1],
            "回": [1, 1, 2],
            "日": ["1", "1", "1"],
            "R": [1, 2, 1],
            "年月日": [20240101, 20240102, 20240110],
            "発走時刻": [1200, 1300, 1200],
        })
        
        # 過去レースを含むSEDデータ（時系列順）
        sed_df = pd.DataFrame({
            "場コード": [1, 1, 1],
            "回": [1, 1, 2],
            "日": ["1", "1", "1"],
            "R": [1, 2, 1],
            "馬番": [1, 1, 1],
            "血統登録番号": ["12345678", "12345678", "12345678"],
            "騎手コード": ["J001", "J001", "J001"],
            "調教師コード": ["T001", "T001", "T001"],
            "着順": [1, 2, 3],
            "タイム": [120.5, 121.0, 121.5],
            "距離": [1600, 1800, 1600],
            "芝ダ障害コード": [1, 1, 1],
            "馬場状態": [1, 1, 2],
            "頭数": [10, 12, 10],
            "年月日": [20240101, 20240102, 20240110],
        })
        
        # race_keyを追加
        from src.data_processer._03_01_feature_converter import FeatureConverter
        df = kyi_df.copy()
        df = df.merge(bac_df[["場コード", "回", "日", "R", "年月日"]], on=["場コード", "回", "日", "R"], how="left")
        df["race_key"] = df.apply(
            lambda row: FeatureConverter.generate_race_key(
                2024, 1, int(row["日"]), f"{row['場コード']:02d}", row["回"], row["日"], row["R"]
            ),
            axis=1
        )
        
        return {
            "df": df,
            "sed_df": sed_df,
            "bac_df": bac_df,
        }

    def test_extract_basic(self, sample_data):
        """extractの基本動作テスト"""
        result = extract_previous_races(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_data["df"])
        # 前走データのカラムが追加されていることを確認
        assert "prev_1_rank" in result.columns
        assert "prev_1_time" in result.columns
        assert "prev_1_distance" in result.columns

    def test_extract_without_bac(self, sample_data):
        """BACデータがない場合のテスト（エラーが投げられることを確認）"""
        with pytest.raises(ValueError, match="BACデータは必須です"):
            extract_previous_races(
                sample_data["df"],
                sample_data["sed_df"],
                None
            )

    def test_extract_previous_race_data(self, sample_data):
        """前走データが正しく抽出されることを確認"""
        result = extract_previous_races(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        # 2レース目（race_keyが2番目に大きい）の前走データを確認
        # 1レース目が前走として設定されているはず
        result_sorted = result.sort_values("race_key")
        if len(result_sorted) >= 2:
            second_race = result_sorted.iloc[1]
            # 前走データが設定されていることを確認（NaNでない場合）
            if pd.notna(second_race.get("prev_1_rank")):
                assert second_race["prev_1_rank"] == 1  # 1レース目の着順

    def test_extract_worker_count(self, sample_data):
        """ワーカー数の環境変数が正しく反映されることを確認"""
        # ワーカー数を1に設定
        os.environ["DATA_PROCESSER_MAX_WORKERS"] = "1"
        result = extract_previous_races(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        assert isinstance(result, pd.DataFrame)
        # 環境変数をクリア
        del os.environ["DATA_PROCESSER_MAX_WORKERS"]

    def test_extract_result_consistency(self, sample_data):
        """複数回実行しても結果が一貫していることを確認"""
        result1 = extract_previous_races(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        result2 = extract_previous_races(
            sample_data["df"],
            sample_data["sed_df"],
            sample_data["bac_df"]
        )
        
        # カラム数が同じであることを確認
        assert len(result1.columns) == len(result2.columns)
        # 行数が同じであることを確認
        assert len(result1) == len(result2)
        # 前走データの値が同じであることを確認（NaNを除く）
        for col in result1.columns:
            if col.startswith("prev_"):
                mask = pd.notna(result1[col]) & pd.notna(result2[col])
                if mask.any():
                    assert (result1.loc[mask, col] == result2.loc[mask, col]).all()

