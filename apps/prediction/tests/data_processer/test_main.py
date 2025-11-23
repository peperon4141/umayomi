"""DataProcessorの統合テスト - NpzLoader.load()をモックして簡易データでテスト"""

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
        return DataProcessor(base_path=base_path)

    @patch('src.data_processer.main.NpzLoader.load')
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

    @patch('src.data_processer.main.NpzLoader.load')
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
        mock_load.assert_called_once_with(['KYI', 'BAC', 'SED'], 2024)

    @patch('src.data_processer.main.NpzLoader.load')
    def test_process_minimal_data(self, mock_load, processor):
        """最小限のデータ（KYI+BACのみ）でのテスト"""
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
            }),
            "BAC": pd.DataFrame({
                "場コード": [1],
                "回": [1],
                "日": ["1"],
                "R": [1],
                "年月日": [20240101],
                "発走時刻": [1200],
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

    @patch('src.data_processer.main.NpzLoader.load')
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

    @patch('src.data_processer.main.NpzLoader.load')
    def test_process_empty_data(self, mock_load, processor):
        """空のデータの場合のエラーテスト"""
        mock_load.return_value = {}
        
        with pytest.raises(ValueError, match="データが空です"):
            processor.process(
                data_types=['KYI', 'BAC'],
                year=2024
            )

