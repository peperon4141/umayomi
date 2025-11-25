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

