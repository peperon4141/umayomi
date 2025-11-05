import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  timeout: 30 * 1000, // グローバルタイムアウト
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 4,
  reporter: process.env.CI 
    ? [['github'], ['html', { outputFolder: 'playwright-report' }]] 
    : 'list',
  use: {
    baseURL: 'http://127.0.0.1:5100',
    trace: 'on-first-retry',
    headless: true,
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
    actionTimeout: 5000, // アクションタイムアウト
    navigationTimeout: 10000 // ナビゲーションタイムアウト
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
    command: 'cd ../.. && pnpm -F firebase run stop && pnpm -F functions run build && cd apps/firebase && pnpm run start',
    url: 'http://127.0.0.1:5100',
    reuseExistingServer: process.env.CI ? false : true,
    timeout: 120 * 1000,
    stdout: 'pipe',
    stderr: 'pipe',
  }
})
