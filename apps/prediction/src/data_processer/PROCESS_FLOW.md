# データ処理フロー

## 概要
JRDBデータを読み込み、特徴量を追加し、学習用データに変換する処理フロー。

## 処理ステップ

### 1. データ読み込み (`NpzLoader`)
- NPZファイルから各データタイプ（KYI, BAC, SED等）を読み込み
- データタイプをキー、DataFrameを値とする辞書を返す

### 2. データ結合 (`JrdbCombiner`)
- KYIをベースに、BAC/SED等を`race_key`や結合キーでマージ
- 日本語キーの結合済みDataFrameを返す

### 3. 特徴量追加 (`FeatureExtractor`)
- **前走データ抽出** (`previous_race_extractor`): 各馬の過去5走のデータを追加
- **統計特徴量計算** (`statistical_feature_calculator`): 
  - 騎手・調教師・馬の過去成績統計（勝率、連対率等）
  - 騎手・調教師の直近レース情報

### 4. データ変換 (`KeyConverter`)
- **キー変換・数値化** (`numeric_converter`, `label_encoder`): 日本語キー→英語キー、カテゴリ→数値
- **データ型最適化** (`dtype_optimizer`): メモリ効率化のためデータ型を最適化

### 5. 時系列分割・カラム選択 (`split_date`指定時)
- **時系列分割** (`TimeSeriesSplitter`): `split_date`で学習/テストに分割
- **学習用カラム選択** (`ColumnSelector`): `training_schema.json`に基づき学習用カラムのみ抽出
- **評価用データ準備** (`ColumnSelector`): 日本語キーの全カラムを保持（評価用）

## 出力
- `split_date`未指定: 変換済みDataFrame（英語キー）
- `split_date`指定: `(train_df, test_df, eval_df)` のタプル
  - `train_df`, `test_df`: 学習用カラムのみ（英語キー）
  - `eval_df`: 評価用カラム（日本語キー、`rank`, `馬番`, `確定単勝オッズ`等を含む）

## 重要なポイント
- **未来情報の除外**: 統計特徴量は各レースの`start_datetime`より前のデータのみを使用
- **キーの分離**: 学習時は英語キー、評価時は日本語キーを使用
- **メモリ効率**: 使用済みDataFrameは`del`で削除

