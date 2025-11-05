import { logger } from 'firebase-functions'
import * as https from 'https'
import * as http from 'http'

/**
 * JRDBのURLからlzhファイルをダウンロード
 * 認証が必要な場合は環境変数から取得
 */
export async function downloadJRDBFile(url: string): Promise<Buffer> {
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

    logger.info('Downloading JRDB file', { url: urlObj.href })

    const req = client.request(options, (res) => {
      if (res.statusCode && (res.statusCode < 200 || res.statusCode >= 300)) {
        reject(new Error(`Failed to download file: HTTP ${res.statusCode}`))
        return
      }

      const chunks: Buffer[] = []
      res.on('data', (chunk: Buffer) => {
        chunks.push(chunk)
      })
      res.on('end', () => {
        const buffer = Buffer.concat(chunks)
        logger.info('JRDB file downloaded successfully', { 
          url: urlObj.href,
          size: buffer.length 
        })
        resolve(buffer)
      })
    })

    req.on('error', (error) => {
      logger.error('Error downloading JRDB file', { error: error.message, url: urlObj.href })
      reject(error)
    })

    req.end()
  })
}

/**
 * URLからファイル名を抽出
 */
export function extractFileNameFromUrl(url: string): string {
  const urlObj = new URL(url)
  const pathname = urlObj.pathname
  const fileName = pathname.split('/').pop() || 'file.lzh'
  return fileName
}

/**
 * URLからファイル名（拡張子を除く）を抽出
 * 例: "https://jrdb.com/member/data/Jrdb/JRDB251102.lzh" -> "JRDB251102"
 */
export function extractBaseFileNameFromUrl(url: string): string {
  const fileName = extractFileNameFromUrl(url)
  // 拡張子を除く
  const baseName = fileName.replace(/\.(lzh|LZH)$/, '')
  return baseName
}

/**
 * ファイル名からデータ種別と年を推測
 * 例: JRDB251102.lzh -> データ種別と年を推測
 */
export function parseFileName(fileName: string): { dataType: string | null; year?: number; month?: number; day?: number } {
  // JRDB251102.lzh のような形式を想定
  // 251102 -> 25年11月02日 または データ種別の可能性
  const match = fileName.match(/JRDB(\d{6})\.lzh/)
  if (match) {
    const dateStr = match[1]
    // 最初の2桁が年（西暦の下2桁）、次の2桁が月、最後の2桁が日またはデータ種別
    const year = parseInt('20' + dateStr.substring(0, 2))
    const month = parseInt(dateStr.substring(2, 4))
    const day = parseInt(dateStr.substring(4, 6))
    return { dataType: null, year, month, day }
  }
  return { dataType: null }
}

