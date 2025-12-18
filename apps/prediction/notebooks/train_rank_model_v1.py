# %%
# JRDBデータを使用したランキング学習モデル

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

# パス設定
PREDICTION_APP_DIRECTORY = Path(__file__).resolve().parent.parent
PROJECT_ROOT_DIRECTORY = PREDICTION_APP_DIRECTORY.parent.parent
sys.path.insert(0, str(PREDICTION_APP_DIRECTORY))

# 日本語フォント設定
try:
    matplotlib.rcParams['font.family'] = 'Hiragino Sans'
except:
    try:
        matplotlib.rcParams['font.family'] = 'Arial Unicode MS'
    except:
        pass

from src.data_processer import DataProcessor
from src.rank_predictor import RankPredictor
from src.feature_enhancers import enhance_features
from src.evaluator import evaluate_model, print_evaluation_results

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)

# %%
# 定数定義
PARQUET_BASE_PATH = PREDICTION_APP_DIRECTORY / 'cache' / 'jrdb' / 'parquet'
PRE_TRAINING_CACHE_DIR = PREDICTION_APP_DIRECTORY / 'cache' / 'pre_training'
YEARS = [2024]
TRAIN_TEST_SPLIT_DATE = "2024-06-01"
MODEL_PATH = PREDICTION_APP_DIRECTORY / 'models' / f'rank_model_{datetime.now().strftime("%Y%m%d%H%M")}_v1.txt'
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

# %%
# データ読み込みと前処理
import os
import warnings
# メモリ最適化により、デフォルト値（DATA_PROCESSER_MAX_WORKERS=4, FEATURE_EXTRACTOR_MAX_WORKERS=2）を使用
os.environ["PYTHONUNBUFFERED"] = "1"
warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing.resource_tracker")

from src.utils.parquet_loader import ParquetLoader
from src.utils.cache_manager import CacheManager
from src.data_processer.main import _DATA_TYPES

parquet_loader = ParquetLoader(PARQUET_BASE_PATH)
parquet_loader.check_parquet_files(YEARS[0])

# キャッシュから前処理済みデータを読み込み（あれば前処理をスキップ）
cache_manager = CacheManager(PREDICTION_APP_DIRECTORY)
cached_data = cache_manager.load(_DATA_TYPES, YEARS[0], TRAIN_TEST_SPLIT_DATE)

if cached_data is None:
    # キャッシュがない場合は前処理を実行
    data_processor = DataProcessor(
        base_path=PROJECT_ROOT_DIRECTORY,
        parquet_base_path=PARQUET_BASE_PATH
    )
    
    train_data, test_data, evaluation_data = data_processor.process_multiple_years(
        years=YEARS,
        split_date=TRAIN_TEST_SPLIT_DATE
    )
    del data_processor
    
    print(f"前処理完了: 学習={len(train_data):,}件, テスト={len(test_data):,}件")
else:
    # キャッシュから読み込み
    train_data, test_data, evaluation_data = cached_data
    print(f"キャッシュから読み込み完了: 学習={len(train_data):,}件, テスト={len(test_data):,}件")

print(f"データ形状: 学習={train_data.shape}, テスト={test_data.shape}")

# 必須カラム確認
required_eval_columns = ["race_key", "馬番", "着順"]
eval_check = evaluation_data.reset_index() if evaluation_data.index.name == "race_key" else evaluation_data
missing = [col for col in required_eval_columns if col not in eval_check.columns]
if missing:
    raise ValueError(f"評価用データに必須カラムが不足: {missing}。キャッシュを削除して再処理してください。")

# %%
# モデル学習前のデータ保存（特徴量強化前）
PRE_TRAINING_CACHE_DIR.mkdir(parents=True, exist_ok=True)
file_prefix = f"{YEARS[0]}_{TRAIN_TEST_SPLIT_DATE.replace('-', '')}"
train_data.to_parquet(PRE_TRAINING_CACHE_DIR / f"train_{file_prefix}.parquet")
test_data.to_parquet(PRE_TRAINING_CACHE_DIR / f"test_{file_prefix}.parquet")
print(f"モデル学習前データ保存完了: {PRE_TRAINING_CACHE_DIR}")

# %%
# 特徴量強化
train_data_enhanced = enhance_features(train_data, "race_key")
test_data_enhanced = enhance_features(test_data, "race_key")
del train_data, test_data
print(f"特徴量強化完了: 学習={train_data_enhanced.shape}, テスト={test_data_enhanced.shape}")

# %%
# モデル学習
rank_predictor = RankPredictor(train_data_enhanced, test_data_enhanced)
model = rank_predictor.train()
model.save_model(str(MODEL_PATH))
print(f"モデル保存完了: {MODEL_PATH}")

# %%
# 予測と評価
predictions = RankPredictor.predict(model, test_data_enhanced, rank_predictor.features)
if "predicted_score" not in predictions.columns:
    if "predict" not in predictions.columns:
        raise KeyError(f"predictionsにpredicted_score/predict列が存在しません。columns={list(predictions.columns)}")
    predictions = predictions.rename(columns={"predict": "predicted_score"})

# 馬番を追加
test_data_merged = test_data_enhanced.reset_index() if test_data_enhanced.index.name == "race_key" else test_data_enhanced.copy()
if "horse_number" in test_data_merged.columns:
    predictions["馬番"] = test_data_merged["horse_number"].values
else:
    eval_merged = evaluation_data.reset_index() if evaluation_data.index.name == "race_key" else evaluation_data.copy()
    predictions["馬番"] = pd.merge(
        pd.DataFrame({"race_key": test_data_merged["race_key"].values, "_order": range(len(test_data_merged))}),
        pd.DataFrame({"race_key": eval_merged["race_key"].values, "馬番": eval_merged["馬番"].values, "_order": range(len(eval_merged))}),
        on=["race_key", "_order"], how="left"
    )["馬番"].values

# 評価データとマージ
eval_reset = evaluation_data.reset_index() if evaluation_data.index.name == "race_key" else evaluation_data.copy()
predictions = predictions.merge(eval_reset, on=["race_key", "馬番"], how="left")

# 予測順位を追加
predictions = predictions.sort_values(["race_key", "predicted_score"], ascending=[True, False])
predictions["predicted_rank"] = predictions.groupby("race_key").cumcount() + 1
if "着順" in predictions.columns and "rank" not in predictions.columns:
    predictions["rank"] = pd.to_numeric(predictions["着順"], errors="coerce")

# 評価
odds_col = "確定単勝オッズ" if "確定単勝オッズ" in predictions.columns and predictions["確定単勝オッズ"].notna().any() else None
evaluation_result = evaluate_model(predictions, odds_col=odds_col)
print_evaluation_results(evaluation_result)

# %%
# 特徴量重要度
importance_scores = model.feature_importance(importance_type='gain')
model_features = model.feature_name()
importance_df = pd.DataFrame({
    'feature': model_features,
    'importance': importance_scores[:len(model_features)]
}).sort_values('importance', ascending=False)

print("\n特徴量重要度（上位30）:")
print(importance_df.head(30))

new_features = importance_df[importance_df['feature'].str.contains('_rank|_x_', regex=True)]
if len(new_features) > 0:
    print(f"\n新規特徴量（上位10）:")
    print(new_features.head(10))

plt.figure(figsize=(12, 10))
sns.barplot(data=importance_df.head(30), y='feature', x='importance')
plt.title('特徴量重要度（上位30）')
plt.xlabel('重要度')
plt.tight_layout()
plt.show()

