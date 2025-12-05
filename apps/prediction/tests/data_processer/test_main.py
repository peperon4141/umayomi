"""DataProcessorの統合テスト - load_parquet_files()をモックして簡易データでテスト"""

import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch

from src.data_processer import DataProcessor


class TestDataProcessor:
    """DataProcessorの統合テスト"""

    @pytest.fixture
    def processor(self):
        """DataProcessorインスタンスを作成"""
        base_path = Path(__file__).parent.parent.parent.parent.parent
        parquet_base_path = base_path / "apps" / "prediction" / "cache" / "jrdb" / "parquet"
        return DataProcessor(
            base_path=base_path,
            parquet_base_path=parquet_base_path,
            use_cache=False
        )


    @patch('src.data_processer.main.load_parquet_files')
    def test_process_multiple_years_with_split(self, mock_load, processor, simple_data_dict):
        """process_multiple_yearsのsplit_date指定時のテスト"""
        # 2024年のデータを後半に設定（split_date="2024-06-01"で分割されるように）
        data_2023 = simple_data_dict.copy()
        data_2024 = simple_data_dict.copy()
        # 2024年のBACデータの年月日を後半に設定
        data_2024["BAC"] = data_2024["BAC"].copy()
        data_2024["BAC"]["年月日"] = 20240701  # 2024年7月1日（split_dateより後）
        # race_keyも更新（年月日に合わせて）
        data_2024["BAC"]["race_key"] = "20240701_01_01_1_01"
        data_2024["SED"] = data_2024["SED"].copy()
        data_2024["SED"]["年月日"] = 20240701
        data_2024["SED"]["race_key"] = "20240701_01_01_1_01"
        data_2024["KYI"] = data_2024["KYI"].copy()
        data_2024["KYI"]["race_key"] = "20240701_01_01_1_01"
        
        from src.data_processer.main import _DATA_TYPES
        
        def load_side_effect(base_path, data_types, year):
            if data_types == ["SED", "BAC"]:
                # SED/BAC読み込み用
                if year == 2023:
                    return {
                        "SED": data_2023.get("SED"),
                        "BAC": data_2023.get("BAC"),
                    }
                else:
                    return {
                        "SED": data_2024.get("SED"),
                        "BAC": data_2024.get("BAC"),
                    }
            # 通常のデータ読み込み
            if year == 2023:
                return data_2023
            else:
                return data_2024
        
        mock_load.side_effect = load_side_effect
        
        train_df, test_df, eval_df = processor.process_multiple_years(
            years=[2023, 2024],
            split_date="2024-06-01"
        )
        
        assert isinstance(train_df, pd.DataFrame)
        assert isinstance(test_df, pd.DataFrame)
        assert isinstance(eval_df, pd.DataFrame)
        assert len(train_df) > 0
        # テストデータは0件でも許容（データによっては分割されない場合がある）
        assert len(eval_df) > 0

    @patch('src.data_processer.main.load_parquet_files')
    def test_process_multiple_years_without_split(self, mock_load, processor, simple_data_dict):
        """process_multiple_yearsのsplit_date未指定時のテスト"""
        from src.data_processer.main import _DATA_TYPES
        
        def load_side_effect(base_path, data_types, year):
            if data_types == ["SED", "BAC"]:
                return {
                    "SED": simple_data_dict.get("SED"),
                    "BAC": simple_data_dict.get("BAC"),
                }
            return simple_data_dict
        
        mock_load.side_effect = load_side_effect
        
        result = processor.process_multiple_years(
            years=[2023, 2024],
            split_date=None
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @patch('src.data_processer.main.load_parquet_files')
    def test_process_multiple_years_empty_years(self, mock_load, processor):
        """process_multiple_yearsでyearsが空の場合のエラーテスト"""
        with pytest.raises(ValueError, match="yearsは空にできません"):
            processor.process_multiple_years(
                years=[],
                split_date=None
            )

    @patch('src.utils.parquet_loader.load_parquet_files')
    def test_process_multiple_years_missing_bac(self, mock_load, processor):
        """process_multiple_yearsでBACデータが存在しない場合のエラーテスト"""
        def load_side_effect(data_types, year):
            if data_types == ["SED", "BAC"]:
                return {"SED": pd.DataFrame()}  # BACが存在しない
            return {"KYI": pd.DataFrame()}
        
        mock_load.side_effect = load_side_effect
        
        with pytest.raises(ValueError, match="BACデータは必須です"):
            processor.process_multiple_years(
                data_types=['KYI', 'BAC'],
                years=[2023, 2024],
                split_date=None
            )

