# 統合特徴量抽出仕様書

## 概要

馬ごとにgroupbyし、1回の時系列フィルタリングで前走データ・統計量・直近レースを同時に計算する統合的な特徴量抽出方式。

## 全体データフロー（学習・予測・評価まで含む）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 【フェーズ1: データ前処理】                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────────────────────────────┐
    │ ① キャッシュ読み込み試行                                   │
    │    cache_manager.load()                                    │
    └───────────────────────────────────────────────────────────┘
                    ↓
        ┌───────────────┐
        │ キャッシュ存在?│
        └───────────────┘
            │         │
         YES│         │NO
            │         │
            ↓         ↓
    [キャッシュ返却]  [データ読み込み・結合]
    [処理終了]        raw_df (日本語キー)
                            ↓
                    [start_datetime追加]
                    df_with_datetime
                            ↓
                    [SEDデータから統計量計算用カラム抽出]
                    stats_df
                            ↓
    ┌───────────────────────────────────────────────────────────┐
    │ ② 統合特徴量抽出（1回のgroupbyで全特徴量計算）            │
    │                                                           │
    │ 馬ごとにgroupby → start_datetimeより前をフィルタ         │
    │   → 前走データ（過去5走）+ 馬の統計量を同時計算          │
    │                                                           │
    │ 騎手ごとにgroupby → start_datetimeより前をフィルタ       │
    │   → 騎手の統計量 + 直近3レース詳細を同時計算             │
    │                                                           │
    │ 調教師ごとにgroupby → start_datetimeより前をフィルタ     │
    │   → 調教師の統計量 + 直近3レース詳細を同時計算           │
    └───────────────────────────────────────────────────────────┘
                            ↓
                    featured_df (日本語キー、全特徴量結合済み)
                            ↓
                    [キャッシュ保存: featured_df] ← 特徴量抽出結果を保存
                            ↓
                    ┌───────────────────────────────────────────────────────────┐
                    │ ③ データ変換                                             │
                    │   数値化 → ラベルエンコーディング → データ型最適化        │
                    └───────────────────────────────────────────────────────────┘
                            ↓
                    converted_df (英語キー、数値化済み、最適化済み)
                            ↓
                    [キャッシュ保存: converted_df] ← 変換済みデータを保存
                            ↓
                    ┌───────────────────────┐
                    │ split_date指定の有無?   │
                    └───────────────────────┘
                        │              │
                    未指定│              │指定
                        │              │
                        ↓              ↓
            [キャッシュ保存]    [時系列分割]
            (converted_df)     train_df / test_df
                        │              │
            [処理終了]   │              │
                        │              ↓
                        │      [カラム選択（学習用のみ）]
                        │      train_df / test_df
                        │              │
                        │              ↓
                        │      [eval_df準備（評価用カラム）]
                        │      eval_df
                        │              │
                        │              ↓
                        │      [キャッシュ保存]
                        │      (train_df, test_df, eval_df)
                        │              │
                        └──────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 【フェーズ2: モデル学習】                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                ↓
                    ┌───────────────────────────┐
                    │ ④ 特徴量強化               │
                    │ レース内相対特徴量追加     │
                    │ インタラクション特徴量追加  │
                    └───────────────────────────┘
                                ↓
                    train_df_enhanced / val_df_enhanced
                                ↓
                    ┌───────────────────────────┐
                    │ ⑤ モデル学習               │
                    │ LightGBM LambdaRank        │
                    │ ハイパーパラメータチューニング│
                    └───────────────────────────┘
                                ↓
                    学習済みモデル (model)
                                ↓
                    [モデル保存]
                                ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 【フェーズ3: 予測】                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                ↓
                    test_df (検証用データ)
                                ↓
                    ┌───────────────────────────┐
                    │ ⑥ 特徴量強化               │
                    │ レース内相対特徴量追加     │
                    └───────────────────────────┘
                                ↓
                    test_df_enhanced
                                ↓
                    ┌───────────────────────────┐
                    │ ⑦ 予測実行                 │
                    │ model.predict()            │
                    └───────────────────────────┘
                                ↓
                    predictions (予測スコア)
                                ↓
                    ┌───────────────────────────┐
                    │ ⑧ 予測結果に評価用データ追加│
                    │ predictions + eval_df    │
                    │ (トレーニング時に使用していない│
                    │  カラムを後から追加)      │
                    └───────────────────────────┘
                                ↓
                    val_predictions
                    (予測スコア + 実際の着順 + オッズ等)
                                ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ 【フェーズ4: 評価】                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                ↓
                    ┌───────────────────────────┐
                    │ ⑨ 評価指標計算             │
                    │ - NDCG@1, NDCG@2, NDCG@3   │
                    │ - 的中率（1着、3着内）     │
                    │ - 順位誤差                 │
                    │ - 回収率（単勝、複勝）     │
                    │ - WIN5的中率               │
                    │   （同一日の5レース全的中）│
                    └───────────────────────────┘
                                ↓
                    evaluation_result
                                ↓
                    [評価結果表示]
                                ↓
                    [処理完了]
```

### キャッシュのタイミング

- **読み込み**: フェーズ1の最初（データ読み込み前）
- **保存（featured_df）**: 特徴量抽出後（データ変換前）
- **保存（converted_df）**: データ変換後
  - split_date未指定時: `converted_df`を`data`として保存
  - split_date指定時: `converted_df`を`converted`として保存（`train_df`, `test_df`, `eval_df`も保存）

### start_datetimeについて

`start_datetime`は、レースの開始日時を表す整数値です。

- **生成方法**:
  - `race_key`から日付部分（YYYYMMDD）を抽出し、`YYYYMMDD0000`形式の整数値に変換
  - または、`年月日`と`発走時間`から`YYYYMMDDHHMM`形式の整数値に生成
- **用途**:
  - 時系列フィルタリングで未来情報を除外するために使用
  - 各レースの`start_datetime`より前のデータのみを使用して特徴量を計算することで、データリークを防止

## 設計思想

### 問題点（旧方式）
- 同じデータ（SED）を4回読み込み
- 同じgroupbyと時系列フィルタリングを4回実行
- メモリの無駄（同じデータのコピーを複数作成）
- 処理時間の無駄（同じ計算を重複実行）

### 改善点（新方式）
- 1回のgroupbyと時系列フィルタリングで全ての特徴量を計算
- メモリ効率の向上（データのコピーを最小化）
- 処理時間の短縮（重複計算を排除）

## 処理フロー（詳細）

### 1. データ準備

```
入力:
  - df: 結合済みDataFrame（日本語キー、KYI+BAC+SED+TYB+UKC等）
  - sed_df: SEDデータ（過去の成績データ）
  - bac_df: BACデータ（オプション、race_key生成用）

処理:
  1. dfにstart_datetimeを追加
  2. sed_dfにrace_keyを追加（bac_dfから年月日を取得）
  3. stats_dfを準備（統計量計算用のカラムのみ抽出）
     - race_key, 馬番, 血統登録番号, 騎手コード, 調教師コード
     - 着順, タイム, 距離, 芝ダ障害コード, 馬場状態, 頭数, R
  4. 統計量用のフラグを追加
     - rank_1st: 着順 == 1
     - rank_3rd: 着順 in [1, 2, 3]
  5. stats_dfにstart_datetimeを追加

出力:
  - df_with_datetime: start_datetimeが追加されたDataFrame
  - stats_df: 統計量計算用のDataFrame
```

### 2. 馬ごとの特徴量抽出（統合処理）

```
処理単位: 血統登録番号ごとにgroupby

各馬のグループに対して:
  1. 時系列ソート（start_datetime昇順）
  2. 累積統計量を事前計算
     - horse_cumsum_1st: 1着回数の累積
     - horse_cumsum_3rd: 連対回数の累積
     - horse_cumsum_rank: 着順の累積
     - horse_cumcount: 出走回数の累積
  
  3. 各ターゲットレース（df_with_datetimeの各行）に対して:
     a. 時系列フィルタリング
        - 現在のレースのstart_datetimeより前のレースを取得
        - mask = group_stats["start_datetime"] < target_time
        - past_indices = np.where(mask)[0]
     
     b. 前走データ（過去5走）を抽出
        - prev_indices = past_indices[-5:] if len >= 5 else past_indices
        - 新しい順にソート（prev_indices[::-1]）
        - 各前走レースから以下を抽出:
          * prev_1_race_num ~ prev_5_race_num: R
          * prev_1_num_horses ~ prev_5_num_horses: 頭数
          * prev_1_frame ~ prev_5_frame: 枠番
          * prev_1_horse_number ~ prev_5_horse_number: 馬番
          * prev_1_rank ~ prev_5_rank: 着順
          * prev_1_time ~ prev_5_time: タイム
          * prev_1_distance ~ prev_5_distance: 距離
          * prev_1_course_type ~ prev_5_course_type: 芝ダ障害コード
          * prev_1_ground_condition ~ prev_5_ground_condition: 馬場状態
          * prev_1_race_key ~ prev_5_race_key: レースキー（リーク検証用）
     
     c. 馬の統計量を計算
        - 最後の過去レースの累積統計量から取得
        - 馬勝率 = cumsum_1st / cumcount
        - 馬連対率 = cumsum_3rd / cumcount
        - 馬平均着順 = cumsum_rank / cumcount
        - 馬出走回数 = cumcount

出力:
  - 前走データ（prev_1_* ~ prev_5_*）
  - 馬の統計量（馬勝率、馬連対率、馬平均着順、馬出走回数）
```

### 3. 騎手ごとの特徴量抽出（統合処理）

```
処理単位: 騎手コードごとにgroupby

各騎手のグループに対して:
  1. 時系列ソート（start_datetime昇順）
  2. 累積統計量を事前計算
     - jockey_cumsum_1st: 1着回数の累積
     - jockey_cumsum_3rd: 連対回数の累積
     - jockey_cumsum_rank: 着順の累積
     - jockey_cumcount: 出走回数の累積
  
  3. 各ターゲットレースに対して:
     a. 時系列フィルタリング
        - 現在のレースのstart_datetimeより前のレースを取得
        - past_indices = np.where(group_stats["start_datetime"] < target_time)[0]
     
     b. 騎手の統計量を計算
        - 最後の過去レースの累積統計量から取得
        - 騎手勝率 = cumsum_1st / cumcount
        - 騎手連対率 = cumsum_3rd / cumcount
        - 騎手平均着順 = cumsum_rank / cumcount
        - 騎手出走回数 = cumcount
     
     c. 騎手の直近3レースを抽出
        - recent_indices = past_indices[-3:] if len >= 3 else past_indices
        - 新しい順にソート（recent_indices[::-1]）
        - 各直近レースから以下を抽出:
          * 騎手直近1着順 ~ 騎手直近3着順: 着順
          * 騎手直近1タイム ~ 騎手直近3タイム: タイム
          * 騎手直近1距離 ~ 騎手直近3距離: 距離
          * 騎手直近1芝ダ障害コード ~ 騎手直近3芝ダ障害コード: 芝ダ障害コード
          * 騎手直近1馬場状態 ~ 騎手直近3馬場状態: 馬場状態
          * 騎手直近1頭数 ~ 騎手直近3頭数: 頭数
          * 騎手直近1R ~ 騎手直近3R: R
          * 騎手直近1race_key ~ 騎手直近3race_key: レースキー（リーク検証用）

出力:
  - 騎手の統計量（騎手勝率、騎手連対率、騎手平均着順、騎手出走回数）
  - 騎手の直近3レース詳細（騎手直近1* ~ 騎手直近3*）
```

### 4. 調教師ごとの特徴量抽出（統合処理）

```
処理単位: 調教師コードごとにgroupby

各調教師のグループに対して:
  1. 時系列ソート（start_datetime昇順）
  2. 累積統計量を事前計算
     - trainer_cumsum_1st: 1着回数の累積
     - trainer_cumsum_3rd: 連対回数の累積
     - trainer_cumsum_rank: 着順の累積
     - trainer_cumcount: 出走回数の累積
  
  3. 各ターゲットレースに対して:
     a. 時系列フィルタリング
        - 現在のレースのstart_datetimeより前のレースを取得
        - past_indices = np.where(group_stats["start_datetime"] < target_time)[0]
     
     b. 調教師の統計量を計算
        - 最後の過去レースの累積統計量から取得
        - 調教師勝率 = cumsum_1st / cumcount
        - 調教師連対率 = cumsum_3rd / cumcount
        - 調教師平均着順 = cumsum_rank / cumcount
        - 調教師出走回数 = cumcount
     
     c. 調教師の直近3レースを抽出
        - recent_indices = past_indices[-3:] if len >= 3 else past_indices
        - 新しい順にソート（recent_indices[::-1]）
        - 各直近レースから以下を抽出:
          * 調教師直近1着順 ~ 調教師直近3着順: 着順
          * 調教師直近1タイム ~ 調教師直近3タイム: タイム
          * 調教師直近1距離 ~ 調教師直近3距離: 距離
          * 調教師直近1芝ダ障害コード ~ 調教師直近3芝ダ障害コード: 芝ダ障害コード
          * 調教師直近1馬場状態 ~ 調教師直近3馬場状態: 馬場状態
          * 調教師直近1頭数 ~ 調教師直近3頭数: 頭数
          * 調教師直近1R ~ 調教師直近3R: R
          * 調教師直近1race_key ~ 調教師直近3race_key: レースキー（リーク検証用）

出力:
  - 調教師の統計量（調教師勝率、調教師連対率、調教師平均着順、調教師出走回数）
  - 調教師の直近3レース詳細（調教師直近1* ~ 調教師直近3*）
```


## 学習プロセス

### 1. データ準備

```
入力:
  - train_df: 学習用DataFrame（英語キー、学習用カラムのみ）
  - val_df: 検証用DataFrame（英語キー、学習用カラムのみ）

処理:
  1. 特徴量強化（レース内相対特徴量とインタラクション特徴量を追加）
     - enhance_features(train_df, race_key_col="race_key")
     - enhance_features(val_df, race_key_col="race_key")
  
  2. RankPredictorのインスタンス作成
     - rank_predictor = RankPredictor(train_df, val_df)
     - features = rank_predictor.features

出力:
  - train_df_enhanced: 特徴量強化済み学習用DataFrame
  - val_df_enhanced: 特徴量強化済み検証用DataFrame
```

### 2. モデル学習

```
処理:
  1. LightGBMデータセットの作成
     - lgb_train = rank_predictor.lgb_train
     - lgb_val = rank_predictor.lgb_val
  
  2. ハイパーパラメータチューニング（Optuna）
     - optunaLgb.train()で最適パラメータを探索
  
  3. モデル学習
     - lgb.train()でLambdaRankモデルを学習

出力:
  - model: 学習済みLightGBMモデル
```

### 3. モデル保存

```
処理:
  - model.save_model(str(MODEL_PATH))

出力:
  - MODEL_PATH: 学習済みモデルファイル（.txt形式）
```

## 予測プロセス

### 1. 予測データ準備

```
入力:
  - test_df: 検証用DataFrame（英語キー、学習用カラムのみ）
  - eval_df: 評価用DataFrame（日本語キー、全カラム）

処理:
  1. 特徴量強化
     - test_df_enhanced = enhance_features(test_df, race_key_col="race_key")
  
  2. 予測実行
     - predictions = RankPredictor.predict(model, test_df_enhanced, features)

出力:
  - predictions: 予測結果（DataFrame）
    - race_key: レースキー（文字列）
    - predicted_score: 予測スコア（浮動小数点数、小数点第2位まで丸め）
```

### 2. 予測結果に評価用情報を追加

```
処理:
  1. 馬番の取得
     - test_dfにhorse_number（英語キー）が含まれている場合はそれを使用
     - 含まれていない場合はeval_dfから馬番（日本語キー）を取得
  
  2. 評価用列の決定
     - **重要**: トレーニング時に使用していないカラム（オッズなど）は、予測結果に後から追加する必要がある
     - デフォルト: 評価に必要な最小限の列を自動的に追加
       - 必須: race_key, 馬番, 着順
       - オプション（存在する場合）: WIN5フラグ, 確定単勝オッズ
     - カスタマイズ: eval_colsパラメータで追加の列を指定可能
       - 例: ["タイム", "着差", "賞金", "確定複勝オッズ"]など
  
  3. 予測結果に評価用情報を追加
     - 予測結果（predictions）をベースに
     - eval_dfから指定された列のみを追加（race_keyと馬番でマージ）
     - **注意**: eval_dfは`featured_df`（日本語キー、全カラム）から作成されるため、
       トレーニング時に使用していないカラム（オッズ、WIN5フラグなど）も含まれる
  
  4. 予測順位の追加
     - レースごとにpredicted_scoreでソートして順位を付与
     - predicted_rank: 予測順位（1から開始）
  
  5. rank列の追加（評価用）
     - rank = pd.to_numeric(着順, errors="coerce")

出力:
  - val_predictions: 予測結果と評価用情報が結合されたDataFrame
  
  **予測結果フィールド（必須）**:
    - race_key: レースキー（文字列）
    - 馬番: 馬番（整数）
    - predicted_score: 予測スコア（浮動小数点数、小数点第2位まで丸め）
    - predicted_rank: 予測順位（整数、レース内での順位）
  
  **評価用フィールド（最小限）**:
    - 着順: 実際の着順（整数）
    - rank: 実際の着順（浮動小数点数、評価用、着順から生成）
    - WIN5フラグ: WIN5対象レースのフラグ（1～5、オプション、WIN5評価用）
    - 確定単勝オッズ: 確定単勝オッズ（浮動小数点数、オプション、回収率計算用）
  
  **注意**: 元データ全体は含まれません。評価に必要な最小限の情報のみを追加します。

### 予測結果に含めるデータの設定方法

予測結果に含める評価用データは、**評価用スキーマ（`evaluation_schema.json`）**に基づいて定義されます。

**評価用スキーマ**:
- ファイル: `packages/data/schemas/jrdb_processed/evaluation_schema.json`
- 評価に必要なカラムを定義（必須カラム、オプションカラム、評価指標ごとの必要カラム）

**重要な前提**:
- **トレーニング時に使用していないカラム**（オッズ、WIN5フラグなど）は、予測結果に後から追加する必要がある
- これらは`use_for_training: false`として定義されており、学習用データ（`train_df`, `test_df`）には含まれない
- `eval_df`は`featured_df`（日本語キー、全カラム）から作成されるため、トレーニング時に使用していないカラムも含まれる

**使用方法**:

1. **デフォルト（評価に必要な最小限）**:
```python
from apps.prediction.src.data_processer.column_selector import ColumnSelector

selector = ColumnSelector(base_path)
eval_df = selector.select_evaluation(featured_df, include_optional=False)
# 必須カラムのみ: race_key, 馬番, 着順
```

2. **オプションカラムを含める**:
```python
eval_df = selector.select_evaluation(featured_df, include_optional=True)
# 必須カラム + オプションカラム（WIN5フラグ、確定単勝オッズなど）
```

3. **評価指標に基づいてカラムを選択**:
```python
# 特定の評価指標に必要なカラムのみを選択
metrics = ["ndcg", "hit_rate", "return_rate_single", "win5_accuracy"]
eval_df = selector.select_evaluation(featured_df, metrics=metrics)
```

4. **手動でカラムを指定**（従来の方法、後方互換性のため）:
```python
eval_cols = ["race_key", "馬番", "着順"]
if "WIN5フラグ" in original_eval.columns:
    eval_cols.append("WIN5フラグ")
if "確定単勝オッズ" in original_eval.columns:
    eval_cols.append("確定単勝オッズ")
eval_df = original_eval[eval_cols].copy()
```

**評価用スキーマの構造**:
- **マージキー**: `race_key`, `馬番`（必須）
- **必須カラム**: `着順`（評価指標計算に必須）
- **オプションカラム**: `WIN5フラグ`, `確定単勝オッズ`, `確定複勝オッズ`, `確定3連複オッズ`, `タイム`, `着差`, `本賞金`など
- **評価指標マッピング**: 各評価指標に必要なカラムを定義

**利用可能な列**:
- `evaluation_schema.json`で定義された全カラム（日本語キー）
- **トレーニング時に使用していないカラムも含まれる**:
  - オッズ関連: 確定単勝オッズ、確定複勝オッズ、確定3連複オッズなど
  - WIN5フラグ: WIN5対象レースのフラグ
  - その他: タイム、着差、本賞金、確定単勝人気順位、異常区分など

**注意**: 
- `race_key`と`馬番`はマージキーとして必須
- 存在しない列を指定した場合は無視される
- 評価に必要な列（着順、WIN5フラグ、確定単勝オッズ）は自動的に追加される
- トレーニング時に使用していないカラムは、`eval_df`から取得して追加する必要がある
```

## スキーマとデータの状態管理

### スキーマファイル一覧

| スキーマファイル | 用途 | キー形式 | カラム数 | 備考 |
|----------------|------|---------|---------|------|
| `full_info_schema.json` | 全カラム定義（結合・変換・特徴量定義） | 日本語キー + 英語キー（feature_name） | 359 | 結合キー、数値化、ラベルエンコーディングに使用 |
| `training_schema.json` | 学習用カラム定義 | 英語キー | 141 | 学習時に使用する特徴量のみ定義 |
| `evaluation_schema.json` | 評価用カラム定義 | 日本語キー | 12 | 評価時に使用するカラムのみ定義 |

### 各処理段階でのスキーマ適用状態

| 処理段階 | データ名 | キー形式 | データ型 | 適用スキーマ | スキーマ適用範囲 | 含まれるカラム |
|---------|---------|---------|---------|------------|----------------|--------------|
| **① データ読み込み** | `data_dict` | 日本語キー（各データタイプ別） | 元データ型 | `full_info_schema.json` | 結合キー定義のみ | KYI, BAC, SED, TYB, UKCの各カラム |
| **② データ結合** | `raw_df` | 日本語キー | 元データ型 | `full_info_schema.json` | 結合キー定義のみ | KYIベース + 他データタイプ（サフィックス付き） |
| **③ start_datetime追加** | `df_with_datetime` | 日本語キー | 元データ型 + `start_datetime` | `full_info_schema.json` | 結合キー定義のみ | `raw_df` + `start_datetime` |
| **④ 特徴量抽出** | `featured_df` | 日本語キー | 元データ型 + 計算済み特徴量 | `full_info_schema.json` | カラム定義の一部（前走データ・統計量は計算済み） | `df_with_datetime` + 前走データ（`prev_1_*` ~ `prev_5_*`） + 馬統計量 + 騎手統計量 + 調教師統計量 |
| **⑤ データ変換** | `converted_df` | 英語キー | 数値型（最適化済み） | `full_info_schema.json` | `feature_name`定義のみ | `featured_df`の全カラムを英語キーに変換、数値化、最適化 |
| **⑥ 時系列分割** | `train_df`, `test_df` | 英語キー | 数値型（最適化済み） | `full_info_schema.json` | 全カラム（分割のみ） | `converted_df`を時系列で分割 |
| **⑦ 学習用カラム選択** | `train_df`, `test_df` | 英語キー | 数値型（最適化済み） | `training_schema.json` | スキーマ全体 | `use_for_training: true`のカラムのみ（141カラム） |
| **⑧ 評価用カラム選択** | `eval_df` | 日本語キー | 元データ型 | `evaluation_schema.json` | スキーマ全体 | 評価用カラムのみ（12カラム、オプション含む） |

### スキーマ適用の詳細

#### ① データ読み込み段階
- **適用スキーマ**: `full_info_schema.json`（結合キー定義のみ）
- **使用箇所**: `JrdbCombiner.combine()`
- **適用範囲**: `joinKeys`セクションのみ
  - KYI: `["race_key", "馬番"]`
  - BAC: `["race_key"]`
  - SED: `["race_key", "馬番"]`（`use_bac_date: true`）
  - UKC: `["血統登録番号"]`
  - TYB: `["race_key", "馬番"]`（`use_bac_date: true`）
- **データ状態**: 各データタイプ別のDataFrame（日本語キー、元データ型）

#### ② データ結合段階
- **適用スキーマ**: `full_info_schema.json`（結合キー定義のみ）
- **使用箇所**: `JrdbCombiner.combine()`
- **適用範囲**: `joinKeys`セクション + `baseDataType`（デフォルト: "KYI"）
- **データ状態**: `raw_df`（日本語キー、KYIベース、他データタイプはサフィックス付きで結合）
- **サフィックス規則**: base_type（KYI）はなし、他は`_{data_type}`（例: `_BAC`, `_SED`）

#### ③ start_datetime追加段階
- **適用スキーマ**: `full_info_schema.json`（カラム定義の一部）
- **使用箇所**: `FeatureConverter.add_start_datetime_to_df()`
- **適用範囲**: `年月日`, `発走時間`, `race_key`カラムの定義
- **データ状態**: `df_with_datetime`（日本語キー、`start_datetime`カラム追加）

#### ④ 特徴量抽出段階
- **適用スキーマ**: `full_info_schema.json`（カラム定義の一部）
- **使用箇所**: `unified_feature_extractor.extract_all_features_unified()`
- **適用範囲**: 
  - 前走データ: 計算済み（スキーマには定義されていないが、`prev_1_*` ~ `prev_5_*`形式で追加）
  - 馬統計量: 計算済み（`馬勝率`, `馬連対率`, `馬平均着順`, `馬出走回数`）
  - 騎手統計量: 計算済み（`騎手勝率`, `騎手連対率`, `騎手平均着順`, `騎手出走回数`, `騎手直近1_*` ~ `騎手直近3_*`）
  - 調教師統計量: 計算済み（`調教師勝率`, `調教師連対率`, `調教師平均着順`, `調教師出走回数`, `調教師直近1_*` ~ `調教師直近3_*`）
- **データ状態**: `featured_df`（日本語キー、全特徴量結合済み）
- **注意**: 計算済み特徴量はスキーマに定義されていないが、`full_info_schema.json`の`computed`ソースとして扱われる

#### ⑤ データ変換段階
- **適用スキーマ**: `full_info_schema.json`（`feature_name`定義のみ）
- **使用箇所**: 
  - `NumericConverter.convert_to_numeric()`: 数値化
  - `LabelEncoder.encode()`: ラベルエンコーディング（`training_schema.json`も参照）
  - `DtypeOptimizer.optimize()`: データ型最適化（`training_schema.json`も参照）
- **適用範囲**: 
  - 日本語キー → 英語キー変換: `feature_name`を使用
  - 数値化: `type`定義を使用
  - ラベルエンコーディング: `training_schema.json`の`category_mapping_name`を使用
- **データ状態**: `converted_df`（英語キー、数値型、最適化済み）

#### ⑥ 時系列分割段階
- **適用スキーマ**: `full_info_schema.json`（全カラム、分割のみ）
- **使用箇所**: `TimeSeriesSplitter.split()`
- **適用範囲**: 全カラム（分割のみ、カラム選択なし）
- **データ状態**: `train_df`, `test_df`（英語キー、数値型、最適化済み、全カラム）

#### ⑦ 学習用カラム選択段階
- **適用スキーマ**: `training_schema.json`（スキーマ全体）
- **使用箇所**: `ColumnSelector.select_training()`
- **適用範囲**: スキーマ全体（141カラム）
- **データ状態**: `train_df`, `test_df`（英語キー、数値型、最適化済み、学習用カラムのみ）
- **選択基準**: `training_schema.json`で定義されたカラム名（英語キー）のみ

#### ⑧ 評価用カラム選択段階
- **適用スキーマ**: `evaluation_schema.json`（スキーマ全体）
- **使用箇所**: `ColumnSelector.select_evaluation()`
- **適用範囲**: スキーマ全体（12カラム、オプション含む）
- **データ状態**: `eval_df`（日本語キー、元データ型、評価用カラムのみ）
- **選択基準**: `evaluation_schema.json`で定義されたカラム名（日本語キー）のみ
- **注意**: `featured_df`（日本語キー）から選択するため、トレーニング時に使用していないカラム（オッズなど）も含まれる

### スキーマ名とデータ名の対応

| データ名 | スキーマ名 | 対応関係 | 備考 |
|---------|-----------|---------|------|
| `raw_df` | `full_info_schema.json` | 部分適用（結合キー定義のみ） | 結合時に使用 |
| `featured_df` | `full_info_schema.json` | 部分適用（カラム定義の一部） | 前走データ・統計量は計算済み |
| `converted_df` | `full_info_schema.json` | 部分適用（`feature_name`定義のみ） | 変換時に使用 |
| `train_df`, `test_df` | `training_schema.json` | 完全適用 | 学習時に使用 |
| `eval_df` | `evaluation_schema.json` | 完全適用 | 評価時に使用 |

### スキーマの部分適用の詳細

#### `full_info_schema.json`の部分適用

1. **結合段階**: `joinKeys`セクションのみ使用
   - 使用箇所: `JrdbCombiner.combine()`
   - 使用内容: 結合キー定義、`baseDataType`

2. **特徴量抽出段階**: カラム定義の一部を使用
   - 使用箇所: `unified_feature_extractor.extract_all_features_unified()`
   - 使用内容: 元データカラムの定義（前走データ・統計量は計算済み）

3. **データ変換段階**: `feature_name`定義のみ使用
   - 使用箇所: `NumericConverter.convert_to_numeric()`, `LabelEncoder.encode()`
   - 使用内容: 日本語キー → 英語キー変換、数値化、ラベルエンコーディング

#### `training_schema.json`の完全適用

- **使用箇所**: `ColumnSelector.select_training()`
- **使用内容**: スキーマ全体（141カラム）
- **適用条件**: `split_date`指定時のみ

#### `evaluation_schema.json`の完全適用

- **使用箇所**: `ColumnSelector.select_evaluation()`
- **使用内容**: スキーマ全体（12カラム、オプション含む）
- **適用条件**: `split_date`指定時のみ

## 評価プロセス

### 1. 評価指標の計算

```
入力:
  - val_predictions: 予測結果と評価用データが結合されたDataFrame

処理:
  1. NDCG計算
     - NDCG@1, NDCG@2, NDCG@3を計算
     - レースごとに予測スコアでソートし、実際の着順との一致度を評価
  
  2. 的中率計算
     - 1着的中率: 予測1位が実際に1着だった割合
     - 3着内的中率: 予測3着内が実際に3着内だった割合
  
  3. 順位誤差計算
     - 平均順位誤差: 予測順位と実際の順位の差の平均
     - 順位誤差の標準偏差
  
  4. 回収率計算（オッズデータがある場合）
     - 単勝回収率: 予測1位に賭けた場合の回収率
     - 複勝回収率: 予測3着内に賭けた場合の回収率
  
  5. WIN5評価（WIN5フラグデータがある場合）
     - WIN5的中率: 同一日のWIN5対象5レース（フラグ1～5）すべてで1着的中した日の割合
     - WIN5的中日数: WIN5的中した日数
     - WIN5評価対象日数: WIN5フラグ1～5が揃った日数
     - 評価方法: 同一日付内でWIN5フラグ1～5の5レースすべてが存在し、かつすべてのレースで予測1位が実際に1着だった場合を的中とする

出力:
  - evaluation_result: 評価結果（辞書形式）
    - ndcg_1, ndcg_2, ndcg_3
    - hit_rate_1st, hit_rate_3rd
    - mean_rank_error, std_rank_error
    - return_rate_single, return_rate_place（オッズデータがある場合）
    - win5_accuracy, win5_success_days, win5_total_days（WIN5フラグデータがある場合）
```

### 2. 評価結果の表示

```
処理:
  - print_evaluation_results(evaluation_result)

出力:
  - コンソールに評価結果を表示
    - NDCG@1, NDCG@2, NDCG@3
    - 1着的中率、3着内的中率
    - 平均順位誤差、順位誤差の標準偏差
    - 単勝回収率、複勝回収率（オッズデータがある場合）
```

## パフォーマンス最適化

### メモリ効率化

1. **累積統計量の事前計算**
   - groupby後に累積統計量を一度だけ計算
   - 各ターゲットレースでは累積値から直接取得

2. **データのコピーを最小化**
   - 必要なカラムのみを抽出
   - 不要なDataFrameは即座に削除

3. **ベクトル化処理**
   - numpy配列を使用した高速なフィルタリング
   - `np.searchsorted`を使用した時系列検索

### 処理時間の短縮

1. **1回のgroupbyとフィルタリング**
   - 同じデータに対して複数回のgroupbyを実行しない
   - 1回の時系列フィルタリングで全ての特徴量を計算

2. **並列処理の最適化**
   - 馬・騎手・調教師ごとの処理は独立しているため並列化可能
   - ただし、メモリ効率を考慮してシーケンシャル処理も選択可能

## データ整合性の保証

### 未来情報の除外

- **時系列フィルタリング**: 各レースの`start_datetime`より前のレースのみを使用
- **累積統計量**: 時系列順にソート後、累積値を計算することで未来情報を除外

### 重複カラムの防止

- **カラム名の一意性**: 各特徴量に一意のカラム名を付与
- **結合時の検証**: 重複カラムが検出された場合はエラーを投げる

### データ型の一貫性

- **数値型**: 統計量はfloat型、出走回数はint型
- **文字列型**: race_keyはobject型（文字列）

## エラーハンドリング

### 必須カラムの検証

- `血統登録番号`、`騎手コード`、`調教師コード`が存在しない場合は処理をスキップ
- `start_datetime`が存在しない場合はエラーを投げる

### データ不整合の検出

- 重複カラムが検出された場合はエラーを投げる（データ整合性を保つため）
- 予測結果と評価用データの行数が一致しない場合はエラーを投げる

## キャッシュ戦略

### キャッシュの保存（2段階キャッシュ）

1. **featured_df（特徴量抽出後）**
   - タイミング: 特徴量抽出完了後、データ変換前
   - 内容: 日本語キー、全特徴量結合済み
   - ファイル名: `{data_types}_{year}_{split_date}_featured.parquet`
   - メリット: 特徴量抽出は時間がかかるため、変換処理を変更しても再利用可能

2. **converted_df（データ変換後）**
   - タイミング: データ変換・最適化完了後
   - 内容: 英語キー、数値化済み、最適化済み
   - ファイル名: 
     - split_date未指定: `{data_types}_{year}_data.parquet`（後方互換性のため）
     - split_date指定: `{data_types}_{year}_{split_date}_converted.parquet`
   - メリット: 変換処理をスキップして直接使用可能

3. **train_df, test_df, eval_df（時系列分割後、split_date指定時のみ）**
   - タイミング: 時系列分割とカラム選択完了後
   - 内容: 学習用・検証用・評価用に分割済み
   - ファイル名: 
     - `{data_types}_{year}_{split_date}_train.parquet`
     - `{data_types}_{year}_{split_date}_test.parquet`
     - `{data_types}_{year}_{split_date}_eval.parquet`

### キャッシュの読み込み

- データタイプ、年度、分割日時が一致する場合はキャッシュから読み込み
- 優先順位: `train_df/test_df/eval_df` > `converted_df` > `featured_df`
- キャッシュが存在しない場合のみ特徴量抽出を実行

## 実装ファイル

- `unified_feature_extractor.py`: 統合特徴量抽出の実装
- `feature_extractor.py`: 既存の特徴量抽出（後方互換性のため保持）
- `main.py`: データ処理のオーケストレーター
- `rank_predictor.py`: ランキング学習モデル
- `evaluator.py`: 評価指標の計算

