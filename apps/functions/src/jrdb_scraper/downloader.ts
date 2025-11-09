import { logger } from 'firebase-functions'
import * as https from 'https'
import * as http from 'http'
import { config } from 'dotenv'

// 環境変数を読み込む
config()

/**
 * JRDBのURLからlzhファイルをダウンロード
 * 認証が必要な場合は環境変数から取得
 */
export async function downloadJRDBFile(url: string): Promise<Buffer> {
  const jrdbUsername = process.env.JRDB_USERNAME
  const jrdbPassword = process.env.JRDB_PASSWORD

  if (!jrdbUsername || !jrdbPassword) throw new Error('JRDB_USERNAME and JRDB_PASSWORD environment variables are required')

  logger.info('Downloading JRDB file', { url })
  
  const buffer = await downloadFileAsBuffer(url, {
    username: jrdbUsername,
    password: jrdbPassword
  })
  
  logger.info('JRDB file downloaded successfully', { 
    url,
    size: buffer.length 
  })
  
  return buffer
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
  // JRDB251102.lzh のような形式を想定（統合アーカイブファイル）
  // 注意: "JRDB"はデータ種別ではなく、複数のデータ種別を含む統合アーカイブのプレフィックス
  // 251102 -> 25年11月02日
  const match = fileName.match(/JRDB(\d{6})\.lzh/)
  if (match) {
    const dateStr = match[1]
    // 最初の2桁が年（西暦の下2桁）、次の2桁が月、最後の2桁が日
    const year = parseInt('20' + dateStr.substring(0, 2))
    const month = parseInt(dateStr.substring(2, 4))
    const day = parseInt(dateStr.substring(4, 6))
    return { dataType: null, year, month, day }
  }
  return { dataType: null }
}

/**
 * URLからファイルをダウンロードしてBufferとして返す
 * リダイレクトにも対応
 * @param url - ダウンロードするURL
 * @param options - オプション（認証情報など）
 */
export async function downloadFileAsBuffer(
  url: string,
  options?: { username?: string; password?: string }
): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url)
    const client = urlObj.protocol === 'https:' ? https : http
    
    const requestOptions: http.RequestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0'
      }
    }
    
    if (options?.username && options?.password) {
      const auth = Buffer.from(`${options.username}:${options.password}`).toString('base64')
      requestOptions.headers = {
        ...requestOptions.headers,
        'Authorization': `Basic ${auth}`
      }
    }
    
    const req = client.request(requestOptions, (response) => {
      if (response.statusCode === 301 || response.statusCode === 302) {
        const redirectUrl = response.headers.location
        if (!redirectUrl) {
          reject(new Error(`リダイレクト先が見つかりません: ${url}`))
          return
        }
        downloadFileAsBuffer(redirectUrl, options).then(resolve).catch(reject)
        return
      }
      
      if (response.statusCode !== 200) {
        reject(new Error(`HTTP ${response.statusCode}: ${url}`))
        return
      }
      
      const chunks: Buffer[] = []
      response.on('data', (chunk: Buffer) => {
        chunks.push(chunk)
      })
      
      response.on('end', () => {
        resolve(Buffer.concat(chunks))
      })
      
      response.on('error', reject)
    })
    
    req.on('error', reject)
    req.end()
  })
}

