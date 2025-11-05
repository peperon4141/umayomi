# JRDBデータParquet変換・Firebase Storage保存機能実装計画

## 概要
JRDBから取得した10年間の競馬データ（lzh形式）をParquet形式に変換し、Firebase Storageに保存する機能を実装します。データ取得・変換は全てNode.jsで行い、Pythonはモデル処理のみに使用します。データ種別ごとにフォルダ分けして保存します。

## コスト見積もり
- **ストレージ容量**: 5GB無料、超過分は$0.026/GB/月
- **データダウンロード**: 1日あたり1GB無料、超過分は$0.12/GB
- **10年間のデータ想定**: 約100GBの場合、月額約$2.47（ストレージ）+ 使用量に応じたダウンロード料金

## 実装内容

### 1. Firebase Storage設定
- `apps/firebase.json`にStorageエミュレーター設定を追加
- Storageルールファイル（`apps/firebase/storage.rules`）を作成
- 認証済みユーザーのみ読み取り可能、Cloud Functionsからのみ書き込み可能

### 2. lzh展開・Parquet変換処理（Node.js）
- `apps/functions/src/utils/jrdbConverter.ts`を作成
  - lzhファイルの展開処理（Node.jsライブラリを使用）
  - **ShiftJISエンコーディング対応**: txtファイルがShiftJISの場合、`iconv-lite`または`encoding-japanese`ライブラリを使用してUTF-8に変換
  - JRDBデータ形式（固定長テキスト）の解析
  - Parquetファイルへの変換（`parquetjs`または`parquets`ライブラリを使用）
  - データ種別（KY, UK, ZE, BA, SEなど）ごとの処理
  - **Playwrightは不要**（既存のlzhファイルを処理する想定）

### 3. Firebase Storageアップロード処理（Node.js）
- `apps/functions/src/utils/storageUploader.ts`を作成
  - Firebase Admin SDKを使用してStorageにアップロード
  - ディレクトリ構造: `jrdb_data/{dataType}/{dataType}_{year}.parquet`（データ種別ごとにフォルダ分け）
  - メタデータ（ファイルサイズ、変換日時など）を保存

### 4. Cloud Functions（Node.js）
- `apps/functions/src/index.ts`に新しいFunctionを追加
  - `convertJRDBToParquet`: lzhファイルをアップロードしてParquetに変換し、Firebase Storageにアップロード（変換とアップロードを1つの関数内で処理）
  - **認証・認可**: 認証済みユーザーのみ実行可能にする
    - 方法1: `onRequest`を使用し、関数内で`request.headers.authorization`からFirebase IDトークンを検証
    - 方法2: Cloud Functions Gen 2の`invoker`設定で`allAuthenticatedUsers`のみ許可（推奨）
    - 方法3: 管理者ロールを持つユーザーのみ許可（`request.auth.token.role === 'admin'`）
  - バッチ処理対応（複数ファイルの一括処理）

### 5. Python Functions（Firebase Functions Gen 2）- モデル処理のみ
- `apps/functions-python/`ディレクトリを新規作成
- `apps/functions-python/main.py`: Firebase Functionsエントリーポイント
- `apps/functions-python/requirements.txt`: Python依存関係（pandas, pyarrow, firebase-admin, firebase-functions, lightgbm等）
- `apps/functions-python/.python-version`: Python 3.11以上を指定
- **機能1**: Firebase StorageからParquetファイルをダウンロードして競馬予想モデルを更新
  - `HorseRacePrediction/backend/prediction/`の既存コードを活用
  - Parquetファイルをpandasで読み込み
  - LightGBMモデルを学習
- **機能2**: 作成したモデル（LightGBM Booster）をFirebase Storageに保存
  - `HorseRacePrediction/backend/prediction/ModelTrainer.py`の`save_model`メソッドを参考に実装
  - モデルファイル（`.txt`形式）を一時的にローカルに保存
  - Firebase Admin SDKの`storage.bucket().blob()`を使用してStorageにアップロード
  - 保存パス: `models/{modelType}/{modelType}_{timestamp}.txt`
- **認証・認可**: 認証済みユーザーのみ実行可能にする
  - `firebase-functions`の`onRequest`で`invoker`を`allAuthenticatedUsers`に設定
  - または、関数内でFirebase IDトークンを検証
- **役割**: モデル処理のみ（データ取得・変換は行わない）
- **デプロイ**: `firebase.json`にPython Functionsの設定を追加し、`firebase deploy --only functions`でデプロイ

### 6. 依存関係の追加
- `apps/functions/package.json`に以下を追加:
  - `parquetjs`または`parquets`: Parquetファイルの読み書き（Node.jsで処理）
  - `lzh`または`node-lzh`: lzhファイルの展開（Node.jsで処理）
  - `iconv-lite`または`encoding-japanese`: ShiftJISからUTF-8への文字コード変換

### 7. 型定義
- `apps/shared/src/jrdb.ts`にJRDBデータの型定義を追加
  - 各データ種別（KY, UK, ZE等）の型定義
  - Parquet変換時のスキーマ定義

## ファイル構成
```
apps/
├── functions/              # Node.js Functions (Firebase Functions)
│   ├── src/
│   │   ├── index.ts (更新)
│   │   └── utils/
│   │       ├── jrdbConverter.ts (新規: lzh展開・Parquet変換)
│   │       └── storageUploader.ts (新規: Storageアップロード)
│   └── package.json
├── functions-python/        # Python Functions (Firebase Functions Gen 2)
│   ├── main.py (新規)
│   ├── requirements.txt (新規)
│   ├── .python-version (新規)
│   └── .gcloudignore (新規)
├── firebase/
│   ├── firebase.json (更新: Storageエミュレーター追加、Python Functions設定追加)
│   └── storage.rules (新規)
└── shared/
    └── src/
        └── jrdb.ts (更新: 型定義追加)
```

## データ構造
Storage内のディレクトリ構造（データ種別ごとにフォルダ分け）:
```
jrdb_data/
├── ky/          # 競走馬データ
│   ├── ky_2014.parquet
│   ├── ky_2015.parquet
│   └── ...
├── uk/          # 馬基本データ
│   ├── uk_2014.parquet
│   └── ...
├── ze/          # 前走データ
│   ├── ze_2014.parquet
│   └── ...
├── ba/          # 番組データ
└── se/          # 成績データ

models/          # 学習済みモデル
├── classifier/
│   ├── classifier_20250101_120000.txt
│   └── ...
├── regressor/
│   └── ...
└── ...
```

## 処理フロー
1. **データ取得・変換（Node.js Functions）**
   - lzhファイルをアップロード
   - lzh展開 → テキスト解析 → Parquet変換
   - Firebase Storageにアップロード（`jrdb_data/{dataType}/`配下）

2. **モデル更新（Python Functions）**
   - Firebase StorageからParquetファイルをダウンロード
   - `HorseRacePrediction/backend/prediction/`の既存コードを使用してモデル学習
   - 学習済みモデルをローカルに保存（`.txt`形式）
   - Firebase Storageにアップロード（`models/{modelType}/`配下）

## 構成の考え方

### Node.js Functions（Firebase Functions）
- **場所**: `apps/functions/`
- **デプロイ方法**: `firebase deploy --only functions`（`apps/firebase.json`から）
- **設定**: `apps/firebase.json`の`functions`セクションで定義
- **エミュレーター**: Firebase Emulatorsで実行可能（ポート5101）

### Python Functions（Firebase Functions Gen 2）
- **場所**: `apps/functions-python/`
- **デプロイ方法**: `firebase.json`にPython Functionsの設定を追加し、`firebase deploy --only functions`でデプロイ
- **設定**: `apps/firebase.json`に`functions-python`セクションを追加（または既存の`functions`セクションに複数ソースを定義）
- **エミュレーター**: Firebase Emulatorsで実行可能

## 次のステップ
1. Python FunctionsでParquetファイルを読み込んで競馬予想モデルを更新
2. 学習済みモデルをFirebase Storageに保存
3. 定期的なデータ更新処理の実装（スケジュール実行）
4. モデル更新の自動化（新しいデータが追加された際の自動処理）

## 注意事項
- **データ取得・変換は全てNode.jsで実装**（Playwrightは不要）
- **Pythonはモデル処理のみに使用**（Firebase Functions Gen 2でPythonをサポート）
- **ShiftJISエンコーディング対応**: JRDBデータのtxtファイルはShiftJISエンコーディングの可能性が高いため、`iconv-lite`や`encoding-japanese`を使用してUTF-8に変換してから処理する必要がある
- **認証・認可**: Cloud Functionsの実行を完全公開しないようにするため、以下のいずれかの方法で認証を必須にする
  - Cloud Functions Gen 2の`invoker`設定で`allAuthenticatedUsers`のみ許可（推奨）
  - 関数内でFirebase IDトークンを検証して認証済みユーザーのみ実行可能にする
  - 管理者ロールを持つユーザーのみ実行可能にする（`request.auth.token.role === 'admin'`）
- lzh展開ライブラリの選択（Node.jsで実装可能なライブラリを選択）
- 大量データ処理時のタイムアウト対策（バッチ処理、並列処理の検討）
- Firebase Functionsのタイムアウト設定（最大60分）
- データ種別ごとにフォルダ分けすることで、特定のデータ種別のみを処理可能
- Parquetライブラリ（`parquetjs`）はPythonの`pyarrow`ほど成熟していないが、基本的な読み書きは可能
- モデルファイルはLightGBMの`.txt`形式で保存（`HorseRacePrediction`の既存実装に合わせる）

