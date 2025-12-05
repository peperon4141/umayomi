"""時系列分割処理"""

from datetime import datetime
from typing import Tuple, Union

import pandas as pd

from ._05_01_data_splitter import DataSplitter


class TimeSeriesSplitter:
    """時系列で学習/テストデータに分割するクラス（staticメソッドのみ）"""

    @staticmethod
    def split(
        df: pd.DataFrame, split_date: Union[str, datetime]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """時系列で学習/テストデータに分割。df: 変換済みDataFrame、split_date: 分割日時。(train_df, test_df)を返す"""
        return DataSplitter.split_train_test(df, split_date)

