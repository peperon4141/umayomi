# メモリ最適化: DataFrame結合方法の調査と実装

## 📋 概要

`apps/prediction/src/data_processer/_02_jrdb_combiner.py`で使用しているDataFrame結合方法を最適化し、メモリ使用量を削減するための調査と実装内容。

## 🔍 問題の背景

### 発見された問題

1. **TYBマージ処理中にメモリが異常に増加**
   - TYBマージ直前のメモリ: 1827.7MB
   - マージ処理中にプロセスがkillされる
   - メモリ使用量が100GBを超える

2. **結合キーの問題**
   - TYBデータが`['馬番']`だけでマージされている
   - 1つの馬番に対して複数のレースデータが存在
   - 行数が異常に増加（261,375行 → 予測では数千万行に増加する可能性）

3. **UKCマージでも行数が5.5倍に増加**
   - 47,181行 → 261,375行
   - メモリ使用量が1.8GBまで増加

## 🔧 実装した解決策

### 1. メモリ最適化の結合方法の選択

結合方法を自動選択し、メモリ効率を最適化：

#### 1対1マッピング（単一キー、重複なし）
- **方法**: `map()`を使用
- **メリット**: 
  - 最もメモリ効率が良い
  - 新しいDataFrameを作成して列を追加（元のDataFrameを変更しない）
  - メモリ使用量が最小限
- **実装**:
```python
df_indexed = df.set_index(key_col)
combined_df = old_combined_df.copy()  # 元のDataFrameを変更しない
for col in merge_cols:
    new_col_name = col if col not in old_combined_df.columns else f"{col}_{data_type}"
    combined_df[new_col_name] = combined_df[key_col].map(df_indexed[col])
```

#### 1対1マッピング（行数が同じ）
- **方法**: `concat()`を使用（インデックスベース）
- **メリット**:
  - フラグメント化を回避
  - メモリ効率が良い
- **実装**:
```python
old_combined_df_indexed = old_combined_df.set_index(actual_keys)
df_indexed = df.set_index(actual_keys)
# インデックスが一致しているか確認
if old_combined_df_indexed.index.equals(df_indexed.index):
    combined_df = pd.concat([old_combined_df_indexed, df_subset], axis=1)
    combined_df = combined_df.reset_index()
else:
    # インデックスが一致しない場合はmerge()を使用
    combined_df = old_combined_df.merge(df, on=actual_keys, how="left")
```

#### 1対多マッピング（重複キーあり）
- **方法**: `merge()`を使用
- **最適化**:
  - 必要な列のみを選択してメモリ使用量を削減
  - 重複キーがある場合は行数が増加する可能性がある
- **実装**:
```python
merge_cols = actual_keys + [col for col in df.columns if col not in actual_keys and col not in old_combined_df.columns]
df_subset = df[merge_cols]
combined_df = old_combined_df.merge(df_subset, on=actual_keys, how="left", suffixes=("", f"_{data_type}"))
```

### 2. メモリ監視の強化

- マージ処理の前後でメモリ使用量を詳細に記録
- DataFrameのメモリ使用量を表示
- 行数の増加を予測して警告を表示

### 3. エラーハンドリングの改善

- メモリ不足エラーの詳細表示
- トレースバックの表示
- エラー発生時のクリーンアップ処理

## 📊 結合方法の比較

| 結合方法 | メモリ効率 | 使用ケース | 制約 |
|---------|-----------|-----------|------|
| `map()` | ⭐⭐⭐⭐⭐ | 1対1マッピング（単一キー） | 重複キー不可 |
| `concat()` | ⭐⭐⭐⭐ | 1対1マッピング（行数が同じ） | インデックスが一致している必要がある |
| `merge()` | ⭐⭐⭐ | 1対多マッピング | 重複キーがあると行数が増加 |

## ⚠️ 重要な問題: TYBデータの結合キー

### 現在の問題

- TYBデータに`race_key`が含まれていない
- `['馬番']`だけでマージしている
- 1つの馬番に対して複数のレースデータが存在
- 行数が異常に増加する可能性

### 根本的な解決策

1. **TYBデータに`race_key`を追加**
   - LZH→Parquet変換時に`race_key`を生成
   - `['race_key', '馬番']`でマージ

2. **代替キーでマージ**
   - `['場コード', '回', '日', 'R', '馬番']`でマージ
   - `race_key`が不要な場合の代替案

### 実装した修正

```python
# TYBデータにrace_keyがない場合の処理
if data_type in ["TYB", "KYI"] and "race_key" not in df.columns:
    # race_key以外のキーでマージ
    keys_without_race_key = [k for k in config_keys if k != "race_key"]
    actual_keys = [k for k in keys_without_race_key if k in combined_df.columns and k in df.columns]
    
    # TYBデータの場合、race_keyがない場合は代替キー（場コード、回、日、R、馬番）を使用
    if data_type == "TYB" and len(actual_keys) == 1 and actual_keys[0] == "馬番":
        # 馬番だけでは不十分なので、場コード、回、日、R、馬番でマージを試みる
        alternative_keys = ["場コード", "回", "日", "R", "馬番"]
        alternative_actual_keys = [k for k in alternative_keys if k in combined_df.columns and k in df.columns]
        if len(alternative_actual_keys) >= 4:  # 最低4つのキーが必要
            print(f"[_02_] TYBデータ: race_keyがないため、代替キー({alternative_actual_keys})でマージします。")
            actual_keys = alternative_actual_keys
        else:
            print(f"[_02_] 警告: TYBデータにrace_keyがなく、代替キー({alternative_actual_keys})も不完全です。行数が異常に増加する可能性があります。")
```

## 📝 実装ファイル

- `apps/prediction/src/data_processer/_02_jrdb_combiner.py`
  - メモリ最適化の結合方法を実装
  - メモリ監視の強化
  - エラーハンドリングの改善

## 🔄 今後の改善案

1. **チャンク処理の実装**
   - 大きなDataFrameを小さなチャンクに分割してマージ
   - メモリ使用量をさらに削減

2. **データ型の最適化**
   - マージ前にデータ型を最適化
   - メモリ使用量を削減

3. **結合キーの検証**
   - マージ前に結合キーの整合性を検証
   - 行数が異常に増加する前に警告

## 📚 参考資料

- [Pandas Merge Performance](https://pandas.pydata.org/docs/user_guide/merging.html)
- [Memory Optimization in Pandas](https://pandas.pydata.org/docs/user_guide/scale.html)
- [Pandas Best Practices](https://pandas.pydata.org/docs/user_guide/best_practices.html)

## 🎯 チェックリスト

- [x] メモリ最適化の結合方法を実装
- [x] メモリ監視の強化
- [x] エラーハンドリングの改善
- [x] TYBデータの結合キー問題の改善（代替キーを使用）
- [x] `map()`実装の修正（元のDataFrameを変更しない）
- [x] `concat()`実装の修正（インデックス一致チェックを追加）
- [ ] TYBデータに`race_key`を追加する根本的な解決
- [ ] チャンク処理の実装
- [ ] データ型の最適化

## 🔄 修正内容（2025-12-05）

### 修正1: TYBデータの結合キー問題の改善
- **問題**: TYBデータが`['馬番']`だけでマージされていた
- **修正**: `race_key`がない場合、代替キー（`['場コード', '回', '日', 'R', '馬番']`）を使用
- **効果**: 行数の異常な増加を抑制

### 修正2: `map()`実装の修正
- **問題**: 元のDataFrameを直接変更していた
- **修正**: `combined_df = old_combined_df.copy()`でコピーを作成
- **効果**: 元のDataFrameを保護し、メモリ管理を改善

### 修正3: `concat()`実装の修正
- **問題**: インデックスが一致していない場合にエラーが発生する可能性
- **修正**: インデックス一致チェックを追加し、一致しない場合は`merge()`を使用
- **効果**: エラーを防止し、適切な結合方法を選択
