"""
JRDBデータ用特徴量定義
オッズ関連のフィールドは除外（予測には使用せず、掛け方計算用に別途保持）
"""

from dataclasses import dataclass
from functools import cached_property
from typing import Any, Dict, List, Optional


@dataclass
class FieldDefinition:
    """フィールド定義（JRDBフィールド名、特徴量名、データタイプ、除外フラグなどを一元管理）"""
    jrdb_name: Optional[str]  # JRDBの元フィールド名（Noneの場合は計算フィールド）
    feature_name: Optional[str]  # 特徴量名（マッピング後、Noneの場合は除外フィールド）
    data_types: List[str]  # どのデータタイプから来るか（["BAC"], ["KYI"], ["SED"], ["KYI", "UKC"]など）
    is_excluded: bool = False  # 除外するかどうか（オッズ関連など）
    is_categorical: bool = False  # カテゴリカルかどうか
    is_numeric: bool = True  # 数値かどうか
    category_map: Optional[Dict[str, int]] = None  # カテゴリマッピング（COURSE_TYPEなど）
    category_list: Optional[List[str]] = None  # カテゴリリスト（WEATHERなど）
    is_computed: bool = False  # 計算されたフィールドかどうか（start_datetime, ageなど）
    is_integer: bool = False  # 整数型にダウンキャストするかどうか（数値変換時）


class Features:
    """
    JRDBデータから抽出する特徴量の定義
    オッズ関連フィールドは除外
    """

    # カテゴリカル特徴量のマッピング
    COURSE_TYPE = {
        "芝": 0,
        "ダ": 1,
        "ダート": 1,
        "障": 2,
        "障害": 2,
    }

    WEATHER = ["晴", "曇", "雨", "小雨", "小雪", "雪"]
    GROUND_CONDITION = ["良", "稍", "重", "不", "重不"]
    SEX = ["牡", "牝", "セ"]

    TARGET = "rank"

    # フィールド定義（JRDBフィールド名、特徴量名、データタイプ、除外フラグなどを一元管理）
    FIELD_DEFINITIONS: List[FieldDefinition] = [
        # レース情報（BAC）
        FieldDefinition("回", "round", ["BAC"], is_numeric=True),
        FieldDefinition("日", "day", ["BAC"], is_numeric=True),
        FieldDefinition("場コード", "place", ["BAC"], is_categorical=True, is_numeric=False),
        FieldDefinition("頭数", "num_horses", ["BAC"], is_numeric=True),
        FieldDefinition("1着賞金", "prize_1", ["BAC"], is_numeric=True),
        FieldDefinition("2着賞金", "prize_2", ["BAC"], is_numeric=True),
        FieldDefinition("3着賞金", "prize_3", ["BAC"], is_numeric=True),
        FieldDefinition(None, "start_datetime", ["BAC"], is_numeric=True, is_computed=True),
        FieldDefinition("芝ダ障害コード", "course_type", ["BAC"], is_categorical=True, category_map=COURSE_TYPE),
        FieldDefinition("距離", "course_length", ["BAC"], is_numeric=True),
        FieldDefinition("内外", "course_setting", ["BAC"], is_categorical=True, is_numeric=False),
        FieldDefinition("天候コード", "weather", ["BAC"], is_categorical=True, category_list=WEATHER, is_numeric=False),
        FieldDefinition("馬場状態", "ground_condition", ["BAC"], is_categorical=True, category_list=GROUND_CONDITION, is_numeric=False),
        FieldDefinition("グレード", "race_grade", ["BAC"], is_categorical=True, is_numeric=False),
        FieldDefinition("種別", "race_class", ["BAC"], is_categorical=True, is_numeric=False),
        FieldDefinition("条件", "race_condition", ["BAC"], is_categorical=True, is_numeric=False),
        FieldDefinition("記号", "race_mark", ["BAC"], is_categorical=True, is_numeric=False),
        FieldDefinition("重量", "weight_type", ["BAC"], is_categorical=True, is_numeric=False),
        FieldDefinition("R", "race_number", ["BAC"], is_numeric=True),
        # オッズ関連（除外）
        FieldDefinition("単勝", None, ["BAC"], is_excluded=True),
        FieldDefinition("複勝", None, ["BAC"], is_excluded=True),
        FieldDefinition("枠連", None, ["BAC"], is_excluded=True),
        FieldDefinition("馬連", None, ["BAC"], is_excluded=True),
        FieldDefinition("馬単", None, ["BAC"], is_excluded=True),
        FieldDefinition("ワイド", None, ["BAC"], is_excluded=True),
        FieldDefinition("３連複", None, ["BAC"], is_excluded=True),
        FieldDefinition("３連単", None, ["BAC"], is_excluded=True),
        # 馬情報（KYI）
        FieldDefinition("枠番", "frame", ["KYI"], is_numeric=True, is_integer=True),
        FieldDefinition("馬番", "horse_number", ["KYI"], is_numeric=True, is_integer=True),
        FieldDefinition("血統登録番号", "horse_id", ["KYI"], is_numeric=True),
        FieldDefinition("騎手コード", "jockey_id", ["KYI"], is_numeric=True, is_integer=True),
        FieldDefinition("調教師コード", "trainer_id", ["KYI"], is_numeric=True, is_integer=True),
        FieldDefinition("負担重量", "jockey_weight", ["KYI"], is_numeric=True),
        FieldDefinition("性別コード", "sex", ["KYI"], is_categorical=True, category_list=SEX, is_numeric=False),
        FieldDefinition(None, "age", ["KYI"], is_numeric=True, is_computed=True),
        FieldDefinition("調教師所属", "stable", ["KYI"], is_categorical=True, is_numeric=False),
        # 指数データ（KYI）
        FieldDefinition("IDM", "idm", ["KYI"], is_numeric=True),
        FieldDefinition("騎手指数", "jockey_index", ["KYI"], is_numeric=True),
        FieldDefinition("情報指数", "info_index", ["KYI"], is_numeric=True),
        FieldDefinition("総合指数", "total_index", ["KYI"], is_numeric=True),
        FieldDefinition("調教指数", "training_index", ["KYI"], is_numeric=True),
        FieldDefinition("厩舎指数", "stable_index", ["KYI"], is_numeric=True),
        # オッズ関連（KYI - 除外）
        FieldDefinition("基準オッズ", None, ["KYI"], is_excluded=True),
        FieldDefinition("基準人気順位", None, ["KYI"], is_excluded=True),
        FieldDefinition("基準複勝オッズ", None, ["KYI"], is_excluded=True),
        FieldDefinition("基準複勝人気順位", None, ["KYI"], is_excluded=True),
        # 事前予想データ（KYI - 除外）
        FieldDefinition("テン指数", None, ["KYI"], is_excluded=True),
        FieldDefinition("ペース指数", None, ["KYI"], is_excluded=True),
        FieldDefinition("上がり指数", None, ["KYI"], is_excluded=True),
        FieldDefinition("位置指数", None, ["KYI"], is_excluded=True),
        FieldDefinition("ペース予想", None, ["KYI"], is_excluded=True),
        FieldDefinition("道中順位", None, ["KYI"], is_excluded=True),
        FieldDefinition("道中差", None, ["KYI"], is_excluded=True),
        FieldDefinition("道中内外", None, ["KYI"], is_excluded=True),
        FieldDefinition("後３Ｆ順位", None, ["KYI"], is_excluded=True),
        FieldDefinition("後３Ｆ差", None, ["KYI"], is_excluded=True),
        FieldDefinition("後３Ｆ内外", None, ["KYI"], is_excluded=True),
        FieldDefinition("ゴール順位", None, ["KYI"], is_excluded=True),
        FieldDefinition("ゴール差", None, ["KYI"], is_excluded=True),
        FieldDefinition("ゴール内外", None, ["KYI"], is_excluded=True),
        FieldDefinition("展開記号", None, ["KYI"], is_excluded=True),
        FieldDefinition("テン指数順位", None, ["KYI"], is_excluded=True),
        FieldDefinition("ペース指数順位", None, ["KYI"], is_excluded=True),
        FieldDefinition("上がり指数順位", None, ["KYI"], is_excluded=True),
        FieldDefinition("位置指数順位", None, ["KYI"], is_excluded=True),
        # 適性データ（KYI）
        FieldDefinition("脚質", "running_style", ["KYI"], is_numeric=True),
        FieldDefinition("距離適性", "distance_aptitude", ["KYI"], is_numeric=True),
        FieldDefinition("芝適性コード", "turf_aptitude", ["KYI"], is_categorical=True, is_numeric=False),
        FieldDefinition("ダ適性コード", "dirt_aptitude", ["KYI"], is_categorical=True, is_numeric=False),
        FieldDefinition("重適正コード", "weight_aptitude", ["KYI"], is_numeric=True),
        # 馬基本データ（UKC）
        FieldDefinition("血統登録番号", "horse_id", ["UKC"], is_numeric=True),
        FieldDefinition("性別コード", "sex", ["UKC"], is_categorical=True, category_list=SEX, is_numeric=False),
        # 直前情報（TYB）
        FieldDefinition("馬体重", "horse_weight", ["TYB"], is_numeric=True),
        FieldDefinition("馬体重増減", "horse_weight_diff", ["TYB"], is_numeric=True),
        FieldDefinition("パドック指数", "paddock_index", ["TYB"], is_numeric=True),
        # オッズ関連（TYB - 除外）
        FieldDefinition("オッズ指数", None, ["TYB"], is_excluded=True),
        FieldDefinition("単勝オッズ", None, ["TYB"], is_excluded=True),
        FieldDefinition("複勝オッズ", None, ["TYB"], is_excluded=True),
        FieldDefinition("オッズ印", None, ["TYB"], is_excluded=True),
        # 成績データ（SED - 評価用、予測には使用しない）
        FieldDefinition("着順", "rank", ["SED"], is_numeric=True, is_excluded=True),  # ターゲット変数のため除外
        FieldDefinition("タイム", "time", ["SED"], is_numeric=True),
        FieldDefinition("確定単勝オッズ", None, ["SED"], is_excluded=True),
        FieldDefinition("確定単勝人気順位", None, ["SED"], is_excluded=True),
        FieldDefinition("確定複勝オッズ下1", None, ["SED"], is_excluded=True),
        FieldDefinition("確定複勝オッズ下2", None, ["SED"], is_excluded=True),
        FieldDefinition("確定複勝オッズ下3", None, ["SED"], is_excluded=True),
        # 前走データ（SEDから抽出）
        FieldDefinition("R", "prev_1_race_num", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("頭数", "prev_1_num_horses", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("枠番", "prev_1_frame", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("馬番", "prev_1_horse_number", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("着順", "prev_1_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("タイム", "prev_1_time", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("距離", "prev_1_distance", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("芝ダ障害コード", "prev_1_course_type", ["SED"], is_categorical=True, category_map=COURSE_TYPE, is_computed=True),
        FieldDefinition("馬場状態", "prev_1_ground_condition", ["SED"], is_categorical=True, category_list=GROUND_CONDITION, is_computed=True),
        FieldDefinition("R", "prev_2_race_num", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("頭数", "prev_2_num_horses", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("枠番", "prev_2_frame", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("馬番", "prev_2_horse_number", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("着順", "prev_2_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("タイム", "prev_2_time", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("距離", "prev_2_distance", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("芝ダ障害コード", "prev_2_course_type", ["SED"], is_categorical=True, category_map=COURSE_TYPE, is_computed=True),
        FieldDefinition("馬場状態", "prev_2_ground_condition", ["SED"], is_categorical=True, category_list=GROUND_CONDITION, is_computed=True),
        FieldDefinition("R", "prev_3_race_num", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("頭数", "prev_3_num_horses", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("枠番", "prev_3_frame", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("馬番", "prev_3_horse_number", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("着順", "prev_3_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("タイム", "prev_3_time", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("距離", "prev_3_distance", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("芝ダ障害コード", "prev_3_course_type", ["SED"], is_categorical=True, category_map=COURSE_TYPE, is_computed=True),
        FieldDefinition("馬場状態", "prev_3_ground_condition", ["SED"], is_categorical=True, category_list=GROUND_CONDITION, is_computed=True),
        FieldDefinition("R", "prev_4_race_num", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("頭数", "prev_4_num_horses", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("枠番", "prev_4_frame", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("馬番", "prev_4_horse_number", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("着順", "prev_4_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("タイム", "prev_4_time", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("距離", "prev_4_distance", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("芝ダ障害コード", "prev_4_course_type", ["SED"], is_categorical=True, category_map=COURSE_TYPE, is_computed=True),
        FieldDefinition("馬場状態", "prev_4_ground_condition", ["SED"], is_categorical=True, category_list=GROUND_CONDITION, is_computed=True),
        FieldDefinition("R", "prev_5_race_num", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("頭数", "prev_5_num_horses", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("枠番", "prev_5_frame", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("馬番", "prev_5_horse_number", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("着順", "prev_5_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("タイム", "prev_5_time", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("距離", "prev_5_distance", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("芝ダ障害コード", "prev_5_course_type", ["SED"], is_categorical=True, category_map=COURSE_TYPE, is_computed=True),
        FieldDefinition("馬場状態", "prev_5_ground_condition", ["SED"], is_categorical=True, category_list=GROUND_CONDITION, is_computed=True),
        # 統計特徴量（計算フィールド）
        FieldDefinition(None, "horse_win_rate", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "horse_place_rate", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "horse_avg_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "horse_race_count", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "jockey_win_rate", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "jockey_place_rate", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "jockey_avg_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "jockey_race_count", ["SED"], is_numeric=True, is_computed=True),
        # 騎手の直近3レース詳細（SEDから抽出）
        FieldDefinition("着順", "jockey_recent_1_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("タイム", "jockey_recent_1_time", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("距離", "jockey_recent_1_distance", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("芝ダ障害コード", "jockey_recent_1_course_type", ["SED"], is_categorical=True, category_map=COURSE_TYPE, is_computed=True),
        FieldDefinition("馬場状態", "jockey_recent_1_ground_condition", ["SED"], is_categorical=True, category_list=GROUND_CONDITION, is_computed=True),
        FieldDefinition("頭数", "jockey_recent_1_num_horses", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("R", "jockey_recent_1_race_num", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("着順", "jockey_recent_2_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("タイム", "jockey_recent_2_time", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("距離", "jockey_recent_2_distance", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("芝ダ障害コード", "jockey_recent_2_course_type", ["SED"], is_categorical=True, category_map=COURSE_TYPE, is_computed=True),
        FieldDefinition("馬場状態", "jockey_recent_2_ground_condition", ["SED"], is_categorical=True, category_list=GROUND_CONDITION, is_computed=True),
        FieldDefinition("頭数", "jockey_recent_2_num_horses", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("R", "jockey_recent_2_race_num", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("着順", "jockey_recent_3_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("タイム", "jockey_recent_3_time", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("距離", "jockey_recent_3_distance", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("芝ダ障害コード", "jockey_recent_3_course_type", ["SED"], is_categorical=True, category_map=COURSE_TYPE, is_computed=True),
        FieldDefinition("馬場状態", "jockey_recent_3_ground_condition", ["SED"], is_categorical=True, category_list=GROUND_CONDITION, is_computed=True),
        FieldDefinition("頭数", "jockey_recent_3_num_horses", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition("R", "jockey_recent_3_race_num", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "trainer_win_rate", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "trainer_place_rate", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "trainer_avg_rank", ["SED"], is_numeric=True, is_computed=True),
        FieldDefinition(None, "trainer_race_count", ["SED"], is_numeric=True, is_computed=True),
    ]

    @cached_property
    def field_mapping(self) -> Dict[str, str]:
        """JRDBフィールド名 → 特徴量名のマッピング（除外フィールドを除く）"""
        mapping = {}
        for field in self.FIELD_DEFINITIONS:
            if field.jrdb_name and field.feature_name and not field.is_excluded:
                mapping[field.jrdb_name] = field.feature_name
        return mapping

    @cached_property
    def excluded_fields(self) -> set[str]:
        """除外するフィールドのセット"""
        excluded = set()
        for field in self.FIELD_DEFINITIONS:
            if field.is_excluded and field.jrdb_name:
                excluded.add(field.jrdb_name)
        return excluded

    @cached_property
    def feature_names(self) -> list[str]:
        """特徴量名のリスト（除外フィールドを除く）"""
        names = []
        for field in self.FIELD_DEFINITIONS:
            if field.feature_name and not field.is_excluded:
                names.append(field.feature_name)
        return sorted(set(names))  # 重複を除去してソート

    @cached_property
    def categorical_features(self) -> list[dict[str, Any]]:
        """カテゴリカル特徴量の定義"""
        categorical = []
        for field in self.FIELD_DEFINITIONS:
            if field.is_categorical and field.feature_name and not field.is_excluded:
                cat_def = {"name": field.feature_name, "type": str}
                if field.category_map:
                    cat_def["map"] = field.category_map
                if field.category_list:
                    cat_def["list"] = field.category_list
                categorical.append(cat_def)
        return categorical

    @cached_property
    def numeric_features(self) -> list[str]:
        """数値特徴量のリスト"""
        numeric = []
        for field in self.FIELD_DEFINITIONS:
            if field.is_numeric and field.feature_name and not field.is_excluded:
                numeric.append(field.feature_name)
        return sorted(set(numeric))  # 重複を除去してソート

    @cached_property
    def integer_features(self) -> list[str]:
        """整数型にダウンキャストする特徴量のリスト"""
        integer = []
        for field in self.FIELD_DEFINITIONS:
            if field.is_integer and field.feature_name and not field.is_excluded:
                integer.append(field.feature_name)
        return sorted(set(integer))  # 重複を除去してソート

    @cached_property
    def encoded_feature_names(self) -> list[str]:
        """エンコード済み特徴量名のリスト（カテゴリカル特徴量はe_プレフィックス付き）"""
        encoded_names = []
        categorical_names = {f["name"] for f in self.categorical_features}

        for name in self.feature_names:
            encoded_names.append(name)
            if name in categorical_names:
                encoded_names.append(f"e_{name}")

        return encoded_names

    def should_exclude_field(self, field_name: str) -> bool:
        """フィールドを除外すべきかどうか（オッズ関連チェック）"""
        return field_name in self.excluded_fields

    def get_field_by_jrdb_name(self, jrdb_name: str) -> Optional[FieldDefinition]:
        """JRDBフィールド名からフィールド定義を取得"""
        for field in self.FIELD_DEFINITIONS:
            if field.jrdb_name == jrdb_name:
                return field
        return None

    def get_field_by_feature_name(self, feature_name: str) -> Optional[FieldDefinition]:
        """特徴量名からフィールド定義を取得"""
        for field in self.FIELD_DEFINITIONS:
            if field.feature_name == feature_name:
                return field
        return None

    # データタイプごとの結合キー定義
    DATA_TYPE_JOIN_KEYS = {
        "BAC": {"keys": ["race_key"], "use_bac_date": False},  # レース情報なのでrace_keyのみ
        "KYI": {"keys": ["race_key", "馬番"], "use_bac_date": False},  # レースキー+馬番
        "SED": {"keys": ["race_key", "馬番"], "use_bac_date": True},  # レースキー+馬番（BACから年月日取得）
        "SEC": {"keys": ["race_key", "馬番"], "use_bac_date": True},  # SEDと同じ
        "UKC": {"keys": ["血統登録番号"], "use_bac_date": False},  # 血統登録番号
        "TYB": {"keys": ["race_key", "馬番"], "use_bac_date": True},  # レースキー+馬番
    }
