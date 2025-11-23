# training_data_processor

学習前処理モジュール。JRDBデータの読み込みから学習用データの準備まで一括実行します。

## 処理フロー図

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    TrainingDataProcessor.process()                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ステップ1: データ読み込みと結合                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  NPZファイル (BAC, KYI, SED, UKC, TYB)                                  │
│         │                                                                 │
│         ▼                                                                 │
│  JrdbProcessor.combine_data()                                           │
│         │                                                                 │
│         ▼                                                                 │
│  combined_df (結合済みDataFrame)                                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ステップ2: 特徴量変換                                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  1. PreviousRaceExtractor.extract()                                      │
│     └─> prev_1_*, prev_2_*, ... (前走データ)                            │
│                                                                           │
│  2. StatisticalFeatureCalculator.calculate()                            │
│     ├─> HorseStatistics: horse_win_rate, horse_place_rate, ...          │
│     ├─> JockeyStatistics: jockey_win_rate, jockey_recent_race_*, ...   │
│     └─> TrainerStatistics: trainer_win_rate, trainer_place_rate, ...   │
│                                                                           │
│  3. TargetAdder.add_rank_and_time()                                      │
│     └─> rank, time (着順・タイム)                                        │
│                                                                           │
│  4. NumericConverter.convert_to_numeric()                                │
│     └─> JRDBフィールド名 → 特徴量名マッピング                            │
│                                                                           │
│  5. LabelEncoder.encode()                                                │
│     └─> e_* (エンコード済みカテゴリカル特徴量)                           │
│                                                                           │
│  6. DtypeOptimizer.optimize()                                            │
│     └─> float64→float32, int64→int32 (メモリ最適化)                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  ステップ3: データ分割とフィルタリング (split_date指定時)                │
├─────────────────────────────────────────────────────────────────────────┤
│  combined_df                                                              │
│         │                                                                 │
│         ├─> DataSplitter.split_train_test()                              │
│         │   ├─> train_df (split_date以前)                                │
│         │   └─> test_df (split_date以降)                                 │
│         │                                                                 │
│         └─> ColumnFilter.get_evaluation_columns()                        │
│             └─> original_df (評価用: rank, odds, time等)                  │
│                                                                           │
│  ColumnFilter.filter_training_columns()                                  │
│         │                                                                 │
│         ├─> train_df (training_schema.jsonのカラム + rank)               │
│         └─> test_df (training_schema.jsonのカラム + rank)                │
│                                                                           │
│  DataValidator.validate()                                                │
│         │                                                                 │
│         ├─> train_df ✓                                                   │
│         └─> test_df ✓                                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                          ┌─────────┴─────────┐
                          │                   │
                    train_df              test_df
                    (学習用)              (検証用)
                          │                   │
                          └─────────┬─────────┘
                                    │
                              original_df
                              (評価用: rank含む)
```

## 詳細な処理ステップ

### ステップ1: データ読み込みと結合

1. **生データの読み込み** (`JrdbProcessor.load_data()`)
   - NPZファイルから各データタイプ（BAC, KYI, SED, UKC, TYB）を読み込む

2. **データの結合** (`JrdbProcessor.combine_data()`)
   - 複数のデータタイプを1つのDataFrameに結合
   - キャッシュ（Parquet形式）があれば読み込む

### ステップ2: 特徴量変換

3. **前走データ抽出** (`PreviousRaceExtractor.extract()`)
   - SEDデータから各馬の前走データ（最大5走）を抽出
   - `prev_1_*`, `prev_2_*`, ... などのカラムを追加

4. **統計特徴量計算** (`StatisticalFeatureCalculator.calculate()`)
   - **馬の統計量**: `horse_win_rate`, `horse_place_rate`, `horse_avg_rank`, `horse_race_count`
   - **騎手の統計量**: `jockey_win_rate`, `jockey_place_rate`, `jockey_avg_rank`, `jockey_race_count`
   - **騎手の直近レース**: `jockey_recent_race_1_*`, `jockey_recent_race_2_*`, `jockey_recent_race_3_*`
   - **調教師の統計量**: `trainer_win_rate`, `trainer_place_rate`, `trainer_avg_rank`, `trainer_race_count`
   - ⚠️ **未来情報除外**: 各レースの`start_datetime`より前のデータのみを使用

5. **ターゲット変数追加** (`TargetAdder.add_rank_and_time()`)
   - SEDデータから着順（`rank`）とタイム（`time`）を抽出して追加

6. **数値変換** (`NumericConverter.convert_to_numeric()`)
   - JRDBフィールド名を特徴量名にマッピング

7. **ラベルエンコーディング** (`LabelEncoder.encode()`)
   - カテゴリカル特徴量を数値にエンコーディング
   - `e_*` プレフィックス付きのカラムを追加

8. **データ型最適化** (`DtypeOptimizer.optimize()`)
   - float64→float32、int64→int32に変換してメモリ使用量を削減

### ステップ3: 学習用データ準備（`split_date`指定時）

9. **時系列分割** (`DataSplitter.split_train_test()`)
   - `split_date`以前を学習データ、以降をテストデータに分割

10. **評価用カラムの取得** (`ColumnFilter.get_evaluation_columns()`)
    - オッズ、着順（`rank`）、タイムなどの評価用カラムを識別

11. **学習用カラムの選択** (`ColumnFilter.filter_training_columns()`)
    - `training_schema.json`で定義された特徴量を選択（`rank`は自動的に追加）

12. **データ検証** (`DataValidator.validate()`)
    - フィールド数、必須カラム、欠損値、時系列整合性を検証

## 重要なポイント

### rank列の扱い（ターゲット変数）

`rank`は**ターゲット変数（target variable / label）**です。予測対象であり、学習時に必要です。
- **追加**: ステップ2の`TargetAdder.add_rank_and_time()`で追加
- **学習データ**: `filter_training_columns()`で自動的に含まれる
- **評価データ**: `original_df`に含まれる
- **スキーマ**: `training_schema.json`には特徴量のみ定義、`rank`は別途追加

### 未来情報の除外

統計特徴量計算では、各レースの`start_datetime`より**前**のデータのみを使用します。
- `np.searchsorted(..., side='left')`を使用して未来情報を完全に除外
- 時系列で累積統計量を計算（`groupby().cumsum()`）

## ファイル構成

```
training_data_processor/
├── main.py                          # メインのオーケストレーター
├── jrdb_processor.py                 # JRDBデータ処理
├── previous_race_extractor.py       # 前走データ抽出
├── statistical_feature_calculator.py # 統計特徴量計算
│   ├── horse_statistics.py          # 馬の統計量
│   ├── jockey_statistics.py         # 騎手の統計量
│   └── trainer_statistics.py        # 調教師の統計量
├── target_adder.py                   # rankとタイム追加
├── numeric_converter.py              # 数値変換
├── label_encoder.py                  # ラベルエンコーディング
├── dtype_optimizer.py                # データ型最適化
├── data_splitter.py                  # 時系列分割
├── column_filter.py                  # 学習用カラム選択
└── data_validator.py                 # データ検証
```

## 使用方法

```python
from src.training_data_processor import TrainingDataProcessor
from pathlib import Path

processor = TrainingDataProcessor(base_path=Path(__file__).parent.parent.parent.parent)

train_df, test_df, original_df = processor.process(
    base_path=Path("./data"),
    data_types=["BAC", "KYI", "SED", "UKC", "TYB"],
    years=[2024],
    split_date="2024-06-01"
)

# train_df: 学習用（training_schema.jsonのカラム + rank）
# test_df: 検証用（training_schema.jsonのカラム + rank）
# original_df: 評価用（rank, odds, time等）
```

## スキーマ定義

学習用データの**特徴量**定義は `packages/data/schemas/jrdb_processed/training_schema.json` に定義されています。
- **特徴量**: `training_schema.json`で定義されたカラム（入力変数）
- **ターゲット変数**: `rank`（予測対象、スキーマには含まれていないが、学習時に自動的に追加される）
- `column_filter.py`: スキーマから特徴量を選択し、`rank`を自動的に追加
- `data_validator.py`: スキーマに基づいてデータを検証
