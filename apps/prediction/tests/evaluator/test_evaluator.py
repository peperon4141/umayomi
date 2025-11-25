"""evaluatorモジュールのテスト"""

import numpy as np
import pandas as pd
import pytest

from src.evaluator import evaluate_model, print_evaluation_results, calculate_ndcg


class TestCalculateNdcg:
    """calculate_ndcg関数のテスト"""

    def test_calculate_ndcg_perfect_prediction(self):
        """完全に正しい予測の場合"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([5, 4, 3, 2, 1])  # 完全に逆順（予測値が大きい順に1着）

        # 予測順位: 5, 4, 3, 2, 1 → 実際の着順: 1, 2, 3, 4, 5
        # これは完全に正しい予測
        ndcg = calculate_ndcg(y_true, y_pred, k=3)
        assert ndcg == 1.0

    def test_calculate_ndcg_wrong_prediction(self):
        """間違った予測の場合"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([1, 2, 3, 4, 5])  # 完全に逆順（予測値が小さい順）

        # 予測順位: 1, 2, 3, 4, 5 → 実際の着順: 1, 2, 3, 4, 5
        # これは完全に間違った予測
        ndcg = calculate_ndcg(y_true, y_pred, k=3)
        assert ndcg < 1.0

    def test_calculate_ndcg_k_parameter(self):
        """kパラメータのテスト"""
        y_true = np.array([1, 2, 3, 4, 5])
        y_pred = np.array([5, 4, 3, 2, 1])

        ndcg1 = calculate_ndcg(y_true, y_pred, k=1)
        ndcg3 = calculate_ndcg(y_true, y_pred, k=3)
        ndcg5 = calculate_ndcg(y_true, y_pred, k=5)

        # kが大きいほど、より多くの要素を考慮する
        assert ndcg1 <= ndcg3 <= ndcg5


class TestEvaluateModel:
    """evaluate_model関数のテスト"""

    @pytest.fixture
    def sample_predictions(self):
        """サンプル予測データ"""
        return pd.DataFrame({
            "race_key": ["race1", "race1", "race1", "race2", "race2", "race2"],
            "rank": [1, 2, 3, 1, 2, 3],
            "predict": [3.0, 2.0, 1.0, 3.0, 2.0, 1.0],  # 完全に正しい予測
            "馬番": [1, 2, 3, 1, 2, 3],
        })

    def test_evaluate_model_basic(self, sample_predictions):
        """基本的な評価テスト"""
        results = evaluate_model(sample_predictions)

        # 基本的な評価指標が含まれていることを確認
        assert "ndcg@1" in results
        assert "ndcg@2" in results
        assert "ndcg@3" in results
        assert "accuracy_1st" in results
        assert "accuracy_top3" in results
        assert "mean_rank_error" in results

        # 完全に正しい予測の場合、NDCGは高い値になる
        assert results["ndcg@1"] > 0.5

    def test_evaluate_model_1st_accuracy(self, sample_predictions):
        """1着的中率のテスト"""
        results = evaluate_model(sample_predictions)

        # 完全に正しい予測の場合、1着的中率は100%
        assert results["accuracy_1st"] == 100.0
        assert results["correct_1st"] == 2  # 2レース
        assert results["total_races"] == 2

    def test_evaluate_model_top3_accuracy(self, sample_predictions):
        """3着以内的中率のテスト"""
        results = evaluate_model(sample_predictions)

        # 完全に正しい予測の場合、3着以内的中率は100%
        assert results["accuracy_top3"] == 100.0

    def test_evaluate_model_mean_rank_error(self, sample_predictions):
        """平均順位誤差のテスト"""
        results = evaluate_model(sample_predictions)

        # 完全に正しい予測の場合、平均順位誤差は0
        assert results["mean_rank_error"] == 0.0

    def test_evaluate_model_with_abnormal_ranks(self):
        """異常な着順値が含まれる場合のテスト"""
        # 異常値（0以下や極端に大きい値）を含むデータ
        predictions = pd.DataFrame({
            "race_key": ["race1", "race1", "race1"],
            "rank": [1, 0, 100],  # 異常値を含む
            "predict": [3.0, 2.0, 1.0],
            "馬番": [1, 2, 3],
        })

        results = evaluate_model(predictions)

        # 異常値が除外されて計算されることを確認
        # 平均順位誤差が異常に大きくならないことを確認
        assert results["mean_rank_error"] < 100.0  # 異常に大きくない

    def test_evaluate_model_missing_rank(self):
        """rank列が欠損している場合のテスト"""
        predictions = pd.DataFrame({
            "race_key": ["race1", "race1", "race1"],
            "着順": [1, 2, 3],  # rank列の代わりに着順列
            "predict": [3.0, 2.0, 1.0],
            "馬番": [1, 2, 3],
        })

        results = evaluate_model(predictions)

        # 着順列からrank列が生成されることを確認
        assert "ndcg@1" in results

    def test_evaluate_model_missing_race_key(self):
        """race_keyが存在しない場合のエラーテスト"""
        predictions = pd.DataFrame({
            "rank": [1, 2, 3],
            "predict": [3.0, 2.0, 1.0],
            "馬番": [1, 2, 3],
        })

        with pytest.raises(ValueError, match="race_key"):
            evaluate_model(predictions)

    def test_evaluate_model_empty_data(self):
        """空のデータの場合のエラーテスト"""
        predictions = pd.DataFrame({
            "race_key": [],
            "rank": [],
            "predict": [],
            "馬番": [],
        })

        with pytest.raises(ValueError, match="評価可能なデータがありません"):
            evaluate_model(predictions)

    def test_evaluate_model_with_odds(self):
        """オッズデータがある場合のテスト"""
        predictions = pd.DataFrame({
            "race_key": ["race1", "race1", "race1"],
            "rank": [1, 2, 3],
            "predict": [3.0, 2.0, 1.0],
            "馬番": [1, 2, 3],
            "確定単勝オッズ": [2.5, 3.0, 4.0],
        })

        results = evaluate_model(predictions, odds_col="確定単勝オッズ")

        # 回収率が計算されることを確認
        assert "recovery_rate" in results
        assert results["recovery_rate"] is not None


class TestPrintEvaluationResults:
    """print_evaluation_results関数のテスト"""

    def test_print_evaluation_results(self, capsys):
        """評価結果の表示テスト"""
        results = {
            "ndcg@1": 0.5,
            "ndcg@2": 0.4,
            "ndcg@3": 0.3,
            "accuracy_1st": 20.0,
            "correct_1st": 2,
            "total_races": 10,
            "accuracy_top3": 60.0,
            "correct_top3": 6,
            "mean_rank_error": 2.5,
        }

        print_evaluation_results(results)
        captured = capsys.readouterr()

        # 出力に主要な指標が含まれていることを確認
        assert "NDCG" in captured.out
        assert "1着的中率" in captured.out
        assert "3着以内的中率" in captured.out
        assert "平均順位誤差" in captured.out

    def test_print_evaluation_results_with_odds(self, capsys):
        """オッズデータがある場合の表示テスト"""
        results = {
            "ndcg@1": 0.5,
            "ndcg@2": 0.4,
            "ndcg@3": 0.3,
            "accuracy_1st": 20.0,
            "correct_1st": 2,
            "total_races": 10,
            "accuracy_top3": 60.0,
            "correct_top3": 6,
            "mean_rank_error": 2.5,
            "recovery_rate": 120.0,
            "total_investment": 1000,
            "total_return": 1200,
            "valid_races": 10,
        }

        print_evaluation_results(results)
        captured = capsys.readouterr()

        # 回収率が表示されることを確認
        assert "単勝回収率" in captured.out

