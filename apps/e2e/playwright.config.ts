import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  timeout: 30 * 1000, // グローバルタイムアウトを30秒に設定
  testDir: './tests',
  fullyParallel: true, // 並列実行を有効化
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0, // リトライ回数を削減
  workers: 4, // CI環境では2、ローカルでは6に増加
  reporter: process.env.CI 
    ? [['github'], ['html', { outputFolder: 'playwright-report' }]] 
    : 'list',
  use: {
    baseURL: 'http://127.0.0.1:5100', // Firebase Emulator hosting
    trace: 'on-first-retry',
    // ヘッドレスモード用の設定
    headless: true, // ヘッドレスモードで実行
    video: 'retain-on-failure', // 失敗時にビデオを保存
    screenshot: 'only-on-failure', // 失敗時にスクリーンショットを保存
    actionTimeout: 5000, // アクションタイムアウトを5秒に設定（通常テスト用）
    navigationTimeout: 10000 // ナビゲーションタイムアウトを10秒に設定
  },
  projects: [
    {
      name: 'chromium',
      testMatch: '**/!(cloud_function_firestore).test.ts', // Functionsテスト以外
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'chromium-functions',
      testMatch: '**/cloud_function_firestore.test.ts', // Functionsテストのみ
      use: { 
        ...devices['Desktop Chrome'],
        actionTimeout: 90 * 1000, // Cloud Functions用のタイムアウトを90秒に短縮
        navigationTimeout: 30 * 1000, // ナビゲーションタイムアウトを30秒に設定
      },
    },
  ],
  // Firebase Emulatorの起動と待機処理
  webServer: {
    command: 'cd ../firebase && pnpm run start',
    url: 'http://127.0.0.1:5100',
    reuseExistingServer: process.env.CI ? false : true,
    timeout: 120 * 1000,
    stdout: 'inherit',
    stderr: 'inherit',
    // Functionsエミュレーターも起動するまで待機
    ready: async () => {
      try {
        const response = await fetch('http://127.0.0.1:5101/umayomi-fbb2b/us-central1/scrapeJRARaceResult?year=2025&month=10&day=13', { 
          signal: AbortSignal.timeout(3000) 
        })
        // 200、400、500でもエンドポイントが存在することを意味する
        return response.status === 200 || response.status === 400 || response.status === 500
      } catch {
        return false
      }
    },
  }
})
