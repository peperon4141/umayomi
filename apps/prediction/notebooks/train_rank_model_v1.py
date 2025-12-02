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

import pandas as pd
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
model_save_timestamp = datetime.now().strftime('%Y%m%d%H%M')
MODEL_PATH = Path(__file__).parent.parent / 'models' / f'rank_model_{model_save_timestamp}_v1.txt'
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

# Parquetファイルは apps/prediction/cache/jrdb/parquet/ に保存されている
jrdb_parquet_cache_directory = Path(__file__).parent.parent / 'cache' / 'jrdb' / 'parquet'
print(f"Parquetファイルパス: {jrdb_parquet_cache_directory.absolute()}")
if jrdb_parquet_cache_directory.exists():
    jrdb_parquet_files_for_2024 = list(jrdb_parquet_cache_directory.glob('*_2024.parquet'))
    print(f"見つかった2024年度のParquetファイル: {len(jrdb_parquet_files_for_2024)}件")
    for parquet_file in jrdb_parquet_files_for_2024[:5]:
        print(f"  - {parquet_file.name}")
else:
    print(f"警告: {jrdb_parquet_cache_directory} が存在しません")

# %%
# ## データ読み込みと前処理
prediction_app_directory = Path(__file__).resolve().parent.parent  # notebooks/ -> apps/prediction/
project_root_directory = prediction_app_directory.parent.parent  # apps/prediction/ -> プロジェクトルート
data_processor = DataProcessor(base_path=project_root_directory)

print("[_01_] データ読み込みと前処理を開始します...")
train_test_split_date = "2024-06-01"  # 2024年のデータを6月1日で分割（学習/テスト）

# メモリ使用量を削減するため、並列処理のワーカー数を制限
import os
import gc
os.environ["DATA_PROCESSER_MAX_WORKERS"] = "1"  # 並列処理を無効化してメモリ使用量を削減
os.environ["FEATURE_EXTRACTOR_MAX_WORKERS"] = "1"  # 特徴量抽出の並列処理も無効化

# メモリ使用量を監視
def print_memory_usage(stage: str):
    """メモリ使用量を表示"""
    try:
        import psutil
        import os as os_module
        process = psutil.Process(os_module.getpid())
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / 1024 / 1024
        print(f"[メモリ使用量] {stage}: {mem_mb:.1f} MB")
    except ImportError:
        pass  # psutilがインストールされていない場合はスキップ

print_memory_usage("処理開始前")

try:
    # 複数年度のデータを処理（DataProcessorを使用）
    train_data, test_data, evaluation_data = data_processor.process_multiple_years(
        data_types=DATA_TYPES,
        years=YEARS,
        split_date=train_test_split_date
    )
    
    print_memory_usage("データ処理完了後")
    
    # 変換済みデータは不要なので削除（既にtrain_df, test_dfに分割済み）
    gc.collect()
    print_memory_usage("ガベージコレクション後")
    
    print(f"\n前処理完了: 学習={len(train_data):,}件, テスト={len(test_data):,}件")
    print(f"レース数: 学習={train_data.index.nunique() if train_data.index.name == 'race_key' else len(train_data)}, テスト={test_data.index.nunique() if test_data.index.name == 'race_key' else len(test_data)}")
    print(f"\nデータ形状: 学習={train_data.shape}, テスト={test_data.shape}")
    
    # rank列の確認
    if 'rank' not in train_data.columns:
        raise ValueError("train_dataにrank列が含まれていません。filter_training_columns()でtarget_variableが含まれるはずです。")
    if 'rank' not in test_data.columns:
        raise ValueError("test_dataにrank列が含まれていません。filter_training_columns()でtarget_variableが含まれるはずです。")
    
    train_data_rank_count = train_data['rank'].notna().sum()
    test_data_rank_count = test_data['rank'].notna().sum()
    print(f"rank列の状態: 学習={train_data_rank_count:,}件, 検証={test_data_rank_count:,}件")
    
    if train_data_rank_count == 0 or test_data_rank_count == 0:
        raise ValueError(f"rank列が不足しています。学習={train_data_rank_count:,}件, 検証={test_data_rank_count:,}件")
    
    # メモリ効率化: 不要な参照を削除
    train_data_for_enhancement = train_data.copy() if hasattr(train_data, 'copy') else train_data
    test_data_for_enhancement = test_data.copy() if hasattr(test_data, 'copy') else test_data
    evaluation_data_with_japanese_keys = evaluation_data.copy() if hasattr(evaluation_data, 'copy') else evaluation_data
    
    # 元の参照を削除してメモリを解放
    del train_data, test_data, evaluation_data
    gc.collect()
    print_memory_usage("データコピー後")
    
    # キャッシュデータの整合性確認（evaluation_schema.jsonに基づく必須カラムの存在確認）
    print("\n評価用データの整合性確認中...")
    # インデックスがrace_keyの場合は一時的にリセットして確認
    evaluation_data_for_column_check = evaluation_data_with_japanese_keys.reset_index() if evaluation_data_with_japanese_keys.index.name == "race_key" else evaluation_data_with_japanese_keys.copy()
    required_evaluation_columns = ["race_key", "馬番", "着順"]
    missing_evaluation_columns = [col for col in required_evaluation_columns if col not in evaluation_data_for_column_check.columns]
    if missing_evaluation_columns:
        print(f"警告: 評価用データに必須カラムが不足しています: {missing_evaluation_columns}")
        print("evaluation_schema.jsonに基づいて再選択します...")
        from src.data_processer._06_column_selector import ColumnSelector
        column_selector = ColumnSelector(base_path=project_root_directory)
        # featured_dfを再読み込みする必要があるが、キャッシュから読み込んだeval_dfが不整合な場合は
        # データ処理を再実行する必要がある（キャッシュを無効化）
        # ここでは、eval_dfをそのまま使用し、不足しているカラムがあればエラーを投げる
        raise ValueError(f"キャッシュから読み込んだeval_dfがevaluation_schema.jsonに準拠していません。必須カラムが不足: {missing_evaluation_columns}。キャッシュを削除して再処理してください。")
    else:
        print(f"評価用データの整合性確認完了（必須カラムが存在します: {required_evaluation_columns}）")
        # オプションカラムの存在確認（情報表示のみ）
        optional_evaluation_columns = ["WIN5フラグ", "確定単勝オッズ"]
        existing_optional_evaluation_columns = [col for col in optional_evaluation_columns if col in evaluation_data_for_column_check.columns]
        if existing_optional_evaluation_columns:
            print(f"オプションカラムが存在します: {existing_optional_evaluation_columns}")
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
race_key_column_name = "race_key"

# race_keyがインデックスまたはカラムとして存在するか確認
if train_data_for_enhancement.index.name == race_key_column_name:
    # インデックス名がrace_keyの場合、一時的にリセット
    train_data_with_reset_index = train_data_for_enhancement.reset_index()
    test_data_with_reset_index = test_data_for_enhancement.reset_index()
    should_restore_race_key_index = True
elif race_key_column_name in train_data_for_enhancement.columns:
    # race_keyがカラムの場合
    train_data_with_reset_index = train_data_for_enhancement.copy()
    test_data_with_reset_index = test_data_for_enhancement.copy()
    should_restore_race_key_index = False
elif train_data_for_enhancement.index.name is None and len(train_data_for_enhancement.index) > 0:
    # インデックス名がNoneでも、インデックスが存在する場合（Parquet読み込み時など）
    # インデックスをリセットしてカラムに変換（インデックス値がrace_keyの可能性がある）
    train_data_with_reset_index = train_data_for_enhancement.reset_index()
    test_data_with_reset_index = test_data_for_enhancement.reset_index()
    # リセット後のカラム名を確認
    if race_key_column_name in train_data_with_reset_index.columns:
        should_restore_race_key_index = True
    else:
        # リセット後もrace_keyが存在しない場合、エラー
        raise ValueError(
            f"race_key（{race_key_column_name}）がインデックスにもカラムにも存在しません。\n"
            f"  インデックス名: {train_data_for_enhancement.index.name}\n"
            f"  インデックス型: {type(train_data_for_enhancement.index)}\n"
            f"  カラム（最初の10個）: {list(train_data_for_enhancement.columns[:10])}\n"
            f"  リセット後のカラム: {list(train_data_with_reset_index.columns[:10])}\n"
            f"  データ形状: {train_data_for_enhancement.shape}"
        )
else:
    # race_keyが存在しない場合、エラーを投げる（デバッグ情報付き）
    raise ValueError(
        f"race_key（{race_key_column_name}）がインデックスにもカラムにも存在しません。\n"
        f"  インデックス名: {train_data_for_enhancement.index.name}\n"
        f"  インデックス型: {type(train_data_for_enhancement.index)}\n"
        f"  カラム（最初の10個）: {list(train_data_for_enhancement.columns[:10])}\n"
        f"  データ形状: {train_data_for_enhancement.shape}"
    )

# 特徴量強化を実行
train_data_after_enhancement = enhance_features(train_data_with_reset_index, race_key_column_name)
test_data_after_enhancement = enhance_features(test_data_with_reset_index, race_key_column_name)

# インデックスを復元（必要に応じて）
if should_restore_race_key_index:
    train_data_after_enhancement = train_data_after_enhancement.set_index(race_key_column_name)
    test_data_after_enhancement = test_data_after_enhancement.set_index(race_key_column_name)
    # 元のインデックス順序を保持
    if len(train_data_after_enhancement) == len(train_data_for_enhancement):
        train_data_after_enhancement = train_data_after_enhancement.reindex(train_data_for_enhancement.index)
    if len(test_data_after_enhancement) == len(test_data_for_enhancement):
        test_data_after_enhancement = test_data_after_enhancement.reindex(test_data_for_enhancement.index)

# 更新されたDataFrameを使用
train_data_with_enhanced_features = train_data_after_enhancement
test_data_with_enhanced_features = test_data_after_enhancement

print(f"\n特徴量強化後のデータ形状: 学習={train_data_with_enhanced_features.shape}, テスト={test_data_with_enhanced_features.shape}")

# %%
# ## リークチェック用データの保存（前走データ含む）
# 特徴量抽出完了後のfeatured_df（前走データ含む、日本語キー）をキャッシュから読み込んで保存
# リークチェックには前走データ（prev_*_race_key）が含まれる段階のデータが必要
print("\n" + "=" * 80)
print("リークチェック用データを保存中...")
print("=" * 80)

# CacheManagerからfeatured_dfを読み込み（前走データ含む）
from src.data_processer._07_cache_manager import CacheManager
data_cache_manager = CacheManager(project_root / "cache")

# 複数年度の場合は最初の年度のfeatured_dfを読み込む
feature_extracted_data_with_previous_races = None
for year in YEARS:
    feature_extracted_data_with_previous_races = data_cache_manager.load_featured_df(DATA_TYPES, year, train_test_split_date)
    if feature_extracted_data_with_previous_races is not None:
        print(f"  {year}年度のfeature_extracted_data_with_previous_racesを読み込み: {len(feature_extracted_data_with_previous_races):,}件")
        break

if feature_extracted_data_with_previous_races is None:
    print("警告: feature_extracted_data_with_previous_racesのキャッシュが見つかりません。リークチェック用データを保存できません。")
    print("      データ処理を実行してから再度試してください。")
else:
    # 前走データのカラムを確認
    previous_race_key_column_names = [f"prev_{i}_race_key" for i in range(1, 6)]
    existing_previous_race_key_columns = [col for col in previous_race_key_column_names if col in feature_extracted_data_with_previous_races.columns]
    if existing_previous_race_key_columns:
        print(f"  前走データカラムを確認: {len(existing_previous_race_key_columns)}個のprev_*_race_keyカラムが見つかりました")
    else:
        print("  警告: 前走データのrace_keyカラムが見つかりません")
    
    # 時系列分割（train_test_split_dateに基づく）
    if train_test_split_date:
        from src.data_processer._05_time_series_splitter import TimeSeriesSplitter
        # feature_extracted_data_with_previous_racesにstart_datetimeを追加（まだ追加されていない場合）
        if "start_datetime" not in feature_extracted_data_with_previous_races.columns:
            from src.data_processer._03_01_feature_converter import FeatureConverter
            feature_extracted_data_with_previous_races = FeatureConverter.add_start_datetime_to_df(feature_extracted_data_with_previous_races)
        
        # race_keyをインデックスに設定（まだ設定されていない場合）
        if feature_extracted_data_with_previous_races.index.name != "race_key" and "race_key" in feature_extracted_data_with_previous_races.columns:
            feature_extracted_data_with_previous_races = feature_extracted_data_with_previous_races.set_index("race_key")
        
        # 時系列分割
        time_series_splitter = TimeSeriesSplitter()
        train_data_with_previous_races, test_data_with_previous_races = time_series_splitter.split(feature_extracted_data_with_previous_races, train_test_split_date)
        
        # リークチェック用に保存（apps/prediction/cache/leak_check/）
        leak_check_cache_directory = project_root / "cache" / "leak_check"
        leak_check_cache_directory.mkdir(parents=True, exist_ok=True)
        
        train_data_cache_file_path = leak_check_cache_directory / f"train_featured_{YEARS[0]}_{train_test_split_date.replace('-', '')}.parquet"
        test_data_cache_file_path = leak_check_cache_directory / f"test_featured_{YEARS[0]}_{train_test_split_date.replace('-', '')}.parquet"
        
        train_data_with_previous_races.to_parquet(train_data_cache_file_path)
        test_data_with_previous_races.to_parquet(test_data_cache_file_path)
        
        print(f"  学習データ（前走データ含む）: {train_data_cache_file_path}")
        print(f"  テストデータ（前走データ含む）: {test_data_cache_file_path}")
        print(f"\n✅ リークチェック用データ保存完了: {leak_check_cache_directory.absolute()}")
        print(f"リークチェックを実行する場合:")
        print(f"  python {project_root / 'tmp' / 'check_leakage.py'}")
    else:
        print("  警告: train_test_split_dateが指定されていないため、時系列分割ができません。")

# %%
# ## モデル学習
# RankPredictorのインスタンスを作成
rank_predictor = RankPredictor(train_data_with_enhanced_features, test_data_with_enhanced_features)

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
test_predictions_without_evaluation_data = RankPredictor.predict(model, test_data_with_enhanced_features, rank_predictor.features)

# 馬番を取得してtest_predictions_without_evaluation_dataに追加（マージキー用）
# test_data_with_enhanced_featuresにhorse_number（英語キー）が含まれている場合はそれを使用
# 含まれていない場合はevaluation_data_with_japanese_keysから馬番（日本語キー）を取得
test_data_for_merging = test_data_with_enhanced_features.copy()
if test_data_for_merging.index.name == "race_key":
    test_data_for_merging = test_data_for_merging.reset_index()
elif "race_key" not in test_data_for_merging.columns:
    raise ValueError("test_data_with_enhanced_featuresにrace_key列が含まれていません")

# test_predictions_without_evaluation_dataとtest_data_for_mergingの行数が一致することを確認
if len(test_predictions_without_evaluation_data) != len(test_data_for_merging):
    raise ValueError(f"予測結果の行数({len(test_predictions_without_evaluation_data)})とtest_data_with_enhanced_featuresの行数({len(test_data_for_merging)})が一致しません")

# test_data_with_enhanced_featuresにhorse_number（英語キー）が含まれているか確認
if "horse_number" in test_data_for_merging.columns:
    # test_data_with_enhanced_featuresにhorse_numberが含まれている場合はそれを使用
    test_predictions_without_evaluation_data["馬番"] = test_data_for_merging["horse_number"].values
else:
    # test_data_with_enhanced_featuresにhorse_numberが含まれていない場合はevaluation_data_with_japanese_keysから取得
    evaluation_data_for_merging = evaluation_data_with_japanese_keys.copy()
    if evaluation_data_for_merging.index.name == "race_key":
        evaluation_data_for_merging = evaluation_data_for_merging.reset_index()
    elif "race_key" not in evaluation_data_for_merging.columns:
        raise ValueError("evaluation_data_with_japanese_keysにrace_key列が含まれていません")
    
    if "馬番" not in evaluation_data_for_merging.columns:
        raise ValueError("evaluation_data_with_japanese_keysに馬番列が含まれていません")
    
    # race_keyでマージして馬番を取得
    # test_data_with_enhanced_featuresと同じ順序で予測結果が返されるため、race_keyでマージ
    test_data_race_keys_for_merging = pd.DataFrame({
        "race_key": test_data_for_merging["race_key"].values,
        "_order": range(len(test_data_for_merging))
    })
    # evaluation_data_with_japanese_keysからrace_keyと馬番の対応関係を取得
    # 同じrace_keyに複数の馬がいる場合を考慮して、行の順序で対応
    evaluation_data_subset_with_horse_numbers = evaluation_data_for_merging[["race_key", "馬番"]].copy()
    evaluation_data_subset_with_horse_numbers["_order"] = range(len(evaluation_data_subset_with_horse_numbers))
    
    # race_keyでマージ（同じrace_keyに複数の馬がいる場合、行の順序で対応）
    merged_with_horse_numbers = test_data_race_keys_for_merging.merge(evaluation_data_subset_with_horse_numbers, on=["race_key", "_order"], how="left")
    
    # マージに失敗した場合はrace_keyのみでマージ（順序が一致している場合）
    if merged_with_horse_numbers["馬番"].isna().any():
        # race_keyのみでマージ（最初の馬を取得）
        merged_with_horse_numbers = test_data_race_keys_for_merging.merge(
            evaluation_data_subset_with_horse_numbers[["race_key", "馬番"]].drop_duplicates(subset="race_key", keep="first"),
            on="race_key",
            how="left"
        )
    
    test_predictions_without_evaluation_data["馬番"] = merged_with_horse_numbers["馬番"].values

# evaluation_data_with_japanese_keys（eval_df、日本語キー、evaluation_schema.jsonに基づいて選択済み）を使用
# 注: キャッシュから読み込んだeval_dfは既にevaluation_schema.jsonに基づいて選択されているため、
#     再度select_evaluation()を呼び出す必要はない（仕様書に沿った実装）
evaluation_data_with_reset_index = evaluation_data_with_japanese_keys.copy()

# インデックスがrace_keyの場合はリセット
if evaluation_data_with_reset_index.index.name == "race_key":
    evaluation_data_with_reset_index = evaluation_data_with_reset_index.reset_index()
elif "race_key" not in evaluation_data_with_reset_index.columns:
    raise ValueError("evaluation_data_with_reset_indexにrace_key列が含まれていません")

# キャッシュデータの整合性確認（evaluation_schema.jsonに基づく必須カラムの存在確認）
required_evaluation_columns_for_prediction = ["race_key", "馬番", "着順"]
missing_evaluation_columns_for_prediction = [col for col in required_evaluation_columns_for_prediction if col not in evaluation_data_with_reset_index.columns]
if missing_evaluation_columns_for_prediction:
    raise ValueError(f"キャッシュから読み込んだeval_dfがevaluation_schema.jsonに準拠していません。必須カラムが不足: {missing_evaluation_columns_for_prediction}。キャッシュを削除して再処理してください。")

print(f"評価用データのカラム数: {len(evaluation_data_with_reset_index.columns)}")
print(f"評価用データのカラム: {list(evaluation_data_with_reset_index.columns)[:10]}...")  # 最初の10カラムを表示

# 予測結果をベースに、評価に必要な最小限の情報だけを追加
test_predictions_with_evaluation_data = test_predictions_without_evaluation_data.copy()

# 評価に必要な情報を追加（race_keyと馬番でマージ）
evaluation_data_for_prediction_merge = evaluation_data_with_reset_index.copy()
test_predictions_with_evaluation_data = test_predictions_with_evaluation_data.merge(evaluation_data_for_prediction_merge, on=["race_key", "馬番"], how="left")

# 予測順位を追加（レースごとにpredicted_scoreでソートして順位を付与）
test_predictions_with_evaluation_data = test_predictions_with_evaluation_data.sort_values(["race_key", "predicted_score"], ascending=[True, False])
test_predictions_with_evaluation_data["predicted_rank"] = test_predictions_with_evaluation_data.groupby("race_key").cumcount() + 1

# 評価用にrank列を追加（着順から）
if "着順" in test_predictions_with_evaluation_data.columns and "rank" not in test_predictions_with_evaluation_data.columns:
    test_predictions_with_evaluation_data["rank"] = pd.to_numeric(test_predictions_with_evaluation_data["着順"], errors="coerce")

if "rank" not in test_predictions_with_evaluation_data.columns or "馬番" not in test_predictions_with_evaluation_data.columns:
    raise ValueError("結合後の予測結果に必須列が含まれていません")

print(f"予測完了: {len(test_predictions_with_evaluation_data)}件")
print(f"\n予測結果のサンプル:")
print(test_predictions_with_evaluation_data.head(10))

# オッズデータの有無を確認
has_win_odds_data = "確定単勝オッズ" in test_predictions_with_evaluation_data.columns and test_predictions_with_evaluation_data["確定単勝オッズ"].notna().any()
win_odds_column_name = "確定単勝オッズ" if has_win_odds_data else None

print("\n" + "=" * 60)
print(f"モデル評価（{'オッズあり' if has_win_odds_data else 'オッズなし'}）:")
print("=" * 60)
from src.evaluator import evaluate_model, print_evaluation_results
evaluation_result = evaluate_model(test_predictions_with_evaluation_data, odds_col=win_odds_column_name)
print_evaluation_results(evaluation_result)

# %%
# ## 特徴量重要度
feature_importance_scores = model.feature_importance(importance_type='gain')
encoded_feature_names_from_predictor = [f for f in rank_predictor.features.encoded_feature_names if f in test_data_with_enhanced_features.columns]

# 新しく追加された特徴量も含めて重要度を計算
all_feature_names_in_test_data = list(test_data_with_enhanced_features.columns)
# rank列とrace_key列を除外
all_feature_names_in_test_data = [f for f in all_feature_names_in_test_data if f not in ['rank', 'race_key']]

# 重要度と特徴量名を対応付け
feature_importance_dict = {}
for i, feature_name in enumerate(encoded_feature_names_from_predictor[:len(feature_importance_scores)]):
    if feature_name in feature_importance_dict:
        # 重複がある場合は最大値を取る
        feature_importance_dict[feature_name] = max(feature_importance_dict[feature_name], feature_importance_scores[i])
    else:
        feature_importance_dict[feature_name] = feature_importance_scores[i]

# 新しく追加された特徴量の重要度を取得（モデルに含まれている場合）
model_feature_names_from_lightgbm = model.feature_name()
for i, feature_name in enumerate(model_feature_names_from_lightgbm):
    if feature_name not in feature_importance_dict:
        # 新しく追加された特徴量
        if i < len(feature_importance_scores):
            feature_importance_dict[feature_name] = feature_importance_scores[i]

feature_importance_dataframe = pd.DataFrame({
    'feature': list(feature_importance_dict.keys()),
    'importance': list(feature_importance_dict.values())
}).sort_values('importance', ascending=False)

print("\n特徴量重要度（上位30）:")
print(feature_importance_dataframe.head(30))

# 新しく追加された特徴量の重要度を確認
newly_added_feature_names = [f for f in feature_importance_dataframe['feature'] if '_rank' in f or '_x_' in f]
if newly_added_feature_names:
    print(f"\n新しく追加された特徴量（上位10）:")
    newly_added_features_dataframe = feature_importance_dataframe[feature_importance_dataframe['feature'].isin(newly_added_feature_names)].head(10)
    print(newly_added_features_dataframe)

# 可視化
plt.figure(figsize=(12, 10))
sns.barplot(data=feature_importance_dataframe.head(30), y='feature', x='importance')
plt.title('特徴量重要度（上位30）')
plt.xlabel('重要度')
plt.tight_layout()
plt.show()

