import { logger } from 'firebase-functions'
import * as cheerio from 'cheerio'
import * as https from 'https'
import * as http from 'http'

/**
 * JRDBメンバーページからファイルURLを取得
 * @param dataType - データ種別（例: 'KYI', 'KYH', 'KYG', 'KKA'）
 * @param date - 日付（YYMMDD形式、例: "251102"）
 * @returns 実際のファイルダウンロードURL
 */
export async function getJRDBFileUrlFromMemberPage(dataType: string, date: string): Promise<string | null> {
  // データ種別コードを大文字小文字混在形式に変換（例: KYI -> Kyi, KKA -> Kka）
  const dataTypeCode = dataType.charAt(0).toUpperCase() + dataType.substring(1).toLowerCase()
  const memberPageUrl = `https://jrdb.com/member/data/${dataTypeCode}/index.html`
  
  logger.info('JRDBメンバーページからファイルURLを取得', { 
    dataType, 
    date, 
    memberPageUrl 
  })

  try {
    // メンバーページのHTMLを取得（Basic認証が必要）
    const html = await fetchJRDBMemberPageHtml(memberPageUrl)
    
    // HTMLを解析してファイルリンクを取得
    const fileUrl = parseFileUrlFromMemberPage(html, dataType, date)
    
    if (!fileUrl) {
      logger.warn('メンバーページからファイルURLが見つかりませんでした', {
        dataType,
        date,
        memberPageUrl
      })
      return null
    }
    
    logger.info('メンバーページからファイルURLを取得しました', {
      dataType,
      date,
      fileUrl
    })
    
    return fileUrl
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    logger.error('メンバーページからのファイルURL取得に失敗', {
      dataType,
      date,
      memberPageUrl,
      error: errorMessage
    })
    throw error
  }
}

/**
 * JRDBメンバーページのHTMLを取得（Basic認証付き）
 */
function fetchJRDBMemberPageHtml(url: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const jrdbUsername = process.env.JRDB_USERNAME
    const jrdbPassword = process.env.JRDB_PASSWORD

    if (!jrdbUsername || !jrdbPassword) {
      reject(new Error('JRDB_USERNAME and JRDB_PASSWORD environment variables are required'))
      return
    }

    // Basic認証ヘッダーを作成
    const auth = Buffer.from(`${jrdbUsername}:${jrdbPassword}`).toString('base64')
    
    const urlObj = new URL(url)
    const client = urlObj.protocol === 'https:' ? https : http
    
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: 'GET',
      headers: {
        'Authorization': `Basic ${auth}`,
        'User-Agent': 'Mozilla/5.0'
      }
    }

    logger.info('JRDBメンバーページを取得', { url: urlObj.href })

    const req = client.request(options, (res) => {
      if (res.statusCode && (res.statusCode < 200 || res.statusCode >= 300)) {
        reject(new Error(`Failed to fetch member page: HTTP ${res.statusCode}`))
        return
      }

      const chunks: Buffer[] = []
      res.on('data', (chunk: Buffer) => {
        chunks.push(chunk)
      })
      res.on('end', () => {
        const html = Buffer.concat(chunks).toString('utf-8')
        logger.info('JRDBメンバーページ取得完了', { 
          url: urlObj.href,
          htmlLength: html.length 
        })
        resolve(html)
      })
    })

    req.on('error', (error) => {
      logger.error('Error fetching JRDB member page', { error: error.message, url: urlObj.href })
      reject(error)
    })

    req.end()
  })
}

/**
 * メンバーページのHTMLからファイルURLを解析
 * @param html - メンバーページのHTML
 * @param dataType - データ種別（例: 'KYI'）
 * @param date - 日付（YYMMDD形式、例: "251102"）
 * @returns ファイルURL（見つからない場合はnull）
 */
function parseFileUrlFromMemberPage(html: string, dataType: string, date: string): string | null {
  const $ = cheerio.load(html)
  const fileName = `${dataType}${date}.lzh`
  
  // ファイル名に一致するリンクを探す
  const links = $('a[href$=".lzh"]')
  
  for (let i = 0; i < links.length; i++) {
    const link = links.eq(i)
    const href = link.attr('href')
    if (href && href.includes(fileName)) {
      // 相対URLの場合は絶対URLに変換
      if (href.startsWith('http')) {
        return href
      }
      // 相対URLの場合、メンバーページのベースURLから構築
      const dataTypeCode = dataType.charAt(0).toUpperCase() + dataType.substring(1).toLowerCase()
      return `https://jrdb.com/member/data/${dataTypeCode}/${href}`
    }
  }
  
  return null
}

