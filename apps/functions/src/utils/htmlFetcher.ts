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
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  })
  
  try {
    const page = await browser.newPage()
    
    await page.setExtraHTTPHeaders({
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    await page.goto(url, { waitUntil: 'networkidle' })
    await page.waitForTimeout(2000)
    
    const html = await page.content()
    
    logger.info('HTML fetched with Playwright', { 
      url, 
      htmlLength: html.length 
    })
    
    return html
    
  } finally {
    await browser.close()
  }
}
