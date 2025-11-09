import { chromium } from 'playwright'
import { logger } from 'firebase-functions'
import * as path from 'path'
import * as fs from 'fs'

/**
 * Playwrightを使用してJRAサイトからHTMLを取得
 * 
 * Cloud BuildでpostinstallスクリプトによりPlaywrightブラウザがインストールされる
 */
export async function fetchJRAHtmlWithPlaywright(url: string): Promise<string> {
  let browser: any = null
  
  try {
    logger.info('Launching Chromium browser', { 
      url,
      cwd: process.cwd()
    })
    
    // Playwrightブラウザのパスを設定（必須）
    if (!process.env.PLAYWRIGHT_BROWSERS_PATH) throw new Error(
        'PLAYWRIGHT_BROWSERS_PATH環境変数が設定されていません。' +
        'postinstallスクリプトでPlaywrightブラウザがインストールされているか確認してください。'
      )
    
    
    // ブラウザの実行ファイルパスを動的に検出
    const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH
    let executablePath: string | undefined
    
    // browsersPathディレクトリ内のchromium_headless_shell-*ディレクトリを検索
    if (fs.existsSync(browsersPath)) {
      const entries = fs.readdirSync(browsersPath)
      const chromiumDir = entries.find(entry => entry.startsWith('chromium_headless_shell-'))
      
      if (chromiumDir) {
        const candidatePath = path.join(browsersPath, chromiumDir, 'chrome-linux', 'headless_shell')
        if (fs.existsSync(candidatePath)) executablePath = candidatePath
        
      }
    }
    
    logger.info('Playwrightブラウザの設定', {
      browsersPath,
      executablePath,
      executableExists: executablePath ? fs.existsSync(executablePath) : false,
      cwd: process.cwd()
    })
    
    // executablePathが見つかった場合は明示的に指定、見つからなかった場合はPlaywrightに自動検出を任せる
    const launchOptions: any = {
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    }
    
    if (executablePath) launchOptions.executablePath = executablePath
    
    
    browser = await chromium.launch(launchOptions)
    
    logger.info('Browser launched successfully')
    
    const page = await browser.newPage()
    
    await page.setExtraHTTPHeaders({
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    logger.info('Navigating to URL', { url })
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 })
    await page.waitForTimeout(2000)
    
    const html = await page.content()
    
    logger.info('HTML fetched with Playwright', { 
      url, 
      htmlLength: html.length 
    })
    
    return html
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error'
    const errorStack = error instanceof Error ? error.stack : undefined
    
    logger.error('Failed to fetch HTML with Playwright', { 
      url, 
      error: errorMessage,
      stack: errorStack,
      errorType: error?.constructor?.name
    })
    
    // Playwrightのブラウザインストールエラーの場合、より詳細なメッセージを返す
    if (errorMessage.includes('Executable doesn\'t exist') || 
        errorMessage.includes('Browser has not been found') ||
        errorMessage.includes('chromium') ||
        errorMessage.includes('executable')) throw new Error(
        `Playwrightブラウザがインストールされていません: ${errorMessage}. ` +
        `デプロイ時に 'playwright install chromium' が実行されているか確認してください。`
      )
    
    
    throw new Error(`HTML取得に失敗しました: ${errorMessage}`)
  } finally {
    if (browser) 
      try {
        await browser.close()
      } catch (closeError) {
        logger.warn('Failed to close browser', { error: closeError })
      }
    
  }
}
