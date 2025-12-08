"""メモリ使用量を監視するユーティリティ"""

from typing import Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class MemoryMonitor:
    """メモリ使用量を監視するクラス（staticメソッドのみ）"""

    @staticmethod
    def get_memory_usage_mb() -> Optional[float]:
        """
        現在のプロセスのメモリ使用量をMB単位で取得
        
        Returns:
            メモリ使用量（MB）、psutilが利用できない場合はNone
        """
        if not PSUTIL_AVAILABLE:
            return None
        
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            return memory_info.rss / (1024 * 1024)  # バイトをMBに変換
        except Exception:
            return None

    @staticmethod
    def print_memory_usage(step_name: str, before_mb: Optional[float] = None) -> Optional[float]:
        """
        メモリ使用量を表示
        
        Args:
            step_name: ステップ名
            before_mb: 前回のメモリ使用量（MB）、差分を表示する場合に使用
        
        Returns:
            現在のメモリ使用量（MB）
        """
        current_mb = MemoryMonitor.get_memory_usage_mb()
        
        if current_mb is None:
            print(f"[MEM] {step_name}: メモリ使用量の取得に失敗しました（psutilがインストールされていない可能性があります）")
            return None
        
        if before_mb is not None:
            diff_mb = current_mb - before_mb
            diff_gb = diff_mb / 1024
            print(f"[MEM] {step_name}: {current_mb:,.0f}MB ({current_mb/1024:.2f}GB) [差分: {diff_mb:+,.0f}MB ({diff_gb:+.2f}GB)]")
        else:
            print(f"[MEM] {step_name}: {current_mb:,.0f}MB ({current_mb/1024:.2f}GB)")
        
        return current_mb

