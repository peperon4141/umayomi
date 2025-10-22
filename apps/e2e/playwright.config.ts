import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  timeout: 15 * 1000, // グローバルタイムアウトを15秒に設定
  testDir: './tests',
  fullyParallel: true, // 並列実行を有効化
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0, // リトライ回数を削減
  workers: process.env.CI ? 2 : 4, // ワーカー数を増加
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: 'http://127.0.0.1:5100', // Firebase Emulator Hosting
    trace: 'on-first-retry',
    // ヘッドレスモード用の設定
    headless: true, // ヘッドレスモードで実行
    video: 'retain-on-failure', // 失敗時にビデオを保存
    screenshot: 'only-on-failure', // 失敗時にスクリーンショットを保存
    actionTimeout: 5000, // アクションタイムアウトを5秒に設定
    navigationTimeout: 10000 // ナビゲーションタイムアウトを10秒に設定
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // CI環境ではwebServerを無効化（Firebase Emulatorが既に起動しているため）
  webServer: process.env.CI ? undefined : {
    command: 'cd ../hosting && pnpm dev:serve',
    url: 'http://127.0.0.1:3100',
    reuseExistingServer: false,
  },
})
