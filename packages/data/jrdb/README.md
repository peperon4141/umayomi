# JRDBデータマッピング

JRDBデータファイルで使用されるコードのマッピング定義。

## ファイル一覧

- `venue_code_map.json`: JRDBデータファイル用の場コードマッピング（2桁コード）
- `paddock_code_map.json`: JRDBパドック観察データ用の場コードマッピング（1桁コード）

## 重要な注意事項

JRDBには**2種類の場コード**が存在します：

1. **データファイル場コード（2桁）**: BAC、KYI等のデータファイルで使用
   - 例: 01=札幌、05=東京、07=京都
   - ファイル: `venue_code_map.json`

2. **パドックコード（1桁）**: パドック観察データ（TYB等）で使用
   - 例: 1=東京、3=京都、4=阪神
   - ファイル: `paddock_code_map.json`
   - 参考: http://www.jrdb.com/program/jrdb_code.txt の「場のコード」セクション

**注意**: データファイル（BAC、KYI等）を処理する際は、必ず2桁コード（`venue_code_map.json`）を使用してください。

