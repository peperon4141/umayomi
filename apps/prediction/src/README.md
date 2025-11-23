# 競馬予測システム - ソースコード構成

このディレクトリには、JRDBデータを使用した競馬予測システムのコアモジュールが含まれています。

## 📁 ファイル構成と役割

### データ読み込み・管理

#### `data_loader.py`
- **役割**: JRDBデータのNPZファイル読み込み処理
- **主要機能**:
  - `load_jrdb_npz()`: NPZファイルからデータを読み込み
  - `load_annual_pack_npz()`: 年度パックNPZファイルを読み込み
  - `load_multiple_npz_files()`: 複数のNPZファイルを結合
- **使用場面**: データの初期読み込み時

#### `cache_loader.py`
- **役割**: 生データ（結合済みJRDBデータ）のキャッシュ管理
- **主要機能**:
  - `set_raw_data()`: 生データを設定
  - `get_raw_data()`: 生データを取得（データタイプ指定可）
  - `get_evaluation_data()`: 評価用データ（着順・タイム・オッズ）を取得
  - `merge_evaluation_data()`: 予測結果に評価用データをマージ
  - `save_to_cache()` / `load_from_cache()`: キャッシュの保存・読み込み
- **使用場面**: データの永続化と評価時のデータ取得

### 特徴量処理

#### `feature_converter.py`
- **役割**: 特徴量変換ユーティリティ（race_key生成、年月日処理など）
- **主要機能**:
  - `generate_race_key()`: レースキーを生成（例: "20241102_01_1_a_01"）
  - `safe_int()` / `safe_ymd()`: 安全な数値・年月日変換
  - `add_race_key_to_df()`: DataFrameにrace_keyを追加
- **使用場面**: データ結合時や前処理時

#### `features.py`
- **役割**: JRDBデータから抽出する特徴量の定義
- **主要機能**:
  - `Features`クラス: 特徴量名、カテゴリカル特徴量のマッピングを定義
  - オッズ関連フィールドは除外（予測には使用せず、評価用に別途保持）
- **使用場面**: モデル学習・予測時

### 前処理

#### `preprocessor.py`
- **役割**: JRDBデータの前処理クラス（データ読み込みから特徴量変換まで一括実行）
- **主要機能**:
  - `load_and_combine_data()`: 複数データタイプを読み込んで結合
  - `combine_data_types()`: データタイプを結合（KYI, BAC, SED, UKC, TYBなど）
  - `extract_previous_race_data()`: 前走データ抽出
  - `add_statistical_features()`: 統計特徴量の追加（馬・騎手・調教師の過去成績）
  - `convert_to_numeric()`: 数値変換
  - `label_encode()`: ラベルエンコーディング
  - `process()`: 前処理を一括実行（キャッシュ対応）
  - `split()`: 学習・検証データに分割（レース単位で時系列分割）
- **使用場面**: モデル学習前のデータ準備

### 予測モデル

#### `rank_predictor.py`
- **役割**: LambdaRankを使用したランキング学習モデル
- **主要機能**:
  - `train()`: モデル学習（Optunaによるハイパーパラメータ最適化）
  - `predict()`: 予測実行
  - `print_evaluation()`: 評価結果の表示
- **使用場面**: レース内での相対的な順位予測

#### `lambdamart_predictor.py`
- **役割**: LambdaMARTを使用したランキング学習モデル
- **主要機能**:
  - `train()`: モデル学習
  - `predict()`: 予測実行
  - `evaluate()`: モデル評価
- **使用場面**: LambdaRankの代替モデル

#### `complementary_predictor.py`
- **役割**: 補完的予測モデル（順位予測とタイム予測の組み合わせ）
- **主要機能**:
  - `train()`: 順位モデルとタイムモデルを学習
  - `predict()`: 両モデルを使用して予測
- **使用場面**: 順位とタイムの両方を予測したい場合

#### `pytorch_multitask_predictor.py`
- **役割**: PyTorchベースのマルチタスク学習モデル
- **主要機能**:
  - `train()`: 順位予測とタイム予測を同時に学習
  - `predict()`: 予測実行
- **使用場面**: 深層学習モデルを使用したい場合

### 評価

#### `evaluator.py`
- **役割**: モデル評価用のユーティリティ
- **主要機能**:
  - `calculate_ndcg()`: NDCG（Normalized Discounted Cumulative Gain）を計算
  - `evaluate_model()`: モデル評価を実行
    - NDCG@1, @2, @3
    - 1着的中率、トップ3的中率
    - 平均順位誤差
    - 単勝回収率（オッズデータがある場合）
  - `print_evaluation_results()`: 評価結果を整形して表示
- **使用場面**: モデルの性能評価

## 🔄 データ分析の流れ

### 1. データ読み込みフェーズ

```
data_loader.py
  ↓
NPZファイルからデータを読み込み
  ↓
cache_loader.py
  ↓
生データをキャッシュに保存（初回のみ）
```

**役割**:
- `data_loader.py`: NPZファイルから生データを読み込み
- `cache_loader.py`: 読み込んだ生データをキャッシュに保存（次回以降はキャッシュから読み込み）

### 2. 前処理フェーズ

```
preprocessor.py
  ├─ load_and_combine_data() → data_loader.pyを使用
  ├─ combine_data_types() → feature_converter.pyを使用（race_key生成）
  ├─ extract_previous_race_data() → 前走データ抽出
  ├─ add_statistical_features() → 統計特徴量計算
  ├─ convert_to_numeric() → 数値変換
  ├─ label_encode() → ラベルエンコーディング
  └─ process() → 一括実行
```

**役割**:
- `preprocessor.py`: 前処理のオーケストレーション
- `feature_converter.py`: race_key生成などの変換処理
- `cache_loader.py`: 生データの取得（前走データ抽出や統計特徴量計算で使用）

### 3. データ分割フェーズ

```
preprocessor.py
  └─ split() → 学習・検証データに分割（レース単位で時系列分割）
```

**役割**:
- `preprocessor.py`: 時系列を考慮したデータ分割

### 4. モデル学習フェーズ

```
rank_predictor.py / lambdamart_predictor.py / complementary_predictor.py / pytorch_multitask_predictor.py
  ├─ features.py → 特徴量定義を参照
  ├─ train() → モデル学習
  └─ ハイパーパラメータ最適化（Optuna）
```

**役割**:
- 各`*_predictor.py`: モデル学習
- `features.py`: 使用する特徴量の定義

### 5. 予測フェーズ

```
rank_predictor.py / lambdamart_predictor.py / complementary_predictor.py / pytorch_multitask_predictor.py
  └─ predict() → 予測実行
```

**役割**:
- 各`*_predictor.py`: 予測実行

### 6. 評価フェーズ

```
cache_loader.py
  └─ get_evaluation_data() → 評価用データ（着順・タイム・オッズ）を取得
      ↓
cache_loader.py
  └─ merge_evaluation_data() → 予測結果に評価用データをマージ
      ↓
evaluator.py
  └─ evaluate_model() → モデル評価
      ├─ NDCG計算
      ├─ 的中率計算
      ├─ 順位誤差計算
      └─ 回収率計算（オッズデータがある場合）
```

**役割**:
- `cache_loader.py`: 評価用データの取得とマージ
- `evaluator.py`: 評価指標の計算

## 📊 データフロー図

```
[NPZファイル]
    ↓
[data_loader.py] → データ読み込み
    ↓
[cache_loader.py] → 生データをキャッシュに保存
    ↓
[preprocessor.py] → 前処理
    ├─ [feature_converter.py] → race_key生成など
    └─ [cache_loader.py] → 生データ取得（前走データ抽出など）
    ↓
[前処理済みデータ]
    ↓
[preprocessor.split()] → 学習・検証データに分割
    ↓
[rank_predictor.py等] → モデル学習
    ├─ [features.py] → 特徴量定義
    └─ [evaluator.py] → 評価（学習中）
    ↓
[学習済みモデル]
    ↓
[rank_predictor.py等.predict()] → 予測実行
    ↓
[cache_loader.merge_evaluation_data()] → 評価用データをマージ
    ↓
[evaluator.py] → 最終評価
```

## 🔑 重要な設計思想

### 1. キャッシュによる高速化
- 生データと前処理済みデータをキャッシュに保存
- 次回以降はキャッシュから読み込み（処理時間の大幅短縮）

### 2. 統一されたインターフェース
- `cache_loader.py`により、キャッシュの有無に関わらず同じインターフェースでデータを扱える
- `get_raw_data()`, `get_evaluation_data()`, `merge_evaluation_data()`で統一

### 3. 評価用データの分離
- 予測には使用しないが、評価に必要なデータ（着順・タイム・オッズ）を別途保持
- 予測時には未来の情報が混入しないよう設計

### 4. 時系列を考慮したデータ分割
- レース単位で時系列分割（過去のレースで学習、未来のレースで検証）
- データリークを防止

## 📊 学習時と予想時のデータ結合方法

### 学習時（モデル作成時）

学習時は、**過去のレースデータ**を使用してモデルを学習します。以下のデータタイプを組み合わせて使用します：

#### 必須データ
- **KYI**: 競走馬データ（前日情報系）
  - 各馬の状態、IDM、各種指数を格納
  - レースキーで他のデータと結合
- **BAC**: 番組データ（前日情報系）
  - レース情報（距離、コース、条件など）
  - レースキーで他のデータと結合
- **SED**: 成績データ（成績系）
  - **正解データとして使用**（着順、タイム、オッズ）
  - レースキー+馬番で結合
  - 前走データ抽出や統計特徴量計算にも使用

#### 推奨データ
- **UKC**: 馬基本データ（前日情報系）
  - 血統登録番号で結合
  - 馬の基本情報（性別、毛色など）
- **TYB**: 直前情報データ（直前情報系）
  - 発走15分前の情報（オッズ、パドック情報など）
  - レースキー+馬番で結合
- **ZED/ZEC**: 前走データ（前日情報系）
  - 過去5走の成績データ
  - 競走成績キーで結合
  - 前走データ抽出で使用（SEDからも抽出可能）

#### オプションデータ
- **OZ/OW/OU/OT/OV**: 基準オッズデータ（前日情報系）
  - レースキーで結合
  - オッズ情報（予測には使用せず、評価用）
- **JOA**: 情報データ（前日情報系）
  - レースキー+馬番で結合
  - 詳細情報
- **KKA**: 競走馬拡張データ（前日情報系）
  - レースキー+馬番で結合
  - 各種集計データ
- **CYB/CYA**: 調教分析データ（前日情報系）
  - レースキー+馬番で結合
  - 調教分析情報
- **CHA**: 調教本追切データ（前日情報系）
  - レースキー+馬番で結合
  - 本追切情報
- **KZA/CZA**: 騎手・調教師マスタ（マスタ系）
  - 騎手コード・調教師コードで結合
  - マスタ情報（統計特徴量計算には使用しない）

#### データ結合の流れ（学習時）
```
KYI（競走馬データ）[中心]
  ├─[レースキー]→ BAC（番組データ）
  ├─[レースキー+馬番]→ SED（成績データ）← 正解データ
  ├─[血統登録番号]→ UKC（馬基本データ）
  ├─[レースキー+馬番]→ TYB（直前情報データ）
  ├─[競走成績キー]→ ZED/ZEC（前走データ）
  └─[騎手コード/調教師コード]→ KZA/CZA（マスタデータ）
```

#### 特徴量の定義
- **`features.py`**で定義された特徴量を使用
- オッズ関連フィールド（`確定単勝オッズ`など）は**予測には使用せず、評価用に別途保持**
- JRDBの事前予想データ（`テン指数`、`ペース指数`など）も除外

### 予想時（実際の予測時）

予想時は、**未来のレース**を予測するため、**レース結果（SED）は使用できません**。以下のデータタイプを組み合わせて使用します：

#### 必須データ
- **KYI**: 競走馬データ（前日情報系）
  - 各馬の状態、IDM、各種指数
  - レースキーで他のデータと結合
- **BAC**: 番組データ（前日情報系）
  - レース情報（距離、コース、条件など）
  - レースキーで他のデータと結合

#### 推奨データ
- **UKC**: 馬基本データ（前日情報系）
  - 血統登録番号で結合
  - 馬の基本情報
- **TYB**: 直前情報データ（直前情報系）
  - 発走15分前の情報（オッズ、パドック情報など）
  - レースキー+馬番で結合
- **ZED/ZEC**: 前走データ（前日情報系）
  - 過去5走の成績データ
  - 競走成績キーで結合
  - **注意**: 予想対象レースより前のレースのデータのみ使用

#### オプションデータ
- **OZ/OW/OU/OT/OV**: 基準オッズデータ（前日情報系）
  - レースキーで結合
  - オッズ情報（予測には使用せず、参考用）
- **JOA**: 情報データ（前日情報系）
  - レースキー+馬番で結合
- **KKA**: 競走馬拡張データ（前日情報系）
  - レースキー+馬番で結合
- **CYB/CYA**: 調教分析データ（前日情報系）
  - レースキー+馬番で結合
- **CHA**: 調教本追切データ（前日情報系）
  - レースキー+馬番で結合
- **KZA/CZA**: 騎手・調教師マスタ（マスタ系）
  - 騎手コード・調教師コードで結合
  - マスタ情報（統計特徴量計算には使用しない）

#### データ結合の流れ（予想時）
```
KYI（競走馬データ）[中心]
  ├─[レースキー]→ BAC（番組データ）
  ├─[血統登録番号]→ UKC（馬基本データ）
  ├─[レースキー+馬番]→ TYB（直前情報データ）
  ├─[競走成績キー]→ ZED/ZEC（前走データ）
  └─[騎手コード/調教師コード]→ KZA/CZA（マスタデータ）

※ SED（成績データ）は使用しない（レース結果が未確定のため）
```

#### 特徴量の定義
- **`features.py`**で定義された特徴量を使用（学習時と同じ）
- オッズ関連フィールドは除外（予測には使用しない）
- JRDBの事前予想データも除外

### 重要な注意事項

1. **未来の情報の混入防止**
   - 予想時は、レース結果（SED）を使用しない
   - 統計特徴量計算時は、`shift(1)`で未来の情報を除外
   - マスターデータ（KZA, CZA）の「本年」統計は使用しない

2. **時系列の考慮**
   - 前走データ（ZED/ZEC）は、予想対象レースより前のレースのみ使用
   - 統計特徴量は、その時点までの過去データのみを使用

3. **データの整合性**
   - 学習時と予想時で同じ特徴量定義（`features.py`）を使用
   - データ結合方法も同じ（レースキー、血統登録番号、競走成績キーなど）

## 📝 使用例

### 学習時の例

```python
from src.preprocessor import Preprocessor
from src.rank_predictor import RankPredictor

# 1. データ読み込みと前処理（学習時）
preprocessor = Preprocessor()
# SEDを含む（正解データとして使用）
df = preprocessor.process(
    base_path="./data",
    data_types=['BAC', 'KYI', 'SED', 'UKC', 'TYB'],  # SEDを含む
    years=[2024],
    use_cache=True
)

# 2. データ分割
train_df, val_df = preprocessor.split(df, train_ratio=0.8)

# 3. モデル学習
rank_predictor = RankPredictor(train_df, val_df)
model = rank_predictor.train()

# 4. 予測と評価
predictions = RankPredictor.predict(model, val_df, rank_predictor.features)
predictions_with_eval = preprocessor.merge_evaluation_data(predictions)
RankPredictor.print_evaluation(predictions_with_eval, odds_col='確定単勝オッズ')
```

### 予想時の例

```python
from src.preprocessor import Preprocessor
from src.rank_predictor import RankPredictor

# 1. データ読み込みと前処理（予想時）
preprocessor = Preprocessor()
# SEDを含まない（レース結果が未確定のため）
df = preprocessor.process(
    base_path="./data",
    data_types=['BAC', 'KYI', 'UKC', 'TYB'],  # SEDを含まない
    years=[2024],
    use_cache=True
)

# 2. 予測実行（学習済みモデルを使用）
# 注意: 学習時と同じ特徴量定義（features.py）を使用
predictions = RankPredictor.predict(model, df, rank_predictor.features)

# 3. 予測結果の表示
print(predictions[['race_key', '馬番', 'predict']].sort_values(['race_key', 'predict'], ascending=[True, False]))
```

## 🎯 依存関係

- `data_loader.py`, `feature_converter.py`, `features.py`, `evaluator.py`: 独立モジュール
- `cache_loader.py` → `feature_converter.py`
- `preprocessor.py` → `data_loader.py`, `feature_converter.py`, `cache_loader.py`
- `rank_predictor.py`等 → `features.py`, `evaluator.py`

## 📌 注意事項

1. **未来の情報の混入防止**: マスターデータ（KZA, CZA）の「本年」統計は使用しない
2. **時系列の考慮**: 統計特徴量は`shift(1)`で未来の情報を除外
3. **キャッシュの管理**: データを変更した場合はキャッシュをクリアするか、`use_cache=False`で実行
4. **メモリ使用量**: 大量のデータを扱う場合は、年度ごとに処理を分割

