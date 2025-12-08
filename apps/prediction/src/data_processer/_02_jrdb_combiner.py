"""データ結合処理"""

import gc
import logging
from typing import Dict

import pandas as pd

from src.jrdb_scraper.entities.jrdb import JRDBDataType
from src.utils.jrdb_format_loader import JRDBFormatLoader

logger = logging.getLogger(__name__)

class JrdbCombiner:
    """複数のJRDBデータタイプを1つのDataFrameに結合するクラス（static関数のみ）"""

    @staticmethod
    def combine(data_dict: Dict[JRDBDataType, pd.DataFrame], schema: Dict, format_loader: JRDBFormatLoader) -> pd.DataFrame:
        """全データタイプを1つのDataFrameに結合（結合キーは各データタイプのidentifierColumnsから自動決定）"""
        # 早期バリデーション
        if not data_dict: raise ValueError("データが空です")
        if JRDBDataType.KYI not in data_dict: raise ValueError(f"{JRDBDataType.KYI.value}データが必要です。現在のデータタイプ: {', '.join([dt.value for dt in data_dict.keys()])}")
        if JRDBDataType.BAC not in data_dict: raise ValueError(f"{JRDBDataType.BAC.value}データが必要です。現在のデータタイプ: {', '.join([dt.value for dt in data_dict.keys()])}")
        if "baseDataType" not in schema: raise ValueError("スキーマにbaseDataTypeが定義されていません。スキーマファイルを確認してください。")
        if "columns" not in schema: raise ValueError("スキーマにcolumnsが定義されていません。スキーマファイルを確認してください。")
        
        base_type = schema["baseDataType"]
        target_data_types = [JRDBDataType(x) for x in schema["targetDataTypes"]]
        # base DataFrameをコピーして、元のDataFrameへの参照を切る（メモリ効率化）
        # 注意: copy()はメモリを一時的に増やすが、後続のmerge操作でメモリを効率的に管理するため必要
        combined_df = data_dict[base_type].copy()
        
        # baseのidentifierColumnsを取得（インデックスにも使用）
        base_format = format_loader.load_format_definition(base_type)
        if not base_format: raise ValueError(f"baseデータタイプ '{base_type.value}' のフォーマット定義が見つかりません")
        base_identifier_columns = set(base_format["identifierColumns"])

        try:
            # 各データタイプを結合
            for target_data_type in target_data_types:
                logger.info(f"データタイプ '{target_data_type.value}' の結合を開始")
                target_df = data_dict[target_data_type]
                logger.info(f"データタイプ '{target_data_type.value}' のデータ行数: {len(target_df)}")
                
                # 結合先のidentifierColumnsを取得
                target_format = format_loader.load_format_definition(target_data_type)
                if not target_format: raise ValueError(f"データタイプ '{target_data_type.value}' のフォーマット定義が見つかりません")
                target_identifier_columns = target_format["identifierColumns"]
                logger.info(f"データタイプ '{target_data_type.value}' のidentifierColumns: {target_identifier_columns}")
                
                # 結合キーを自動決定
                logger.info(f"データタイプ '{target_data_type.value}' の結合キーを決定中...")
                if set(target_identifier_columns) == base_identifier_columns:
                    # 1. 一致している場合 → targetのidentifierColumnsを使用
                    target_join_keys = target_identifier_columns
                    logger.info(f"データタイプ '{target_data_type.value}': 一致している場合 → {target_join_keys}")
                elif set(target_identifier_columns).issubset(base_identifier_columns):
                    # 2. targetがbaseのサブセット → targetのidentifierColumnsを使用
                    target_join_keys = target_identifier_columns
                    logger.info(f"データタイプ '{target_data_type.value}': targetがbaseのサブセット → {target_join_keys}")
                elif not any(col in base_identifier_columns for col in target_identifier_columns):
                    # 3. targetのidentifierColumnsがbaseのidentifierColumnsに全く含まれていない場合 → baseのDataFrameにtargetのidentifierColumnsが含まれているか確認（マスターデータなど）
                    available_in_base = [col for col in target_identifier_columns if col in combined_df.columns]
                    if available_in_base:
                        target_join_keys = available_in_base
                        logger.info(f"データタイプ '{target_data_type.value}': マスターデータとして結合 → {target_join_keys}")
                    else:
                        logger.error(f"データタイプ '{target_data_type.value}' の結合キーが見つかりません。baseのDataFrameカラム: {list(combined_df.columns)[:20]}")
                        raise ValueError(f"データタイプ '{target_data_type.value}' とbase '{base_type.value}' のidentifierColumnsに共通部分がなく、baseのDataFrameにも結合先のidentifierColumnsが存在しません。base: {list(base_identifier_columns)}, {target_data_type.value}: {target_identifier_columns}, baseのDataFrameカラム: {list(combined_df.columns)[:20]}")
                else:
                    # それ以外はエラー（baseがtargetのサブセットの場合も含む）
                    if base_identifier_columns.issubset(set(target_identifier_columns)):
                        logger.error(f"データタイプ '{target_data_type.value}' のidentifierColumnsがbaseより厳しい条件です")
                        raise ValueError(f"データタイプ '{target_data_type.value}' のidentifierColumnsがbase '{base_type.value}' より厳しい条件です。結合時に情報が失われる可能性があります。base: {list(base_identifier_columns)}, {target_data_type.value}: {target_identifier_columns}")
                    else:
                        logger.error(f"データタイプ '{target_data_type.value}' とbaseのidentifierColumnsの関係が不明です")
                        raise ValueError(f"データタイプ '{target_data_type.value}' とbase '{base_type.value}' のidentifierColumnsの関係が不明です。base: {list(base_identifier_columns)}, {target_data_type.value}: {target_identifier_columns}")
                
                # 識別キーで重複を削除（全カラムを保持）
                existing_target_identifier_columns = [col for col in target_identifier_columns if col in target_df.columns]
                if not existing_target_identifier_columns: raise ValueError(f"{target_data_type.value}データに識別キーが存在しません。識別キー: {target_identifier_columns}, 利用可能なカラム: {list(target_df.columns)[:10]}")
                logger.info(f"データタイプ '{target_data_type.value}' の重複削除前: {len(target_df)}行")
                target_source_df = target_df.drop_duplicates(subset=existing_target_identifier_columns, keep='first')
                logger.info(f"データタイプ '{target_data_type.value}' の重複削除後: {len(target_source_df)}行")
                # 元のtarget_dfへの参照を削除（メモリ効率化）
                del target_df

                # 結合キーの決定（実際に存在するカラムのみ）
                actual_join_keys = [k for k in target_join_keys if k in combined_df.columns and k in target_source_df.columns]
                logger.info(f"データタイプ '{target_data_type.value}' の実際の結合キー: {actual_join_keys}")
                
                if not actual_join_keys:
                    logger.error(f"データタイプ '{target_data_type.value}' の結合キーが存在しません。")
                    logger.error(f"  期待される結合キー: {target_join_keys}")
                    logger.error(f"  combined_dfのカラム（最初の20個）: {list(combined_df.columns)[:20]}")
                    logger.error(f"  target_source_dfのカラム（最初の20個）: {list(target_source_df.columns)[:20]}")
                    logger.error(f"  combined_dfに存在する結合キー候補: {[k for k in target_join_keys if k in combined_df.columns]}")
                    logger.error(f"  target_source_dfに存在する結合キー候補: {[k for k in target_join_keys if k in target_source_df.columns]}")
                    raise ValueError(
                        f"データタイプ '{target_data_type.value}' の結合キーが存在しません。\n"
                        f"  期待される結合キー: {target_join_keys}\n"
                        f"  combined_dfのカラム: {list(combined_df.columns)[:20]}\n"
                        f"  target_source_dfのカラム: {list(target_source_df.columns)[:20]}\n"
                        f"  parquetファイルにrace_keyが含まれていない可能性があります。parquetファイルを再生成してください。"
                    )

                # マージ処理（全カラムを結合）
                logger.info(f"データタイプ '{target_data_type.value}' のマージ開始。結合前の行数: {len(combined_df)}")
                # mergeは常に新しいDataFrameを作成するため、明示的に古いDataFrameを削除
                old_combined_df = combined_df
                combined_df = old_combined_df.merge(target_source_df, on=actual_join_keys, how="left", suffixes=("", f"_{target_data_type.value}"))
                logger.info(f"データタイプ '{target_data_type.value}' のマージ完了。結合後の行数: {len(combined_df)}")
                
                # メモリ解放（明示的に削除してからgc.collect()を呼ぶ）
                del old_combined_df
                del target_source_df
                # 結合処理後は定期的にガベージコレクションを実行（メモリ使用量を抑制）
                gc.collect()

            # baseのidentifierColumnsをMultiIndexに設定
            existing_index_columns = [col for col in base_format["identifierColumns"] if col in combined_df.columns]
            if len(existing_index_columns) == len(base_format["identifierColumns"]):
                # set_indexは新しいDataFrameを作成する可能性があるため、明示的にメモリを解放
                old_combined_df = combined_df
                combined_df = old_combined_df.set_index(existing_index_columns)
                del old_combined_df
                gc.collect()
            elif existing_index_columns:
                logger.warning(f"baseのidentifierColumnsが不完全です。定義: {base_format['identifierColumns']}, 存在: {existing_index_columns}")

            return combined_df

        except Exception as e:
            logger.error(f"データ結合エラー: {type(e).__name__}: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def _cleanup_resources(bac_df: pd.DataFrame = None, bac_df_subset: pd.DataFrame = None) -> None:
        """リソースのクリーンアップ（未使用）"""
        try:
            if bac_df is not None: del bac_df
            if bac_df_subset is not None: del bac_df_subset
            gc.collect()
        except Exception:
            pass
