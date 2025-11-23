# スキーマファイルの問題点

## 調査結果サマリー

スキーマファイルを調査した結果、以下の問題点が確認されました。

## 1. `full_info_schema.json`の問題

### 問題1: `rank`と`time`が定義されていない

**現状**:
- `着順`は`feature_name: "jockey_recent_1_rank"`として定義されている（181行目）
  - これは統計特徴量（騎手の直近1レース目の着順）であり、ターゲット変数の`rank`とは異なる
- `タイム`は`feature_name: "jockey_recent_1_time"`として定義されている（183行目）
  - これは統計特徴量（騎手の直近1レース目のタイム）であり、評価用の`time`とは異なる

**影響**:
- `get_all_japanese_columns()`で`rank`が取得できない
- `numeric_converter.convert_to_numeric()`で`着順`→`rank`に変換されるが、スキーマに定義されていないため、後続処理で問題が発生する
- `full_data_df`に`rank`が含まれない可能性がある

**解決策**:
`full_info_schema.json`に以下を追加する必要があります：
```json
{"name":"着順","source":"SED","type":"integer","feature_name":"rank","use_for_training":true},
{"name":"タイム","source":"SED","type":"integer","feature_name":"time","use_for_training":false}
```

ただし、既存の`着順`と`タイム`の定義（統計特徴量）と競合するため、以下のいずれかの対応が必要：
1. ターゲット変数の`rank`と`time`を別名で定義（例: `target_rank`, `target_time`）
2. 統計特徴量の`着順`と`タイム`を別名で定義（例: `jockey_recent_1_rank`, `jockey_recent_1_time`は既に定義済み）
3. ターゲット変数は`着順`と`タイム`のまま保持し、`rank`と`time`は変換時にのみ生成

### 問題2: `R`列の`feature_name`の不整合

**現状**:
- `full_info_schema.json`では`R`の`feature_name`が`jockey_recent_1_race_num`（16行目）
- `training_schema.json`では`race_number`の`jrdb_name`が`R`（113行目）

**影響**:
- `numeric_converter.convert_to_numeric()`で`R`→`jockey_recent_1_race_num`に変換されるが、`training_schema.json`では`race_number`として期待されている可能性がある

**解決策**:
`full_info_schema.json`の`R`列の`feature_name`を`race_number`に変更するか、`training_schema.json`の`race_number`の`jrdb_name`を確認する必要がある。

## 2. `training_schema.json`の問題

### 問題1: `rank`が`columns`に含まれていない

**現状**:
- `target_variable`として`rank`が定義されている（5行目）
- しかし、`columns`には`rank`が含まれていない
- `time`は`columns`に含まれている（131行目）

**影響**:
- `filter_training_columns()`で`rank`が取得できない可能性がある
- `get_training_columns()`で`target_variable`を追加する処理が必要

**解決策**:
`training_schema.json`の`columns`に`rank`を追加するか、`filter_training_columns()`で`target_variable`を自動的に追加する処理を確認する必要がある。

## 3. `combined_schema.json`の問題

**現状**:
- `着順`と`タイム`が定義されているが、`rank`と`time`は定義されていない
- これは生データのスキーマなので問題ない

**影響**: なし（生データのスキーマなので）

## 4. 実装との不整合

### 問題1: `numeric_converter.convert_to_numeric()`の処理

**現状**:
- `numeric_converter.py`の113-118行目で、`着順`→`rank`、`タイム`→`time`に変換している
- しかし、`full_info_schema.json`に`rank`と`time`が定義されていないため、`get_all_japanese_columns()`で取得できない

**影響**:
- `full_data_df`に`rank`が含まれない
- `train_df`に`rank`が含まれない（エラーの原因）

**解決策**:
`full_info_schema.json`に`rank`と`time`を追加するか、`numeric_converter.convert_to_numeric()`の処理を変更する必要がある。

## 推奨される修正方針

1. **`full_info_schema.json`に`rank`と`time`を追加**
   - `着順`を`rank`に変換する際のターゲット変数として定義
   - `タイム`を`time`に変換する際の評価用変数として定義
   - 統計特徴量の`着順`と`タイム`は既に`jockey_recent_1_rank`と`jockey_recent_1_time`として定義されているため、競合しない

2. **`R`列の`feature_name`を確認**
   - `full_info_schema.json`の`R`列の`feature_name`を`race_number`に変更するか、実装を確認する

3. **`training_schema.json`の`rank`を確認**
   - `columns`に`rank`を追加するか、`filter_training_columns()`で`target_variable`を自動的に追加する処理を確認する

## 優先度

1. **高**: `full_info_schema.json`に`rank`と`time`を追加（現在のエラーの直接的な原因）
2. **中**: `R`列の`feature_name`の不整合を確認
3. **低**: `training_schema.json`の`rank`を`columns`に追加（既に`target_variable`として定義されているため）

