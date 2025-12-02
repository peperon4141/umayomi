"""LZHファイル展開
lhaコマンドを使用して解凍
"""

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple

from .entities.jrdb import JRDBDataType
from .parsers.jrdb_parser import parse_jrdb_file_name

logger = logging.getLogger(__name__)


def extract_lzh_file(lzhBuffer: bytes) -> List[Tuple[bytes, str]]:
    """lzhファイルを展開してすべてのテキストファイルを取得
    lhaコマンドを使用して解凍
    エミュレータ環境では、事前にlhaコマンドをインストールする必要があります（macOS: brew install lhasa）
    
    Args:
        lzhBuffer: LZHファイルのバイト列
    
    Returns:
        展開されたすべての.txtファイルのバッファとファイル名のリスト
    
    Raises:
        Exception: 解凍に失敗した場合
    """
    # 一時ディレクトリを作成
    tempDir = tempfile.mkdtemp(prefix='lzh-extract-')
    tempLzhPath = Path(tempDir) / 'input.lzh'
    extractDir = Path(tempDir) / 'extract'
    
    try:
        # LZHファイルを一時ファイルに書き込む
        extractDir.mkdir(parents=True, exist_ok=True)
        tempLzhPath.write_bytes(lzhBuffer)
        
        # lhaコマンドのパスを取得
        lhaCommand = 'lha'
        try:
            # まずwhichコマンドでパスを確認
            whichResult = subprocess.run(
                ['which', 'lha'],
                capture_output=True,
                text=True,
                check=False
            )
            if whichResult.returncode == 0 and whichResult.stdout.strip():
                lhaCommand = whichResult.stdout.strip()
        except Exception:
            # whichコマンドが失敗した場合、直接lhaコマンドを試す
            pass
        
        # lhaコマンドで解凍（lha x <ファイル> でカレントディレクトリに解凍される）
        subprocess.run(
            ['sh', '-c', f'cd "{extractDir}" && "{lhaCommand}" x "{tempLzhPath}"'],
            capture_output=True,
            check=True,
            text=True
        )
        
        # 解凍されたファイルを探す
        extractedFiles = list(extractDir.iterdir())
        if not extractedFiles:
            raise ValueError('解凍されたファイルが見つかりません')
        
        # .txtファイルのみを処理
        txtFiles = [f for f in extractedFiles if f.name.endswith('.txt')]
        if not txtFiles:
            raise ValueError('解凍された.txtファイルが見つかりません')
        
        # すべての.txtファイルを返す
        return [(f.read_bytes(), f.name) for f in txtFiles]
    
    except subprocess.CalledProcessError as e:
        errorMessage = str(e)
        if 'lha' in errorMessage.lower() or 'command not found' in errorMessage.lower():
            import platform
            installCmd = 'brew install lhasa' if platform.system() == 'Darwin' else 'apt-get install -y lhasa'
            raise ValueError(f'lhaコマンドが見つかりません。事前にインストールしてください: {installCmd}')
        raise ValueError(f'LZH解凍に失敗しました: {errorMessage}')
    except Exception as e:
        raise ValueError(f'LZH解凍に失敗しました: {str(e)}')
    finally:
        # 一時ディレクトリを削除
        try:
            shutil.rmtree(tempDir, ignore_errors=True)
        except Exception:
            # クリーンアップ失敗は無視
            pass


def extract_data_type_from_file_name(fileName: str) -> Optional[JRDBDataType]:
    """展開後のファイル名からデータ種別を推測
    
    Args:
        fileName: 展開後のファイル名（例: "KYG251102.txt"）
    
    Returns:
        データ種別、見つからない場合はNone
    """
    try:
        parsed = parse_jrdb_file_name(fileName)
        if not parsed:
            return None
        
        dataType = parsed.get('dataType')
        if isinstance(dataType, JRDBDataType):
            return dataType
        return None
    except Exception:
        # ファイル名が.txtで終わる場合は、拡張子を除いて解析を試みる
        if fileName.endswith('.txt'):
            nameWithoutExt = fileName.replace('.txt', '')
            parsed = parse_jrdb_file_name(nameWithoutExt + '.lzh')
            if parsed:
                dataType = parsed.get('dataType')
                if isinstance(dataType, JRDBDataType):
                    return dataType
        return None

