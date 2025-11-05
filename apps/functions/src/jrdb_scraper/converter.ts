import { logger } from 'firebase-functions'
import * as iconv from 'iconv-lite'
import * as fs from 'fs'
import * as path from 'path'
import * as os from 'os'
import { execSync } from 'child_process'
// @ts-expect-error - parquetjsには型定義がない
import { ParquetWriter, ParquetSchema } from 'parquetjs'
import { JRDBDataType } from '../../../shared/src/jrdb'
import { parseJRDBDataFromBuffer } from './parsers/jrdbParser'

/**
 * lzhファイルを展開してテキストデータを取得
 * lhaコマンドを使用して解凍
 * エミュレータ環境では、事前にlhaコマンドをインストールする必要があります（macOS: brew install lhasa）
 */
export async function extractLzhFile(lzhBuffer: Buffer): Promise<Buffer> {
  logger.info('Extracting LZH file', { size: lzhBuffer.length })
  
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
      if (whichResult) {
        lhaCommand = whichResult
      }
    } catch (err) {
      // whichコマンドが失敗した場合、直接lhaコマンドを試す
      logger.info('which lha failed, trying direct lha command', { error: err instanceof Error ? err.message : String(err) })
    }
    
    logger.info('Using lha command', { lhaCommand })
    
    // lhaコマンドで解凍（lha x <ファイル> でカレントディレクトリに解凍される）
    execSync(`cd "${extractDir}" && "${lhaCommand}" x "${tempLzhPath}"`, {
      stdio: ['ignore', 'pipe', 'pipe'],
      encoding: 'utf8'
    })
    
    // 解凍されたファイルを探す
    const extractedFiles = fs.readdirSync(extractDir)
    if (extractedFiles.length === 0) {
      throw new Error('解凍されたファイルが見つかりません')
    }
    
    // 最初のファイルを読み込む（通常は1つのファイルのみ）
    const extractedFilePath = path.join(extractDir, extractedFiles[0])
    const extractedBuffer = fs.readFileSync(extractedFilePath)
    
    logger.info('LZH file extracted successfully', { 
      originalSize: lzhBuffer.length,
      decompressedSize: extractedBuffer.length,
      extractedFileName: extractedFiles[0]
    })
    
    return extractedBuffer
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    
    // lhaコマンドが見つからない場合のエラーメッセージを改善
    if (errorMessage.includes('lha') || errorMessage.includes('command not found')) {
      const isEmulator = process.env.FUNCTIONS_EMULATOR === 'true' || process.env.NODE_ENV === 'development'
      const installCmd = process.platform === 'darwin' ? 'brew install lhasa' : 'apt-get install -y lhasa'
      const errorMsg = `lhaコマンドが見つかりません。${isEmulator ? 'エミュレータ環境では' : ''}事前にインストールしてください: ${installCmd}`
      logger.error('lha command not found', { 
        error: errorMessage,
        isEmulator,
        platform: process.platform,
        installCommand: installCmd
      })
      throw new Error(errorMsg)
    }
    
    logger.error('Failed to extract LZH file', { 
      error: errorMessage,
      bufferSize: lzhBuffer.length,
      tempDir
    })
    throw new Error(`LZH解凍に失敗しました: ${errorMessage}`)
  } finally {
    // 一時ディレクトリを削除
    try {
      fs.rmSync(tempDir, { recursive: true, force: true })
    } catch (cleanupError) {
      logger.warn('Failed to cleanup temp directory', {
        tempDir,
        error: cleanupError instanceof Error ? cleanupError.message : String(cleanupError)
      })
    }
  }
}

/**
 * ShiftJISエンコーディングのテキストをUTF-8に変換
 */
export function convertShiftJISToUTF8(buffer: Buffer): string {
  return iconv.decode(buffer, 'shift_jis')
}

/**
 * 展開後のバッファからファイル名を抽出し、データ種別を推測
 * 例: "KYG251102.txt" -> "KY"
 */
export function extractDataTypeFromExtractedBuffer(buffer: Buffer): JRDBDataType | null {
  // JRDBデータ種別の有効な値のリスト
  const validDataTypes: JRDBDataType[] = [
    JRDBDataType.KY, JRDBDataType.KYI, JRDBDataType.KYH, JRDBDataType.KYG, JRDBDataType.KKA,
    JRDBDataType.UK, JRDBDataType.ZE, JRDBDataType.ZK, JRDBDataType.BA, JRDBDataType.OZ,
    JRDBDataType.OW, JRDBDataType.OU, JRDBDataType.OT, JRDBDataType.OV, JRDBDataType.JO,
    JRDBDataType.KK, JRDBDataType.TY, JRDBDataType.HJ, JRDBDataType.SE, JRDBDataType.SR,
    JRDBDataType.SK, JRDBDataType.KZ, JRDBDataType.KS, JRDBDataType.CZ, JRDBDataType.CS,
    JRDBDataType.MZ, JRDBDataType.MS
  ]
  
  try {
    // 最初の数KBをShiftJISとしてデコードしてファイル名を探す
    const previewBuffer = buffer.slice(0, Math.min(2000, buffer.length))
    const previewText = convertShiftJISToUTF8(previewBuffer)
    
    logger.info('Searching for data type in extracted buffer', {
      previewTextLength: previewText.length,
      firstChars: previewText.substring(0, 300)
    })
    
    // ファイル名パターンを探す（例: KYG251102.txt, UK251102.txt など）
    // JRDBのデータ種別コード（2-3文字）+ 日付 + .txt の形式
    // LZHヘッダー内のファイル名を探す
    const fileNameMatches = [
      previewText.match(/([A-Z]{2,3})\d{6}\.txt/i),  // 通常のパターン
      previewText.match(/KYG\d{6}\.txt/i),  // KYGの特殊パターン
      previewText.match(/UKG\d{6}\.txt/i),  // UKGの特殊パターン
    ].filter(m => m !== null)
    
    if (fileNameMatches.length > 0) {
      const match = fileNameMatches[0]
      if (match && match[1]) {
        const code = match[1].toUpperCase()
        logger.info('Extracted data type code from file name', { 
          code, 
          match: match[0],
          previewText: previewText.substring(0, 300) 
        })
        
        // コードがvalidDataTypesに存在するか確認（KYI, KYH, KYG, KKAなどの3文字コードも含む）
        let dataTypeCode: JRDBDataType | null = null
        
        // まず3文字コードを確認（KYI, KYH, KYG, KKAなど）
        const codeEnum = Object.values(JRDBDataType).find(v => v === code)
        if (codeEnum && validDataTypes.includes(codeEnum)) {
          dataTypeCode = codeEnum
        } else if (code.length >= 2) {
          // 2文字コードを確認（KY, UKなど）
          const twoCharCode = code.substring(0, 2)
          const twoCharCodeEnum = Object.values(JRDBDataType).find(v => v === twoCharCode)
          if (twoCharCodeEnum && validDataTypes.includes(twoCharCodeEnum)) {
            dataTypeCode = twoCharCodeEnum
          }
        }
        
        if (dataTypeCode) {
          logger.info('Data type determined from file name', { 
            originalCode: code,
            dataTypeCode,
            match: match[0]
          })
          return dataTypeCode
        }
      }
    }
    
    logger.warn('Could not extract data type from buffer', {
      previewText: previewText.substring(0, 500)
    })
    return null
  } catch (error) {
    logger.warn('Failed to extract data type from buffer', {
      error: error instanceof Error ? error.message : String(error)
    })
    return null
  }
}

/**
 * LZHヘッダーをスキップして実際のデータ部分を抽出
 * LZHファイルが展開されていない場合、ヘッダー部分をスキップする
 */
function skipLzhHeader(text: string): string {
  // LZHヘッダーのバイナリパターンを検出（"J\u0000-lh5"など）
  // ShiftJISとして解釈された場合、このパターンが含まれる可能性がある
  // eslint-disable-next-line no-control-regex
  const lzhHeaderPattern = /J\u0000-lh\d/
  const lzhHeaderMatch = text.match(lzhHeaderPattern)
  
  if (lzhHeaderMatch && lzhHeaderMatch.index !== undefined) {
    logger.info('LZHヘッダーのバイナリパターンを検出', {
      pattern: lzhHeaderMatch[0],
      index: lzhHeaderMatch.index,
      textPreview: text.substring(0, Math.min(500, text.length))
    })
    
    // LZHヘッダーの後、ファイル名パターンを探す
    const afterHeader = text.substring(lzhHeaderMatch.index + lzhHeaderMatch[0].length)
    const fileNamePattern = /([A-Z]{2,3})\d{6}\.txt/i
    const fileNameMatch = afterHeader.match(fileNamePattern)
    
    if (fileNameMatch && fileNameMatch.index !== undefined) {
      // ファイル名の後のデータ開始位置を探す
      const dataStartOffset = lzhHeaderMatch.index + lzhHeaderMatch[0].length + fileNameMatch.index + fileNameMatch[0].length
      
      // ファイル名の後の制御文字をスキップしてデータ開始位置を探す
      let actualDataStart = dataStartOffset
      let skippedChars = 0
      
      // 制御文字をスキップして、長いデータ行を探す
      while (actualDataStart < text.length && skippedChars < 1000) {
        const char = text[actualDataStart]
        const charCode = char.charCodeAt(0)
        
        // 制御文字（0x00-0x1f、0x1bなど）をスキップ
        if (charCode < 0x20 || charCode === 0x1b) {
          actualDataStart++
          skippedChars++
          continue
        }
        
        // 通常の文字が見つかったら、データ開始位置の候補
        // 改行文字を探して、行の長さを確認
        const nextLineEnd = text.indexOf('\n', actualDataStart)
        const nextCarriageReturn = text.indexOf('\r', actualDataStart)
        let lineEnd = -1
        if (nextLineEnd !== -1 && nextCarriageReturn !== -1) {
          lineEnd = Math.min(nextLineEnd, nextCarriageReturn)
        } else if (nextLineEnd !== -1) {
          lineEnd = nextLineEnd
        } else if (nextCarriageReturn !== -1) {
          lineEnd = nextCarriageReturn
        }
        
        const nextLine = lineEnd !== -1
          ? text.substring(actualDataStart, lineEnd)
          : text.substring(actualDataStart, Math.min(actualDataStart + 600, text.length))
        
        // 長い行（100文字以上）で、制御文字が少ない（5%以下）場合、データ開始位置
        // eslint-disable-next-line no-control-regex
        const controlCharCount = (nextLine.match(/[\u0000-\u001F\u001B]/g) || []).length
        const controlCharRatio = controlCharCount / nextLine.length
        if (nextLine.length >= 100 && controlCharRatio < 0.05) {
          const cleanedText = text.substring(actualDataStart)
          logger.info('LZHヘッダーをスキップしました（バイナリパターン検出）', {
            headerPattern: lzhHeaderMatch[0],
            fileNameMatch: fileNameMatch[0],
            dataStartOffset: actualDataStart,
            skippedChars,
            firstDataLineLength: nextLine.length,
            firstDataLinePreview: nextLine.substring(0, 100),
            controlCharRatio,
            remainingTextLength: cleanedText.length
          })
          return cleanedText
        }
        
        // 長い行が見つからない場合、次の改行まで進む
        if (lineEnd !== -1) {
          actualDataStart = lineEnd + 1
          skippedChars = 0
        } else {
          break
        }
      }
    }
  }
  
  // ファイル名パターンを探す（例: KYG251102.txt）
  const fileNamePattern = /([A-Z]{2,3})\d{6}\.txt/i
  const match = text.match(fileNamePattern)
  
  if (match && match.index !== undefined) {
    logger.info('LZHヘッダー内のファイル名を検出', {
      fileNameMatch: match[0],
      fileNameIndex: match.index,
      textPreview: text.substring(0, Math.min(500, text.length))
    })
    
    // ファイル名が見つかった場合、その後のデータ開始位置を探す
    const fileNameEnd = match.index + match[0].length
    const afterFileName = text.substring(fileNameEnd)
    
    // ファイル名の後の制御文字（0x00-0x1f、0x1bなど）をスキップして、データ開始位置を探す
    // 実際のデータ行は通常100文字以上（KYGデータは545バイト）
    let dataStartOffset = 0
    
    // まず、ファイル名の後の制御文字をスキップ
    for (let i = 0; i < Math.min(1000, afterFileName.length); i++) {
      const char = afterFileName[i]
      const charCode = char.charCodeAt(0)
      
      // 制御文字（0x00-0x1f）をスキップ
      if (charCode < 0x20) {
        dataStartOffset = i + 1
        continue
      }
      
      // 通常の文字（0x20以上）が見つかったら、データ開始位置の候補
      // 改行文字を探す
      if (char === '\n' || char === '\r') {
        // 改行文字の後の行を確認
        let nextLineStart = fileNameEnd + i + 1
        // \r\nの場合は2文字進める
        if (char === '\r' && afterFileName[i + 1] === '\n') {
          nextLineStart = fileNameEnd + i + 2
        }
        
        // 次の行の長さを確認（改行文字まで）
        const nextNewlineIndex = text.indexOf('\n', nextLineStart)
        const nextCarriageReturnIndex = text.indexOf('\r', nextLineStart)
        let nextLineEnd = -1
        if (nextNewlineIndex !== -1 && nextCarriageReturnIndex !== -1) {
          nextLineEnd = Math.min(nextNewlineIndex, nextCarriageReturnIndex)
        } else if (nextNewlineIndex !== -1) {
          nextLineEnd = nextNewlineIndex
        } else if (nextCarriageReturnIndex !== -1) {
          nextLineEnd = nextCarriageReturnIndex
        }
        
        const nextLine = nextLineEnd === -1 
          ? text.substring(nextLineStart)
          : text.substring(nextLineStart, nextLineEnd)
        
        // 次の行が長い（100文字以上）場合、データ開始位置
        if (nextLine.length >= 100) {
          const cleanedText = text.substring(nextLineStart)
          logger.info('LZHヘッダーをスキップしました（ファイル名パターン検出、改行後）', {
            fileNameMatch: match[0],
            fileNameIndex: match.index,
            dataStartOffset: nextLineStart,
            firstDataLineLength: nextLine.length,
            firstDataLinePreview: nextLine.substring(0, 100),
            remainingTextLength: cleanedText.length
          })
          return cleanedText
        }
      }
    }
    
    // ファイル名の後、制御文字をスキップしてデータ開始位置を探す（改行なしの場合）
    // ファイル名の後、制御文字をスキップした後、長いテキストが続く場合
    const potentialDataStart = fileNameEnd + dataStartOffset
    if (potentialDataStart < text.length) {
      const potentialData = text.substring(potentialDataStart)
      // 最初の200文字が制御文字でない場合、データ開始位置
      const firstChars = potentialData.substring(0, Math.min(200, potentialData.length))
      // eslint-disable-next-line no-control-regex
      const hasNonControlChars = /[^\u0000-\u001F]/.test(firstChars)
      
      if (hasNonControlChars && potentialData.length > 100) {
        logger.info('LZHヘッダーをスキップしました（制御文字スキップ後、改行なし）', {
          fileNameMatch: match[0],
          fileNameIndex: match.index,
          dataStartOffset: potentialDataStart,
          firstChars: firstChars.substring(0, 100),
          remainingTextLength: potentialData.length
        })
        return potentialData
      }
    }
  }
  
  // ファイル名パターンが見つからない場合、行単位で判定
  const lines = text.split(/\r?\n/)
  if (lines.length > 1) {
    const firstLine = lines[0]
    const hasFileName = fileNamePattern.test(firstLine)
    const isShortLine = firstLine.length < 200
    // eslint-disable-next-line no-control-regex
    const hasControlChars = /[\u0000-\u001F]/.test(firstLine)
    
    // 最初の行がヘッダー行の可能性が高い場合、スキップ
    if (hasFileName && (isShortLine || hasControlChars)) {
      // 2行目以降が長い行（データ行）かどうか確認
      for (let i = 1; i < Math.min(5, lines.length); i++) {
        if (lines[i].length >= 100) {
          // 長い行が見つかったら、2行目から処理
          const cleanedText = lines.slice(1).join('\n')
          logger.info('LZHヘッダー行をスキップしました（行単位判定）', {
            skippedFirstLine: firstLine.substring(0, 100),
            firstLineLength: firstLine.length,
            secondLineLength: lines[i].length,
            remainingLines: lines.length - 1,
            firstChars: cleanedText.substring(0, 200)
          })
          return cleanedText
        }
      }
    }
    
    // 最初の行にファイル名が含まれていて、制御文字が多い場合
    // 最初の行全体をスキップして、2行目以降を確認
    if (hasFileName && hasControlChars && firstLine.length < 300) {
      // 2行目以降を確認（最大10行まで）
      for (let i = 1; i < Math.min(10, lines.length); i++) {
        if (lines[i].length >= 100) {
          const cleanedText = lines.slice(i).join('\n')
          logger.info('LZHヘッダー行をスキップしました（制御文字が多い行をスキップ）', {
            skippedLines: i,
            skippedFirstLine: firstLine.substring(0, 100),
            firstDataLineLength: lines[i].length,
            remainingLines: lines.length - i,
            firstChars: cleanedText.substring(0, 200)
          })
          return cleanedText
        }
      }
    }
  }
  
  // ヘッダーが見つからない場合は、そのまま返す
  logger.info('LZHヘッダーは検出されませんでした。テキスト全体を処理します', {
    firstLineLength: lines[0]?.length || 0,
    totalLines: lines.length,
    textPreview: text.substring(0, 200)
  })
  return text
}

/**
 * JRDBデータの固定長テキストを解析
 * データ種別ごとに異なるフォーマットを持つため、基本的な解析のみ実装
 */
export function parseJRDBText(text: string, dataType: JRDBDataType): Record<string, unknown>[] {
  logger.info('Parsing JRDB text', { 
    textLength: text.length,
    dataType,
    firstChars: text.substring(0, 200)
  })
  
  // LZHヘッダーをスキップ（展開されていない場合）
  const cleanedText = skipLzhHeader(text)
  
  const lines = cleanedText.split(/\r?\n/).filter(line => line.trim().length > 0)
  logger.info('Text split into lines', { 
    totalLines: lines.length,
    firstFewLines: lines.slice(0, 5)
  })
  
  const records: Record<string, unknown>[] = []

  for (const line of lines) {
    // LZHヘッダーが含まれている行をスキップ
    // バイナリパターン（J\u0000-lh5など）またはファイル名パターン（KYG251102.txtなど）が含まれている場合
    // eslint-disable-next-line no-control-regex
    if (/J\u0000-lh\d/.test(line) || /^[A-Z]{2,3}\d{6}\.txt/.test(line)) {
      logger.info('LZHヘッダーを含む行をスキップしました', {
        linePreview: line.substring(0, 100),
        lineLength: line.length
      })
      continue
    }
    
    // 制御文字が多すぎる行（ヘッダーの可能性）をスキップ
    // eslint-disable-next-line no-control-regex
    const controlCharCount = (line.match(/[\u0000-\u001F\u001B]/g) || []).length
    const controlCharRatio = controlCharCount / line.length
    if (controlCharRatio > 0.1 && line.length < 200) {
      logger.info('制御文字が多い行（ヘッダーの可能性）をスキップしました', {
        linePreview: line.substring(0, 100),
        lineLength: line.length,
        controlCharRatio
      })
      continue
    }
    
    // TODO: データ種別ごとの固定長フォーマットに基づいて解析
    // 現時点では基本的な構造のみ
    records.push({
      raw: line,
      dataType
    })
  }

  // 最初の数行のサンプルをログに出力（文字コード確認用）
  if (records.length > 0) {
    logger.info('Sample parsed records (first 3 lines)', {
      sampleRecords: records.slice(0, 3).map(r => ({
        rawLength: (r.raw as string).length,
        rawPreview: (r.raw as string).substring(0, 100),
        // UTF-8文字列が正しく保存されているか確認（日本語文字が含まれているか）
        hasJapaneseChars: /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/.test(r.raw as string)
      }))
    })
  }

  logger.info('Parsed records', { recordCount: records.length })
  return records
}

/**
 * データをParquet形式に変換
 */
export async function convertToParquet(
  records: Record<string, unknown>[],
  outputPath: string,
  schema: Record<string, { type: string; optional?: boolean }>
): Promise<void> {
  if (records.length === 0) {
    logger.warn('変換するレコードがありません')
    throw new Error('cannot write parquet file with zero rows')
  }

  // Parquetスキーマを定義
  const parquetSchemaObj: Record<string, { type: string; optional?: boolean }> = {}
  
  // 最初のレコードからスキーマを推測
  const firstRecord = records[0]
  for (const [key, value] of Object.entries(firstRecord)) {
    if (schema[key]) {
      parquetSchemaObj[key] = schema[key]
    } else {
      // 型を推測
      if (typeof value === 'string') {
        parquetSchemaObj[key] = { type: 'UTF8', optional: true }
      } else if (typeof value === 'number') {
        // 整数か小数かを判定（小数点以下がある場合はDOUBLE、ない場合はINT64）
        if (Number.isInteger(value)) {
          parquetSchemaObj[key] = { type: 'INT64', optional: true }
        } else {
          parquetSchemaObj[key] = { type: 'DOUBLE', optional: true }
        }
      } else if (typeof value === 'boolean') {
        parquetSchemaObj[key] = { type: 'BOOLEAN', optional: true }
      } else {
        parquetSchemaObj[key] = { type: 'UTF8', optional: true }
      }
    }
  }

  // ParquetSchemaオブジェクトを作成
  const parquetSchema = new ParquetSchema(parquetSchemaObj)

  // Parquetファイルを作成
  const writer = await ParquetWriter.openFile(parquetSchema, outputPath)
  
  try {
    for (const record of records) {
      // スキーマに合わせてレコードの値を変換
      const convertedRecord: Record<string, unknown> = {}
      for (const [key, value] of Object.entries(record)) {
        const fieldSchema = parquetSchemaObj[key]
        if (!fieldSchema) {
          // スキーマにないフィールドはスキップ
          continue
        }
        
        // null値の処理：optionalフィールドの場合はundefinedにする
        if (value === null) {
          if (fieldSchema.optional) {
            convertedRecord[key] = undefined
          } else {
            // 必須フィールドの場合はデフォルト値を使用
            if (fieldSchema.type === 'INT64') {
              convertedRecord[key] = 0
            } else if (fieldSchema.type === 'DOUBLE') {
              convertedRecord[key] = 0.0
            } else if (fieldSchema.type === 'UTF8') {
              convertedRecord[key] = ''
            } else if (fieldSchema.type === 'BOOLEAN') {
              convertedRecord[key] = false
            } else {
              convertedRecord[key] = undefined
            }
          }
        } else {
          // 型をスキーマに合わせて変換
          if ((fieldSchema.type === 'INT64' || fieldSchema.type === 'DOUBLE') && typeof value === 'number') {
            convertedRecord[key] = value
          } else if (fieldSchema.type === 'UTF8' && typeof value === 'string') {
            convertedRecord[key] = value
          } else if (fieldSchema.type === 'BOOLEAN' && typeof value === 'boolean') {
            convertedRecord[key] = value
          } else {
            // 型が一致しない場合は文字列に変換
            convertedRecord[key] = String(value)
          }
        }
      }
      await writer.appendRow(convertedRecord)
    }
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    logger.error('Error writing to Parquet file', { 
      error: errorMessage,
      recordCount: records.length,
      outputPath
    })
    throw error
  } finally {
    await writer.close()
  }
}

/**
 * lzhファイルからParquetファイルへの変換処理
 */
export async function convertLzhToParquet(
  lzhBuffer: Buffer,
  dataType: JRDBDataType | null,
  year: number,
  outputPath: string
): Promise<{ actualDataType: JRDBDataType; records: Record<string, unknown>[] }> {

  // 1. lzhファイルを展開
  const extractedBuffer = await extractLzhFile(lzhBuffer)
  
  // データ種別の決定：引数で指定されたdataTypeを優先、未指定の場合のみ推測
  let actualDataType: JRDBDataType
  if (dataType !== null) {
    actualDataType = dataType
  } else {
    const extractedDataType = extractDataTypeFromExtractedBuffer(extractedBuffer)
    if (extractedDataType) {
      actualDataType = extractedDataType
    } else {
      logger.warn('データ種別の推測に失敗しました。デフォルト値KYを使用します')
      actualDataType = JRDBDataType.KY
    }
  }
  
  // 2. ShiftJISからUTF-8に変換
  let text: string
  try {
    text = convertShiftJISToUTF8(extractedBuffer)
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error)
    logger.error('Failed to convert ShiftJIS to UTF-8', { error: errorMessage })
    throw new Error(`Failed to convert encoding: ${errorMessage}`)
  }
  
  // 3. データ種別に応じて適切なパーサーを使用してパース
  let records: Record<string, unknown>[]
  
  // 汎用パーサーを使用
  records = parseJRDBDataFromBuffer(extractedBuffer, actualDataType)
  
  // 汎用パーサーで対応していない場合は、古いパーサーを使用
  if (records.length === 0) {
    records = parseJRDBText(text, actualDataType)
  }
  
  if (records.length === 0) {
    logger.warn('No records parsed')
    throw new Error('cannot write parquet file with zero rows')
  }
  
  // 4. Parquet形式に変換
  await convertToParquet(records, outputPath, {})
  
  return { actualDataType, records }
}

