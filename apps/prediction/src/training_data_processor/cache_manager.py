"""学習データのキャッシュ管理クラス（Parquet形式）"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from .main import TrainingDataProcessor


class CacheSaveError(Exception):
    """キャッシュ保存時のエラー"""
    pass


class CacheManager:
    """学習データのキャッシュ管理クラス（Parquet形式）"""

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """
        初期化

        Args:
            base_path: プロジェクトのベースパス（デフォルト: apps/prediction/）
        """
        if base_path is None:
            base_path = Path(__file__).parent.parent.parent
        self._base_path = Path(base_path)
        self._cache_dir = self._base_path / "cache"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._schemas_dir = self._base_path.parent.parent / "packages" / "data" / "schemas" / "jrdb_processed"

    @lru_cache(maxsize=128)
    def _generate_cache_key_cached(
        self,
        data_types_tuple: Tuple[str, ...],
        years_tuple: Optional[Tuple[int, ...]],
        split_date_str: Optional[str],
    ) -> str:
        """
        キャッシュキーを生成（キャッシュ付き）

        Args:
            data_types_tuple: データタイプのタプル（ソート済み）
            years_tuple: 年度のタプル（ソート済み、Noneの場合は"all"）
            split_date_str: 時系列分割日時の文字列（Noneの場合は追加しない）

        Returns:
            キャッシュキー
        """
        data_types_str = "_".join(data_types_tuple)
        years_str = "_".join(map(str, years_tuple)) if years_tuple else "all"

        meta_parts = [data_types_str, years_str]
        if split_date_str:
            meta_parts.append(f"split-{split_date_str}")

        meta = "_".join(meta_parts)
        # ファイル名に使えない文字を置換（安全のため）
        meta = meta.replace("/", "_").replace("\\", "_")

        return meta

    def _get_column_aliases(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        カラム名のエイリアス（日本語キー→英語キー）を取得
        
        Args:
            df: DataFrame（日本語キー）
            
        Returns:
            カラム名のマッピング辞書（日本語キー→英語キー）
        """
        try:
            schema_file = self._schemas_dir / "full_info_schema.json"
            if not schema_file.exists():
                return {}
            
            with open(schema_file, "r", encoding="utf-8") as f:
                schema = json.load(f)
            
            aliases = {}
            for col in schema.get("columns", []):
                jp_name = col.get("name")
                feature_name = col.get("feature_name")
                if jp_name and feature_name and jp_name in df.columns:
                    aliases[jp_name] = feature_name
            
            return aliases
        except Exception:
            return {}

    def generate_cache_key(
        self,
        data_types: List[str],
        years: Optional[List[int]] = None,
        split_date: Optional[Union[str, pd.Timestamp]] = None,
    ) -> str:
        """
        キャッシュキーを生成

        Args:
            data_types: データタイプのリスト
            years: 年度のリスト
            split_date: 時系列分割日時

        Returns:
            キャッシュキー（例: BAC_KYI_SED_UKC_2024 または BAC_KYI_SED_UKC_2024_split-2024-06-01）
        """
        # タプルに変換してキャッシュ可能にする
        data_types_tuple = tuple(sorted(data_types))
        years_tuple = tuple(sorted(years)) if years else None

        # split_dateを文字列に変換
        split_date_str = None
        if split_date is not None:
            if isinstance(split_date, pd.Timestamp):
                split_date_str = split_date.strftime("%Y-%m-%d")
            else:
                split_date_str = str(split_date)

        return self._generate_cache_key_cached(data_types_tuple, years_tuple, split_date_str)

    def get_cache_path(
        self,
        data_name: str,
        data_types: List[str],
        years: Optional[List[int]] = None,
        split_date: Optional[Union[str, pd.Timestamp]] = None,
    ) -> Path:
        """
        キャッシュファイルのパスを取得

        Args:
            data_name: データ名（例: "training-data"）
            data_types: データタイプのリスト
            years: 年度のリスト
            split_date: 時系列分割日時

        Returns:
            キャッシュファイルのベースパス（拡張子なし）
        """
        meta = self.generate_cache_key(data_types, years, split_date)
        filename = f"{data_name}_{meta}"
        return self._cache_dir / filename

    def _is_split_cache(self, base_path: Path) -> bool:
        """
        分割キャッシュかどうかを判定

        Args:
            base_path: ベースパス（拡張子なし）

        Returns:
            分割キャッシュの場合True
        """
        train_path = base_path.with_name(f"{base_path.stem}_train.parquet")
        return train_path.exists()

    def save(
        self,
        data: Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]],
        data_name: str,
        data_types: List[str],
        years: Optional[List[int]] = None,
        split_date: Optional[Union[str, pd.Timestamp]] = None,
    ) -> Path:
        """
        データをキャッシュに保存（Parquet形式、アトミック書き込み）

        Args:
            data: 保存するデータ（DataFrameまたは(train_df, test_df, original_df)のタプル）
            data_name: データ名（例: "training-data"）
            data_types: データタイプのリスト
            years: 年度のリスト
            split_date: 時系列分割日時

        Returns:
            保存先のベースパス（拡張子なし）
        """
        base_path = self.get_cache_path(data_name, data_types, years, split_date)

        if isinstance(data, tuple):
            # 分割ありの場合: 3つのParquetファイルに保存
            train_df, test_df, original_df = data

            # 一時ファイルに保存（アトミック書き込み）
            temp_paths = []
            final_paths = []
            try:
                # train_df
                train_path = base_path.with_name(f"{base_path.stem}_train.parquet")
                temp_train_path = train_path.with_suffix('.tmp.parquet')
                train_df.to_parquet(
                    temp_train_path,
                    compression='snappy',
                    index=True,
                    engine='pyarrow',
                )
                temp_paths.append(temp_train_path)
                final_paths.append(train_path)

                # test_df
                test_path = base_path.with_name(f"{base_path.stem}_test.parquet")
                temp_test_path = test_path.with_suffix('.tmp.parquet')
                test_df.to_parquet(
                    temp_test_path,
                    compression='snappy',
                    index=True,
                    engine='pyarrow',
                )
                temp_paths.append(temp_test_path)
                final_paths.append(test_path)

                # original_df（日本語キー）にカラム名エイリアス（英語キー）をメタデータとして保存
                original_path = base_path.with_name(f"{base_path.stem}_original.parquet")
                temp_original_path = original_path.with_suffix('.tmp.parquet')
                
                # カラム名のマッピング（日本語キー→英語キー）を取得
                column_aliases = self._get_column_aliases(original_df)
                
                # PyArrow Tableに変換してメタデータを追加
                table = pa.Table.from_pandas(original_df, preserve_index=True)
                if column_aliases:
                    # 既存のメタデータを取得
                    existing_metadata = table.schema.metadata or {}
                    # カラム名エイリアスをJSON形式でメタデータに追加
                    existing_metadata[b'column_aliases'] = json.dumps(column_aliases, ensure_ascii=False).encode('utf-8')
                    # メタデータを更新
                    table = table.replace_schema_metadata(existing_metadata)
                
                # Parquetファイルに書き込み
                pq.write_table(table, temp_original_path, compression='snappy')
                temp_paths.append(temp_original_path)
                final_paths.append(original_path)

                # アトミックにリネーム
                for temp_path, final_path in zip(temp_paths, final_paths):
                    temp_path.replace(final_path)

                print(f"キャッシュに保存しました: {base_path.stem} (Parquet形式, 分割あり)")
                return base_path

            except Exception as e:
                # エラー時は一時ファイルを削除
                for temp_path in temp_paths:
                    temp_path.unlink(missing_ok=True)
                raise CacheSaveError(f"キャッシュの保存に失敗しました: {e}") from e
        else:
            # 分割なしの場合: 1つのParquetファイルに保存
            parquet_path = base_path.with_suffix('.parquet')
            temp_path = parquet_path.with_suffix('.tmp.parquet')

            try:
                data.to_parquet(
                    temp_path,
                    compression='snappy',
                    index=True,
                    engine='pyarrow',
                )
                # アトミックにリネーム
                temp_path.replace(parquet_path)
                print(f"キャッシュに保存しました: {parquet_path} (Parquet形式)")
                return base_path

            except Exception as e:
                # エラー時は一時ファイルを削除
                temp_path.unlink(missing_ok=True)
                raise CacheSaveError(f"キャッシュの保存に失敗しました: {e}") from e

    def load(
        self,
        data_name: str,
        data_types: List[str],
        years: Optional[List[int]] = None,
        split_date: Optional[Union[str, pd.Timestamp]] = None,
    ) -> Optional[Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]]:
        """
        キャッシュからデータを読み込み（Parquet形式）

        Args:
            data_name: データ名（例: "training-data"）
            data_types: データタイプのリスト
            years: 年度のリスト
            split_date: 時系列分割日時

        Returns:
            読み込んだデータ（DataFrameまたは(train_df, test_df, original_df)のタプル）、見つからない場合はNone
        """
        base_path = self.get_cache_path(data_name, data_types, years, split_date)

        try:
            if self._is_split_cache(base_path):
                # 分割ありの場合
                train_path = base_path.with_name(f"{base_path.stem}_train.parquet")
                test_path = base_path.with_name(f"{base_path.stem}_test.parquet")
                original_path = base_path.with_name(f"{base_path.stem}_original.parquet")

                train_df = pd.read_parquet(train_path, engine='pyarrow')
                test_df = pd.read_parquet(test_path, engine='pyarrow')
                
                # original_dfを読み込み、メタデータからカラム名エイリアスを取得
                parquet_file = pq.ParquetFile(original_path)
                table = parquet_file.read()
                original_df = table.to_pandas()
                
                # メタデータからカラム名エイリアスを取得
                metadata = table.schema.metadata
                if metadata and b'column_aliases' in metadata:
                    column_aliases = json.loads(metadata[b'column_aliases'].decode('utf-8'))
                    # DataFrameの属性として保存（必要に応じて使用可能）
                    original_df.attrs['column_aliases'] = column_aliases
                    # 逆マッピング（英語キー→日本語キー）も追加
                    original_df.attrs['column_aliases_reverse'] = {v: k for k, v in column_aliases.items()}

                print(f"キャッシュから読み込みました: {base_path.stem} (Parquet形式, 分割あり)")
                return train_df, test_df, original_df
            else:
                # 分割なしの場合
                parquet_path = base_path.with_suffix('.parquet')
                if not parquet_path.exists():
                    return None

                combined_df = pd.read_parquet(parquet_path, engine='pyarrow')
                print(f"キャッシュから読み込みました: {parquet_path} (Parquet形式)")
                return combined_df

        except Exception as e:
            print(f"キャッシュの読み込みに失敗しました: {e}")
            return None

    def get_or_create(
        self,
        data_name: str,
        base_path: Union[str, Path],
        data_types: List[str],
        years: Optional[List[int]] = None,
        split_date: Optional[Union[str, pd.Timestamp]] = None,
        processor: Optional[TrainingDataProcessor] = None,
    ) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]]:
        """
        キャッシュがあればロード、なければ作成して保存

        Args:
            data_name: データ名（例: "training-data"）
            base_path: データのベースパス
            data_types: データタイプのリスト
            years: 年度のリスト
            split_date: 時系列分割日時
            processor: TrainingDataProcessorのインスタンス（Noneの場合は新規作成）

        Returns:
            データ（DataFrameまたは(train_df, test_df, original_df)のタプル）
        """
        # キャッシュから読み込みを試行
        cached_data = self.load(data_name, data_types, years, split_date)
        if cached_data is not None:
            return cached_data

        # キャッシュがない場合は作成
        # TrainingDataProcessorにはプロジェクトルート（スキーマファイルがある場所）を渡す
        # self._base_pathはapps/prediction/なので、2つ親に上がってプロジェクトルートを取得
        if processor is None:
            # プロジェクトルートを取得（apps/prediction/ -> apps/ -> プロジェクトルート）
            if self._base_path.name == "prediction" and self._base_path.parent.name == "apps":
                project_root = self._base_path.parent.parent
            else:
                # デフォルトの動作（__file__から計算）
                project_root = Path(__file__).parent.parent.parent.parent
            processor = TrainingDataProcessor(base_path=project_root)

        print("キャッシュが見つかりません。データを作成します...")
        data = processor.process(
            base_path=base_path,
            data_types=data_types,
            years=years,
            split_date=split_date,
        )

        # キャッシュに保存（Parquet形式）
        self.save(data, data_name, data_types, years, split_date)

        return data
