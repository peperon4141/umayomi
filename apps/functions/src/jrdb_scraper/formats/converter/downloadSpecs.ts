import * as fs from 'fs'
import * as path from 'path'
import * as iconv from 'iconv-lite'
import { downloadFileAsBuffer } from '../../downloader'
import { getAllDataTypes, getSpecificationUrl } from '../../entities/jrdb'

// ディレクトリが存在しない場合は作成
const baseDir = process.cwd().includes('apps/functions') 
  ? process.cwd() 
  : path.join(process.cwd(), 'apps/functions')

const specsDir = path.join(baseDir, 'src/jrdb_scraper/formats/specs')
if (!fs.existsSync(specsDir)) fs.mkdirSync(specsDir, { recursive: true })

async function downloadAllSpecs() {
  const dataTypes = getAllDataTypes()
  console.log(`仕様書を${dataTypes.length}件ダウンロードします...`)
  
  for (const dataType of dataTypes) {
    const url = getSpecificationUrl(dataType)
    
    const fileName = path.basename(url)
    const filePath = path.join(specsDir, fileName)
    
    try {
      console.log(`ダウンロード中: ${dataType} (${fileName}) - ${url}`)
      const buffer = await downloadFileAsBuffer(url)
      const utf8Text = iconv.decode(buffer, 'shift_jis')
      fs.writeFileSync(filePath, utf8Text, 'utf8')
      console.log(`✓ 保存完了: ${fileName}`)
    } catch (error) {
      console.error(`✗ ダウンロード失敗: ${dataType} (${fileName}) - ${error instanceof Error ? error.message : String(error)}`)
    }
  }
  
  console.log('すべての仕様書のダウンロードが完了しました。')
}

if (require.main === module) 
  downloadAllSpecs()
    .then(() => {
      process.exit(0)
    })
    .catch((error) => {
      console.error('エラー:', error)
      process.exit(1)
    })


