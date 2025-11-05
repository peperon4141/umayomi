# JRDBデータとレース情報の連携実装計画

## 概要

現在のhostingサイトのレース情報表示に、JRDBデータを連携してより詳細な情報を表示できるようにします。

## 現状の実装

### レースデータ構造

- **Firestoreコレクション**: `races`
- **レースIDフォーマット**: `YYYY-MM-DD_競馬場_レース番号`（例: `2024-10-15_東京_1`）
- **主要フィールド**:
  - `date`: レース日
  - `racecourse`: 競馬場
  - `raceNumber`: レース番号
  - `raceName`: レース名
  - `distance`: 距離
  - `surface`: コース（芝/ダ）
  - `results`: レース結果配列

### レース詳細表示

- **ファイル**: `apps/hosting/src/views/RaceDetail.vue`
- **データ取得**: Firestoreの`races`コレクションから直接取得
- **表示内容**: レース基本情報、レース結果（着順、馬名、騎手、タイム、オッズ）

## 連携方法

### 1. レースキーの生成とマッピング

JRDBデータは「レースキー」でレースを識別します。レースキーの形式は以下の通りです：

```
レースキー = 開催日（YYYYMMDD）+ 場コード（2桁）+ 開催回数（1桁）+ 日目（1桁）+ レース番号（2桁）
```

例: `202410150101` = 2024年10月15日、東京、1回、1日目、1レース

#### レースキー変換関数の要件

- 競馬場名をJRDB場コードに変換する関数が必要
- レースIDからJRDBレースキーを生成する関数が必要
- RaceオブジェクトからJRDBレースキーを生成する関数が必要
- ファイル: `apps/hosting/src/utils/jrdbKeyConverter.ts`

### 2. JRDBデータのFirestore保存構造

#### コレクション構造

```
jrdb_race_data/
  {raceKey}/
    race_info: {
      raceKey: string
      date: Timestamp
      racecourse: string
      raceNumber: number
      // 番組データ（BA）の情報
      raceName?: string
      distance?: number
      surface?: string
      weather?: string
      trackCondition?: string
    }
    horses: [
      {
        horseNumber: number
        // 競走馬データ（KY）の情報
        horseId?: string
        horseName?: string
        jockey?: string
        trainer?: string
        // 直前データ（TY）の情報
        odds?: number
        // 情報データ（JO）の情報
        // 調教分析データ（CY）の情報
        // 調教本追切データ（CH）の情報
      }
    ]
    odds: {
      // 基準オッズデータ（OZ/OW/OU/OT/OV）の情報
      win?: number
      place?: number
      exacta?: number
      quinella?: number
      wide?: number
      trifecta?: number
      trio?: number
    }
    results: {
      // 成績データ（SE）の情報
      // 払戻情報データ（HJ）の情報
    }
```

### 3. レース詳細ページへのJRDBデータ統合

#### 実装方針

`RaceDetail.vue`を拡張して、JRDBデータを取得して表示します。

- レース詳細取得時に、JRDBデータも取得する
- オッズ情報（単勝、複勝など）を表示
- 競走馬詳細情報（馬名、騎手、調教師、オッズなど）を表示
- エラーハンドリング: JRDBデータがない場合も正常動作する

### 4. Composablesの作成

- `useJRDBRace` composableを作成
- ファイル: `apps/hosting/src/composables/useJRDBRace.ts`
- JRDBデータの取得、ローディング状態、エラーハンドリングを管理

## 実装ステップ

### ステップ1: レースキー変換ユーティリティの作成

1. `apps/hosting/src/utils/jrdbKeyConverter.ts` を作成
2. レースキー生成関数を実装
3. 競馬場名→JRDB場コードのマッピングを実装

### ステップ2: JRDBデータのFirestore保存

1. Cloud FunctionsでJRDBデータをFirestoreに保存する処理を実装
2. レースキーをドキュメントIDとして使用
3. データ構造を定義

### ステップ3: フロントエンドの統合

1. `useJRDBRace` composableを作成
2. `RaceDetail.vue`にJRDBデータ表示を追加
3. オッズ情報、競走馬詳細情報などを表示

### ステップ4: データマッピングの最適化

1. レースIDとJRDBレースキーの対応関係を確認
2. 開催回数・日目の情報を正確に取得できるように改善
3. エラーハンドリングを強化

## 注意事項

1. **レースキーの正確性**: JRDBのレースキーは開催回数・日目の情報が必要です。現在の実装では暫定的に`1`としていますが、実際のデータから取得する必要があります。

2. **データの存在確認**: JRDBデータがないレースも存在する可能性があるため、エラーハンドリングを適切に行う必要があります。

3. **パフォーマンス**: JRDBデータの取得は追加のFirestoreクエリになるため、必要に応じてキャッシュを検討します。

4. **データの更新タイミング**: JRDBデータはレース前日や当日に更新されるため、適切なタイミングでデータを取得・更新する必要があります。

## 参考

- [JRDBデータ仕様書](.cursor/rules/JRDB_SPECIFICATIONS.mdc)
- [Firestore費用見積もり](reports/JRDB_FIRESTORE_COST_ESTIMATE.md)

