import { logger } from 'firebase-functions'

/**
 * 月のカレンダーページから開催日リンクを取得
 */
export async function getRaceDayLinks(page: any, monthUrl: string) {
  try {
    logger.info('Accessing calendar page', { url: monthUrl })
    
    await page.goto(monthUrl, { waitUntil: 'networkidle' })
    
    // ページのHTML構造をデバッグ用にログ出力
    const pageTitle = await page.title()
    const pageContent = await page.content()
    logger.info('Page loaded', { 
      title: pageTitle,
      contentLength: pageContent.length,
      url: monthUrl
    })
    
    // すべてのリンクを取得してデバッグ
    const allLinks = await page.$$eval('a', (links: any[]) => 
      links.map((link: any) => ({
        href: link.getAttribute('href'),
        text: link.textContent?.trim() || ''
      })).filter((link: any) => link.href && link.text)
    )
    logger.info('All links found', { 
      count: allLinks.length,
      links: allLinks.slice(0, 10) // 最初の10個だけ表示
    })
    
    // 開催日程ページから個別開催日のリンクを取得
    const raceDayLinks = await page.$$eval('a[href*="/calendar2025/2025/10/"]', (links: any[]) => 
      links.map((link: any) => ({
        href: link.getAttribute('href'),
        text: link.textContent?.trim() || ''
      })).filter((link: any) => link.href && link.text)
    )

    // もし2025年のリンクが見つからない場合は、2024年のリンクも探す
    if (raceDayLinks.length === 0) {
      const raceDayLinks2024 = await page.$$eval('a[href*="/calendar2024/2024/10/"]', (links: any[]) => 
        links.map((link: any) => ({
          href: link.getAttribute('href'),
          text: link.textContent?.trim() || ''
        })).filter((link: any) => link.href && link.text)
      )
      raceDayLinks.push(...raceDayLinks2024)
    }

    // それでも見つからない場合は、一般的な開催日リンクを探す
    if (raceDayLinks.length === 0) {
      const generalLinks = await page.$$eval('a[href*="/calendar"]', (links: any[]) => 
        links.map((link: any) => ({
          href: link.getAttribute('href'),
          text: link.textContent?.trim() || ''
        })).filter((link: any) => link.href && link.text && link.text.includes('10月'))
      )
      raceDayLinks.push(...generalLinks)
    }

    logger.info('Found race day links', { 
      count: raceDayLinks.length,
      links: raceDayLinks.map((link: any) => ({ href: link.href, text: link.text }))
    })

    return raceDayLinks

  } catch (error) {
    logger.error('Error getting race day links', { 
      monthUrl, 
      error: error instanceof Error ? error.message : 'Unknown error' 
    })
    throw error
  }
}
