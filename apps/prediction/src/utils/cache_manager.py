"""前処理済みデータのキャッシュ管理"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd


class CacheManager:
    """前処理済みデータのキャッシュ管理クラス（staticなパスを持つ）"""

    def __init__(self, prediction_app_path: Optional[Union[str, Path]] = None):
        """
        初期化
        
        Args:
            prediction_app_path: apps/predictionディレクトリのパス（デフォルト: 自動検出）
        """
        if prediction_app_path is None:
            # apps/predictionディレクトリを自動検出（このファイルから2階層上）
            prediction_app_path = Path(__file__).parent.parent.parent
        self._prediction_app_path = Path(prediction_app_path)
        
        # staticなキャッシュディレクトリパス
        self._cache_dir = self._prediction_app_path / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _generate_cache_key(
        self,
        data_types: List[str],
        year: int,
        split_date: Optional[Union[str, datetime]] = None,
    ) -> str:
        """
        キャッシュキーを生成

        Args:
            data_types: データタイプのリスト
            year: 年度
            split_date: 時系列分割日時（オプション）

        Returns:
            キャッシュキー（文字列）
        """
        # データタイプをソートして一意性を保証
        data_types_sorted = sorted(data_types)
        key_parts = [
            "_".join(data_types_sorted),
            str(year),
        ]
        
        if split_date is not None:
            if isinstance(split_date, datetime):
                split_date_str = split_date.strftime("%Y-%m-%d")
            else:
                split_date_str = str(split_date)
            key_parts.append(split_date_str.replace("-", ""))
        
        cache_key = "_".join(key_parts)
        
        # ハッシュ化してファイル名に適した形式に（長すぎる場合）
        if len(cache_key) > 200:
            cache_key_hash = hashlib.md5(cache_key.encode()).hexdigest()[:16]
            cache_key = f"{cache_key[:100]}_{cache_key_hash}"
        
        return cache_key

    def _get_cache_paths(
        self, cache_key: str, split_date: Optional[Union[str, datetime]] = None
    ) -> Dict[str, Path]:
        """
        キャッシュファイルのパスを取得

        Args:
            cache_key: キャッシュキー
            split_date: 時系列分割日時（オプション）

        Returns:
            キャッシュファイルのパス辞書
        """
        if split_date is not None:
            return {
                "train": self._cache_dir / f"{cache_key}_train.parquet",
                "test": self._cache_dir / f"{cache_key}_test.parquet",
                "eval": self._cache_dir / f"{cache_key}_eval.parquet",
                "featured": self._cache_dir / f"{cache_key}_featured.parquet",
                "converted": self._cache_dir / f"{cache_key}_converted.parquet",
                "metadata": self._cache_dir / f"{cache_key}_metadata.json",
            }
        else:
            return {
                "data": self._cache_dir / f"{cache_key}_data.parquet",
                "featured": self._cache_dir / f"{cache_key}_featured.parquet",
                "converted": self._cache_dir / f"{cache_key}_converted.parquet",
                "metadata": self._cache_dir / f"{cache_key}_metadata.json",
            }

    def save(
        self,
        data_types: List[str],
        year: int,
        split_date: Optional[Union[str, datetime]],
        train_df: Optional[pd.DataFrame] = None,
        test_df: Optional[pd.DataFrame] = None,
        eval_df: Optional[pd.DataFrame] = None,
        featured_df: Optional[pd.DataFrame] = None,
        converted_df: Optional[pd.DataFrame] = None,
    ) -> None:
        """
        前処理済みデータをキャッシュに保存

        Args:
            data_types: データタイプのリスト
            year: 年度
            split_date: 時系列分割日時（オプション）
            train_df: 学習用DataFrame（split_date指定時）
            test_df: テスト用DataFrame（split_date指定時）
            eval_df: 評価用DataFrame（split_date指定時）
            featured_df: 特徴量抽出後のDataFrame（日本語キー）
            converted_df: 変換済みDataFrame（英語キー、split_date未指定時はdataとして保存）
        """
        cache_key = self._generate_cache_key(data_types, year, split_date)
        cache_paths = self._get_cache_paths(cache_key, split_date)

        # メタデータを保存
        metadata = {
            "data_types": data_types,
            "year": year,
            "split_date": str(split_date) if split_date else None,
            "cache_key": cache_key,
            "has_split": split_date is not None,
        }

        if split_date is not None:
            if train_df is not None:
                metadata["train_rows"] = len(train_df)
                metadata["train_columns"] = len(train_df.columns)
            if test_df is not None:
                metadata["test_rows"] = len(test_df)
                metadata["test_columns"] = len(test_df.columns)
            if eval_df is not None:
                metadata["eval_rows"] = len(eval_df)
                metadata["eval_columns"] = len(eval_df.columns)

            # 学習用データを保存
            if train_df is not None:
                self._save_dataframe(train_df, cache_paths["train"])
                print(f"[_07_] 学習用データをキャッシュに保存: {cache_paths['train']}")

            # テスト用データを保存
            if test_df is not None:
                self._save_dataframe(test_df, cache_paths["test"])
                print(f"[_07_] テスト用データをキャッシュに保存: {cache_paths['test']}")

            # 評価用データを保存
            if eval_df is not None:
                self._save_dataframe(eval_df, cache_paths["eval"])
                print(f"[_07_] 評価用データをキャッシュに保存: {cache_paths['eval']}")
        else:
            if converted_df is not None:
                metadata["data_rows"] = len(converted_df)
                metadata["data_columns"] = len(converted_df.columns)
                self._save_dataframe(converted_df, cache_paths["data"])
                print(f"[_07_] 前処理済みデータをキャッシュに保存: {cache_paths['data']}")

        # featured_dfを保存（split_dateの有無に関わらず）
        if featured_df is not None:
            metadata["featured_rows"] = len(featured_df)
            metadata["featured_columns"] = len(featured_df.columns)
            self._save_dataframe(featured_df, cache_paths["featured"])
            print(f"[_07_] 特徴量抽出データをキャッシュに保存: {cache_paths['featured']}")

        # converted_dfを保存（split_date指定時も保存可能）
        if converted_df is not None and split_date is not None:
            metadata["converted_rows"] = len(converted_df)
            metadata["converted_columns"] = len(converted_df.columns)
            self._save_dataframe(converted_df, cache_paths["converted"])
            print(f"[_07_] 変換済みデータをキャッシュに保存: {cache_paths['converted']}")

        # メタデータを保存
        with open(cache_paths["metadata"], "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _save_dataframe(self, df: pd.DataFrame, path: Path) -> None:
        """
        DataFrameをParquet形式で保存（インデックス情報も自動保存）

        Args:
            df: 保存するDataFrame
            path: 保存先のパス
        """
        # 親ディレクトリが存在しない場合は作成
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Parquet形式で保存（インデックスも自動的に保存される）
        # compression='snappy'は高速で圧縮効率も良い
        df.to_parquet(
            path,
            index=True,  # インデックスを自動的に保存
            compression='snappy',  # 高速で圧縮効率も良い
            engine='pyarrow',  # pyarrowエンジンを使用
        )

    def load(
        self,
        data_types: List[str],
        year: int,
        split_date: Optional[Union[str, datetime]] = None,
    ) -> Optional[Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]]:
        """
        前処理済みデータをキャッシュから読み込み

        Args:
            data_types: データタイプのリスト
            year: 年度
            split_date: 時系列分割日時（オプション）

        Returns:
            キャッシュが存在する場合: DataFrameまたはタプル
            キャッシュが存在しない場合: None
        """
        cache_key = self._generate_cache_key(data_types, year, split_date)
        cache_paths = self._get_cache_paths(cache_key, split_date)

        # メタデータを確認
        metadata_path = cache_paths["metadata"]
        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # データタイプと年度が一致するか確認
            if (
                set(metadata.get("data_types", [])) != set(data_types)
                or metadata.get("year") != year
            ):
                print(f"[_07_] [DEBUG] キャッシュのデータタイプまたは年度が一致しません")
                print(f"[_07_]   メタデータ: data_types={metadata.get('data_types')}, year={metadata.get('year')}")
                print(f"[_07_]   リクエスト: data_types={data_types}, year={year}")
                return None

            if split_date is not None:
                # 分割データを読み込み
                train_df = None
                test_df = None
                eval_df = None

                if cache_paths["train"].exists():
                    train_df = self._load_dataframe(cache_paths["train"])
                    print(f"[_07_] 学習用データをキャッシュから読み込み: {cache_paths['train']} ({len(train_df):,}件)")

                if cache_paths["test"].exists():
                    test_df = self._load_dataframe(cache_paths["test"])
                    print(f"[_07_] テスト用データをキャッシュから読み込み: {cache_paths['test']} ({len(test_df):,}件)")

                if cache_paths["eval"].exists():
                    eval_df = self._load_dataframe(cache_paths["eval"])
                    print(f"[_07_] 評価用データをキャッシュから読み込み: {cache_paths['eval']} ({len(eval_df):,}件)")

                if train_df is not None and test_df is not None and eval_df is not None:
                    return train_df, test_df, eval_df
                else:
                    return None
            else:
                # 単一データを読み込み
                if cache_paths["data"].exists():
                    df = self._load_dataframe(cache_paths["data"])
                    print(f"[_07_] 前処理済みデータをキャッシュから読み込み: {cache_paths['data']} ({len(df):,}件)")
                    return df
                else:
                    return None

        except Exception as e:
            print(f"[_07_] キャッシュの読み込み中にエラーが発生しました: {e}")
            return None

    def load_featured_df(
        self,
        data_types: List[str],
        year: int,
        split_date: Optional[Union[str, datetime]] = None,
    ) -> Optional[pd.DataFrame]:
        """
        特徴量抽出済みデータ（featured_df）をキャッシュから読み込み
        
        Args:
            data_types: データタイプのリスト
            year: 年度
            split_date: 時系列分割日時（オプション、キャッシュキー生成に使用）
        
        Returns:
            キャッシュが存在する場合: featured_df（日本語キー、前走データ含む）
            キャッシュが存在しない場合: None
        """
        cache_key = self._generate_cache_key(data_types, year, split_date)
        cache_paths = self._get_cache_paths(cache_key, split_date)
        
        if cache_paths["featured"].exists():
            featured_df = self._load_dataframe(cache_paths["featured"])
            print(f"[_07_] 特徴量抽出データをキャッシュから読み込み: {cache_paths['featured']} ({len(featured_df):,}件)")
            return featured_df
        else:
            print(f"[_07_] [DEBUG] 特徴量抽出データのキャッシュが見つかりません: {cache_paths['featured']}")
            return None

    def _load_dataframe(self, path: Path) -> pd.DataFrame:
        """
        Parquet形式からDataFrameを読み込み（インデックス情報も自動復元）

        Args:
            path: 読み込み元のパス

        Returns:
            DataFrame（インデックスも自動的に復元される）
        """
        # Parquet形式から読み込み（インデックスも自動的に復元される）
        df = pd.read_parquet(
            path,
            engine='pyarrow',  # pyarrowエンジンを使用
        )
        return df

    def clear_cache(
        self,
        data_types: Optional[List[str]] = None,
        year: Optional[int] = None,
        split_date: Optional[Union[str, datetime]] = None,
    ) -> None:
        """
        キャッシュを削除

        Args:
            data_types: データタイプのリスト（指定時は該当するキャッシュのみ削除）
            year: 年度（指定時は該当するキャッシュのみ削除）
            split_date: 時系列分割日時（指定時は該当するキャッシュのみ削除）
        """
        if data_types is not None and year is not None:
            # 特定のキャッシュを削除
            cache_key = self._generate_cache_key(data_types, year, split_date)
            cache_paths = self._get_cache_paths(cache_key, split_date)
            
            for path in cache_paths.values():
                if path.exists():
                    path.unlink()
                    print(f"[_07_] キャッシュを削除: {path}")
        else:
            # すべてのキャッシュを削除
            for path in self._cache_dir.glob("*.parquet"):
                path.unlink()
            for path in self._cache_dir.glob("*.json"):
                path.unlink()
            print(f"[_07_] すべてのキャッシュを削除: {self._cache_dir}")

