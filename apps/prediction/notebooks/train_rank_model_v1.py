# %%
# JRDBデータを使用したランキング学習モデル（特徴量強化版）
# 
# 年度パックNPZファイルからデータを読み込み、LambdaRankモデルを学習します。
# レース内相対特徴量とインタラクション特徴量を追加して的中精度を向上させます。

# %%
# ## インポート
import sys
from pathlib import Path
import importlib
from datetime import datetime

# プロジェクトルート（apps/prediction/）をパスに追加
project_root = Path(__file__).resolve().parent.parent  # notebooks/ -> apps/prediction/
sys.path.insert(0, str(project_root))

print(f"実行開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# 既にインポート済みのモジュールを明示的にリロード（初回実行時）
submodules_to_reload = [
    'src.data_processer',
    'src.rank_predictor',
    'src.features',
    'src.evaluator',
    'src.feature_enhancers',
]

for module_name in submodules_to_reload:
    if module_name in sys.modules:
        importlib.reload(sys.modules[module_name])

import numpy as np
import pandas as pd
import lightgbm as lgb
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

# 日本語フォント設定（macOS用）
try:
    matplotlib.rcParams['font.family'] = 'Hiragino Sans'
except:
    try:
        matplotlib.rcParams['font.family'] = 'Arial Unicode MS'
    except:
        pass  # フォント設定に失敗した場合はデフォルトを使用

from src.data_processer import DataProcessor
from src.rank_predictor import RankPredictor
from src.features import Features
from src.feature_enhancers import enhance_features

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)

# %%
# ## 設定
# NPZファイルが格納されているベースパス
BASE_PATH = Path(__file__).parent / 'data'  # apps/prediction/notebooks/data

# 使用するデータタイプ
DATA_TYPES = [
    'BAC',  # 番組データ（レース条件・出走馬一覧）
    'KYI',  # 競走馬データ（牧場先情報付き・最も詳細）
    'SED',  # 成績速報データ（過去の成績・前走データ抽出に使用）
    'UKC',  # 馬基本データ（血統登録番号・性別・生年月日・血統情報）
    'TYB',  # 直前情報データ（出走直前の馬の状態・当日予想に最重要）
]

# 使用する年度
YEARS = [2024]

# モデル保存パス（日時ベース）
model_timestamp = datetime.now().strftime('%Y%m%d%H%M')
MODEL_PATH = Path(__file__).parent.parent / 'models' / f'rank_model_{model_timestamp}_v1.txt'
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

print(f"BASE_PATH: {BASE_PATH.absolute()}")
if BASE_PATH.exists():
    npz_files = list(BASE_PATH.glob('*.npz'))
    print(f"見つかったNPZファイル: {len(npz_files)}件")
    for f in npz_files[:5]:
        print(f"  - {f.name}")
else:
    print(f"警告: {BASE_PATH} が存在しません")

# %%
# ## データ読み込みと前処理
base_project_path = Path(__file__).resolve().parent.parent  # notebooks/ -> apps/prediction/
data_processor = DataProcessor(base_path=base_project_path.parent.parent)  # apps/prediction/ -> プロジェクトルート

print("データ読み込みと前処理を開始します...")
split_date = "2024-06-01"

try:
    train_df, test_df, eval_df = data_processor.process(
        data_types=DATA_TYPES,
        year=YEARS[0],
        split_date=split_date,
    )
    
    print(f"\n前処理完了: 学習={len(train_df):,}件, テスト={len(test_df):,}件")
    print(f"レース数: 学習={train_df.index.nunique() if train_df.index.name == 'race_key' else len(train_df)}, テスト={test_df.index.nunique() if test_df.index.name == 'race_key' else len(test_df)}")
    print(f"\nデータ形状: 学習={train_df.shape}, テスト={test_df.shape}")
    
    # rank列の確認
    if 'rank' not in train_df.columns:
        raise ValueError("train_dfにrank列が含まれていません。filter_training_columns()でtarget_variableが含まれるはずです。")
    if 'rank' not in test_df.columns:
        raise ValueError("test_dfにrank列が含まれていません。filter_training_columns()でtarget_variableが含まれるはずです。")
    
    train_rank_count = train_df['rank'].notna().sum()
    test_rank_count = test_df['rank'].notna().sum()
    print(f"rank列の状態: 学習={train_rank_count:,}件, 検証={test_rank_count:,}件")
    
    if train_rank_count == 0 or test_rank_count == 0:
        raise ValueError(f"rank列が不足しています。学習={train_rank_count:,}件, 検証={test_rank_count:,}件")
    
    df = train_df
    val_df = test_df
    original_df = eval_df  # eval_dfが評価用データ（日本語キー、evaluation_schema.jsonに基づいて選択済み）
    
    # キャッシュデータの整合性確認（evaluation_schema.jsonに基づく必須カラムの存在確認）
    print("\n評価用データの整合性確認中...")
    # インデックスがrace_keyの場合は一時的にリセットして確認
    original_df_for_check = original_df.reset_index() if original_df.index.name == "race_key" else original_df.copy()
    required_eval_cols = ["race_key", "馬番", "着順"]
    missing_cols = [col for col in required_eval_cols if col not in original_df_for_check.columns]
    if missing_cols:
        print(f"警告: 評価用データに必須カラムが不足しています: {missing_cols}")
        print("evaluation_schema.jsonに基づいて再選択します...")
        from src.data_processer.column_selector import ColumnSelector
        column_selector = ColumnSelector(base_path=base_project_path.parent.parent)
        # featured_dfを再読み込みする必要があるが、キャッシュから読み込んだeval_dfが不整合な場合は
        # データ処理を再実行する必要がある（キャッシュを無効化）
        # ここでは、eval_dfをそのまま使用し、不足しているカラムがあればエラーを投げる
        raise ValueError(f"キャッシュから読み込んだeval_dfがevaluation_schema.jsonに準拠していません。必須カラムが不足: {missing_cols}。キャッシュを削除して再処理してください。")
    else:
        print(f"評価用データの整合性確認完了（必須カラムが存在します: {required_eval_cols}）")
        # オプションカラムの存在確認（情報表示のみ）
        optional_eval_cols = ["WIN5フラグ", "確定単勝オッズ"]
        existing_optional_cols = [col for col in optional_eval_cols if col in original_df_for_check.columns]
        if existing_optional_cols:
            print(f"オプションカラムが存在します: {existing_optional_cols}")
        else:
            print("オプションカラムは存在しません（WIN5フラグ、確定単勝オッズ）")
        
except Exception as e:
    print(f"エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
    raise

# %%
# ## 特徴量強化（レース内相対特徴量とインタラクション特徴量を追加）
print("\n" + "=" * 80)
print("特徴量強化を開始します...")
print("=" * 80)

# レースキーの取得方法を確認
race_key_col = "race_key"
if df.index.name == race_key_col:
    # インデックスがrace_keyの場合、一時的にリセット
    df_for_enhance = df.reset_index()
    val_df_for_enhance = val_df.reset_index()
    use_index = True
else:
    df_for_enhance = df.copy()
    val_df_for_enhance = val_df.copy()
    use_index = False

# 特徴量強化を実行
df_enhanced = enhance_features(df_for_enhance, race_key_col)
val_df_enhanced = enhance_features(val_df_for_enhance, race_key_col)

# インデックスを復元（必要に応じて）
if use_index:
    df_enhanced = df_enhanced.set_index(race_key_col)
    val_df_enhanced = val_df_enhanced.set_index(race_key_col)
    # 元のインデックス順序を保持
    if len(df_enhanced) == len(df):
        df_enhanced = df_enhanced.reindex(df.index)
    if len(val_df_enhanced) == len(val_df):
        val_df_enhanced = val_df_enhanced.reindex(val_df.index)

# 更新されたDataFrameを使用
df = df_enhanced
val_df = val_df_enhanced

print(f"\n特徴量強化後のデータ形状: 学習={df.shape}, テスト={val_df.shape}")

# %%
# ## モデル学習
# RankPredictorのインスタンスを作成
rank_predictor = RankPredictor(df, val_df)

print("\n" + "=" * 80)
print("モデル学習を開始します...")
print("（Optunaによるハイパーパラメータチューニングが実行されます）")
print("=" * 80)

model = rank_predictor.train()
print("\nモデル学習完了")

# %%
# ## モデル保存
model.save_model(str(MODEL_PATH))
print(f"モデルを保存しました: {MODEL_PATH}")

# %%
# ## 予測と評価
print("\n" + "=" * 80)
print("検証データで予測を実行します...")
print("=" * 80)
val_predictions_raw = RankPredictor.predict(model, val_df, rank_predictor.features)

# 馬番を取得してval_predictions_rawに追加（マージキー用）
# val_dfにhorse_number（英語キー）が含まれている場合はそれを使用
# 含まれていない場合はoriginal_dfから馬番（日本語キー）を取得
val_df_for_merge = val_df.copy()
if val_df_for_merge.index.name == "race_key":
    val_df_for_merge = val_df_for_merge.reset_index()
elif "race_key" not in val_df_for_merge.columns:
    raise ValueError("val_dfにrace_key列が含まれていません")

# val_predictions_rawとval_df_for_mergeの行数が一致することを確認
if len(val_predictions_raw) != len(val_df_for_merge):
    raise ValueError(f"予測結果の行数({len(val_predictions_raw)})とval_dfの行数({len(val_df_for_merge)})が一致しません")

# val_dfにhorse_number（英語キー）が含まれているか確認
if "horse_number" in val_df_for_merge.columns:
    # val_dfにhorse_numberが含まれている場合はそれを使用
    val_predictions_raw["馬番"] = val_df_for_merge["horse_number"].values
else:
    # val_dfにhorse_numberが含まれていない場合はoriginal_dfから取得
    original_df_for_merge = original_df.copy()
    if original_df_for_merge.index.name == "race_key":
        original_df_for_merge = original_df_for_merge.reset_index()
    elif "race_key" not in original_df_for_merge.columns:
        raise ValueError("original_dfにrace_key列が含まれていません")
    
    if "馬番" not in original_df_for_merge.columns:
        raise ValueError("original_dfに馬番列が含まれていません")
    
    # race_keyでマージして馬番を取得
    # val_dfと同じ順序で予測結果が返されるため、race_keyでマージ
    val_df_race_keys = pd.DataFrame({
        "race_key": val_df_for_merge["race_key"].values,
        "_order": range(len(val_df_for_merge))
    })
    # original_dfからrace_keyと馬番の対応関係を取得
    # 同じrace_keyに複数の馬がいる場合を考慮して、行の順序で対応
    original_df_subset = original_df_for_merge[["race_key", "馬番"]].copy()
    original_df_subset["_order"] = range(len(original_df_subset))
    
    # race_keyでマージ（同じrace_keyに複数の馬がいる場合、行の順序で対応）
    merged = val_df_race_keys.merge(original_df_subset, on=["race_key", "_order"], how="left")
    
    # マージに失敗した場合はrace_keyのみでマージ（順序が一致している場合）
    if merged["馬番"].isna().any():
        # race_keyのみでマージ（最初の馬を取得）
        merged = val_df_race_keys.merge(
            original_df_subset[["race_key", "馬番"]].drop_duplicates(subset="race_key", keep="first"),
            on="race_key",
            how="left"
        )
    
    val_predictions_raw["馬番"] = merged["馬番"].values

# original_df（eval_df、日本語キー、evaluation_schema.jsonに基づいて選択済み）を使用
# 注: キャッシュから読み込んだeval_dfは既にevaluation_schema.jsonに基づいて選択されているため、
#     再度select_evaluation()を呼び出す必要はない（仕様書に沿った実装）
original_eval = original_df.copy()

# インデックスがrace_keyの場合はリセット
if original_eval.index.name == "race_key":
    original_eval = original_eval.reset_index()
elif "race_key" not in original_eval.columns:
    raise ValueError("original_evalにrace_key列が含まれていません")

# キャッシュデータの整合性確認（evaluation_schema.jsonに基づく必須カラムの存在確認）
required_eval_cols = ["race_key", "馬番", "着順"]
missing_cols = [col for col in required_eval_cols if col not in original_eval.columns]
if missing_cols:
    raise ValueError(f"キャッシュから読み込んだeval_dfがevaluation_schema.jsonに準拠していません。必須カラムが不足: {missing_cols}。キャッシュを削除して再処理してください。")

print(f"評価用データのカラム数: {len(original_eval.columns)}")
print(f"評価用データのカラム: {list(original_eval.columns)[:10]}...")  # 最初の10カラムを表示

# 予測結果をベースに、評価に必要な最小限の情報だけを追加
val_predictions = val_predictions_raw.copy()

# 評価に必要な情報を追加（race_keyと馬番でマージ）
eval_data = original_eval.copy()
val_predictions = val_predictions.merge(eval_data, on=["race_key", "馬番"], how="left")

# 予測順位を追加（レースごとにpredicted_scoreでソートして順位を付与）
val_predictions = val_predictions.sort_values(["race_key", "predicted_score"], ascending=[True, False])
val_predictions["predicted_rank"] = val_predictions.groupby("race_key").cumcount() + 1

# 評価用にrank列を追加（着順から）
if "着順" in val_predictions.columns and "rank" not in val_predictions.columns:
    val_predictions["rank"] = pd.to_numeric(val_predictions["着順"], errors="coerce")

if "rank" not in val_predictions.columns or "馬番" not in val_predictions.columns:
    raise ValueError("結合後の予測結果に必須列が含まれていません")

print(f"予測完了: {len(val_predictions)}件")
print(f"\n予測結果のサンプル:")
print(val_predictions.head(10))

# オッズデータの有無を確認
has_odds = "確定単勝オッズ" in val_predictions.columns and val_predictions["確定単勝オッズ"].notna().any()
odds_col = "確定単勝オッズ" if has_odds else None

print("\n" + "=" * 60)
print(f"モデル評価（{'オッズあり' if has_odds else 'オッズなし'}）:")
print("=" * 60)
from src.evaluator import evaluate_model, print_evaluation_results
evaluation_result = evaluate_model(val_predictions, odds_col=odds_col)
print_evaluation_results(evaluation_result)

# %%
# ## 特徴量重要度
importance = model.feature_importance(importance_type='gain')
feature_names = [f for f in rank_predictor.features.encoded_feature_names if f in val_df.columns]

# 新しく追加された特徴量も含めて重要度を計算
all_feature_names = list(val_df.columns)
# rank列とrace_key列を除外
all_feature_names = [f for f in all_feature_names if f not in ['rank', 'race_key']]

# 重要度と特徴量名を対応付け
importance_dict = {}
for i, feat_name in enumerate(feature_names[:len(importance)]):
    if feat_name in importance_dict:
        # 重複がある場合は最大値を取る
        importance_dict[feat_name] = max(importance_dict[feat_name], importance[i])
    else:
        importance_dict[feat_name] = importance[i]

# 新しく追加された特徴量の重要度を取得（モデルに含まれている場合）
model_feature_names = model.feature_name()
for i, feat_name in enumerate(model_feature_names):
    if feat_name not in importance_dict:
        # 新しく追加された特徴量
        if i < len(importance):
            importance_dict[feat_name] = importance[i]

importance_df = pd.DataFrame({
    'feature': list(importance_dict.keys()),
    'importance': list(importance_dict.values())
}).sort_values('importance', ascending=False)

print("\n特徴量重要度（上位30）:")
print(importance_df.head(30))

# 新しく追加された特徴量の重要度を確認
new_features = [f for f in importance_df['feature'] if '_rank' in f or '_x_' in f]
if new_features:
    print(f"\n新しく追加された特徴量（上位10）:")
    new_features_df = importance_df[importance_df['feature'].isin(new_features)].head(10)
    print(new_features_df)

# 可視化
plt.figure(figsize=(12, 10))
sns.barplot(data=importance_df.head(30), y='feature', x='importance')
plt.title('特徴量重要度（上位30）')
plt.xlabel('重要度')
plt.tight_layout()
plt.show()

