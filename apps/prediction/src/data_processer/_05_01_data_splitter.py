"""時系列で学習/テストデータに分割する（未来のデータが学習データに混入しないようにする）"""

import logging
from datetime import datetime
from typing import Tuple, Union

import pandas as pd

logger = logging.getLogger(__name__)


class DataSplitter:
    """時系列で学習/テストデータに分割するクラス"""

    @staticmethod
    def split_train_test(
        df: pd.DataFrame, split_date: Union[str, datetime]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """時系列で学習/テストデータに分割。df: 結合済みDataFrame、split_date: 分割日時"""
        if isinstance(split_date, str):
            split_date = pd.to_datetime(split_date)
        elif isinstance(split_date, datetime):
            split_date = pd.Timestamp(split_date)

        if "start_datetime" not in df.columns:
            raise ValueError("start_datetimeカラムが存在しません。")

        start_datetime_dt = None
        train_mask = None
        
        try:
            if df["start_datetime"].dtype in ["int64", "int32", "int", "float64", "float32"]:
                start_datetime_dt = pd.to_datetime(df["start_datetime"].astype(str), format="%Y%m%d%H%M", errors="coerce")
                mask = start_datetime_dt.isna()
                if mask.any():
                    start_datetime_dt[mask] = pd.to_datetime(
                        df.loc[mask, "start_datetime"].astype(str).str[:8], format="%Y%m%d", errors="coerce"
                    )
                train_mask = start_datetime_dt <= split_date
            else:
                train_mask = df["start_datetime"] <= split_date

            # main.pyから参照で渡されるため、ここでcopy()が必要
            train_df = df[train_mask].copy()
            test_df = df[~train_mask].copy()

            logger.info(f"時系列分割: 分割日時={split_date}, 学習={len(train_df):,}行, テスト={len(test_df):,}行")
            return train_df, test_df
        finally:
            # クリーンアップ: 不要なデータを削除
            if 'start_datetime_dt' in locals() and start_datetime_dt is not None:
                del start_datetime_dt
            if 'train_mask' in locals() and train_mask is not None:
                del train_mask
            import gc
            gc.collect()

