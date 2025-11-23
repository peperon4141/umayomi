"""時系列分割処理"""

from datetime import datetime
from typing import Tuple, Union

import pandas as pd

from .data_splitter import DataSplitter as BaseDataSplitter


class TimeSeriesSplitter:
    """時系列で学習/テストデータに分割するクラス"""

    def __init__(self):
        """初期化"""
        self._splitter = BaseDataSplitter()

    def split(
        self, df: pd.DataFrame, split_date: Union[str, datetime]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """時系列で学習/テストデータに分割。df: 変換済みDataFrame、split_date: 分割日時。(train_df, test_df)を返す"""
        return self._splitter.split_train_test(df, split_date)

