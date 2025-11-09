import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'
import { execSync } from 'child_process'
import { JRDBDataType } from './entities/jrdb'
import { parseJRDBFileName } from './parsers/jrdbParser'

/**
 * lzhファイルを展開してすべてのテキストファイルを取得
 * lhaコマンドを使用して解凍
 * エミュレータ環境では、事前にlhaコマンドをインストールする必要があります（macOS: brew install lhasa）
 * @returns 展開されたすべての.txtファイルのバッファとファイル名
 */
export async function extractLzhFile(lzhBuffer: Buffer): Promise<Array<{ buffer: Buffer; fileName: string }>> {
  // 一時ディレクトリを作成
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'lzh-extract-'))
  const tempLzhPath = path.join(tempDir, 'input.lzh')
  const extractDir = path.join(tempDir, 'extract')
  
  try {
    // LZHファイルを一時ファイルに書き込む
    fs.mkdirSync(extractDir, { recursive: true })
    fs.writeFileSync(tempLzhPath, lzhBuffer)
    
    // lhaコマンドのパスを取得
    let lhaCommand = 'lha'
    try {
      // まずwhichコマンドでパスを確認
      const whichResult = execSync('which lha', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim()
      if (whichResult) lhaCommand = whichResult
      
    } catch {
      // whichコマンドが失敗した場合、直接lhaコマンドを試す
    }
    
    // lhaコマンドで解凍（lha x <ファイル> でカレントディレクトリに解凍される）
    execSync(`cd "${extractDir}" && "${lhaCommand}" x "${tempLzhPath}"`, {encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] })
    
    // 解凍されたファイルを探す
    const extractedFiles = fs.readdirSync(extractDir)
    if (extractedFiles.length === 0) throw new Error('解凍されたファイルが見つかりません')
    
    // .txtファイルのみを処理
    const txtFiles = extractedFiles.filter(f => f.endsWith('.txt'))
    if (txtFiles.length === 0) throw new Error('解凍された.txtファイルが見つかりません')
    
    // すべての.txtファイルを返す
    return txtFiles.map(fileName => {
      const filePath = path.join(extractDir, fileName)
      return { buffer: fs.readFileSync(filePath), fileName }
    })
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    
    if (errorMessage.includes('lha') || errorMessage.includes('command not found')) {
      const installCmd = process.platform === 'darwin' ? 'brew install lhasa' : 'apt-get install -y lhasa'
      throw new Error(`lhaコマンドが見つかりません。事前にインストールしてください: ${installCmd}`)
    }
    
    throw new Error(`LZH解凍に失敗しました: ${errorMessage}`)
  } finally {
    // 一時ディレクトリを削除
    try {
      fs.rmSync(tempDir, { recursive: true, force: true })
    } catch {
      // クリーンアップ失敗は無視
    }
  }
}

/**
 * 展開後のファイル名からデータ種別を推測
 * @param fileName - 展開後のファイル名（例: "KYG251102.txt"）
 * @returns データ種別、見つからない場合はnull
 */
export function extractDataTypeFromFileName(fileName: string): JRDBDataType | null {
  try {
    const parsed = parseJRDBFileName(fileName)
    if (!parsed) return null
    
    return parsed.dataType
  } catch {
    // ファイル名が.txtで終わる場合は、拡張子を除いて解析を試みる
    if (fileName.endsWith('.txt')) {
      const nameWithoutExt = fileName.replace(/\.txt$/, '')
      const parsed = parseJRDBFileName(nameWithoutExt + '.lzh')
      if (parsed) return parsed.dataType
    }
    return null
  }
}

