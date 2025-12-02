"""JRDBダウンローダー
HTTPリクエストでLZHファイルをダウンロード
"""

import base64
import logging
import os
import urllib.parse
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)


def download_jrdb_file(url: str) -> bytes:
    """JRDBのURLからlzhファイルをダウンロード
    認証が必要な場合は環境変数から取得
    
    Args:
        url: ダウンロードするURL
    
    Returns:
        ダウンロードしたファイルのバイト列
    
    Raises:
        ValueError: 環境変数が設定されていない場合
        Exception: ダウンロードに失敗した場合
    """
    jrdbUsername = os.getenv('JRDB_USERNAME')
    jrdbPassword = os.getenv('JRDB_PASSWORD')
    
    if not jrdbUsername or not jrdbPassword:
        raise ValueError('JRDB_USERNAME and JRDB_PASSWORD environment variables are required')
    
    logger.info('Downloading JRDB file', extra={'url': url})
    
    buffer = download_file_as_buffer(url, username=jrdbUsername, password=jrdbPassword)
    
    logger.info('JRDB file downloaded successfully', extra={
        'url': url,
        'size': len(buffer)
    })
    
    return buffer


def extract_file_name_from_url(url: str) -> str:
    """URLからファイル名を抽出
    
    Args:
        url: URL
    
    Returns:
        ファイル名
    """
    parsed = urllib.parse.urlparse(url)
    pathname = parsed.path
    fileName = pathname.split('/')[-1] or 'file.lzh'
    return fileName


def extract_base_file_name_from_url(url: str) -> str:
    """URLからファイル名（拡張子を除く）を抽出
    例: "https://jrdb.com/member/data/Jrdb/JRDB251102.lzh" -> "JRDB251102"
    
    Args:
        url: URL
    
    Returns:
        ファイル名（拡張子を除く）
    """
    fileName = extract_file_name_from_url(url)
    # 拡張子を除く
    import re
    baseName = re.sub(r'\.(lzh|LZH)$', '', fileName)
    return baseName


def download_file_as_buffer(
    url: str,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> bytes:
    """URLからファイルをダウンロードしてbytesとして返す
    リダイレクトにも対応
    
    Args:
        url: ダウンロードするURL
        username: 認証ユーザー名（オプション）
        password: 認証パスワード（オプション）
    
    Returns:
        ダウンロードしたファイルのバイト列
    
    Raises:
        Exception: ダウンロードに失敗した場合
    """
    max_redirects = 10
    redirect_count = 0
    
    while redirect_count < max_redirects:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        if username and password:
            auth_string = f'{username}:{password}'
            auth_bytes = auth_string.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            req.add_header('Authorization', f'Basic {auth_b64}')
        
        try:
            with urllib.request.urlopen(req) as response:
                # リダイレクト処理
                if response.status in (301, 302, 303, 307, 308):
                    redirect_url = response.headers.get('Location')
                    if not redirect_url:
                        raise ValueError(f'リダイレクト先が見つかりません: {url}')
                    url = redirect_url
                    redirect_count += 1
                    continue
                
                if response.status != 200:
                    raise Exception(f'HTTP {response.status}: {url}')
                
                return response.read()
        
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                redirect_url = e.headers.get('Location')
                if not redirect_url:
                    raise ValueError(f'リダイレクト先が見つかりません: {url}')
                url = redirect_url
                redirect_count += 1
                continue
            raise
    
    raise Exception(f'リダイレクトが多すぎます: {url}')

