"""予測結果と評価データのマージ処理のテスト

race_keyのみでマージするとデカルト積が発生する問題を検証するテスト
"""

import pandas as pd
import pytest


class TestPredictionMerge:
    """予測結果と評価データのマージ処理のテスト"""

    @pytest.fixture
    def val_predictions_raw(self):
        """予測結果のサンプル（各レースに複数の馬が含まれる）"""
        return pd.DataFrame({
            "race_key": ["race1", "race1", "race1", "race2", "race2"],
            "predict": [3.0, 2.0, 1.0, 2.5, 1.5],
        })

    @pytest.fixture
    def val_df(self):
        """val_dfのサンプル（馬番を含む）"""
        return pd.DataFrame({
            "race_key": ["race1", "race1", "race1", "race2", "race2"],
            "馬番": [1, 2, 3, 1, 2],
            "feature1": [0.1, 0.2, 0.3, 0.4, 0.5],
        })

    @pytest.fixture
    def original_eval(self):
        """評価用データのサンプル（各レースに複数の馬が含まれる）"""
        return pd.DataFrame({
            "race_key": ["race1", "race1", "race1", "race2", "race2"],
            "馬番": [1, 2, 3, 1, 2],
            "着順": [1, 2, 3, 1, 2],
            "確定単勝オッズ": [2.5, 3.0, 4.0, 2.0, 3.5],
            "その他カラム": ["A", "B", "C", "D", "E"],
        })

    def test_merge_with_race_key_only_causes_cartesian_product(
        self, val_predictions_raw, original_eval
    ):
        """race_keyのみでマージするとデカルト積が発生することを確認"""
        # race_keyのみでマージ（バグの再現）
        merged = val_predictions_raw.merge(original_eval, on="race_key", how="left")

        # デカルト積が発生していることを確認
        # race1: 3行 × 3行 = 9行
        # race2: 2行 × 2行 = 4行
        # 合計: 13行（本来は5行であるべき）
        assert len(merged) == 13, "race_keyのみでマージするとデカルト積が発生する"

        # race1の行数を確認
        race1_rows = merged[merged["race_key"] == "race1"]
        assert len(race1_rows) == 9, "race1でデカルト積が発生している"

    def test_merge_with_race_key_and_horse_num_prevents_cartesian_product(
        self, val_predictions_raw, val_df, original_eval
    ):
        """race_keyと馬番の両方でマージすると正しい行数になることを確認"""
        # val_predictions_rawに馬番を追加
        val_df_for_merge = val_df.copy()
        if "race_key" not in val_df_for_merge.columns:
            val_df_for_merge = val_df_for_merge.reset_index()

        # 行数が一致することを確認
        assert len(val_predictions_raw) == len(val_df_for_merge)

        # 馬番を追加
        val_predictions_raw_with_horse_num = val_predictions_raw.copy()
        val_predictions_raw_with_horse_num["馬番"] = val_df_for_merge["馬番"].values

        # race_keyと馬番の両方でマージ（修正後の動作）
        merged = val_predictions_raw_with_horse_num.merge(
            original_eval, on=["race_key", "馬番"], how="left"
        )

        # デカルト積が発生していないことを確認
        assert len(merged) == 5, "race_keyと馬番の両方でマージすると正しい行数になる"

        # 各レースの行数を確認
        race1_rows = merged[merged["race_key"] == "race1"]
        assert len(race1_rows) == 3, "race1は3行であるべき"

        race2_rows = merged[merged["race_key"] == "race2"]
        assert len(race2_rows) == 2, "race2は2行であるべき"

    def test_merge_preserves_data_integrity(
        self, val_predictions_raw, val_df, original_eval
    ):
        """マージ後のデータが正しく結合されていることを確認"""
        # val_predictions_rawに馬番を追加
        val_df_for_merge = val_df.copy()
        if "race_key" not in val_df_for_merge.columns:
            val_df_for_merge = val_df_for_merge.reset_index()

        val_predictions_raw_with_horse_num = val_predictions_raw.copy()
        val_predictions_raw_with_horse_num["馬番"] = val_df_for_merge["馬番"].values

        # race_keyと馬番の両方でマージ
        merged = val_predictions_raw_with_horse_num.merge(
            original_eval, on=["race_key", "馬番"], how="left"
        )

        # データの整合性を確認
        # race1, 馬番1のデータを確認
        race1_horse1 = merged[(merged["race_key"] == "race1") & (merged["馬番"] == 1)]
        assert len(race1_horse1) == 1
        assert race1_horse1.iloc[0]["predict"] == 3.0
        assert race1_horse1.iloc[0]["着順"] == 1
        assert race1_horse1.iloc[0]["確定単勝オッズ"] == 2.5

        # race1, 馬番2のデータを確認
        race1_horse2 = merged[(merged["race_key"] == "race1") & (merged["馬番"] == 2)]
        assert len(race1_horse2) == 1
        assert race1_horse2.iloc[0]["predict"] == 2.0
        assert race1_horse2.iloc[0]["着順"] == 2
        assert race1_horse2.iloc[0]["確定単勝オッズ"] == 3.0

        # すべてのカラムが結合されていることを確認
        expected_cols = ["race_key", "predict", "馬番", "着順", "確定単勝オッズ", "その他カラム"]
        for col in expected_cols:
            assert col in merged.columns, f"{col}が結合後のDataFrameに含まれている"

    def test_merge_with_different_horse_numbers(self):
        """異なる馬番を持つレースのマージをテスト"""
        val_predictions_raw = pd.DataFrame({
            "race_key": ["race1", "race1"],
            "predict": [3.0, 2.0],
        })

        val_df = pd.DataFrame({
            "race_key": ["race1", "race1"],
            "馬番": [1, 2],
        })

        original_eval = pd.DataFrame({
            "race_key": ["race1", "race1", "race1"],
            "馬番": [1, 2, 3],  # 馬番3が予測結果にはない
            "着順": [1, 2, 3],
        })

        # val_predictions_rawに馬番を追加
        val_predictions_raw_with_horse_num = val_predictions_raw.copy()
        val_predictions_raw_with_horse_num["馬番"] = val_df["馬番"].values

        # race_keyと馬番の両方でマージ
        merged = val_predictions_raw_with_horse_num.merge(
            original_eval, on=["race_key", "馬番"], how="left"
        )

        # 予測結果に含まれる馬のみが結合されることを確認
        assert len(merged) == 2
        assert merged["馬番"].tolist() == [1, 2]

    def test_merge_with_missing_race_key_in_original_eval(self):
        """original_evalに存在しないrace_keyがある場合のテスト"""
        val_predictions_raw = pd.DataFrame({
            "race_key": ["race1", "race2", "race3"],
            "predict": [3.0, 2.0, 1.0],
        })

        val_df = pd.DataFrame({
            "race_key": ["race1", "race2", "race3"],
            "馬番": [1, 1, 1],
        })

        original_eval = pd.DataFrame({
            "race_key": ["race1", "race2"],  # race3が存在しない
            "馬番": [1, 1],
            "着順": [1, 1],
        })

        # val_predictions_rawに馬番を追加
        val_predictions_raw_with_horse_num = val_predictions_raw.copy()
        val_predictions_raw_with_horse_num["馬番"] = val_df["馬番"].values

        # race_keyと馬番の両方でマージ
        merged = val_predictions_raw_with_horse_num.merge(
            original_eval, on=["race_key", "馬番"], how="left"
        )

        # すべての行が保持されることを確認（left join）
        assert len(merged) == 3

        # race3のデータが欠損していることを確認
        race3 = merged[merged["race_key"] == "race3"]
        assert race3.iloc[0]["着順"] is pd.NA or pd.isna(race3.iloc[0]["着順"])

