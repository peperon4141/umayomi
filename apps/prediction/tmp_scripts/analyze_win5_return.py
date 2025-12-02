"""
WIN5のリターンと当選確率を分析

評価結果から：
- 1着的中率: 33.72% (671/1,990レース)
- 3着内的中率: 64.77% (1,289/1,990レース)
- 単勝回収率: 84.15%
- WIN5的中率: 0.00% (0/0日) - WIN5フラグ1～5が揃った日が存在しない
"""

import math
from typing import Dict, Tuple


def calculate_win5_probability(first_place_accuracy: float) -> Dict[str, float]:
    """
    WIN5の当選確率を計算
    
    Args:
        first_place_accuracy: 1着的中率（0.0～1.0）
    
    Returns:
        当選確率の辞書
    """
    # 5レースすべて的中する確率
    win5_probability = first_place_accuracy ** 5
    
    # 年間のWIN5開催日数を仮定（実際のデータから取得する必要がある）
    # 一般的に、WIN5は週1回程度開催されるため、年間約50日と仮定
    annual_win5_days = 50
    
    # 年間の当選期待日数
    expected_win_days = win5_probability * annual_win5_days
    
    return {
        "win5_probability": win5_probability,
        "win5_probability_percent": win5_probability * 100,
        "annual_win5_days": annual_win5_days,
        "expected_win_days": expected_win_days,
        "expected_win_days_per_year": expected_win_days,
    }


def calculate_win5_return(
    annual_investment: float,
    first_place_accuracy: float,
    win5_odds: float = 1000000.0,  # WIN5の平均オッズ（仮定: 100万円）
) -> Dict[str, float]:
    """
    WIN5のリターンを計算
    
    Args:
        annual_investment: 年間投資額（円）
        first_place_accuracy: 1着的中率（0.0～1.0）
        win5_odds: WIN5の平均オッズ（倍率）
    
    Returns:
        リターン情報の辞書
    """
    # WIN5の当選確率
    win5_prob = calculate_win5_probability(first_place_accuracy)
    
    # 1日あたりの投資額（WIN5は1日1回のみ）
    # 年間50日開催と仮定
    annual_win5_days = win5_prob["annual_win5_days"]
    daily_investment = annual_investment / annual_win5_days
    
    # 年間の当選期待日数
    expected_win_days = win5_prob["expected_win_days"]
    
    # WIN5のオッズは「払戻額」を表す（倍率ではない）
    # 1回当選した場合の払戻額 = オッズそのもの
    single_win_return = win5_odds
    
    # 年間の期待払戻額（当選期待日数 × 1回当選時の払戻額）
    expected_return = expected_win_days * single_win_return
    
    # 年間の期待損益
    expected_profit = expected_return - annual_investment
    
    # 年間の期待回収率
    expected_recovery_rate = (expected_return / annual_investment) * 100 if annual_investment > 0 else 0
    
    return {
        "annual_investment": annual_investment,
        "daily_investment": daily_investment,
        "win5_probability": win5_prob["win5_probability"],
        "win5_probability_percent": win5_prob["win5_probability_percent"],
        "expected_win_days": expected_win_days,
        "expected_return": expected_return,
        "expected_profit": expected_profit,
        "expected_recovery_rate": expected_recovery_rate,
        "win5_odds": win5_odds,
    }


def analyze_evaluation_results(
    first_place_accuracy: float,
    top3_accuracy: float,
    single_win_recovery_rate: float,
    total_races: int,
    annual_investment: float = 1200000.0,
) -> None:
    """
    評価結果を分析してWIN5のリターンと当選確率を表示
    
    Args:
        first_place_accuracy: 1着的中率（0.0～1.0）
        top3_accuracy: 3着内的中率（0.0～1.0）
        single_win_recovery_rate: 単勝回収率（0.0～1.0）
        total_races: 総レース数
        annual_investment: 年間投資額（円）
    """
    print("=" * 80)
    print("評価結果の分析")
    print("=" * 80)
    
    print(f"\n【評価結果サマリー】")
    print(f"  1着的中率: {first_place_accuracy * 100:.2f}%")
    print(f"  3着内的中率: {top3_accuracy * 100:.2f}%")
    print(f"  単勝回収率: {single_win_recovery_rate * 100:.2f}%")
    print(f"  総レース数: {total_races:,}レース")
    
    # WIN5の当選確率を計算
    win5_prob = calculate_win5_probability(first_place_accuracy)
    
    print(f"\n【WIN5当選確率の分析】")
    print(f"  1着的中率: {first_place_accuracy * 100:.2f}%")
    print(f"  WIN5当選確率（5レース連続的中）: {win5_prob['win5_probability_percent']:.4f}%")
    print(f"  年間WIN5開催日数（仮定）: {win5_prob['annual_win5_days']}日")
    print(f"  年間当選期待日数: {win5_prob['expected_win_days']:.2f}日")
    
    # 年間120万円投資した場合のリターン
    print(f"\n【年間{annual_investment/10000:.0f}万円投資した場合のWIN5リターン分析】")
    
    # 様々なWIN5オッズで計算
    win5_odds_list = [500000, 1000000, 2000000, 5000000, 10000000]  # 50万円、100万円、200万円、500万円、1000万円
    
    for odds in win5_odds_list:
        result = calculate_win5_return(annual_investment, first_place_accuracy, odds)
        print(f"\n  WIN5平均オッズ: {odds/10000:.0f}万円の場合")
        print(f"    1日あたり投資額: {result['daily_investment']:,.0f}円")
        print(f"    WIN5当選確率: {result['win5_probability_percent']:.4f}%")
        years_per_win = 1 / result['expected_win_days'] if result['expected_win_days'] > 0 else float('inf')
        print(f"    年間当選期待日数: {result['expected_win_days']:.2f}日（約{years_per_win:.1f}年に1回当選）")
        print(f"    1回当選時の払戻額: {odds:,.0f}円")
        print(f"    年間期待払戻額: {result['expected_return']:,.0f}円")
        print(f"    年間期待損益: {result['expected_profit']:,.0f}円 ({result['expected_profit']/annual_investment*100:+.2f}%)")
        print(f"    年間期待回収率: {result['expected_recovery_rate']:.2f}%")
        print(f"    ※年間当選期待日数が0.22日ということは、約4.5年に1回当選する期待値です")
    
    # 的中率が高いことについての分析
    print(f"\n【的中率の妥当性について】")
    print(f"  1着的中率33.72%は、以下の要因が考えられます：")
    print(f"    1. テストデータが特定の期間・条件に偏っている可能性")
    print(f"    2. データリークの可能性（未来情報の混入）")
    print(f"    3. モデルが過学習している可能性")
    print(f"    4. 実際の的中率はより低い可能性が高い")
    
    # より保守的な的中率での計算
    conservative_accuracies = [0.20, 0.25, 0.30]  # 20%, 25%, 30%
    print(f"\n【より保守的な的中率でのWIN5分析】")
    for acc in conservative_accuracies:
        win5_prob_conservative = calculate_win5_probability(acc)
        result_conservative = calculate_win5_return(annual_investment, acc, 1000000.0)
        print(f"\n  1着的中率{acc*100:.0f}%の場合:")
        print(f"    WIN5当選確率: {win5_prob_conservative['win5_probability_percent']:.4f}%")
        print(f"    年間当選期待日数: {win5_prob_conservative['expected_win_days']:.2f}日")
        print(f"    年間期待回収率: {result_conservative['expected_recovery_rate']:.2f}%")


if __name__ == "__main__":
    # 評価結果から
    first_place_accuracy = 0.3372  # 33.72%
    top3_accuracy = 0.6477  # 64.77%
    single_win_recovery_rate = 0.8415  # 84.15%
    total_races = 1990
    
    # 年間120万円投資
    annual_investment = 1200000.0
    
    analyze_evaluation_results(
        first_place_accuracy,
        top3_accuracy,
        single_win_recovery_rate,
        total_races,
        annual_investment,
    )

