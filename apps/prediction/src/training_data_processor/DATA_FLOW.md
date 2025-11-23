# データ処理フロー

## 概要

`training_data_processor`は、JRDBのNPZファイルから学習用データを生成するまでの全処理を統合します。

## 処理フロー

```
NPZファイル → 結合 → 特徴量追加 → 変換 → 分割 → 学習用データ
```

## 詳細フロー

### ステップ1: データ読み込みと結合

**処理**: `JrdbProcessor.load_data()` → `JrdbProcessor.combine_data()`

1. **NPZファイル読み込み**
   - 各データタイプ（KYI, BAC, SED, UKC, TYB）を個別に読み込み
   - `data_dict[data_type] = DataFrame` の形式で保持

2. **データ結合**
   - `KYI`をベースに、`joinKeys`定義に基づいて他のデータタイプを結合
   - **重要**: SEDデータの`着順`→`rank`、`タイム`→`time`にリネーム
   - `rank > 0`のレコードのみ残す（取消・除外を除外）
   - `time`は秒単位に変換

**出力**: `combined_df`（日本語キー、全データタイプ結合済み）

### ステップ2: 特徴量追加

**処理**: `PreviousRaceExtractor.extract()` → `StatisticalFeatureCalculator.calculate()`

3. **前走データ抽出**
   - SEDデータから各馬の前走データ（最大5走）を抽出
   - `前走1距離`、`前走1着順`、`前走1タイム`などのカラムを追加

4. **統計特徴量計算**
   - **馬の統計量**: `馬勝率`、`馬連対率`、`馬平均着順`、`馬出走回数`
   - **騎手の統計量**: `騎手勝率`、`騎手連対率`、`騎手平均着順`、`騎手出走回数`
   - **騎手の直近レース**: `騎手直近1着順`、`騎手直近1タイム`など（最大3レース）
   - **調教師の統計量**: `調教師勝率`、`調教師連対率`、`調教師平均着順`、`調教師出走回数`
   - ⚠️ **未来情報除外**: 各レースの`start_datetime`より前のデータのみ使用

**出力**: `combined_df`（日本語キー、統計特徴量・前走データ追加済み）

### ステップ3: データ変換

**処理**: `NumericConverter.convert_to_numeric()` → `LabelEncoder.encode()` → `DtypeOptimizer.optimize()`

5. **数値変換**
   - `full_info_schema.json`に基づいて日本語キー→英語キー（`feature_name`）に変換
   - 例: `馬勝率` → `horse_win_rate`、`前走1距離` → `prev_1_distance`
   - **注意**: `rank`と`time`は`full_info_schema.json`に定義されていないが、リネーム済みのためそのまま残る

6. **ラベルエンコーディング**
   - カテゴリカル変数を数値にエンコーディング
   - `e_*`プレフィックス付きのカラムを追加

7. **データ型最適化**
   - float64→float32、int64→int32に変換してメモリ使用量を削減
   - object型カラムをクリーンアップ

**出力**: `combined_df`（英語キー、数値化・最適化済み）

### ステップ4: 時系列分割とカラム選択（`split_date`指定時）

**処理**: `DataSplitter.split_train_test()` → `ColumnFilter.filter_training_columns()` → `ColumnFilter.get_all_columns()`

8. **時系列分割**
   - `split_date`以前を学習データ、以降を検証データに分割
   - `race_key`をインデックスに設定し、`start_datetime`でソート済み

9. **学習用カラム選択**
   - `full_info_schema.json`の`use_for_training=true`のカラムを選択
   - `training_schema.json`の`target_variable`（`rank`）も含める
   - 英語キー（`feature_name`）で返す

10. **評価用データ作成**
    - `full_info_schema.json`の全カラム（`feature_name`）を取得
    - **問題**: `rank`と`time`は`full_info_schema.json`に定義されていないため、`get_all_columns()`では取得されない
    - **解決策**: `full_info_schema.json`に`rank`と`time`を追加するか、`get_all_columns()`で特別に処理

**出力**: 
- `train_df`: 学習用カラムのみ（`rank`含む）
- `test_df`: 学習用カラムのみ（`rank`含む）
- `original_df`: 全カラム（評価用、`rank`と`time`を含む必要がある）

## 重要なポイント

### 1. `rank`と`time`の扱い

- **生成**: `jrdb_processor.combine_data()`で`着順`→`rank`、`タイム`→`time`にリネーム
- **スキーマ**: `full_info_schema.json`には定義されていない（`着順`は`jockey_recent_1_rank`として定義されているが、これは統計特徴量）
- **問題**: `get_all_columns()`は`full_info_schema.json`の`feature_name`のみを取得するため、`rank`が含まれない
- **解決策**: `full_info_schema.json`に`rank`と`time`を追加する

### 2. 未来情報の除外

- 統計特徴量計算では、各レースの`start_datetime`より**前**のデータのみを使用
- `np.searchsorted(..., side='left')`を使用して未来情報を完全に除外
- 時系列で累積統計量を計算（`groupby().cumsum()`）

### 3. スキーマの役割

- **`full_info_schema.json`**: 全結合データの定義（日本語キー + 英語キー + 学習用フラグ）
- **`training_schema.json`**: 学習用データの定義（ターゲット変数含む）
- **`combined_schema.json`**: 結合キー定義（`joinKeys`）

### 4. データの流れ

```
日本語キー（結合・特徴量追加）
  ↓
英語キー（数値変換）
  ↓
学習用カラム（カラムフィルタリング）
```

## あるべき状態

1. **`full_info_schema.json`に`rank`と`time`を追加**
   - `rank`: `{"name":"rank","source":"SED","type":"integer","feature_name":"rank","use_for_training":true}`
   - `time`: `{"name":"time","source":"SED","type":"numeric","feature_name":"time","use_for_training":false}`

2. **`get_all_columns()`の動作**
   - `full_info_schema.json`の全`feature_name`を取得
   - `rank`と`time`も含まれる

3. **`original_df`の内容**
   - `full_info_schema.json`で定義された全カラム（`rank`と`time`含む）
   - 評価時に必要な情報（`race_key`、`rank`、`馬番`、`time`など）がすべて含まれる

