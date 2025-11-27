# データ処理フロー（速度効率最適化版）

## 概要
JRDBデータを読み込み、特徴量を追加し、学習用データに変換する処理フロー。速度効率を最優先に設計。

## 処理ステップ

### 1. データ読み込み (`NpzLoader`)
- NPZファイルから各データタイプ（KYI, BAC, SED等）を読み込み
- データタイプをキー、DataFrameを値とする辞書を返す

### 2. データ結合 (`JrdbCombiner`)
- KYIをベースに、BAC/SED等を`race_key`や結合キーでマージ
- 日本語キーの結合済みDataFrameを返す

### 3. 特徴量追加（並列処理） (`FeatureExtractor`)
**並列実行可能な処理を同時実行し、結果を結合**

#### 3.1 前処理（共通データ準備）
- `raw_df`に`start_datetime`を追加
- `sed_df`に`race_key`を追加
- `stats_df`を準備（統計量計算用）

#### 3.2 並列処理実行
以下の4つの処理を並列実行：
1. **前走データ抽出** (`previous_race_extractor`): 各馬の過去5走のデータ
2. **馬の統計量計算** (`horse_statistics`): 馬の過去成績統計（勝率、連対率等）
3. **騎手の統計量計算** (`jockey_statistics`): 騎手の過去成績統計と直近3レース詳細
4. **調教師の統計量計算** (`trainer_statistics`): 調教師の過去成績統計と直近3レース詳細

#### 3.3 結果結合
- 並列処理の結果を`raw_df`に`race_key`（または`_original_index`）で結合
- 結合順序：前走データ → 馬統計 → 騎手統計 → 調教師統計
- 各結果は必要なカラムのみを保持して結合（メモリ効率化）

### 4. データ変換 (`KeyConverter`)
- **キー変換・数値化** (`numeric_converter`, `label_encoder`): 日本語キー→英語キー、カテゴリ→数値
- **データ型最適化** (`dtype_optimizer`): メモリ効率化のためデータ型を最適化

### 5. 時系列分割・カラム選択 (`split_date`指定時)
- **時系列分割** (`TimeSeriesSplitter`): `split_date`で学習/テストに分割
- **学習用カラム選択** (`ColumnSelector`): `training_schema.json`に基づき学習用カラムのみ抽出
- **評価用データ準備** (`ColumnSelector`): 日本語キーの全カラムを保持（評価用）

## 並列処理の実装方針

### 並列化の対象
- 前走データ抽出（`previous_race_extractor.extract`）
- 馬統計量計算（`HorseStatistics.calculate`）
- 騎手統計量計算（`JockeyStatistics.calculate`）
- 調教師統計量計算（`TrainerStatistics.calculate`）

### 並列化の方法
- `concurrent.futures.ThreadPoolExecutor`または`ProcessPoolExecutor`を使用
- 各処理は独立して実行可能（`raw_df`と`stats_df`を読み取り専用で共有）
- 各処理は結果のDataFrameを返す（必要なカラムのみ）

### 結合方法
- 各処理の結果は`race_key`（または`_original_index`）をキーとして保持
- `raw_df`をベースに、各結果を順次`merge`で結合
- 結合は`left`結合で、元のデータを保持

## 出力
- `split_date`未指定: 変換済みDataFrame（英語キー）
- `split_date`指定: `(train_df, test_df, eval_df)` のタプル
  - `train_df`, `test_df`: 学習用カラムのみ（英語キー）
  - `eval_df`: 評価用カラム（日本語キー、`rank`, `馬番`, `確定単勝オッズ`等を含む）

## 速度効率化のポイント
- **並列処理**: 独立した特徴量計算を同時実行
- **最小限のコピー**: 各処理は必要なデータのみをコピー
- **効率的な結合**: `race_key`をキーとした高速な`merge`
- **メモリ管理**: 使用済みDataFrameは即座に`del`で削除

## 重要なポイント
- **未来情報の除外**: 統計特徴量は各レースの`start_datetime`より前のデータのみを使用
- **キーの分離**: 学習時は英語キー、評価時は日本語キーを使用
- **データ整合性**: 並列処理でも各処理が同じ`raw_df`と`stats_df`を参照することを保証

## データ結合フロー詳細

### データ結合の流れ（表形式）

| ステップ | 処理クラス/関数 | 入力データ | 出力データ | 使用ファイル | 備考 |
|---------|----------------|----------|-----------|------------|------|
| **0. キャッシュ確認** | `CacheManager.load` | - | `train_df`, `test_df`, `eval_df` または `converted_df` | `apps/prediction/cache/*.parquet` | キャッシュが存在する場合は処理をスキップ |
| **1. データ読み込み** | `NpzLoader.load` | NPZファイル | `data_dict: Dict[str, pd.DataFrame]` | `apps/prediction/notebooks/data/{data_type}_{year}.npz` | KYI, BAC, SED, TYB, UKC等を読み込み |
| **2. データ結合** | `JrdbCombiner.combine` | `data_dict` | `raw_df: pd.DataFrame` (日本語キー) | `packages/data/schemas/jrdb_processed/full_info_schema.json` | KYIをベースに、BAC/SED等を`race_key`でマージ<br>サフィックス: base_type（KYI）はなし、他は`_{data_type}` |
| **3. 特徴量追加（前処理）** | `FeatureConverter` | `raw_df`, `sed_df`, `bac_df` | `df_with_datetime`, `stats_df` | - | `raw_df`に`start_datetime`追加<br>`sed_df`に`race_key`追加<br>`stats_df`を準備（統計量計算用） |
| **3.1. 前走データ抽出** | `previous_race_extractor.extract` | `df_with_datetime`, `sed_df`, `bac_df` | `previous_races: pd.DataFrame` (日本語キー) | - | 各馬の過去5走のデータを抽出<br>結果: `df_with_datetime` + 前走データ（`prev_1_*` ~ `prev_5_*`） |
| **3.2. 馬統計量計算** | `HorseStatistics.calculate` | `stats_df`, `df_with_datetime` | `horse_stats: pd.DataFrame` (日本語キー) | - | 馬の過去成績統計（勝率、連対率等）<br>結果: `df_with_datetime` + 馬統計量（`馬勝率`, `馬連対率`等） |
| **3.3. 騎手統計量計算** | `JockeyStatistics.calculate` | `stats_df`, `df_with_datetime` | `jockey_stats: pd.DataFrame` (日本語キー) | - | 騎手の過去成績統計と直近3レース詳細<br>結果: `df_with_datetime` + 騎手統計量（`騎手勝率`, `騎手直近1着順`等） |
| **3.4. 調教師統計量計算** | `TrainerStatistics.calculate` | `stats_df`, `df_with_datetime` | `trainer_stats: pd.DataFrame` (日本語キー) | - | 調教師の過去成績統計と直近3レース詳細<br>結果: `df_with_datetime` + 調教師統計量（`調教師勝率`, `調教師直近1着順`等） |
| **3.5. 結果結合** | `FeatureExtractor.extract_all_parallel` | `previous_races`, `horse_stats`, `jockey_stats`, `trainer_stats` | `featured_df: pd.DataFrame` (日本語キー) | - | `previous_races`をベースに、各統計量の新規カラムのみを`pd.concat`で結合<br>重複カラムチェックあり |
| **4. データ変換** | `KeyConverter.convert` | `featured_df` (日本語キー) | `converted_df: pd.DataFrame` (英語キー) | `packages/data/schemas/jrdb_processed/full_info_schema.json` | 日本語キー→英語キー変換<br>カテゴリ→数値変換 |
| **4.1. 数値化** | `numeric_converter.convert_to_numeric` | `featured_df` | 数値化済みDataFrame | `full_info_schema.json` | 数値型への変換 |
| **4.2. ラベルエンコーディング** | `label_encoder.LabelEncoder.encode` | 数値化済みDataFrame | エンコード済みDataFrame | `full_info_schema.json` | カテゴリ変数を数値にエンコード |
| **4.3. データ型最適化** | `dtype_optimizer.optimize` | エンコード済みDataFrame | `converted_df` (英語キー) | - | メモリ効率化のためデータ型を最適化 |
| **5. 時系列分割** | `TimeSeriesSplitter.split` | `converted_df`, `split_date` | `train_df`, `test_df` (英語キー) | - | `split_date`で学習/テストに分割 |
| **5.1. 学習用カラム選択** | `ColumnSelector.select_training` | `train_df`, `test_df` | `train_df`, `test_df` (学習用カラムのみ) | `packages/data/schemas/jrdb_processed/training_schema.json` | `use_for_training: true`のカラムのみ抽出 |
| **5.2. 評価用データ準備** | `ColumnSelector.select_evaluation` | `featured_df` (日本語キー) | `eval_df: pd.DataFrame` (日本語キー) | `packages/data/schemas/jrdb_processed/full_info_schema.json` | 日本語キーの全カラムを保持（評価用） |
| **6. キャッシュ保存** | `CacheManager.save` | `train_df`, `test_df`, `eval_df` または `converted_df` | - | `apps/prediction/cache/{data_types}_{year}_{split_date}_*.parquet` | Parquet形式で保存 |

### データ結合の詳細フロー

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 0. キャッシュ確認                                                        │
│    CacheManager.load()                                                   │
│    → キャッシュが存在する場合は処理をスキップ                             │
└─────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. データ読み込み                                                        │
│    NpzLoader.load()                                                     │
│    入力: apps/prediction/notebooks/data/{data_type}_{year}.npz          │
│    出力: data_dict = {                                                  │
│            "KYI": DataFrame,                                            │
│            "BAC": DataFrame,                                            │
│            "SED": DataFrame,                                            │
│            "TYB": DataFrame,                                            │
│            "UKC": DataFrame                                             │
│          }                                                               │
└─────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. データ結合                                                            │
│    JrdbCombiner.combine()                                                │
│    使用ファイル: full_info_schema.json                                   │
│    処理:                                                                 │
│    1. KYIをベース（base_type）として取得                                 │
│    2. BACからrace_keyを取得して結合                                      │
│    3. 各データタイプ（SED, TYB, UKC等）を結合キーでマージ                │
│       - base_type（KYI）: サフィックスなし                               │
│       - その他: _{data_type}サフィックス付き                             │
│    出力: raw_df (日本語キー、全カラム結合済み)                            │
└─────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. 特徴量追加（並列処理）                                                │
│    FeatureExtractor.extract_all_parallel()                              │
│                                                                          │
│    3.1 前処理                                                            │
│        - raw_dfにstart_datetimeを追加                                    │
│        - sed_dfにrace_keyを追加                                           │
│        - stats_dfを準備（統計量計算用）                                   │
│                                                                          │
│    3.2 並列処理実行（ThreadPoolExecutor、max_workers=4）                │
│        ┌──────────────────┐  ┌──────────────────┐                      │
│        │ 前走データ抽出    │  │ 馬統計量計算      │                      │
│        │ previous_race_   │  │ HorseStatistics. │                      │
│        │ extractor.extract│  │ calculate        │                      │
│        │ 入力: df_with_   │  │ 入力: stats_df,   │                      │
│        │ datetime, sed_df │  │ df_with_datetime │                      │
│        │ 出力: previous_  │  │ 出力: horse_stats │                      │
│        │ races            │  │                  │                      │
│        └──────────────────┘  └──────────────────┘                      │
│        ┌──────────────────┐  ┌──────────────────┐                      │
│        │ 騎手統計量計算    │  │ 調教師統計量計算  │                      │
│        │ JockeyStatistics. │  │ TrainerStatistics│                      │
│        │ calculate        │  │ .calculate      │                      │
│        │ 入力: stats_df,   │  │ 入力: stats_df,   │                      │
│        │ df_with_datetime │  │ df_with_datetime │                      │
│        │ 出力: jockey_    │  │ 出力: trainer_   │                      │
│        │ stats            │  │ stats           │                      │
│        └──────────────────┘  └──────────────────┘                      │
│                                                                          │
│    3.3 結果結合                                                          │
│        1. previous_racesをベースとして取得                                │
│        2. 各統計量の結果から、df_with_datetimeに含まれていない            │
│           かつprevious_racesに既に含まれていないカラムのみを抽出          │
│        3. pd.concatで結合（axis=1）                                      │
│        4. 重複カラムチェック（エラーを投げる）                            │
│        出力: featured_df (日本語キー、全特徴量結合済み)                  │
└─────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. データ変換                                                            │
│    KeyConverter.convert() → KeyConverter.optimize()                      │
│    使用ファイル: full_info_schema.json                                   │
│    処理:                                                                 │
│    1. 数値化 (numeric_converter.convert_to_numeric)                      │
│    2. ラベルエンコーディング (label_encoder.LabelEncoder.encode)        │
│    3. データ型最適化 (dtype_optimizer.optimize)                          │
│    出力: converted_df (英語キー、数値化済み、最適化済み)                  │
└─────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. 時系列分割・カラム選択（split_date指定時のみ）                        │
│                                                                          │
│    5.1 時系列分割                                                        │
│        TimeSeriesSplitter.split()                                        │
│        入力: converted_df, split_date                                   │
│        出力: train_df, test_df (英語キー)                                │
│                                                                          │
│    5.2 学習用カラム選択                                                  │
│        ColumnSelector.select_training()                                  │
│        使用ファイル: training_schema.json                                 │
│        処理: use_for_training: trueのカラムのみ抽出                      │
│        出力: train_df, test_df (学習用カラムのみ)                        │
│                                                                          │
│    5.3 評価用データ準備                                                  │
│        ColumnSelector.select_evaluation()                                │
│        使用ファイル: full_info_schema.json                               │
│        処理: 日本語キーの全カラムを保持                                  │
│        出力: eval_df (日本語キー、全カラム)                              │
└─────────────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. キャッシュ保存                                                        │
│    CacheManager.save()                                                   │
│    出力: apps/prediction/cache/{data_types}_{year}_{split_date}_*.parquet│
└─────────────────────────────────────────────────────────────────────────┘
```

### データ結合時のサフィックス規則

| データタイプ | サフィックス | 理由 |
|------------|------------|------|
| KYI | なし | base_type（基準データタイプ）のため |
| BAC | `_BAC` | base_type以外のため |
| SED | `_SED` | base_type以外のため |
| TYB | `_TYB` | base_type以外のため |
| UKC | `_UKC` | base_type以外のため |
| computed（前走データ等） | `_SED` | SEDデータから計算されるため |

### 各ステップでのデータ形式

| ステップ | キー形式 | データ型 | 例 |
|---------|---------|---------|---|
| 1. データ読み込み | 日本語キー | 元データ型 | `場コード`, `年`, `回`, `日`, `R` |
| 2. データ結合 | 日本語キー | 元データ型 | `場コード`, `年`, `回`, `日`, `R`, `race_key` |
| 3. 特徴量追加 | 日本語キー | 元データ型 + 計算済み | `場コード`, `前走1着順`, `馬勝率`, `騎手直近1着順` |
| 4. データ変換 | 英語キー | 数値型（最適化済み） | `venue_code`, `prev_1_rank`, `horse_win_rate`, `jockey_recent_1_rank` |
| 5. カラム選択 | 英語キー（学習用）<br>日本語キー（評価用） | 数値型（学習用）<br>元データ型（評価用） | 学習用: `prev_1_rank`, `horse_win_rate`<br>評価用: `前走1着順`, `確定単勝オッズ` |

