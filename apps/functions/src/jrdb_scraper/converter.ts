import * as fs from 'fs'
import * as path from 'path'
import archiver from 'archiver'
import { dump } from 'npyjs'
import { JRDBDataType } from './entities/jrdb'
import { parseJRDBDataFromBuffer } from './parsers/jrdbParser'
import { extractLzhFile, extractDataTypeFromFileName } from './lzhExtractor'

/**
 * データをJSON形式に変換（1ファイルto1ファイル）
 * すべてのレコードを1つのJSONファイルに保存
 */
export async function convertToJson(
  records: Record<string, unknown>[],
  outputFilePath: string
): Promise<void> {
  if (records.length === 0) throw new Error('cannot write json file with zero rows')

  // 出力ディレクトリを作成
  const outputDir = path.dirname(outputFilePath)
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true })

  // すべてのレコードを1つのJSONファイルとして保存
  const jsonData = JSON.stringify(records, null, 2)
  fs.writeFileSync(outputFilePath, jsonData, 'utf-8')
}

/**
 * LZHファイルからデータを抽出・パースする共通処理
 */
async function extractAndParseLzhData(
  lzhBuffer: Buffer,
  dataType: JRDBDataType | string | null
): Promise<{ actualDataType: JRDBDataType | string; records: Record<string, unknown>[] }> {
  const extractedFiles = await extractLzhFile(lzhBuffer)
  if (extractedFiles.length === 0) throw new Error('展開されたファイルが見つかりません')
  
  const { buffer: extractedBuffer, fileName: extractedFileName } = extractedFiles[0]
  
  let actualDataType: JRDBDataType | string
  if (dataType !== null) 
    actualDataType = dataType
   else {
    const extractedDataType = extractDataTypeFromFileName(extractedFileName)
    if (!extractedDataType) throw new Error(`データ種別の推測に失敗しました。ファイル名: ${extractedFileName}`)
    actualDataType = extractedDataType
  }
  
  const records = parseJRDBDataFromBuffer(extractedBuffer, actualDataType)
  if (records.length === 0) throw new Error('パースされたレコードが0件です')
  
  return { actualDataType, records }
}

/**
 * lzhファイルからJSONファイルへの変換処理（1ファイルto1ファイル）
 */
export async function convertLzhToJson(
  lzhBuffer: Buffer,
  dataType: JRDBDataType | string | null,
  year: number,
  outputFilePath: string
): Promise<{ actualDataType: JRDBDataType | string; records: Record<string, unknown>[] }> {
  const { actualDataType, records } = await extractAndParseLzhData(lzhBuffer, dataType)
  await convertToJson(records, outputFilePath)
  return { actualDataType, records }
}

/**
 * データをNPZ形式に変換（各フィールドごとのNPYファイルをZIP圧縮して1つのNPZファイルに）
 * @param records - レコード配列
 * @param outputFilePath - 出力NPZファイルパス
 */
export async function convertToNpz(
  records: Record<string, unknown>[],
  outputFilePath: string
): Promise<void> {
  if (records.length === 0) throw new Error('cannot write npz file with zero rows')

  // 出力ディレクトリを作成
  const outputDir = path.dirname(outputFilePath)
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true })

  // 一時ディレクトリを作成
  const tempDir = path.join(outputDir, `temp_${Date.now()}`)
  if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true })

  try {
    // すべてのフィールド名を取得
    const allFields = new Set<string>()
    for (const record of records) 
      for (const field of Object.keys(record)) allFields.add(field)
    

    // 各フィールドごとにNPYファイルを作成
    for (const field of allFields) {
      const values: (string | number)[] = []
      for (const record of records) {
        const value = record[field]
        // 数値、文字列、nullをそのまま保存
        // 数値の場合は数値として、それ以外は文字列として保存
        if (value === null || value === undefined) values.push('')
        else if (typeof value === 'number') values.push(value)
        else if (typeof value === 'string') values.push(value)
        else values.push(String(value))
      }

      // NPYファイルとして保存
      const npyFilePath = path.join(tempDir, `${field}.npy`)
      const npyArrayBuffer = dump(values, [values.length])
      const npyBuffer = Buffer.from(npyArrayBuffer)
      fs.writeFileSync(npyFilePath, npyBuffer)
    }

    // すべてのNPYファイルをZIP圧縮してNPZファイルを作成
    return new Promise((resolve, reject) => {
      const output = fs.createWriteStream(outputFilePath)
      const archive = archiver('zip', { zlib: { level: 9 } })

      output.on('close', () => {
        // ZIPファイルの作成が完了したら一時ディレクトリを削除
        if (fs.existsSync(tempDir)) fs.rmSync(tempDir, { recursive: true, force: true })
        resolve()
      })

      archive.on('error', (err: Error) => {
        // エラー時も一時ディレクトリを削除
        if (fs.existsSync(tempDir)) fs.rmSync(tempDir, { recursive: true, force: true })
        reject(err)
      })

      archive.pipe(output)

      // 一時ディレクトリ内のすべてのNPYファイルをアーカイブに追加
      const files = fs.readdirSync(tempDir).filter(f => f.endsWith('.npy'))
      if (files.length === 0) {
        // NPYファイルが存在しない場合はエラー
        if (fs.existsSync(tempDir)) fs.rmSync(tempDir, { recursive: true, force: true })
        reject(new Error('NPYファイルが作成されていません'))
        return
      }
      
      for (const file of files) {
        const filePath = path.join(tempDir, file)
        archive.file(filePath, { name: file })
      }

      archive.finalize()
    })
  } catch (error) {
    // エラー時は一時ディレクトリを削除
    if (fs.existsSync(tempDir)) fs.rmSync(tempDir, { recursive: true, force: true })
    throw error
  }
}

/**
 * lzhファイルからNPZファイルへの変換処理
 * 各フィールドごとのNPYファイルをZIP圧縮して1つのNPZファイルに
 */
export async function convertLzhToNpz(
  lzhBuffer: Buffer,
  dataType: JRDBDataType | string | null,
  year: number,
  outputFilePath: string
): Promise<{ actualDataType: JRDBDataType | string; records: Record<string, unknown>[] }> {
  const { actualDataType, records } = await extractAndParseLzhData(lzhBuffer, dataType)
  await convertToNpz(records, outputFilePath)
  return { actualDataType, records }
}


