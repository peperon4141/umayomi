import * as fs from 'fs'
import * as path from 'path'
import { downloadJRDBFile } from '../../downloader'
import { getAllDataTypes } from '../../entities/jrdb'
import { generateJRDBDataFileUrl } from '../../raceKeyGenerator'

/**
 * モック用のLZHファイルをダウンロードするスクリプト
 */
async function main() {
  const baseDir = process.cwd().includes('apps/functions') 
    ? process.cwd() 
    : path.join(process.cwd(), 'apps/functions')
  
  const outputDir = path.join(baseDir, 'tests/mock/jrdb/raw_lzh')
  
  // 出力ディレクトリを作成
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true })
  
  // 2025年11月2日のデータをダウンロード
  const targetDate = new Date(2025, 10, 2) // 11月は10（0-indexed）
  
  console.log(`ダウンロード開始: ${targetDate.toISOString().split('T')[0]}`)
  
  const dataTypes = getAllDataTypes()
  
  for (const dataType of dataTypes) 
    try {
      // URLを生成
      const url = generateJRDBDataFileUrl(dataType, targetDate)
      
      // ファイル名を抽出
      const fileName = url.split('/').pop() || `${dataType}251102.lzh`
      
      // ダウンロード
      console.log(`ダウンロード中: ${dataType} (${fileName})`)
      const buffer = await downloadJRDBFile(url)
      
      // 保存
      const outputPath = path.join(outputDir, fileName)
      fs.writeFileSync(outputPath, buffer)
      
      console.log(`✓ 保存完了: ${fileName} (${buffer.length} bytes)`)
    } catch (error) {
      console.error(`✗ エラー: ${dataType}`, error instanceof Error ? error.message : String(error))
    }
  
  
  console.log('ダウンロード完了')
  process.exit(0)
}

if (require.main === module) 
  main().catch((error) => {
    console.error('エラー:', error)
    process.exit(1)
  })


