# JRDB KY系データ取得用curlコマンド

## エミュレータ環境用

### 2025-11-02 東京 11レースのKY系データを取得

```bash
curl -X GET "http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/fetchRaceKYData?year=2025&month=11&day=2&racecourse=東京&kaisaiRound=1&kaisaiDay=1&raceNumber=11"
```

### パラメータ説明

- `year`: 年（必須）
- `month`: 月（必須）
- `day`: 日（必須）
- `racecourse`: 競馬場名（必須、例: "東京"）
- `kaisaiRound`: 開催回数（必須、例: 1）
- `kaisaiDay`: 日目（必須、例: 1）
- `raceNumber`: レース番号（必須、例: 11）

### レスポンス例

```json
{
  "success": true,
  "message": "KY系データの取得が完了しました（レースキー: 2025110201011）",
  "raceKey": "2025110201011",
  "dataTypes": ["KYI", "KYH", "KYG", "KKA"],
  "results": [
    {
      "dataType": "KYI",
      "success": true,
      "recordCount": 120
    },
    {
      "dataType": "KYH",
      "success": true,
      "recordCount": 120
    },
    {
      "dataType": "KYG",
      "success": true,
      "recordCount": 120
    },
    {
      "dataType": "KKA",
      "success": true,
      "recordCount": 120
    }
  ],
  "executionTimeMs": 12345
}
```

## 本番環境用

```bash
curl -X GET "https://asia-northeast1-umayomi-fbb2b.cloudfunctions.net/fetchRaceKYData?year=2025&month=11&day=2&racecourse=東京&kaisaiRound=1&kaisaiDay=1&raceNumber=11"
```

## エラーレスポンス例

### パラメータ不足の場合（400 Bad Request）

```bash
curl -X GET "http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/fetchRaceKYData?year=2025&month=11"
```

レスポンス:
```json
{
  "success": false,
  "error": "year, month, day, racecourse, raceNumber parameters are required"
}
```

## 注意事項

1. **開催回数と日目の確認**: `kaisaiRound`と`kaisaiDay`は実際の開催情報に基づいて設定する必要があります。2025年11月2日の東京競馬場の開催回数と日目を確認してください。

2. **エミュレータ起動**: エミュレータ環境で実行する場合は、事前に`make dev`でFunctions Emulatorが起動している必要があります。

3. **認証**: JRDBデータのダウンロードには、環境変数`JRDB_USERNAME`と`JRDB_PASSWORD`が設定されている必要があります。

## 他のレースの例

### 2025年10月15日 中山 3レース

```bash
curl -X GET "http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/fetchRaceKYData?year=2025&month=10&day=15&racecourse=中山&kaisaiRound=1&kaisaiDay=1&raceNumber=3"
```

### 2025年9月28日 阪神 7レース

```bash
curl -X GET "http://127.0.0.1:5101/umayomi-fbb2b/asia-northeast1/fetchRaceKYData?year=2025&month=9&day=28&racecourse=阪神&kaisaiRound=1&kaisaiDay=1&raceNumber=7"
```

