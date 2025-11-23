# %%
# JRDBデータを使用したランキング学習モデル
# 
# 年度パックNPZファイルからデータを読み込み、LambdaRankモデルを学習します。

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
    original_df = eval_df  # eval_dfが評価用データ（日本語キー）
        
except Exception as e:
    print(f"エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()
    raise

# %%
# ## モデル学習
# RankPredictorのインスタンスを作成
rank_predictor = RankPredictor(train_df, val_df)

print("モデル学習を開始します...")
print("（Optunaによるハイパーパラメータチューニングが実行されます）")

model = rank_predictor.train()
print("\nモデル学習完了")

# %%
# ## モデル保存
model.save_model(str(MODEL_PATH))
print(f"モデルを保存しました: {MODEL_PATH}")

# %%
# ## 予測と評価
print("検証データで予測を実行します...")
val_predictions_raw = RankPredictor.predict(model, val_df, rank_predictor.features)

# original_df（full_data_df、日本語キー）から評価用データを取得
original_eval = original_df.copy()
if original_df.index.name == "race_key":
    original_eval = original_eval.reset_index()
elif "race_key" not in original_eval.columns:
    raise ValueError("original_dfにrace_key列が含まれていません")

# 日本語キーで必須列を確認
required_cols_jp = ["race_key", "着順", "馬番"]
missing_cols = [col for col in required_cols_jp if col not in original_eval.columns]
if missing_cols:
    raise ValueError(f"original_dfに必須列が含まれていません: {missing_cols}")

# 評価用カラムを取得（日本語キーのまま）
eval_cols = required_cols_jp + (["タイム"] if "タイム" in original_eval.columns else [])
original_eval = original_eval[eval_cols].copy()

# 予測結果と結合（日本語キーのまま）
val_predictions = val_predictions_raw.merge(original_eval, on="race_key", how="left")

# 評価用にrank列を追加（着順から）
if "着順" in val_predictions.columns and "rank" not in val_predictions.columns:
    val_predictions["rank"] = pd.to_numeric(val_predictions["着順"], errors="coerce")

if "rank" not in val_predictions.columns or "馬番" not in val_predictions.columns:
    raise ValueError("結合後の予測結果に必須列が含まれていません")

print(f"予測完了: {len(val_predictions)}件")
print(f"\n予測結果のサンプル:")
print(val_predictions.head(10))

print("\n" + "=" * 60)
print("モデル評価（オッズなし）:")
print("=" * 60)
from src.evaluator import evaluate_model, print_evaluation_results
evaluation_result = evaluate_model(val_predictions)
print_evaluation_results(evaluation_result)

# %%
# ## 特徴量重要度
importance = model.feature_importance(importance_type='gain')
feature_names = [f for f in rank_predictor.features.encoded_feature_names if f in val_df.columns]

importance_df = pd.DataFrame({
    'feature': feature_names[:len(importance)],
    'importance': importance
}).sort_values('importance', ascending=False)

print("特徴量重要度（上位20）:")
print(importance_df.head(20))

# 可視化
plt.figure(figsize=(10, 8))
sns.barplot(data=importance_df.head(20), y='feature', x='importance')
plt.title('特徴量重要度（上位20）')
plt.xlabel('重要度')
plt.tight_layout()
plt.show()
