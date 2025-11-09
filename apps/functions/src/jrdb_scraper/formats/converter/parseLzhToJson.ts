import * as fs from 'fs'
import * as path from 'path'
import { extractLzhFile } from '../../lzhExtractor'
import { parseJRDBDataFromBuffer, parseJRDBFileName } from '../../parsers/jrdbParser'

/**
 * LZHファイルをパースしてJSONとして保存するスクリプト
 */
async function main() {
  const baseDir = process.cwd().includes('apps/functions') 
    ? process.cwd() 
    : path.join(process.cwd(), 'apps/functions')
  
  const mockLzhDir = path.join(baseDir, 'tests/mock/jrdb/raw_lzh')
  const outputDir = path.join(baseDir, 'tests/mock/jrdb/json_results')
  
  // 出力ディレクトリを作成
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true })
  
  if (!fs.existsSync(mockLzhDir)) {
    console.log('LZHファイルのディレクトリが見つかりません。')
    return
  }
  
  // LZHファイルを検索
  const lzhFiles = fs.readdirSync(mockLzhDir)
    .filter(file => file.endsWith('.lzh'))
    .map(file => path.join(mockLzhDir, file))
  
  if (lzhFiles.length === 0) {
    console.log('パース対象のLZHファイルが見つかりません。')
    return
  }
  
  console.log(`LZHファイルを${lzhFiles.length}件パースします...`)
  
  for (const lzhFile of lzhFiles) {
    const fileName = path.basename(lzhFile)
    
    try {
      console.log(`パース中: ${fileName}`)
      
      // LZHファイルを読み込み
      const buffer = fs.readFileSync(lzhFile)
      
      // LZHファイルを解凍
      const extractedFiles = await extractLzhFile(buffer)
      
      // 各ファイルを処理
      for (const { buffer: extractedBuffer, fileName: extractedFileName } of extractedFiles) {
        // 展開後のファイル名からデータ型と日付を解析
        const parsed = parseJRDBFileName(extractedFileName)
        
        if (!parsed || !parsed.dataType) {
          console.error(`✗ データ種別の取得に失敗: ${extractedFileName}`)
          continue
        }
        
        const dataType = parsed.dataType
        
        // パース
        const records = parseJRDBDataFromBuffer(extractedBuffer, dataType)
        
        // JSONとして保存（展開後のファイル名を使用）
        const jsonFileName = extractedFileName.replace(/\.txt$/i, '.json')
        const jsonFilePath = path.join(outputDir, jsonFileName)
        fs.writeFileSync(jsonFilePath, JSON.stringify(records, null, 2), 'utf-8')
        
        console.log(`✓ JSON保存完了: ${jsonFileName} (${records.length}件のレコード)`)
      }
    } catch (error) {
      console.error(`✗ パース失敗: ${fileName} - ${error instanceof Error ? error.message : String(error)}`)
    }
  }
  
  console.log('すべてのLZHファイルのパースが完了しました。')
}

if (require.main === module) main()

