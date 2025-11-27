"""
WIN5投資のリターン概算計算

1着的中率25.38%の場合、1年間で100万円をWIN5に投資した場合の
期待リターンを計算します。
"""

# パラメータ設定
INVESTMENT_AMOUNT = 1_000_000  # 投資額: 100万円
WIN5_TICKET_PRICE = 200  # WIN5の1口の価格（通常200円）
FIRST_PLACE_ACCURACY = 0.2538  # 1着的中率: 25.38%
RACE_DAYS_PER_YEAR = 288  # 1年間のレース開催日数（JRAの場合、週末開催中心）

# 計算
# 1. 購入可能な口数
total_tickets = INVESTMENT_AMOUNT // WIN5_TICKET_PRICE
print(f"投資額: {INVESTMENT_AMOUNT:,}円")
print(f"WIN5の1口価格: {WIN5_TICKET_PRICE}円")
print(f"購入可能な口数: {total_tickets:,}口")
print()

# 2. 1レースの1着的中確率
print(f"1着的中率: {FIRST_PLACE_ACCURACY * 100:.2f}%")
print()

# 3. WIN5の的中確率（5レースすべて1着的中）
# 各レースが独立していると仮定
win5_probability = FIRST_PLACE_ACCURACY ** 5
print(f"WIN5的中確率（独立と仮定）: {win5_probability * 100:.4f}%")
print(f"  = ({FIRST_PLACE_ACCURACY:.4f})^5")
print()

# 4. 期待的中口数
expected_wins = total_tickets * win5_probability
print(f"期待的中口数: {expected_wins:.2f}口")
print()

# 5. リターン計算（様々な払戻金シナリオ）
print("=" * 60)
print("払戻金シナリオ別のリターン計算")
print("=" * 60)
print()

scenarios = [
    ("低配当", 5_000_000),  # 500万円
    ("中配当", 20_000_000),  # 2,000万円
    ("高配当", 50_000_000),  # 5,000万円
    ("超高配当", 100_000_000),  # 1億円
]

for scenario_name, payout_per_ticket in scenarios:
    expected_return = expected_wins * payout_per_ticket
    net_return = expected_return - INVESTMENT_AMOUNT
    roi = (net_return / INVESTMENT_AMOUNT) * 100
    
    print(f"{scenario_name}（1口あたり {payout_per_ticket:,}円）:")
    print(f"  期待払戻額: {expected_return:,.0f}円")
    print(f"  純利益: {net_return:,.0f}円")
    print(f"  投資収益率(ROI): {roi:.2f}%")
    print()

# 6. 損益分岐点の計算
print("=" * 60)
print("損益分岐点の計算")
print("=" * 60)
print()
break_even_payout = INVESTMENT_AMOUNT / expected_wins if expected_wins > 0 else float('inf')
print(f"損益分岐点（1口あたりの払戻金）: {break_even_payout:,.0f}円")
print(f"  = 投資額({INVESTMENT_AMOUNT:,}円) / 期待的中口数({expected_wins:.2f}口)")
print()

# 7. 実際のWIN5の払戻金について
print("=" * 60)
print("注意事項")
print("=" * 60)
print("""
1. 実際のWIN5の払戻金は変動が大きく、的中した場合でも
   数千万円〜数億円になることが多いです。

2. この計算は各レースが独立していると仮定していますが、
   実際にはレース間の相関（同じ日のレース、同じコースなど）
   があるため、実際の的中確率は異なる可能性があります。

3. 実際のWIN5の的中率は、評価結果のWIN5的中率を確認する
   必要があります（現在の評価結果ではWIN5的中率が表示されていません）。

4. 長期的には、期待値は負になる可能性が高いです。
   ギャンブルは投資ではなく、娯楽として楽しむことが重要です。
""")

