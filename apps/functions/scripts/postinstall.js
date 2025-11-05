#!/usr/bin/env node

const { execSync } = require('child_process')
const path = require('path')

// Playwright Chromiumのインストール
const browsersPath = path.join(__dirname, '..', 'node_modules', 'playwright', '.local-browsers')
process.env.PLAYWRIGHT_BROWSERS_PATH = browsersPath
execSync('npx playwright install chromium', {
  stdio: 'inherit',
  cwd: path.join(__dirname, '..'),
  env: { ...process.env, PLAYWRIGHT_BROWSERS_PATH: browsersPath }
})

// lhaコマンドのインストール（Cloud Build環境でのみ）
const isCloudBuild = process.env.CLOUD_BUILD === 'true'

if (isCloudBuild) {
  try {
    execSync('apt-get update', { stdio: 'ignore', timeout: 30000 })
    execSync('apt-get install -y lhasa', { stdio: 'inherit', timeout: 60000 })
  } catch {
    // エラーは無視
  }
}

