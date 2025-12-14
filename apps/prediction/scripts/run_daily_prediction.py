"""今日のレースデータに対して予測を実行するスクリプト"""

import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートをパスに追加
base_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(base_path / "apps" / "prediction"))

from src.executor.prediction_executor import PredictionExecutor

if __name__ == "__main__":
    # コマンドライン引数から日付とJSONインデントを取得
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='日次データの予測を実行')
    parser.add_argument('date', nargs='?', help='予測対象日付（YYYY-MM-DD形式、省略時は今日）')
    parser.add_argument('--json-indent', type=int, default=2, 
                       help='JSON出力のインデント（None=1行、2=2スペース、4=4スペースなど、デフォルト: 2）')
    parser.add_argument('--json-compact', action='store_true',
                       help='JSONを1行で出力（--json-indentより優先）')
    
    args = parser.parse_args()
    
    if args.date:
        date_str = args.date
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"エラー: 日付形式が正しくありません。YYYY-MM-DD形式で指定してください。例: 2025-12-13")
            exit(1)
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        date_obj = datetime.now()
        date_str = date_obj.strftime("%Y-%m-%d")
    
    # JSONインデントの決定
    json_indent = None if args.json_compact else args.json_indent
    
    # パス設定
    parquet_base_path = base_path / "apps" / "prediction" / "cache" / "jrdb" / "parquet"
    daily_data_path = str(base_path / "data" / "daily")
    model_path = str(base_path / "apps" / "prediction" / "models" / "rank_model_202512111031_v1.txt")
    output_path = str(base_path / "apps" / "prediction" / "output" / f"prediction_results_{date_str}.json")
    
    print(f"予測実行を開始します...")
    print(f"  日付: {date_str}")
    print(f"  モデル: {model_path}")
    print(f"  日次データ: {daily_data_path}")
    print(f"  出力先: {output_path}")
    
    # データの存在確認
    daily_folder = base_path / "data" / "daily" / f"{date_obj.month:02d}" / f"{date_obj.day:02d}"
    if not daily_folder.exists():
        print(f"\n警告: 日次データフォルダが見つかりません: {daily_folder}")
        print("データ取得が必要です。")
        exit(1)
    
    try:
        # 予測実行
        results_df = PredictionExecutor.execute_daily_prediction(
            date_str=date_str,
            model_path=model_path,
            daily_data_path=daily_data_path,
            base_path=base_path,
            parquet_base_path=parquet_base_path,
            output_path=output_path,
            json_indent=json_indent,
        )
        
        print(f"\n予測実行が完了しました！")
        print(f"  予測結果の行数: {len(results_df)}")
        print(f"  予測結果のカラム: {list(results_df.columns)}")
        print(f"  出力ファイル: {output_path}")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

