"""JRDBデータの前処理（NPZファイルからデータを読み込み、特徴量に変換）。未来の情報を含めない（統計特徴量はshift(1)で計算）。"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
from sklearn import preprocessing

from .cache_loader import CacheLoader
from .feature_converter import FeatureConverter
from .feature_extractors import PreviousRaceExtractor, StatisticalFeatureCalculator
from .features import Features


class Preprocessor:
    """JRDBデータの前処理クラス。NPZファイルからデータを読み込み、予測モデル用の特徴量に変換。"""

    def __init__(self):
        self.features = Features()
        self._df = None
        self.label_encoders: Dict[str, preprocessing.LabelEncoder] = {}
        self._preprocessed_data_dir = Path("preprocessed_data")
        self._cache_loader = CacheLoader(cache_dir=self._preprocessed_data_dir)  # 生データのキャッシュ管理
        self._previous_race_extractor = PreviousRaceExtractor(self._cache_loader)  # 前走データ抽出
        self._statistical_feature_calculator = StatisticalFeatureCalculator(self._cache_loader)  # 統計特徴量計算


    def generate_race_key(
        self,
        year: int,
        month: int,
        day: int,
        place_code: str,
        kaisai_round: int,
        kaisai_day: str,
        race_number: int,
    ) -> str:
        """レースキーを生成（FeatureConverterへの委譲）。例: "20241102_01_1_a_01"を返す。"""
        return FeatureConverter.generate_race_key(
            year, month, day, place_code, kaisai_round, kaisai_day, race_number
        )


    def combine_data_types(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        複数のデータタイプを結合

        Args:
            data_dict: データタイプをキー、DataFrameを値とする辞書

        Returns:
            結合されたDataFrame
        """
        if not data_dict:
            raise ValueError("データが空です")
        if "KYI" not in data_dict:
            raise ValueError("KYIデータが必要です。現在のデータタイプ: " + ", ".join(data_dict.keys()))
        if "BAC" not in data_dict:
            raise ValueError("BACデータが必要です。現在のデータタイプ: " + ", ".join(data_dict.keys()))

        base_type = "KYI"
        combined_df = data_dict["KYI"].copy()

        # レースキーを生成（KYIデータには年月日がないため、BACデータから年月日を取得してrace_keyを生成）
        bac_df = FeatureConverter.add_race_key_to_df(data_dict["BAC"].copy(), use_bac_date=False)
        race_key_cols = ["場コード", "回", "日", "R", "race_key"]
        combined_df = combined_df.merge(
            bac_df[race_key_cols].drop_duplicates(),
            on=["場コード", "回", "日", "R"],
            how="inner",
        )

        # 他のデータタイプを結合
        for data_type, df in data_dict.items():
            if data_type == base_type:
                continue

            # 必須設定値を明示的にチェック（fallback禁止）
            if data_type not in self.features.DATA_TYPE_JOIN_KEYS:
                raise ValueError(f"データタイプ '{data_type}' の結合キー定義がありません。DATA_TYPE_JOIN_KEYSに追加してください。")
            join_config = self.features.DATA_TYPE_JOIN_KEYS[data_type]

            # race_keyが必要な場合は生成
            if "race_key" in join_config["keys"]:
                df = FeatureConverter.add_race_key_to_df(
                    df, bac_df=data_dict["BAC"], use_bac_date=join_config["use_bac_date"]
                )

            # 結合キーが存在するか確認
            join_keys = [k for k in join_config["keys"] if k in combined_df.columns and k in df.columns]
            if not join_keys:
                continue

            combined_df = combined_df.merge(df, on=join_keys, how="left", suffixes=("", f"_{data_type}"))

        return combined_df

    def extract_previous_race_data(self, df: pd.DataFrame, sed_df: pd.DataFrame) -> pd.DataFrame:
        """
        SEDデータから前走データを抽出

        Args:
            df: メインのDataFrame
            sed_df: SED（成績データ）のDataFrame

        Returns:
            前走データが追加されたDataFrame
        """
        return self._previous_race_extractor.extract(df, sed_df)

    def add_statistical_features(self, df: pd.DataFrame, sed_df: pd.DataFrame) -> pd.DataFrame:
        """
        馬、騎手、調教師の過去成績統計特徴量を追加

        Args:
            df: メインのDataFrame
            sed_df: SED（成績データ）のDataFrame

        Returns:
            統計特徴量が追加されたDataFrame
        """
        return self._statistical_feature_calculator.calculate(df, sed_df)


    def convert_to_numeric(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数値フィールドを数値型に変換
        """
        df = FeatureConverter.add_start_datetime_to_df(df.copy())

        # フィールド名をマッピング（JRDBフィールド名 → 特徴量名）
        for jrdb_field, feature_name in self.features.field_mapping.items():
            if jrdb_field in df.columns and feature_name not in df.columns:
                df[feature_name] = df[jrdb_field]

        # 数値変換
        for feature_name in self.features.numeric_features:
            if feature_name not in df.columns or feature_name == "start_datetime":
                continue
            df[feature_name] = pd.to_numeric(
                df[feature_name],
                errors="coerce",
                downcast="integer" if feature_name in self.features.integer_features else None,
            )

        return df

    def label_encode(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        カテゴリカル特徴量をラベルエンコーディング
        前走データ（prev_*）のground_conditionフィールドは除外（数値変換済みのため）
        """
        # 必要なカラムのみをコピー（メモリ効率化）
        df = df.copy()
        
        # エンコード済みカラムを一括で作成（df.insert()を避けて高速化）
        encoded_columns = {}
        column_order = list(df.columns)

        for feature_info in self.features.categorical_features:
            feature_name = feature_info["name"]
            if feature_name not in df.columns:
                continue
            if feature_name.startswith("prev_") and "ground_condition" in feature_name:
                continue

            new_column_name = f"e_{feature_name}"
            try:
                if "map" in feature_info:
                    encoded_columns[new_column_name] = df[feature_name].map(feature_info["map"]).fillna(-1).astype("category")
                else:
                    # LabelEncoderを使用
                    if feature_name not in self.label_encoders:
                        self.label_encoders[feature_name] = preprocessing.LabelEncoder()
                        is_numeric = df[feature_name].dtype in ["float64", "float32", "int64", "int32"]
                        feature_values = df[feature_name].astype(str).replace("nan", "__UNKNOWN__") if is_numeric else df[feature_name].fillna("__UNKNOWN__")
                        self.label_encoders[feature_name].fit(feature_values)

                    is_numeric = df[feature_name].dtype in ["float64", "float32", "int64", "int32"]
                    feature_values = df[feature_name].astype(str).replace("nan", "__UNKNOWN__") if is_numeric else df[feature_name].fillna("__UNKNOWN__")
                    encoded_columns[new_column_name] = pd.Series(
                        self.label_encoders[feature_name].transform(feature_values),
                        index=df.index,
                        dtype="category"
                    )
            except Exception as e:
                raise

        # エンコード済みカラムを適切な位置に挿入
        for new_column_name, encoded_series in encoded_columns.items():
            feature_name = new_column_name[2:]  # "e_"を除去
            if feature_name in column_order:
                insert_pos = column_order.index(feature_name) + 1
                column_order.insert(insert_pos, new_column_name)
            else:
                column_order.append(new_column_name)
            df[new_column_name] = encoded_series

        # カラムの順序を維持
        df = df[column_order]

        return df

    def process(
        self,
        base_path: Union[str, Path],
        data_types: List[str],
        years: Optional[List[int]] = None,
        use_annual_pack: bool = True,
        use_cache: bool = True,
        save_cache: bool = True,
    ) -> pd.DataFrame:
        """データの読み込みから前処理まで一括実行。前処理済みのDataFrameを返す。"""
        base_path = Path(base_path)

        # 前処理済みデータをキャッシュから読み込む
        cached_df = self.load_preprocessed_data(data_types, years, use_annual_pack, base_path)
        if cached_df is not None:
            self._cache_loader.load_from_cache(data_types, years, use_annual_pack, base_path)
            self._df = cached_df
            return self._df

        # データを読み込む（キャッシュがあれば読み込み、なければdata_loaderから読み込む）
        if not self._cache_loader.load_data(base_path, data_types, years, use_annual_pack, use_cache=use_cache):
            raise ValueError("読み込めるデータがありませんでした")

        data_dict = self._cache_loader.get_raw_data()
        if data_dict is None:
            raise ValueError("データが取得できませんでした")

        # 指定されたデータタイプがすべて存在するかチェック
        missing_types = [dt for dt in data_types if dt not in data_dict and (dt != "SEC" or "SED" not in data_dict)]
        if missing_types:
            raise ValueError(f"指定されたデータタイプが存在しません: {missing_types}。読み込まれたデータタイプ: {', '.join(data_dict.keys())}")

        # 結合済みデータをキャッシュから読み込む
        combined_df = self._cache_loader.load_combined_data(data_types, years, use_annual_pack, base_path)
        if combined_df is None:
            combined_df = self.combine_data_types(data_dict)
            # 結合済みデータをキャッシュに保存
            if save_cache:
                self._cache_loader.save_combined_data(combined_df, data_types, years, use_annual_pack, base_path)

        # 前走データ抽出と統計特徴量計算
        sed_df = self._cache_loader.get_raw_data("SED")
        bac_df = self._cache_loader.get_raw_data("BAC")
        if sed_df is not None:
            combined_df = self._previous_race_extractor.extract(combined_df, sed_df)
            combined_df = self._statistical_feature_calculator.calculate(combined_df, sed_df)
            combined_df = self._add_rank_and_time(combined_df, sed_df, bac_df)

        # 数値変換
        combined_df = self.convert_to_numeric(combined_df)
        combined_df = self._convert_prev_race_types(combined_df)

        # ラベルエンコーディング
        combined_df = self.label_encode(combined_df)

        # データ型の最適化
        combined_df = self.optimize_dtypes(combined_df)
        combined_df = self._cleanup_object_columns(combined_df)

        # レースIDをインデックスに設定
        if "race_key" in combined_df.columns:
            combined_df.set_index("race_key", inplace=True)
            if "start_datetime" in combined_df.columns:
                combined_df = combined_df.sort_values("start_datetime", ascending=True)

        self._df = combined_df

        # キャッシュに保存
        if save_cache:
            self.save_preprocessed_data(combined_df, data_types, years, use_annual_pack, base_path)
            self._cache_loader.save_to_cache(data_types, years, use_annual_pack, base_path)

        return self._df

    def _convert_prev_race_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        前走データのobject型フィールドを数値型に変換（統合）

        Args:
            df: 対象のDataFrame

        Returns:
            変換後のDataFrame
        """
        df = df.copy()
        for col in df.columns:
            if not col.startswith("prev_"):
                continue
            if df[col].dtype == "object" or df[col].dtype.name == "object":
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df

    def _cleanup_object_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        ラベルエンコーディング後に残ったobject型カラムを削除

        Args:
            df: 対象のDataFrame

        Returns:
            クリーンアップ後のDataFrame
        """
        df = df.copy()
        for col in df.columns:
            if col.startswith("prev_") and (df[col].dtype == "object" or df[col].dtype.name == "object"):
                df = df.drop(columns=[col])
        return df

    def _add_rank_and_time(
        self, df: pd.DataFrame, sed_df: pd.DataFrame, bac_df: Optional[pd.DataFrame]
    ) -> pd.DataFrame:
        """
        SEDデータからrankとタイムを追加

        Args:
            df: メインのDataFrame
            sed_df: SEDデータのDataFrame
            bac_df: BACデータのDataFrame（オプション）

        Returns:
            rankとタイムが追加されたDataFrame
        """
        if "着順" not in sed_df.columns:
            return df

        df = df[df["race_key"].notna()].copy()
        sed_df = FeatureConverter.add_race_key_to_df(sed_df, bac_df=bac_df, use_bac_date=bac_df is not None)

        if "race_key" not in sed_df.columns or "馬番" not in sed_df.columns:
            return df

        df = self._merge_rank_and_time(df, self._extract_rank_and_time_from_sed(sed_df))
        if "タイム" in df.columns:
            df["タイム"] = df["タイム"].apply(FeatureConverter.convert_sed_time_to_seconds)
        return df

    def _extract_rank_and_time_from_sed(self, sed_df: pd.DataFrame) -> pd.DataFrame:
        """
        SEDデータからrankとタイムを抽出

        Args:
            sed_df: SEDデータのDataFrame

        Returns:
            rankとタイムを含むDataFrame
        """
        # rankを抽出
        sed_rank = sed_df[["race_key", "馬番", "着順"]].copy()
        sed_rank = sed_rank.rename(columns={"着順": "rank"})
        sed_rank["rank"] = pd.to_numeric(sed_rank["rank"], errors="coerce")

        # 着順が0以下のデータを除外
        sed_rank = sed_rank[sed_rank["rank"] > 0].copy()

        # タイムを抽出
        sed_time = sed_df[["race_key", "馬番", "タイム"]].copy()

        # マージ
        sed_data = sed_rank.merge(sed_time, on=["race_key", "馬番"], how="left")

        # 型を統一
        sed_data["race_key"] = sed_data["race_key"].astype(str)
        sed_data["馬番"] = pd.to_numeric(sed_data["馬番"], errors="coerce")

        return sed_data

    def _merge_rank_and_time(self, df: pd.DataFrame, sed_data: pd.DataFrame) -> pd.DataFrame:
        """
        rankとタイムをマージ

        Args:
            df: メインのDataFrame
            sed_data: rankとタイムを含むSEDデータ

        Returns:
            マージ後のDataFrame
        """
        df["race_key"] = df["race_key"].astype(str)
        df["馬番"] = pd.to_numeric(df["馬番"], errors="coerce")

        # マージ可能なrace_keyのみを使用
        common_race_keys = set(df["race_key"].unique()) & set(sed_data["race_key"].unique())
        if len(common_race_keys) < len(df["race_key"].unique()):
            df = df[df["race_key"].isin(common_race_keys)].copy()

        df = df.merge(sed_data, on=["race_key", "馬番"], how="left", suffixes=("", "_sed"))

        # 重複カラムを統合
        if "rank_sed" in df.columns:
            df["rank"] = df["rank"].fillna(df["rank_sed"])
            df = df.drop(columns=["rank_sed"])
        if "タイム_sed" in df.columns:
            df["タイム"] = df["タイム"].fillna(df["タイム_sed"])
            df = df.drop(columns=["タイム_sed"])

        return df

    def get_raw_data(self, data_type: Optional[str] = None) -> Optional[Union[pd.DataFrame, Dict[str, pd.DataFrame]]]:
        """
        生データ（raw data）を取得

        Args:
            data_type: データタイプ（例: 'SED', 'BAC'）。Noneの場合は全データを辞書で返す

        Returns:
            指定したデータタイプのDataFrame、または全データの辞書、またはNone
        """
        return self._cache_loader.get_raw_data(data_type)

    def get_evaluation_data(self) -> Optional[pd.DataFrame]:
        """
        評価用データを取得（着順・タイム・オッズなど）

        Returns:
            評価用データのDataFrame（race_key, 馬番, rank, タイム, 確定単勝オッズなど）またはNone
        """
        return self._cache_loader.get_evaluation_data()

    def get_odds_data(self) -> Optional[pd.DataFrame]:
        """
        オッズデータを取得（後方互換性のためのラッパー）

        Returns:
            評価用データのDataFrame（race_key, 馬番, 確定単勝オッズなど）またはNone
        """
        return self.get_evaluation_data()

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
        return self._cache_loader.merge_evaluation_data(predictions_df, eval_columns)


    def save_preprocessed_data(
        self,
        df: pd.DataFrame,
        data_types: List[str],
        years: Optional[List[int]],
        use_annual_pack: bool,
        base_path: Union[str, Path],
    ) -> Path:
        """
        前処理済みデータを保存

        Args:
            df: 前処理済みのDataFrame
            data_types: データタイプのリスト
            years: 年度のリスト
            use_annual_pack: 年度パックを使用するかどうか
            base_path: ベースパス（保存先の親ディレクトリ）

        Returns:
            保存先のパス
        """
        base_path = Path(base_path)
        cache_dir = base_path / self._preprocessed_data_dir
        cache_dir.mkdir(parents=True, exist_ok=True)

        # キャッシュキーを生成
        cache_key = self._cache_loader.generate_cache_key(data_types, years, use_annual_pack)

        # メタデータを保存
        metadata = {
            "data_types": data_types,
            "years": years,
            "use_annual_pack": use_annual_pack,
            "cache_key": cache_key,
            "num_rows": len(df),
            "num_columns": len(df.columns),
        }
        metadata_path = cache_dir / f"{cache_key}_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # データをNPZ形式で保存（PyArrowの互換性問題を回避）
        # NPZ形式はカテゴリカル型を問題なく保存できる
        data_path = cache_dir / f"{cache_key}_data.npz"

        # DataFrameを辞書に変換してNPZ形式で保存
        data_dict = {}
        for col in df.columns:
            # カテゴリカル型はそのまま保存可能（NumPy配列に変換される）
            data_dict[col] = df[col].values

        # インデックスも保存
        data_dict["_index"] = df.index.values
        if df.index.name:
            data_dict["_index_name"] = df.index.name

        # 圧縮付きNPZ形式で保存
        np.savez_compressed(data_path, **data_dict)


        return data_path

    def load_preprocessed_data(
        self,
        data_types: List[str],
        years: Optional[List[int]],
        use_annual_pack: bool,
        base_path: Union[str, Path],
    ) -> Optional[pd.DataFrame]:
        """
        前処理済みデータを読み込み

        Args:
            data_types: データタイプのリスト
            years: 年度のリスト
            use_annual_pack: 年度パックを使用するかどうか
            base_path: ベースパス（保存先の親ディレクトリ）

        Returns:
            前処理済みのDataFrame（見つからない場合はNone）
        """
        base_path = Path(base_path)
        cache_dir = base_path / self._preprocessed_data_dir
        if not cache_dir.exists():
            return None

        cache_key = self._cache_loader.generate_cache_key(data_types, years, use_annual_pack)
        metadata_path = cache_dir / f"{cache_key}_metadata.json"
        data_path = cache_dir / f"{cache_key}_data.npz"
        if not metadata_path.exists() or not data_path.exists():
            return None

        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)

        if metadata["data_types"] != data_types or metadata["years"] != years or metadata["use_annual_pack"] != use_annual_pack:
            return None

        loaded = np.load(data_path, allow_pickle=True)
        data_dict = {key: loaded[key] for key in loaded.files if not key.startswith("_")}
        df = pd.DataFrame(data_dict)

        if "_index" in loaded.files:
            df.index = loaded["_index"]
            if "_index_name" in loaded.files:
                df.index.name = loaded["_index_name"].item()

        # カテゴリカル型を復元（NPZ形式ではobject型として読み込まれる）
        for col in df.columns:
            if col.startswith("e_") and df[col].dtype == "object":
                if df[col].nunique() / len(df) <= 0.5:
                    df[col] = df[col].astype("category")

        return df

    def split(
        self, df: pd.DataFrame, train_ratio: float = 0.8
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        学習・検証データに分割（レース単位で時系列分割）

        Args:
            df: 前処理済みのDataFrame
            train_ratio: 学習データの割合

        Returns:
            (train_df, val_df) のタプル
        """
        if df.index.name != "race_key":
            raise ValueError("DataFrameのインデックスが'race_key'ではありません")

        unique_race_keys = df.index.unique().tolist()
        num_races = len(unique_race_keys)
        border_index = int(round(num_races * train_ratio, 0))

        train_race_keys = unique_race_keys[:border_index]
        val_race_keys = unique_race_keys[border_index:]

        train_df = df[df.index.isin(train_race_keys)]
        val_df = df[df.index.isin(val_race_keys)]

        return train_df, val_df

    def optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データ型を最適化してメモリ使用量と計算速度を向上

        Args:
            df: DataFrame

        Returns:
            データ型が最適化されたDataFrame
        """
        df = df.copy()

        # float64をfloat32に変換（メモリ使用量が約半分に）
        for col in df.select_dtypes(include=["float64"]).columns:
            df[col] = df[col].astype("float32")

        # int64をint32に変換（メモリ使用量が約半分に）
        for col in df.select_dtypes(include=["int64"]).columns:
            col_min, col_max = df[col].min(), df[col].max()
            if -2147483648 <= col_min <= col_max <= 2147483647:
                df[col] = df[col].astype("int32")

        # カテゴリカル特徴量をcategory型に変換
        for feature_info in self.features.categorical_features:
            encoded_name = f"e_{feature_info['name']}"
            if encoded_name in df.columns and df[encoded_name].nunique() / len(df) <= 0.5:
                df[encoded_name] = df[encoded_name].astype("category")

        return df
