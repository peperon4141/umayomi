#!/usr/bin/env python3
"""TypeScriptフォーマット定義をJSONに変換（1オブジェクト1行形式）"""

import json
import re
from pathlib import Path

def parse_ts_format(ts_file: Path) -> dict:
    """TypeScriptフォーマット定義をパースしてJSONに変換"""
    with open(ts_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # dataTypeを抽出
    data_type_match = re.search(r"dataType:\s*['\"](\w+)['\"]", content)
    data_type = data_type_match.group(1) if data_type_match else None
    
    # descriptionを抽出
    desc_match = re.search(r"description:\s*['\"]([^'\"]+)['\"]", content)
    description = desc_match.group(1) if desc_match else None
    
    # recordLengthを抽出
    record_length_match = re.search(r"recordLength:\s*(\d+)", content)
    record_length = int(record_length_match.group(1)) if record_length_match else None
    
    # encodingとlineEndingを抽出
    encoding_match = re.search(r"encoding:\s*['\"](\w+)['\"]", content)
    encoding = encoding_match.group(1) if encoding_match else 'ShiftJIS'
    
    line_ending_match = re.search(r"lineEnding:\s*['\"](\w+)['\"]", content)
    line_ending = line_ending_match.group(1) if line_ending_match else 'CRLF'
    
    # fieldsを抽出（より柔軟なパターンマッチング）
    fields = []
    # 各行からフィールド定義を抽出
    lines = content.split('\n')
    for line in lines:
        # { name: '...', start: ..., length: ..., type: ..., description: '...' } のパターン
        field_match = re.search(r"{\s*name:\s*['\"]([^'\"]+)['\"][^}]*start:\s*(\d+)[^}]*length:\s*(\d+)[^}]*type:\s*JRDBFieldType\.(\w+)[^}]*description:\s*['\"]([^'\"]*)['\"]", line)
        if field_match:
            name = field_match.group(1)
            start = int(field_match.group(2))
            length = int(field_match.group(3))
            field_type = field_match.group(4)
            field_desc = field_match.group(5)
            
            # フィールドタイプのマッピング
            type_map = {
                'INTEGER_NINE': 'integer_nine',
                'INTEGER_ZERO_BLANK': 'integer_zero_blank',
                'STRING': 'string',
                'STRING_HEX': 'string_hex'
            }
            json_type = type_map.get(field_type, 'string')
            
            fields.append({
                'name': name,
                'start': start,
                'length': length,
                'type': json_type,
                'description': field_desc
            })
    
    return {
        'dataType': data_type,
        'description': description,
        'recordLength': record_length,
        'encoding': encoding,
        'lineEnding': line_ending,
        'fields': fields
    }

def save_json_compact(json_data: dict, output_file: Path):
    """1オブジェクト1行形式でJSONを保存"""
    # fields配列内の各オブジェクトを1行にまとめる
    fields_lines = []
    for field in json_data['fields']:
        field_json = json.dumps(field, ensure_ascii=False, separators=(',', ':'))
        fields_lines.append(field_json)
    
    # 全体のJSONを構築（fields配列は1オブジェクト1行）
    result = {
        'dataType': json_data['dataType'],
        'description': json_data['description'],
        'recordLength': json_data['recordLength'],
        'encoding': json_data['encoding'],
        'lineEnding': json_data['lineEnding'],
        'fields': json_data['fields']  # 通常の配列として保存（読み込み時に1行に変換可能）
    }
    
    # 1オブジェクト1行形式で保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json_str = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
        f.write(json_str)

if __name__ == '__main__':
    base_dir = Path(__file__).parent.parent
    schemas_dir = base_dir / 'packages' / 'data' / 'schemas' / 'jrdb-raw'
    schemas_dir.mkdir(parents=True, exist_ok=True)
    
    for data_type in ['KYI', 'BAC', 'SED', 'UKC', 'TYB']:
        ts_file = base_dir / 'apps' / 'functions' / 'src' / 'jrdb_scraper' / 'formats' / f'{data_type.lower()}.ts'
        if not ts_file.exists():
            print(f'Warning: {ts_file} not found')
            continue
        
        json_data = parse_ts_format(ts_file)
        json_file = schemas_dir / f'{data_type}.json'
        save_json_compact(json_data, json_file)
        print(f'Created {json_file}')

