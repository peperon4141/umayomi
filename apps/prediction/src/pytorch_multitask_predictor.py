"""
PyTorchベースのマルチタスク学習モデル

着順予測（ListNet風Listwise Loss）とタイム予測（回帰）を同時に学習
ResNet風のMLPアーキテクチャで精度を優先
"""

from typing import Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

from .evaluator import calculate_ndcg
from .features import Features


class ResidualBlock(nn.Module):
    """ResNet風の残差ブロック"""

    def __init__(self, in_dim: int, out_dim: int, dropout: float = 0.3):
        super().__init__()
        self.linear1 = nn.Linear(in_dim, out_dim)
        self.bn1 = nn.BatchNorm1d(out_dim)
        self.linear2 = nn.Linear(out_dim, out_dim)
        self.bn2 = nn.BatchNorm1d(out_dim)
        self.dropout = nn.Dropout(dropout)
        self.relu = nn.ReLU()

        # スキップ接続用（次元が異なる場合）
        self.skip = nn.Linear(in_dim, out_dim) if in_dim != out_dim else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = self.skip(x)

        out = self.linear1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.dropout(out)

        out = self.linear2(out)
        out = self.bn2(out)

        out += identity
        out = self.relu(out)

        return out


class MultitaskModel(nn.Module):
    """マルチタスク学習モデル（ResNet風MLP）"""

    def __init__(self, input_dim: int, hidden_dims: list[int] = None, dropout: float = 0.3):
        if hidden_dims is None:
            hidden_dims = [512, 256, 128, 64]
        super().__init__()

        # 入力層
        self.input_bn = nn.BatchNorm1d(input_dim)

        # 共有エンコーダー（ResNet風）
        self.encoder = nn.ModuleList()
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            self.encoder.append(ResidualBlock(prev_dim, hidden_dim, dropout))
            prev_dim = hidden_dim

        # タスク固有ヘッド
        self.rank_head = nn.Sequential(
            nn.Linear(hidden_dims[-1], 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
        )

        self.time_head = nn.Sequential(
            nn.Linear(hidden_dims[-1], 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 1),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # 入力正規化
        x = self.input_bn(x)

        # 共有エンコーダー
        for block in self.encoder:
            x = block(x)

        # タスク固有ヘッド
        rank_score = self.rank_head(x)
        time_pred = self.time_head(x)

        return rank_score, time_pred


class ListNetLoss(nn.Module):
    """ListNet風のListwise Loss"""

    def forward(
        self, rank_scores: torch.Tensor, rank_targets: torch.Tensor, group_sizes: list[int]
    ) -> torch.Tensor:
        """
        Args:
            rank_scores: [group_size, 1] または [group_size] ランキングスコア
            rank_targets: [group_size] 実際の着順（1着=1, 2着=2, ...）
            group_sizes: 各レースの頭数リスト（通常は[group_size]の1要素）

        Returns:
            loss: ListNet損失
        """
        # バッチサイズ=1でレース単位なので、group_sizesは通常[group_size]の1要素
        # rank_scoresは[group_size, 1]の形状、rank_targetsは[group_size]の形状
        if len(group_sizes) == 0:
            return torch.tensor(0.0, device=rank_scores.device)

        group_size = group_sizes[0]
        if group_size == 0:
            return torch.tensor(0.0, device=rank_scores.device)

        # レース内のスコアとターゲット
        # rank_scoresは[group_size, 1]の形状なので、squeeze(-1)で[group_size]に
        if rank_scores.dim() > 1:
            race_scores = rank_scores.squeeze(-1)  # [group_size]
        else:
            race_scores = rank_scores  # [group_size]
        race_targets = rank_targets  # [group_size]

        # 実際の着順をスコアに変換（1着=3, 2着=2, 3着=1, その他=0）
        def convert_rank_to_score(rank: int) -> int:
            if rank == 1:
                return 3
            if rank == 2:
                return 2
            if rank == 3:
                return 1
            return 0

        # ターゲットスコアを計算
        target_scores = torch.tensor(
            [convert_rank_to_score(int(r)) for r in race_targets],
            dtype=torch.float32,
            device=race_scores.device,
        )

        # ソフトマックスで確率分布に変換
        pred_probs = F.softmax(race_scores, dim=0)
        target_probs = F.softmax(target_scores, dim=0)

        # クロスエントロピー損失
        loss = -torch.sum(target_probs * torch.log(pred_probs + 1e-8))

        return loss


class RaceDataset(Dataset):
    """レース単位でデータをグループ化するDataset"""

    def __init__(self, df: pd.DataFrame, features: Features, normalize_time: bool = True):
        self.df = df.reset_index() if df.index.name == "race_key" else df.copy()
        self.features = features
        self.normalize_time = normalize_time

        # 特徴量名を取得（object型を除外）
        self.feature_names = self._get_numeric_features()

        # レース単位でグループ化
        if "race_key" in self.df.columns:
            self.race_groups = self.df.groupby("race_key")
        elif self.df.index.name == "race_key":
            self.df["race_key"] = self.df.index
            self.race_groups = self.df.groupby("race_key")
        else:
            raise ValueError("race_keyが見つかりません")

        self.race_keys = list(self.race_groups.groups.keys())

    def _get_numeric_features(self) -> list[str]:
        """数値型特徴量のみを取得"""
        encoded_names = self.features.encoded_feature_names
        numeric_features = []

        for feat in encoded_names:
            if feat in self.df.columns:
                dtype = self.df[feat].dtype
                if dtype != "object" and str(dtype) != "object":
                    # NaNチェック
                    if not self.df[feat].isna().all():
                        numeric_features.append(feat)

        return numeric_features

    def _normalize_time(
        self, time: float, distance: float, course_type: str, ground_condition: str
    ) -> float:
        """タイムを正規化"""
        if pd.isna(time) or pd.isna(distance):
            return np.nan

        # 標準タイム（秒/100m）
        base_time = 6.0
        course_factor = {"芝": 1.0, "ダ": 1.05, "ダート": 1.05, "障": 1.10, "障害": 1.10}.get(
            course_type, 1.0
        )
        ground_factor = {"良": 1.0, "稍": 1.02, "重": 1.05, "不": 1.08, "重不": 1.10}.get(
            ground_condition, 1.0
        )

        standard_time_per_100m = base_time * course_factor * ground_factor

        # タイムを正規化
        time_per_100m = time / (distance / 100)
        if standard_time_per_100m == 0:
            return np.nan
        normalized_time = time_per_100m / standard_time_per_100m

        return normalized_time

    def __len__(self) -> int:
        return len(self.race_keys)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        race_key = self.race_keys[idx]
        race_df = self.race_groups.get_group(race_key)

        # 特徴量を取得
        feature_data = race_df[self.feature_names].values.astype(np.float32)

        # NaNを0で埋める
        feature_data = np.nan_to_num(feature_data, nan=0.0)

        # ターゲットを取得
        if "rank" not in race_df.columns:
            # rankカラムがない場合は、全馬を同順位（中間値）として扱う
            rank_targets = np.full(len(race_df), len(race_df) / 2.0 + 0.5, dtype=np.float32)
        else:
            rank_targets = race_df["rank"].values.astype(np.float32)
            # NaNを中間値で埋める
            if np.isnan(rank_targets).any():
                mean_rank = np.nanmean(rank_targets)
                if np.isnan(mean_rank):
                    mean_rank = len(race_df) / 2.0 + 0.5
                rank_targets = np.nan_to_num(rank_targets, nan=mean_rank)

        # タイムを取得・正規化
        if "タイム" in race_df.columns and self.normalize_time:
            times = race_df["タイム"].values
            # 必須カラムを明示的にチェック（fallback禁止）
            if "course_length" in race_df.columns:
                distances = race_df["course_length"].values
            elif "距離" in race_df.columns:
                distances = race_df["距離"].values
            else:
                raise ValueError("course_lengthまたは距離カラムが必要です")
            
            if "course_type" in race_df.columns:
                course_types = race_df["course_type"].astype(str).values
            else:
                raise ValueError("course_typeカラムが必要です")
            
            if "ground_condition" in race_df.columns:
                ground_conditions = race_df["ground_condition"].astype(str).values
            else:
                raise ValueError("ground_conditionカラムが必要です")

            time_targets = np.array(
                [
                    self._normalize_time(t, d, ct, gc)
                    for t, d, ct, gc in zip(
                        times, distances, course_types, ground_conditions, strict=False
                    )
                ],
                dtype=np.float32,
            )

            # NaNを平均値で埋める
            if np.isnan(time_targets).any():
                mean_time = np.nanmean(time_targets)
                time_targets = np.nan_to_num(
                    time_targets, nan=mean_time if not np.isnan(mean_time) else 1.0
                )
        else:
            # タイムがない場合は1.0（標準タイム）を設定
            time_targets = np.ones(len(race_df), dtype=np.float32)

        return {
            "features": torch.tensor(feature_data),
            "rank_targets": torch.tensor(rank_targets),
            "time_targets": torch.tensor(time_targets),
            "race_key": race_key,
            "group_size": len(race_df),
        }


class MultitaskPredictor:
    """PyTorchベースのマルチタスク学習モデル"""

    def __init__(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        hidden_dims: list[int] = None,
        dropout: float = 0.3,
        rank_weight: float = 0.7,
        time_weight: float = 0.3,
        learning_rate: float = 1e-3,
        device: Optional[str] = None,
    ):
        if hidden_dims is None:
            hidden_dims = [512, 256, 128, 64]
        self.features = Features()
        self.train_df = train_df
        self.val_df = val_df
        self.rank_weight = rank_weight
        self.time_weight = time_weight

        # デバイス設定
        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # データセット作成
        self.train_dataset = RaceDataset(train_df, self.features)
        self.val_dataset = RaceDataset(val_df, self.features)

        # 特徴量次元を取得
        input_dim = len(self.train_dataset.feature_names)

        # モデル作成
        self.model = MultitaskModel(
            input_dim=input_dim, hidden_dims=hidden_dims, dropout=dropout
        ).to(self.device)

        # 損失関数
        self.rank_loss_fn = ListNetLoss()
        self.time_loss_fn = nn.MSELoss()

        # オプティマイザー
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)

        # 学習履歴
        self.train_history = {"rank_loss": [], "time_loss": [], "total_loss": [], "val_ndcg": []}

    def train_epoch(self) -> dict[str, float]:
        """1エポック学習"""
        self.model.train()
        total_rank_loss = 0.0
        total_time_loss = 0.0
        total_loss = 0.0
        num_batches = 0

        # データローダー（バッチサイズ=1レース）
        train_loader = DataLoader(
            self.train_dataset, batch_size=1, shuffle=True, collate_fn=self._collate_fn
        )

        for batch in train_loader:
            features = batch["features"].to(self.device)  # [group_size, num_features]
            rank_targets = batch["rank_targets"].to(self.device)  # [group_size]
            time_targets = batch["time_targets"].to(self.device)  # [group_size]
            group_sizes = batch["group_sizes"]  # List[int]

            # 順伝播
            rank_scores, time_preds = self.model(features)

            # 損失計算（rank_scoresは[group_size, 1]の形状）
            rank_loss = self.rank_loss_fn(rank_scores, rank_targets, group_sizes)
            time_loss = self.time_loss_fn(time_preds.squeeze(-1), time_targets)
            total_batch_loss = self.rank_weight * rank_loss + self.time_weight * time_loss

            # 逆伝播
            self.optimizer.zero_grad()
            total_batch_loss.backward()
            self.optimizer.step()

            total_rank_loss += rank_loss.item()
            total_time_loss += time_loss.item()
            total_loss += total_batch_loss.item()
            num_batches += 1

        return {
            "rank_loss": total_rank_loss / num_batches if num_batches > 0 else 0.0,
            "time_loss": total_time_loss / num_batches if num_batches > 0 else 0.0,
            "total_loss": total_loss / num_batches if num_batches > 0 else 0.0,
        }

    def validate(self) -> dict[str, float]:
        """検証"""
        self.model.eval()
        all_rank_preds = []
        all_rank_targets = []
        all_time_preds = []
        all_time_targets = []
        ndcg_scores = []

        val_loader = DataLoader(
            self.val_dataset, batch_size=1, shuffle=False, collate_fn=self._collate_fn
        )

        with torch.no_grad():
            for batch in val_loader:
                features = batch["features"].to(self.device)
                rank_targets = batch["rank_targets"].cpu().numpy()
                time_targets = batch["time_targets"].cpu().numpy()
                batch["group_sizes"][0]

                rank_scores, time_preds = self.model(features)

                rank_scores_np = rank_scores.squeeze(-1).cpu().numpy()
                time_preds_np = time_preds.squeeze(-1).cpu().numpy()

                # レース単位でNDCGを計算
                ndcg = calculate_ndcg(rank_targets, rank_scores_np, k=3)
                ndcg_scores.append(ndcg)

                all_rank_preds.extend(rank_scores_np)
                all_rank_targets.extend(rank_targets)
                all_time_preds.extend(time_preds_np)
                all_time_targets.extend(time_targets)

        # タイム予測のMAE
        time_mae = np.mean(np.abs(np.array(all_time_preds) - np.array(all_time_targets)))

        return {"ndcg": np.mean(ndcg_scores) if ndcg_scores else 0.0, "time_mae": time_mae}

    def _collate_fn(self, batch: list[dict]) -> dict[str, torch.Tensor]:
        """バッチを結合（レース単位）"""
        # バッチサイズ=1なので、最初の要素を返す
        item = batch[0]

        return {
            "features": item["features"],
            "rank_targets": item["rank_targets"],
            "time_targets": item["time_targets"],
            "race_key": item["race_key"],
            "group_sizes": [item["group_size"]],
        }

    def train(
        self, num_epochs: int = 50, early_stopping_patience: int = 10, verbose: bool = True
    ) -> dict[str, list[float]]:
        """学習実行"""
        best_ndcg = 0.0
        patience_counter = 0

        for epoch in range(num_epochs):
            # 学習
            train_metrics = self.train_epoch()

            # 検証
            val_metrics = self.validate()

            # 履歴に記録
            self.train_history["rank_loss"].append(train_metrics["rank_loss"])
            self.train_history["time_loss"].append(train_metrics["time_loss"])
            self.train_history["total_loss"].append(train_metrics["total_loss"])
            self.train_history["val_ndcg"].append(val_metrics["ndcg"])

            # ベストモデル更新
            if val_metrics["ndcg"] > best_ndcg:
                best_ndcg = val_metrics["ndcg"]
                patience_counter = 0
                # ベストモデルを保存（ここでは履歴に記録のみ）
            else:
                patience_counter += 1

            # ログ出力
            if verbose and (epoch + 1) % 5 == 0:
                print(
                    f"Epoch {epoch + 1}/{num_epochs} | "
                    f"Train Loss: {train_metrics['total_loss']:.4f} "
                    f"(Rank: {train_metrics['rank_loss']:.4f}, "
                    f"Time: {train_metrics['time_loss']:.4f}) | "
                    f"Val NDCG: {val_metrics['ndcg']:.4f} | "
                    f"Time MAE: {val_metrics['time_mae']:.4f}"
                )

            # Early stopping
            if patience_counter >= early_stopping_patience:
                if verbose:
                    print(f"Early stopping at epoch {epoch + 1}")
                break

        return self.train_history

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """予測"""
        self.model.eval()

        # データセット作成
        dataset = RaceDataset(df, self.features)
        loader = DataLoader(dataset, batch_size=1, shuffle=False, collate_fn=self._collate_fn)

        # 予測結果をrace_keyごとに保存
        predictions_dict = {}

        with torch.no_grad():
            for batch in loader:
                features = batch["features"].to(self.device)
                race_key = batch["race_key"]

                rank_scores, time_preds = self.model(features)

                rank_scores_np = rank_scores.squeeze(-1).cpu().numpy()
                time_preds_np = time_preds.squeeze(-1).cpu().numpy()

                predictions_dict[race_key] = {
                    "rank_pred": rank_scores_np,
                    "time_pred": time_preds_np,
                }

        # 結果をDataFrameに変換
        result_df = df.copy()

        # race_keyでグループ化して予測結果を追加
        if result_df.index.name == "race_key":
            result_df = result_df.reset_index()

        rank_preds = []
        time_preds = []

        for race_key, group in result_df.groupby("race_key"):
            if race_key in predictions_dict:
                pred_data = predictions_dict[race_key]
                rank_preds.extend(pred_data["rank_pred"])
                time_preds.extend(pred_data["time_pred"])
            else:
                # 予測がない場合はNaN
                rank_preds.extend([np.nan] * len(group))
                time_preds.extend([np.nan] * len(group))

        result_df["rank_pred"] = rank_preds
        result_df["time_pred"] = time_preds

        # インデックスを復元
        if "race_key" in result_df.columns and df.index.name == "race_key":
            result_df = result_df.set_index("race_key")

        return result_df

    def save_model(self, path: str):
        """モデルを保存"""
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "feature_names": self.train_dataset.feature_names,
                "hidden_dims": [512, 256, 128, 64],  # デフォルト値
                "dropout": 0.3,
                "train_history": self.train_history,
            },
            path,
        )

    def load_model(self, path: str):
        """モデルを読み込み"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.train_history = checkpoint.get("train_history", self.train_history)
