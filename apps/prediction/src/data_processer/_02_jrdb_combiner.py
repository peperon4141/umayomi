"""データ結合処理"""

import logging
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)


class JrdbCombiner:
    """複数のJRDBデータタイプを1つのDataFrameに結合するクラス（static関数のみ）"""

    @staticmethod
    def combine(data_dict: Dict[str, pd.DataFrame], schema: Dict) -> pd.DataFrame:
        """
        全データタイプを1つのDataFrameに結合
        
        Args:
            data_dict: データタイプをキー、DataFrameを値とする辞書
            schema: スキーマ情報の辞書
        
        Returns:
            結合済みDataFrame（日本語キー）
        """
        if not data_dict:
            raise ValueError("データが空です")
        if "KYI" not in data_dict:
            raise ValueError(f"KYIデータが必要です。現在のデータタイプ: {', '.join(data_dict.keys())}")
        if "BAC" not in data_dict:
            raise ValueError(f"BACデータが必要です。現在のデータタイプ: {', '.join(data_dict.keys())}")
        # スキーマファイルにbaseDataTypeが定義されていない場合のデフォルト値
        # KYIは常に存在し、他のデータタイプの結合基準となるため、デフォルト値として適切
        base_type = schema.get("baseDataType", "KYI")
        # mergeは新しいDataFrameを返すため、copy()は不要
        combined_df = data_dict[base_type]

        # BACデータからrace_keyを取得（事前定義済みのキーを使用）
        # 必要なカラムのみを抽出してメモリ使用量を削減
        bac_df = data_dict["BAC"]
        bac_df_subset = None
        
        try:
            if "race_key" not in bac_df.columns:
                raise ValueError("BACデータにrace_keyが含まれていません。LZH→Parquet変換時にrace_keyが生成されている必要があります。")
            race_key_cols = ["場コード", "回", "日", "R", "race_key"]
            bac_df_subset = bac_df[race_key_cols].drop_duplicates()
            combined_df = combined_df.merge(
                bac_df_subset,
                on=["場コード", "回", "日", "R"],
                how="left",
            )

            join_keys = schema.get("joinKeys", {})
            for data_type, df in data_dict.items():
                if data_type == base_type:
                    continue

                if data_type not in join_keys:
                    raise ValueError(f"データタイプ '{data_type}' の結合キー定義がありません")

                join_config = join_keys[data_type]

                if "race_key" in join_config["keys"]:
                    # race_keyが事前定義済みであることを確認（LZH→Parquet変換時に生成されている必要がある）
                    # ただし、TYBとKYIの場合は年月日カラムがないため、BACデータとマージする際にrace_keyを取得する
                    if "race_key" not in df.columns:
                        if data_type in ["TYB", "KYI"]:
                            # TYBとKYIの場合は、BACデータとマージする際にrace_keyを取得する
                            # ここではrace_keyを追加せず、後でBACデータとマージする際に取得する
                            logger.debug(f"{data_type}データにはrace_keyがありません。BACデータとマージする際に取得します。")
                        else:
                            raise ValueError(
                                f"{data_type}データにrace_keyが含まれていません。"
                                f"LZH→Parquet変換時にrace_keyが生成されている必要があります。"
                            )
                    else:
                        logger.debug(f"{data_type}データには既にrace_keyが存在します。事前定義済みのキーを使用します。")

                if data_type == "SED":
                    if "着順" in df.columns:
                        # フィルタリングは新しいDataFrameを返すため、copy()は不要
                        df["着順"] = pd.to_numeric(df["着順"], errors="coerce")
                        df = df[df["着順"] > 0]

                config_keys = join_config["keys"]
                actual_keys = [k for k in config_keys if k in combined_df.columns and k in df.columns]
                
                # TYBとKYIの場合は、race_keyが含まれていない場合でも、場コード、回、日、Rでマージできる
                # マージ後、race_keyがcombined_dfに含まれている場合は、dfにもrace_keyが追加される
                if data_type in ["TYB", "KYI"] and "race_key" not in df.columns:
                    # race_key以外のキーでマージ
                    keys_without_race_key = [k for k in config_keys if k != "race_key"]
                    actual_keys = [k for k in keys_without_race_key if k in combined_df.columns and k in df.columns]
                
                if not actual_keys:
                    continue

                combined_df = combined_df.merge(df, on=actual_keys, how="left", suffixes=("", f"_{data_type}"))

            return combined_df
        finally:
            # クリーンアップ: 不要なデータを削除
            if bac_df is not None:
                del bac_df
            if bac_df_subset is not None:
                del bac_df_subset
            import gc
            gc.collect()

