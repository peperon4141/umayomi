import { chromium } from 'playwright'
import { logger } from 'firebase-functions'

/**
 * Playwrightを使用してJRAサイトからHTMLを取得
 * 
 * Firebase Functions v2 (Gen2) では、Cloud Runベースのため
 * ブラウザバイナリはイメージに含まれるため、特別なパス設定は不要
 * ~/.cache/ms-playwright 以下に自動的にインストールされる
 */
export async function fetchJRAHtmlWithPlaywright(url: string): Promise<string> {
  let browser: any = null
  
  try {
    logger.info('Launching Chromium browser', { url })
    
    browser = await chromium.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    })
    
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
        errorMessage.includes('executable')) {
      throw new Error(
        `Playwrightブラウザがインストールされていません: ${errorMessage}. ` +
        `デプロイ時に 'playwright install chromium' が実行されているか確認してください。`
      )
    }
    
    throw new Error(`HTML取得に失敗しました: ${errorMessage}`)
  } finally {
    if (browser) {
      try {
        await browser.close()
      } catch (closeError) {
        logger.warn('Failed to close browser', { error: closeError })
      }
    }
  }
}
