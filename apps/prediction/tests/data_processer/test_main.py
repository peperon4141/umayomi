"""DataProcessorの統合テスト - ParquetLoader.load()をモックして簡易データでテスト"""

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
        return DataProcessor(base_path=base_path, use_cache=False)

    @patch('src.data_processer._01_parquet_loader.ParquetLoader.load')
    def test_process_without_split(self, mock_load, processor, simple_data_dict):
        """split_date未指定時のテスト"""
        mock_load.return_value = simple_data_dict
        
        result = processor.process(
            data_types=['KYI', 'BAC', 'SED'],
            year=2024
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        assert "race_key" in result.index.names or "race_key" in result.columns
        mock_load.assert_called_once_with(['KYI', 'BAC', 'SED'], 2024)

    @patch('src.data_processer._01_parquet_loader.ParquetLoader.load')
    def test_process_with_split(self, mock_load, processor, simple_data_dict):
        """split_date指定時のテスト"""
        mock_load.return_value = simple_data_dict
        
        train_df, test_df, eval_df = processor.process(
            data_types=['KYI', 'BAC', 'SED'],
            year=2024,
            split_date="2024-06-01"
        )
        
        assert isinstance(train_df, pd.DataFrame)
        assert isinstance(test_df, pd.DataFrame)
        assert isinstance(eval_df, pd.DataFrame)
        assert 'rank' in train_df.columns
        assert 'rank' in test_df.columns
        # eval_dfには評価用カラム（日本語キー）が含まれることを確認
        assert '着順' in eval_df.columns or 'rank' in eval_df.columns
        assert '馬番' in eval_df.columns
        # SEDデータに「確定単勝オッズ」が含まれている場合、eval_dfにも含まれることを確認
        if '確定単勝オッズ' in simple_data_dict['SED'].columns:
            assert '確定単勝オッズ' in eval_df.columns
        mock_load.assert_called_once_with(['KYI', 'BAC', 'SED'], 2024)

    @patch('src.data_processer._01_parquet_loader.ParquetLoader.load')
    def test_process_minimal_data(self, mock_load, processor):
        """最小限のデータ（KYI+BACのみ）でのテスト"""
        # race_keyを事前定義（LZH→Parquet変換時に生成される想定）
        race_key = "20240101_01_01_1_01"
        
        minimal_data = {
            "KYI": pd.DataFrame({
                "場コード": [1],
                "回": [1],
                "日": ["1"],
                "R": [1],
                "馬番": [1],
                "血統登録番号": ["12345678"],
                "騎手コード": ["J001"],
                "調教師コード": ["T001"],
                "race_key": [race_key],  # 事前定義済みのキー
            }),
            "BAC": pd.DataFrame({
                "場コード": [1],
                "回": [1],
                "日": ["1"],
                "R": [1],
                "年月日": [20240101],
                "発走時刻": [1200],
                "race_key": [race_key],  # 事前定義済みのキー
            }),
        }
        mock_load.return_value = minimal_data
        
        result = processor.process(
            data_types=['KYI', 'BAC'],
            year=2024
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
        mock_load.assert_called_once_with(['KYI', 'BAC'], 2024)

    @patch('src.data_processer._01_parquet_loader.ParquetLoader.load')
    def test_process_missing_required_data(self, mock_load, processor):
        """必須データ（KYI/BAC）がない場合のエラーテスト"""
        incomplete_data = {
            "KYI": pd.DataFrame({
                "場コード": [1],
                "回": [1],
                "日": ["1"],
                "R": [1],
                "馬番": [1],
            }),
        }
        mock_load.return_value = incomplete_data
        
        with pytest.raises(ValueError, match="BACデータが必要です"):
            processor.process(
                data_types=['KYI', 'BAC'],
                year=2024
            )

    @patch('src.data_processer._01_parquet_loader.ParquetLoader.load')
    def test_process_empty_data(self, mock_load, processor):
        """空のデータの場合のエラーテスト"""
        mock_load.return_value = {}
        
        with pytest.raises(ValueError, match="データが空です"):
            processor.process(
                data_types=['KYI', 'BAC'],
                year=2024
            )

    @patch('src.data_processer._01_parquet_loader.ParquetLoader.load')
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
        
        def load_side_effect(data_types, year):
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
            data_types=['KYI', 'BAC', 'SED'],
            years=[2023, 2024],
            split_date="2024-06-01"
        )
        
        assert isinstance(train_df, pd.DataFrame)
        assert isinstance(test_df, pd.DataFrame)
        assert isinstance(eval_df, pd.DataFrame)
        assert len(train_df) > 0
        # テストデータは0件でも許容（データによっては分割されない場合がある）
        assert len(eval_df) > 0

    @patch('src.data_processer._01_parquet_loader.ParquetLoader.load')
    def test_process_multiple_years_without_split(self, mock_load, processor, simple_data_dict):
        """process_multiple_yearsのsplit_date未指定時のテスト"""
        def load_side_effect(data_types, year):
            if data_types == ["SED", "BAC"]:
                return {
                    "SED": simple_data_dict.get("SED"),
                    "BAC": simple_data_dict.get("BAC"),
                }
            return simple_data_dict
        
        mock_load.side_effect = load_side_effect
        
        result = processor.process_multiple_years(
            data_types=['KYI', 'BAC', 'SED'],
            years=[2023, 2024],
            split_date=None
        )
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    @patch('src.data_processer._01_parquet_loader.ParquetLoader.load')
    def test_process_multiple_years_empty_years(self, mock_load, processor):
        """process_multiple_yearsでyearsが空の場合のエラーテスト"""
        with pytest.raises(ValueError, match="yearsは空にできません"):
            processor.process_multiple_years(
                data_types=['KYI', 'BAC'],
                years=[],
                split_date=None
            )

    @patch('src.data_processer._01_parquet_loader.ParquetLoader.load')
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

