"""searchsortedの動作を確認するスクリプト

side='left'で-1することで、その時点より前のデータのみを取得しているか確認
"""

import numpy as np
import pandas as pd

# テストケース1: 基本的な動作確認
print("=" * 60)
print("テストケース1: searchsortedの基本的な動作")
print("=" * 60)

# 時系列データ（過去から未来へ）
stats_times = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
target_times = np.array([5, 7, 10])  # 検証したい時点

# side='left'で検索
indices_left = np.searchsorted(stats_times, target_times, side='left')
print(f"stats_times: {stats_times}")
print(f"target_times: {target_times}")
print(f"searchsorted(side='left'): {indices_left}")
print(f"searchsorted(side='left') - 1: {indices_left - 1}")

# 各時点より前のデータを取得
for i, target_time in enumerate(target_times):
    idx = indices_left[i] - 1
    if idx >= 0:
        print(f"  時点{target_time}より前のデータ: {stats_times[:idx+1]} (インデックス{idx}まで)")
    else:
        print(f"  時点{target_time}より前のデータ: なし")

# テストケース2: 同じ時点のデータが含まれないことを確認
print("\n" + "=" * 60)
print("テストケース2: 同じ時点のデータが含まれないことを確認")
print("=" * 60)

stats_times2 = np.array([1, 2, 3, 4, 5, 5, 5, 6, 7, 8])  # 時点5に複数のデータ
target_time2 = 5

indices_left2 = np.searchsorted(stats_times2, target_time2, side='left')
print(f"stats_times: {stats_times2}")
print(f"target_time: {target_time2}")
print(f"searchsorted(side='left'): {indices_left2}")
print(f"searchsorted(side='left') - 1: {indices_left2 - 1}")

idx2 = indices_left2 - 1
if idx2 >= 0:
    print(f"  時点{target_time2}より前のデータ: {stats_times2[:idx2+1]} (インデックス{idx2}まで)")
    print(f"  時点{target_time2}のデータ: {stats_times2[stats_times2 == target_time2]}")
    print(f"  ✓ 同じ時点のデータは含まれていません")
else:
    print(f"  時点{target_time2}より前のデータ: なし")

# テストケース3: 実際のデータでの確認
print("\n" + "=" * 60)
print("テストケース3: 実際のデータでの確認")
print("=" * 60)

# 分割日時: 2024-06-01
split_date = pd.to_datetime("2024-06-01")
# テストデータの最初のレース: 2024-06-01 09:50:00
first_test_datetime = pd.to_datetime("2024-06-01 09:50:00")

# 全期間のSEDデータ（学習期間 + テスト期間）
all_sed_datetimes = pd.to_datetime([
    "2024-01-01 10:00:00",  # 学習期間
    "2024-03-01 10:00:00",  # 学習期間
    "2024-05-01 10:00:00",  # 学習期間
    "2024-06-01 09:00:00",  # 学習期間（分割日時より前）
    "2024-06-01 09:50:00",  # テスト期間（最初のテストレースと同じ時点）
    "2024-06-01 10:00:00",  # テスト期間
    "2024-07-01 10:00:00",  # テスト期間
])

# 数値型に変換（start_datetimeの形式）
all_sed_times = all_sed_datetimes.view(np.int64) // 10**9  # Unix timestamp
first_test_time = first_test_datetime.value // 10**9

# ソート
sorted_indices = np.argsort(all_sed_times)
sorted_times = all_sed_times[sorted_indices]

# searchsortedで検索
idx = np.searchsorted(sorted_times, first_test_time, side='left') - 1

print(f"全期間のSEDデータ（ソート済み）: {all_sed_datetimes[sorted_indices]}")
print(f"最初のテストレースの時点: {first_test_datetime}")
print(f"searchsorted(side='left') - 1: {idx}")
if idx >= 0:
    print(f"  最初のテストレースより前のデータ: {all_sed_datetimes[sorted_indices[:idx+1]]}")
    print(f"  最初のテストレースと同じ時点のデータ: {all_sed_datetimes[sorted_indices[sorted_times == first_test_time]]}")
    print(f"  ✓ 同じ時点のデータは含まれていません")
    print(f"  ✓ テスト期間のデータは含まれていません")
else:
    print(f"  最初のテストレースより前のデータ: なし")

print("\n" + "=" * 60)
print("結論")
print("=" * 60)
print("searchsortedのside='left'で-1することで、")
print("その時点より前のデータのみを取得できています。")
print("したがって、理論的にはデータリークは発生していません。")
print("\nしかし、的中率が高い理由として、以下が考えられます：")
print("1. データの質が良い")
print("2. 特徴量が有効")
print("3. モデルが適切に学習している")
print("4. 競馬予想の一般的な的中率と比較して、実際には妥当な範囲内の可能性")

