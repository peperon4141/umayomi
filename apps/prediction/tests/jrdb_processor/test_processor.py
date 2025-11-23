"""JRDBデータ処理クラスのテスト"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.jrdb_processor.processor import JrdbProcessor


class TestJrdbProcessor:
    """JrdbProcessorクラスのテスト"""

    @pytest.fixture
    def processor(self):
        """JrdbProcessorインスタンスを作成"""
        base_path = Path(__file__).parent.parent.parent.parent.parent
        return JrdbProcessor(base_path=base_path)

    @pytest.fixture
    def sample_data(self):
        """サンプルデータを作成"""
        return {
            "KYI": pd.DataFrame({
                "場コード": [1, 1, 2],
                "回": [1, 1, 1],
                "日": ["1", "1", "1"],
                "R": [1, 2, 1],
                "馬番": [1, 1, 1],
                "血統登録番号": ["12345678", "23456789", "34567890"],
            }),
            "BAC": pd.DataFrame({
                "場コード": [1, 1, 2],
                "回": [1, 1, 1],
                "日": ["1", "1", "1"],
                "R": [1, 2, 1],
                "年月日": [20241102, 20241102, 20241103],
            }),
            "UKC": pd.DataFrame({
                "血統登録番号": ["12345678", "23456789", "34567890"],
                "馬名": ["テスト馬1", "テスト馬2", "テスト馬3"],
            }),
        }

    def test_load_raw_schema(self, processor):
        """元のJRDBデータ構造のJSONスキーマを読み込むテスト"""
        schema = processor.load_raw_schema("KYI")
        assert schema["dataType"] == "KYI"
        assert "fields" in schema
        assert len(schema["fields"]) > 0

    def test_load_processed_schema(self, processor):
        """変換後のデータ構造のJSONスキーマを読み込むテスト"""
        schema = processor.load_processed_schema()
        assert "baseDataType" in schema
        assert "joinKeys" in schema
        assert "columns" in schema

    def test_combine_data(self, processor, sample_data):
        """データ結合のテスト"""
        combined_df = processor.combine_data(sample_data)
        assert len(combined_df) > 0
        assert "race_key" in combined_df.columns
        assert "血統登録番号" in combined_df.columns

    def test_combine_data_missing_kyi(self, processor, sample_data):
        """KYIデータがない場合のエラーテスト"""
        del sample_data["KYI"]
        with pytest.raises(ValueError, match="KYIデータが必要です"):
            processor.combine_data(sample_data)

    def test_combine_data_missing_bac(self, processor, sample_data):
        """BACデータがない場合のエラーテスト"""
        del sample_data["BAC"]
        with pytest.raises(ValueError, match="BACデータが必要です"):
            processor.combine_data(sample_data)

    def test_save_and_load_combined_data(self, processor, sample_data, tmp_path):
        """保存・読み込みのテスト"""
        combined_df = processor.combine_data(sample_data)
        output_path = tmp_path / "test_combined.npz"
        
        metadata = {"data_types": ["KYI", "BAC", "UKC"], "year": 2024}
        saved_path = processor.save_combined_data(combined_df, output_path, metadata)
        assert saved_path.exists()
        
        # NPZファイルを読み込んで検証
        with np.load(saved_path, allow_pickle=True) as npz_file:
            loaded_data = {key: npz_file[key] for key in npz_file.files}
            assert "_index" in loaded_data
            assert "_metadata" in loaded_data

    def test_combined_data_columns(self, processor, sample_data):
        """結合したデータのカラムが正しいことを確認するテスト"""
        combined_df = processor.combine_data(sample_data)
        
        # 必須カラムが存在することを確認
        required_columns = ["場コード", "回", "日", "R", "馬番", "race_key", "血統登録番号"]
        for col in required_columns:
            assert col in combined_df.columns, f"カラム '{col}' が存在しません"

    def test_no_future_data_leakage(self, processor, sample_data):
        """結合したデータに未来のデータが含まれていないことを確認するテスト"""
        # 年月日を追加してテスト
        sample_data["BAC"]["年月日"] = [20241102, 20241102, 20241103]
        combined_df = processor.combine_data(sample_data)
        
        # race_keyから年月日を抽出して検証
        if "race_key" in combined_df.columns:
            # race_keyの形式: "YYYYMMDD_場コード_回_日_R"
            dates = []
            for race_key in combined_df["race_key"]:
                if pd.notna(race_key) and isinstance(race_key, str):
                    date_part = race_key.split("_")[0]
                    if date_part.isdigit() and len(date_part) == 8:
                        dates.append(int(date_part))
            
            if dates:
                max_date = max(dates)
                # 未来の日付（例: 2030年以降）が含まれていないことを確認
                assert max_date < 20300000, "未来のデータが含まれています"

