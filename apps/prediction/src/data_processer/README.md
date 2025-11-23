# data_processer

シンプルで明確なデータ処理フローを提供するパッケージ。

## 概要

`data_processer`は、JRDBのNPZファイルから学習用データを生成するまでの全処理を、シンプルで明確なステップで実行します。

## 使用方法

```python
from pathlib import Path
from src.data_processer import DataProcessor

# プロセッサーを初期化
processor = DataProcessor(base_path=Path(__file__).parent.parent.parent.parent)

# データ処理を実行
data_types = ["KYI", "BAC", "SED", "UKC", "TYB"]
year = 2024
split_date = "2024-10-01"

# 時系列分割あり
train_df, test_df, eval_df = processor.process(
    data_types=data_types,
    year=year,
    split_date=split_date
)

# 時系列分割なし
converted_df = processor.process(
    data_types=data_types,
    year=year
)
```

## 処理フロー

```
main.py (DataProcessor.process)
│
├─> ステップ1: データ読み込みと結合
│   │
│   ├─> npz_loader.py (NpzLoader.load)
│   │   └─> NPZファイル読み込み
│   │
│   └─> jrdb_combiner.py (JrdbCombiner.combine)
│       └─> 複数データタイプを結合
│           └─> feature_converter.py を使用
│
├─> ステップ2: 特徴量追加
│   │
│   └─> feature_extractor.py (FeatureExtractor)
│       ├─> extract_previous_races()
│       │   └─> previous_race_extractor.py
│       │       └─> feature_converter.py を使用
│       │
│       └─> extract_statistics()
│           └─> statistical_feature_calculator.py
│               ├─> horse_statistics.py
│               ├─> jockey_statistics.py
│               └─> trainer_statistics.py
│
├─> ステップ3: データ変換
│   │
│   └─> key_converter.py (KeyConverter)
│       ├─> convert()
│       │   ├─> numeric_converter.py
│       │   │   └─> feature_converter.py を使用
│       │   ├─> label_encoder.py
│       │   └─> dtype_optimizer.py
│       │
│       └─> optimize()
│           └─> dtype_optimizer.py
│
└─> ステップ4: 時系列分割とカラム選択 (split_date指定時)
    │
    ├─> time_series_splitter.py (TimeSeriesSplitter.split)
    │   └─> data_splitter.py
    │
    └─> column_selector.py (ColumnSelector)
        ├─> select_training()
        │   └─> column_filter.py
        │
        └─> select_evaluation()
            └─> column_filter.py
                │
                └─> (train_df, test_df, eval_df)
```

詳細は`DATA_FLOW.md`を参照してください。

## モジュール構成

- `npz_loader.py`: NPZファイル読み込み
- `jrdb_combiner.py`: JRDBデータ結合
- `feature_extractor.py`: 特徴量抽出
- `key_converter.py`: キー変換と数値化
- `time_series_splitter.py`: 時系列分割
- `column_selector.py`: カラム選択
- `main.py`: メインオーケストレーター

