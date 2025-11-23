"""データ型を最適化してメモリ使用量と計算速度を向上させる（float64→float32, int64→int32）"""

import json
from pathlib import Path
from typing import Optional

import pandas as pd

# モジュールレベルのキャッシュ
_training_schema_cache: Optional[dict] = None
_base_path_cache: Optional[Path] = None


def _get_base_path(base_path: Optional[Path] = None) -> Path:
    """ベースパスを取得（デフォルトはプロジェクトルート）"""
    if base_path is None:
        return Path(__file__).parent.parent.parent.parent
    return Path(base_path)


def _load_training_schema(base_path: Optional[Path] = None) -> dict:
    """学習用データスキーマを読み込む（モジュールレベルでキャッシュ）"""
    global _training_schema_cache, _base_path_cache
    base_path = _get_base_path(base_path)
    
    if _training_schema_cache is None or _base_path_cache != base_path:
        schemas_dir = base_path / "packages" / "data" / "schemas" / "jrdb_processed"
        schema_file = schemas_dir / "training_schema.json"
        if not schema_file.exists():
            raise FileNotFoundError(f"スキーマファイルが見つかりません: {schema_file}")
        with open(schema_file, "r", encoding="utf-8") as f:
            _training_schema_cache = json.load(f)
            _base_path_cache = base_path
    return _training_schema_cache


def _get_categorical_features(base_path: Optional[Path] = None) -> list[dict]:
    """カテゴリカル特徴量の定義を取得"""
    schema = _load_training_schema(base_path)
    categorical = []
    for col in schema.get("columns", []):
        if col.get("type") == "categorical":
            feature_name = col.get("name")
            if feature_name:
                categorical.append({"name": feature_name})
    return categorical


def optimize(df: pd.DataFrame, base_path: Optional[Path] = None) -> pd.DataFrame:
    """データ型を最適化。df: 対象のDataFrame"""
    df = df.copy()

    for col in df.select_dtypes(include=["float64"]).columns:
        df[col] = df[col].astype("float32")

    for col in df.select_dtypes(include=["int64"]).columns:
        col_min, col_max = df[col].min(), df[col].max()
        if -2147483648 <= col_min <= col_max <= 2147483647:
            df[col] = df[col].astype("int32")

    categorical_features = _get_categorical_features(base_path)
    for feature_info in categorical_features:
        encoded_name = f"e_{feature_info['name']}"
        if encoded_name in df.columns and df[encoded_name].nunique() / len(df) <= 0.5:
            df[encoded_name] = df[encoded_name].astype("category")

    return df


def cleanup_object_columns(df: pd.DataFrame) -> pd.DataFrame:
    """ラベルエンコーディング後に残ったobject型カラムを削除。df: 対象のDataFrame"""
    df = df.copy()
    for col in df.columns:
        if col.startswith("prev_") and (df[col].dtype == "object" or df[col].dtype.name == "object"):
            df = df.drop(columns=[col])
    return df
