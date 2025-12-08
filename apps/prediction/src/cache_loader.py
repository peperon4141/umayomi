"""
生データ（raw data）のキャッシュ管理
JRDBデータを結合した状態を保存・読み込み・取得する
"""

from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
from tqdm import tqdm

from .data_loader import load_annual_pack_npz
from src.utils.feature_converter import FeatureConverter


class CacheLoader:
    """
    生データ（raw data）のキャッシュ管理クラス
    JRDBデータを結合した状態を保存・読み込み・取得する
    """

    def __init__(self, cache_dir: Union[str, Path] = "preprocessed_data"):
        """
        初期化

        Args:
            cache_dir: キャッシュディレクトリのパス（ベースパスからの相対パス）
        """
        self._raw_data_dict: Optional[Dict[str, pd.DataFrame]] = None
        self._cache_dir = Path(cache_dir)

    def set_raw_data(self, data_dict: Dict[str, pd.DataFrame]) -> None:
        """
        生データを設定

        Args:
            data_dict: データタイプをキー、DataFrameを値とする辞書
        """
        self._raw_data_dict = {k: v.copy() for k, v in data_dict.items()}

    def get_raw_data(self, data_type: Optional[str] = None) -> Optional[Union[pd.DataFrame, Dict[str, pd.DataFrame]]]:
        """
        生データ（raw data）を取得

        Args:
            data_type: データタイプ（例: 'SED', 'BAC'）。Noneの場合は全データを辞書で返す

        Returns:
            指定したデータタイプのDataFrame、または全データの辞書、またはNone
        """
        if self._raw_data_dict is None:
            return None

        if data_type is None:
            return {k: v.copy() for k, v in self._raw_data_dict.items()}

        # SECはSEDとして扱う（内部統一）
        internal_data_type = "SED" if data_type == "SEC" else data_type

        if internal_data_type in self._raw_data_dict:
            return self._raw_data_dict[internal_data_type].copy()
        return None

    def get_evaluation_data(self) -> Optional[pd.DataFrame]:
        """
        評価用データを取得（着順・タイム・オッズなど）

        Returns:
            評価用データのDataFrame（race_key, 馬番, rank, タイム, 確定単勝オッズなど）またはNone
        """
        if self._raw_data_dict is None or "SED" not in self._raw_data_dict:
            return None

        sed_df = self._raw_data_dict["SED"].copy()

        if len(sed_df) == 0:
            return None

        # race_keyを生成（まだない場合）
        if "race_key" not in sed_df.columns:
            # 必須設定値を明示的にチェック（fallback禁止）
            if "BAC" in self._raw_data_dict:
                bac_df = self._raw_data_dict["BAC"]
                sed_df = FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=True)
            else:
                sed_df = FeatureConverter.add_race_key_to_df(sed_df, use_bac_date=False)

        # 評価に必要なカラムを抽出
        eval_columns = ["race_key", "馬番"]

        # 着順
        if "着順" in sed_df.columns:
            eval_columns.append("着順")

        # タイム
        if "タイム" in sed_df.columns:
            eval_columns.append("タイム")

        # オッズ関連
        odds_columns = [col for col in sed_df.columns if 'オッズ' in col]
        eval_columns.extend(odds_columns)

        # 存在するカラムのみ選択
        available_columns = [col for col in eval_columns if col in sed_df.columns]

        if len(available_columns) < 2:  # race_keyと馬番以外にカラムがない
            return None

        eval_df = sed_df[available_columns].copy()

        # race_keyと馬番が有効な行のみを保持
        eval_df = eval_df[eval_df["race_key"].notna() & eval_df["馬番"].notna()].copy()

        if len(eval_df) == 0:
            return None

        # 型を統一
        eval_df["race_key"] = eval_df["race_key"].astype(str)
        eval_df["馬番"] = pd.to_numeric(eval_df["馬番"], errors="coerce")

        # 着順をrankにリネーム（評価で使用するため）
        if "着順" in eval_df.columns:
            eval_df = eval_df.rename(columns={"着順": "rank"})
            eval_df["rank"] = pd.to_numeric(eval_df["rank"], errors="coerce")
            # 着順が0以下のデータを除外
            eval_df = eval_df[eval_df["rank"] > 0].copy()

        return eval_df

    def merge_evaluation_data(
        self, predictions_df: pd.DataFrame,
        eval_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        予測結果に評価用データ（着順・タイム・オッズなど）をマージ

        Args:
            predictions_df: 予測結果のDataFrame（race_key, 馬番を含む）
            eval_columns: マージする評価用カラムのリスト（Noneの場合は全て）

        Returns:
            評価用データがマージされたDataFrame
        """
        eval_df = self.get_evaluation_data()

        if eval_df is None or len(eval_df) == 0:
            print("警告: 評価用データが取得できませんでした")
            return predictions_df.copy()

        # マージ用のDataFrameを準備
        result_df = predictions_df.copy()

        # インデックスがrace_keyの場合はリセット
        if result_df.index.name == "race_key":
            result_df = result_df.reset_index()
        elif "race_key" not in result_df.columns:
            raise ValueError("predictions_dfにrace_keyが存在しません")

        # race_keyと馬番の型を統一
        result_df["race_key"] = result_df["race_key"].astype(str)
        if "馬番" in result_df.columns:
            result_df["馬番"] = pd.to_numeric(result_df["馬番"], errors="coerce")

        # マージするカラムを決定
        if eval_columns is None:
            # デフォルト: race_keyと馬番以外の全てのカラム
            merge_columns = [col for col in eval_df.columns if col not in ["race_key", "馬番"]]
        else:
            # 指定されたカラムのみ（race_keyと馬番は除く）
            merge_columns = [col for col in eval_columns if col in eval_df.columns and col not in ["race_key", "馬番"]]

        if not merge_columns:
            print("警告: マージする評価用カラムがありません")
            return result_df

        # マージ用のDataFrameを作成（race_key, 馬番, マージするカラム）
        merge_df = eval_df[["race_key", "馬番"] + merge_columns].copy()

        # マージ
        result_df = result_df.merge(
            merge_df,
            on=["race_key", "馬番"],
            how="left"
        )

        return result_df

    def load_data(
        self,
        base_path: Union[str, Path],
        data_types: List[str],
        years: Optional[List[int]] = None,
        use_annual_pack: bool = True,
        use_cache: bool = True,
    ) -> bool:
        """
        データを読み込む（キャッシュがあれば読み込み、なければdata_loaderから読み込む）

        Args:
            base_path: NPZファイルが格納されているベースパス
            data_types: データタイプのリスト（例: ['BAC', 'KYI', 'SED', 'UKC']）
            years: 年度のリスト（年度パックを使用する場合）
            use_annual_pack: 年度パックを使用するかどうか
            use_cache: キャッシュを使用するかどうか

        Returns:
            読み込み成功した場合True、失敗した場合False
        """
        base_path = Path(base_path)

        # キャッシュから読み込みを試みる
        if use_cache:
            if self.load_from_cache(data_types, years, use_annual_pack, base_path):
                return True

        # キャッシュがない場合、data_loaderから読み込む
        data_dict = {}
        for data_type in tqdm(data_types, desc="データ読み込み"):
            try:
                # SECはSEDとして扱う（内部統一）
                internal_data_type = "SED" if data_type == "SEC" else data_type

                if use_annual_pack and years:
                    # 年度パックを使用
                    dfs = []
                    for year in years:
                        try:
                            df = load_annual_pack_npz(base_path, data_type, year)
                            dfs.append(df)
                        except FileNotFoundError:
                            continue

                    if dfs:
                        # SECはSEDとして保存（内部統一）
                        if internal_data_type in data_dict:
                            data_dict[internal_data_type] = pd.concat([data_dict[internal_data_type]] + dfs, ignore_index=True)
                        else:
                            data_dict[internal_data_type] = pd.concat(dfs, ignore_index=True)
                else:
                    raise NotImplementedError("日次データの読み込みは後で実装")

            except Exception as e:
                raise

        if data_dict:
            self.set_raw_data(data_dict)
            return True
        return False

    def generate_cache_key(
        self, data_types: List[str], years: Optional[List[int]], use_annual_pack: bool
    ) -> str:
        """
        キャッシュキーを生成（わかりやすい形式）

        Args:
            data_types: データタイプのリスト
            years: 年度のリスト
            use_annual_pack: 年度パックを使用するかどうか

        Returns:
            キャッシュキー（例: BAC_KYI_SED_UKC_2024_annual）
        """
        # データタイプをソートして結合
        data_types_str = "_".join(sorted(data_types))

        # 年度をソートして結合
        if years:
            years_str = "_".join(map(str, sorted(years)))
        else:
            years_str = "all"

        # 年度パック使用有無
        pack_type = "annual" if use_annual_pack else "daily"

        # わかりやすい形式で結合
        cache_key = f"{data_types_str}_{years_str}_{pack_type}"

        # ファイル名に使えない文字を置換（安全のため）
        cache_key = cache_key.replace("/", "_").replace("\\", "_")

        return cache_key

    def save_to_cache(
        self,
        data_types: List[str],
        years: Optional[List[int]],
        use_annual_pack: bool,
        base_path: Union[str, Path],
    ) -> None:
        """
        生データ（結合済み）をキャッシュに保存

        Args:
            data_types: データタイプのリスト
            years: 年度のリスト
            use_annual_pack: 年度パックを使用するかどうか
            base_path: ベースパス
        """
        if self._raw_data_dict is None or len(self._raw_data_dict) == 0:
            return

        base_path = Path(base_path)
        cache_dir = base_path / self._cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_key = self.generate_cache_key(data_types, years, use_annual_pack)
        raw_data_path = cache_dir / f"{cache_key}_raw_data.npz"

        # 各データタイプのDataFrameをNPZ形式で保存
        raw_data_dict = {}
        for data_type, df in self._raw_data_dict.items():
            # 各カラムを配列として保存
            for col in df.columns:
                key = f"{data_type}_{col}"
                raw_data_dict[key] = df[col].values

            # インデックス情報も保存
            raw_data_dict[f"{data_type}_index"] = df.index.values
            if df.index.name:
                raw_data_dict[f"{data_type}_index_name"] = df.index.name

        # データタイプのリストも保存
        raw_data_dict["_data_types"] = list(self._raw_data_dict.keys())

        np.savez_compressed(raw_data_path, **raw_data_dict)

        total_rows = sum(len(df) for df in self._raw_data_dict.values())
        print(f"生データをキャッシュに保存しました: {raw_data_path}")
        print(f"  データタイプ数: {len(self._raw_data_dict)}")
        print(f"  総データ数: {total_rows}件")

    def load_from_cache(
        self,
        data_types: List[str],
        years: Optional[List[int]],
        use_annual_pack: bool,
        base_path: Union[str, Path],
    ) -> bool:
        """
        生データ（結合済み）をキャッシュから読み込み

        Args:
            data_types: データタイプのリスト
            years: 年度のリスト
            use_annual_pack: 年度パックを使用するかどうか
            base_path: ベースパス

        Returns:
            読み込み成功した場合True、失敗した場合False
        """
        base_path = Path(base_path)
        cache_dir = base_path / self._cache_dir

        if not cache_dir.exists():
            return False

        cache_key = self.generate_cache_key(data_types, years, use_annual_pack)
        raw_data_path = cache_dir / f"{cache_key}_raw_data.npz"

        if not raw_data_path.exists():
            print("デバッグ: 生データのキャッシュが見つかりません")
            return False

        try:
            # 生データを読み込み
            loaded = np.load(raw_data_path, allow_pickle=True)

            # データタイプのリストを取得
            if "_data_types" not in loaded.files:
                print("デバッグ: 生データのキャッシュにデータタイプ情報がありません")
                return False

            saved_data_types = loaded["_data_types"].tolist()
            self._raw_data_dict = {}

            # 各データタイプのDataFrameを復元
            for data_type in saved_data_types:
                # このデータタイプのカラムを取得
                columns = []
                for key in loaded.files:
                    if key.startswith(f"{data_type}_") and not key.endswith("_index") and not key.endswith("_index_name"):
                        col_name = key[len(f"{data_type}_"):]
                        columns.append(col_name)

                if not columns:
                    continue

                # DataFrameを作成
                data_dict = {}
                for col in columns:
                    key = f"{data_type}_{col}"
                    if key in loaded.files:
                        data_dict[col] = loaded[key]

                df = pd.DataFrame(data_dict)

                # インデックスを復元
                index_key = f"{data_type}_index"
                if index_key in loaded.files:
                    df.index = loaded[index_key]
                    index_name_key = f"{data_type}_index_name"
                    if index_name_key in loaded.files:
                        df.index.name = loaded[index_name_key].item()

                self._raw_data_dict[data_type] = df

            total_rows = sum(len(df) for df in self._raw_data_dict.values())
            print(f"デバッグ: 生データをキャッシュから読み込みました")
            print(f"  データタイプ数: {len(self._raw_data_dict)}")
            print(f"  総データ数: {total_rows}件")
            return True
        except Exception as e:
            print(f"デバッグ: 生データのキャッシュ読み込みに失敗: {e}")
            import traceback
            traceback.print_exc()
            self._raw_data_dict = None
            return False

    def save_combined_data(
        self,
        combined_df: pd.DataFrame,
        data_types: List[str],
        years: Optional[List[int]],
        use_annual_pack: bool,
        base_path: Union[str, Path],
    ) -> None:
        """
        結合済みデータをキャッシュに保存

        Args:
            combined_df: 結合済みのDataFrame
            data_types: データタイプのリスト
            years: 年度のリスト
            use_annual_pack: 年度パックを使用するかどうか
            base_path: ベースパス
        """
        base_path = Path(base_path)
        cache_dir = base_path / self._cache_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_key = self.generate_cache_key(data_types, years, use_annual_pack)
        combined_data_path = cache_dir / f"{cache_key}_combined_data.npz"

        # DataFrameを辞書に変換してNPZ形式で保存
        data_dict = {}
        for col in combined_df.columns:
            data_dict[col] = combined_df[col].values

        # インデックスも保存
        data_dict["_index"] = combined_df.index.values
        if combined_df.index.name:
            data_dict["_index_name"] = combined_df.index.name

        # メタデータも保存
        data_dict["_num_rows"] = len(combined_df)
        data_dict["_num_columns"] = len(combined_df.columns)

        np.savez_compressed(combined_data_path, **data_dict)
        print(f"結合済みデータをキャッシュに保存しました: {combined_data_path} ({len(combined_df)}行, {len(combined_df.columns)}列)")

    def load_combined_data(
        self,
        data_types: List[str],
        years: Optional[List[int]],
        use_annual_pack: bool,
        base_path: Union[str, Path],
    ) -> Optional[pd.DataFrame]:
        """
        結合済みデータをキャッシュから読み込み

        Args:
            data_types: データタイプのリスト
            years: 年度のリスト
            use_annual_pack: 年度パックを使用するかどうか
            base_path: ベースパス

        Returns:
            結合済みのDataFrame（見つからない場合はNone）
        """
        base_path = Path(base_path)
        cache_dir = base_path / self._cache_dir
        if not cache_dir.exists():
            return None

        cache_key = self.generate_cache_key(data_types, years, use_annual_pack)
        combined_data_path = cache_dir / f"{cache_key}_combined_data.npz"

        if not combined_data_path.exists():
            return None

        # データを読み込み（NPZ形式）
        loaded = np.load(combined_data_path, allow_pickle=True)

        # DataFrameに変換
        data_dict = {}
        for key in loaded.files:
            if not key.startswith("_"):
                data_dict[key] = loaded[key]

        df = pd.DataFrame(data_dict)

        # インデックスを復元
        if "_index" in loaded.files:
            df.index = loaded["_index"]
            if "_index_name" in loaded.files:
                df.index.name = loaded["_index_name"].item()

        print(f"結合済みデータをキャッシュから読み込みました: {combined_data_path} ({len(df)}行, {len(df.columns)}列)")
        return df

