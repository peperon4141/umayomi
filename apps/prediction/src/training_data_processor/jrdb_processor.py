"""JRDBデータ処理クラス（NPZファイルの読み込み・結合）"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

import pandas as pd

from ..data_loader import load_annual_pack_npz
from .feature_converter import FeatureConverter


class JrdbProcessor:
    """JRDBデータ処理クラス。NPZファイルを読み込んで結合する。"""

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """初期化。base_path: プロジェクトのベースパス（デフォルト: 現在のディレクトリ）"""
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent.parent
        self.base_path = Path(base_path)
        self.schemas_dir = self.base_path / "packages" / "data" / "schemas"
        self.raw_schemas_dir = self.schemas_dir / "jrdb_raw"
        self.processed_schemas_dir = self.schemas_dir / "jrdb_processed"

    def load_raw_schema(self, data_type: str) -> Dict:
        """元のJRDBデータ構造のJSONスキーマを読み込む。data_type: データタイプ（KYI、BAC、SED、UKC、TYBなど）"""
        schema_file = self.raw_schemas_dir / f"{data_type}.json"
        if not schema_file.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_file}")
        with open(schema_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_processed_schema(self) -> Dict:
        """変換後のデータ構造のJSONスキーマを読み込む"""
        schema_file = self.processed_schemas_dir / "combined_schema.json"
        if not schema_file.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_file}")
        with open(schema_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_data(
        self, data_type: str, year: int, base_data_path: Optional[Union[str, Path]] = None
    ) -> pd.DataFrame:
        """指定されたデータタイプのNPZファイルを読み込む。data_type: データタイプ、year: 年度、base_data_path: データファイルのベースパス（デフォルト: notebooks/data）"""
        if base_data_path is None:
            base_data_path = self.base_path / "apps" / "prediction" / "notebooks" / "data"
        return load_annual_pack_npz(base_data_path, data_type, year)

    def combine_data(
        self, data_dict: Dict[str, pd.DataFrame], schema: Optional[Dict] = None
    ) -> pd.DataFrame:
        """全データタイプを1つのDataFrameに結合。data_dict: データタイプをキー、DataFrameを値とする辞書、schema: 結合スキーマ（省略時は自動読み込み）"""
        if not data_dict:
            raise ValueError("データが空です")
        if "KYI" not in data_dict:
            raise ValueError(f"KYIデータが必要です。現在のデータタイプ: {', '.join(data_dict.keys())}")
        if "BAC" not in data_dict:
            raise ValueError(f"BACデータが必要です。現在のデータタイプ: {', '.join(data_dict.keys())}")

        if schema is None:
            schema = self.load_processed_schema()

        base_type = schema.get("baseDataType", "KYI")
        combined_df = data_dict[base_type].copy()

        bac_df = FeatureConverter.add_race_key_to_df(data_dict["BAC"].copy(), use_bac_date=False)
        race_key_cols = ["場コード", "回", "日", "R", "race_key"]
        combined_df = combined_df.merge(
            bac_df[race_key_cols].drop_duplicates(),
            on=["場コード", "回", "日", "R"],
            how="inner",
        )

        join_keys = schema.get("joinKeys", {})
        for data_type, df in data_dict.items():
            if data_type == base_type:
                continue

            if data_type not in join_keys:
                raise ValueError(f"データタイプ '{data_type}' の結合キー定義がありません。joinKeysに追加してください。")
            join_config = join_keys[data_type]

            if "race_key" in join_config["keys"]:
                df = FeatureConverter.add_race_key_to_df(
                    df, bac_df=data_dict["BAC"], use_bac_date=join_config.get("use_bac_date", False)
                )

            # SEDデータのフィルタリング（取消・除外を除外）
            if data_type == "SED":
                if "着順" in df.columns:
                    # 着順を数値型に変換して、取消・除外を除外（rankは追加しない、日本語キーのまま）
                    df["着順"] = pd.to_numeric(df["着順"], errors="coerce")
                    df = df[df["着順"] > 0].copy()
                if "タイム" in df.columns:
                    # タイムはそのまま保持（timeは追加しない、日本語キーのまま）
                    pass

            config_keys = join_config["keys"]
            actual_keys = [k for k in config_keys if k in combined_df.columns and k in df.columns]
            if not actual_keys:
                continue

            for key in actual_keys:
                if key in combined_df.columns and key in df.columns:
                    target_dtype = combined_df[key].dtype
                    if df[key].dtype != target_dtype:
                        if str(target_dtype) in ["uint8", "UInt8"] or isinstance(target_dtype, pd.UInt8Dtype):
                            df[key] = df[key].where((df[key] >= 0) & (df[key] <= 255))
                            df[key] = df[key].astype(pd.UInt8Dtype())
                        else:
                            try:
                                df[key] = df[key].astype(target_dtype)
                            except (ValueError, TypeError, pd.errors.IntCastingNaNError):
                                df[key] = pd.to_numeric(df[key], errors="coerce")
                                if "int" in str(target_dtype).lower() or "uint" in str(target_dtype).lower():
                                    if "uint8" in str(target_dtype).lower():
                                        df[key] = df[key].astype(pd.UInt8Dtype())
                                    elif "int8" in str(target_dtype).lower():
                                        df[key] = df[key].astype(pd.Int8Dtype())
                                    else:
                                        pass
                                else:
                                    df[key] = df[key].astype(target_dtype)

            combined_df = combined_df.merge(df, on=actual_keys, how="left", suffixes=("", f"_{data_type}"))

        return combined_df


