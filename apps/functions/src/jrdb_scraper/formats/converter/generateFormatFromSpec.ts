import * as fs from 'fs'
import * as path from 'path'
import { JRDBDataType, getAllDataTypes, getSpecificationUrl } from '../../entities/jrdb'

/**
 * 仕様書からフォーマット定義を自動生成するスクリプト
 * 
 * 対応機能:
 * - レコード長の抽出
 * - フィールド定義のパース（ネスト対応）
 * - TYPE判定（9, Z, X, F, ZZ9.9, ZZZZ9, 99, 999, XXなど）
 * - 繰り返し項目の検出と展開
 * - 特殊ケース（馬券発売フラグなど）の処理
 * - TypeScriptコードの生成
 */

interface ParsedField {
  name: string
  start: number
  length: number
  type: string // 仕様書のTYPE（9, Z, X, F, ZZ9.9など）
  description: string
  indentLevel: number
  isParent: boolean // 子フィールドを持つ親フィールドか
  subFields?: ParsedField[]
  repeatCount?: number // 繰り返し回数（OCC）
}

interface SpecMetadata {
  dataType: string
  recordLength: number
  specificationUrl?: string
  usageGuideUrl?: string
  sampleUrl?: string
}

/**
 * 仕様書ファイルをパース
 */
function parseSpecFile(specPath: string): { metadata: SpecMetadata; fields: ParsedField[] } {
  const content = fs.readFileSync(specPath, 'utf-8')
  const lines = content.split('\n')

  // データタイプをファイル名から抽出
  const fileName = path.basename(specPath, '.txt')
  const dataType = fileName.replace('_doc', '').toUpperCase()

  // レコード長を抽出
  let recordLength = 0
  const recordLengthMatch = content.match(/レコード長[：:]\s*(\d+)\s*BYTE/i)
  if (recordLengthMatch) recordLength = parseInt(recordLengthMatch[1], 10)

  // URLを抽出
  const specUrlMatch = content.match(/https?:\/\/[^\s]+/g)
  const specificationUrl = specUrlMatch?.[0]

  // フィールド定義セクションを探す（タブ区切りやスペース区切りに対応）
  const fieldSectionStart = lines.findIndex(line => {
    const normalized = line.replace(/\t/g, ' ').replace(/[\u3000\s]+/g, ' ')
    return normalized.includes('項目名') && (normalized.includes('OCC') || normalized.includes('occ')) && 
           (normalized.includes('BYTE') || normalized.includes('byte')) && 
           (normalized.includes('TYPE') || normalized.includes('type'))
  })

  if (fieldSectionStart === -1) throw new Error('フィールド定義セクションが見つかりません')

  // フィールド定義をパース
  const fields: ParsedField[] = []
  const fieldStack: ParsedField[] = [] // 階層構造を管理


  // フィールド定義の実際の開始行を探す（***行と空行をスキップ）
  let actualStartLine = fieldSectionStart + 1
  while (actualStartLine < lines.length) {
    const testLine = lines[actualStartLine].replace(/\r$/, '').trim()
    if (testLine.startsWith('***') || testLine === '') actualStartLine++
    else break
    
    
  }

  for (let i = actualStartLine; i < lines.length; i++) {
    let line = lines[i]
    // Windows形式の改行を処理
    line = line.replace(/\r$/, '').trim()

    // セクション終了を検出（改版履歴の行で終了）
    if (line.startsWith('改版履歴') || line.includes('改版履歴')) break
    
    // ===以下第X版で追加=== のような行はスキップ（コメント行として扱う）
    if (line.includes('===以下') && line.includes('追加===')) continue
    
    // ***で始まる区切り線はスキップ
    if (line.startsWith('***')) continue

    // 空行やコメント行をスキップ
    if (!line || line.startsWith('※') || line.startsWith('目的') || line.startsWith('その他')) continue

    // インデントレベルを計算（タブ、全角スペース、半角スペースを考慮）
    const originalLine = lines[i]
    // タブを2スペースとして計算（または1スペースとして扱う）
    const tabCount = (originalLine.match(/^\t+/) || [''])[0].length
    const spaceMatch = originalLine.replace(/^\t+/, '').match(/^[\s\u3000]+/)
    const indentLevel = tabCount * 2 + (spaceMatch ? spaceMatch[0].length : 0)

    // 親フィールド（数値がない行）を検出
    // 形式: 項目名（数値がない、ただし数値がある行は除外）
    // タブ区切りにも対応
    const normalizedForParent = line.replace(/\t/g, ' ').trim()
    const hasNumbers = /\d/.test(normalizedForParent)
    const parentFieldMatch = !hasNumbers && normalizedForParent.match(/^([^\s]+(?:\s+[^\s]+)*?)\s*$/)
    
    // フィールド行をパース
    // 形式: 項目名 [OCC] BYTE TYPE 相対 [備考]
    // タブ区切り、全角スペース、半角スペースの両方に対応
    // タブをスペースに変換してからパース
    // 全角数字（１、２など）を含むフィールド名にも対応
    const normalizedLine = line.replace(/\t/g, ' ').replace(/[\u3000\s]+/g, ' ').trim()
    // フィールド名に全角数字が含まれる場合も考慮（例: "１着賞金"）
    const fieldMatch = normalizedLine.match(/^([^\s]+(?:\s+[^\s]+)*?)\s+(\d+)\s+([\dXZ.]+|F)\s+(\d+)(?:\s+(.+))?$/)
    
    // 特殊ケース: 繰り返し項目の説明行（例: "1バイト目 単勝"）
    if (!fieldMatch && !parentFieldMatch) {
      const byteMatch = line.match(/^\d+\s*バイト目/) || line.match(/^\d+-\d+\s*バイト目/)
      if (!byteMatch) continue
      
      if (fieldStack.length === 0) continue
      
      const parent = fieldStack[fieldStack.length - 1]
      const subFieldMatch = line.match(/(\d+)(?:-(\d+))?\s*バイト目\s+(.+)/)
      if (!subFieldMatch) continue
      
      const startByte = parseInt(subFieldMatch[1], 10)
      const endByte = subFieldMatch[2] ? parseInt(subFieldMatch[2], 10) : startByte
      const subFieldName = subFieldMatch[3].trim()
      
      if (!parent.subFields) parent.subFields = []
      
      // 親フィールドの開始位置を基準に計算
      const parentStart = parent.start
      parent.subFields.push({
        name: subFieldName,
        start: parentStart + startByte - 1,
        length: endByte - startByte + 1,
        type: '9', // デフォルトは数値型
        description: `${subFieldName}（${startByte}バイト目）`,
        indentLevel: indentLevel,
        isParent: false
      })
      continue
    }
    
    // 特殊ケース: "9-16バイト目 予備" のような範囲指定
    if (!fieldMatch && !parentFieldMatch) {
      const rangeMatch = line.match(/(\d+)-(\d+)\s*バイト目\s+(.+)/)
      if (rangeMatch && fieldStack.length > 0) {
        const parent = fieldStack[fieldStack.length - 1]
        const startByte = parseInt(rangeMatch[1], 10)
        const endByte = parseInt(rangeMatch[2], 10)
        const subFieldName = rangeMatch[3].trim()
        
        if (!parent.subFields) parent.subFields = []
        
        const parentStart = parent.start
        parent.subFields.push({
          name: subFieldName,
          start: parentStart + startByte - 1,
          length: endByte - startByte + 1,
          type: '9', // デフォルトは数値型
          description: `${subFieldName}（${startByte}-${endByte}バイト目）`,
          indentLevel: indentLevel,
          isParent: false
        })
        continue
      }
    }

    // 親フィールド（OCCがある行）の処理
    // 形式: 項目名 OCC [空白] 相対 [備考]
    // 例: "単勝払戻        3                       9       9 * 3 = 27 BYTE"
    // OCCの後にBYTEやTYPEがない場合もある（子フィールドの合計長さが記載されている）
    // パターン: 項目名 + OCC（数字） + 空白 + 相対位置（数字）
    const parentWithOccMatch = normalizedLine.match(/^([^\s]+(?:\s+[^\s]+)*?)\s+(\d+)\s+(\d+)(?:\s+(.+))?$/)
    if (parentWithOccMatch && !fieldMatch) {
      const fieldName = parentWithOccMatch[1].trim()
      const occ = parseInt(parentWithOccMatch[2], 10)
      const startPos = parseInt(parentWithOccMatch[3], 10)
      const description = parentWithOccMatch[4]?.trim() || ''
      
      // OCCが1より大きい場合は繰り返し項目の親フィールド
      // ただし、通常のフィールド（OCC=1）と区別するため、子フィールドがあることを前提とする
      if (occ > 1 && startPos > 0) {
        // 階層構造を処理
        while (fieldStack.length > 0 && fieldStack[fieldStack.length - 1].indentLevel >= indentLevel) 
          fieldStack.pop()
        

        const parentField: ParsedField = {
          name: normalizeFieldName(fieldName),
          start: startPos,
          length: 0, // 子フィールドの合計長さ（後で計算）
          type: 'X', // デフォルト
          description: description || fieldName,
          indentLevel,
          isParent: true,
          repeatCount: occ // 繰り返し回数
        }

        // 親フィールドをfieldsに追加（子フィールドを持つ可能性があるため）
        if (fieldStack.length === 0) {
          fields.push(parentField)
          fieldStack.push(parentField)
          continue
        }
        
        const parent = fieldStack[fieldStack.length - 1]
        if (parent.start === 0 && parent.length === 0) {
          if (!parent.subFields) parent.subFields = []
          parent.subFields.push(parentField)
          parent.isParent = true
        } else 
          fields.push(parentField)
        
        
        // スタックに追加（子フィールドを持つ可能性があるため）
        fieldStack.push(parentField)
        continue
      }
    }
    
    // 親フィールド（数値がない行）の処理
    if (parentFieldMatch && !fieldMatch) {
      const fieldName = parentFieldMatch[1].trim()
      
      // 階層構造を処理
      while (fieldStack.length > 0 && fieldStack[fieldStack.length - 1].indentLevel >= indentLevel) 
        fieldStack.pop()
      

      const parentField: ParsedField = {
        name: normalizeFieldName(fieldName),
        start: 0, // 親フィールドは開始位置を持たない
        length: 0, // 親フィールドは長さを持たない
        type: 'X', // デフォルト
        description: fieldName,
        indentLevel,
        isParent: true
      }

      // 親フィールドをfieldsに追加（子フィールドを持つ可能性があるため）
      if (fieldStack.length === 0) {
        fields.push(parentField)
        fieldStack.push(parentField)
        continue
      }
      
      const parent = fieldStack[fieldStack.length - 1]
      if (parent.start === 0 && parent.length === 0) {
        if (!parent.subFields) parent.subFields = []
        parent.subFields.push(parentField)
        parent.isParent = true
      } else 
        fields.push(parentField)
      
      
      // スタックに追加（子フィールドを持つ可能性があるため）
      fieldStack.push(parentField)
      continue
    }

    // 通常のフィールドの処理
    if (!fieldMatch) continue
    
    const fieldName = fieldMatch[1].trim()
    const byteLength = parseInt(fieldMatch[2], 10)
    const type = fieldMatch[3]
    const startPos = parseInt(fieldMatch[4], 10)
    const description = fieldMatch[5]?.trim() || ''

    // 階層構造を処理
    while (fieldStack.length > 0 && fieldStack[fieldStack.length - 1].indentLevel >= indentLevel) 
      fieldStack.pop()
    

    const field: ParsedField = {
      name: normalizeFieldName(fieldName),
      start: startPos,
      length: byteLength,
      type,
      description: description || fieldName,
      indentLevel,
      isParent: false
    }

    // 親フィールドの子として追加するか、トップレベルに追加するか
    if (fieldStack.length === 0) {
      fields.push(field)
      if (field.start > 0 && field.length > 0) fieldStack.push(field)
      continue
    }
    
    const parent = fieldStack[fieldStack.length - 1]
    if (parent.start === 0 && parent.length === 0) {
      if (!parent.subFields) parent.subFields = []
      parent.subFields.push(field)
      parent.isParent = true
    } else 
      fields.push(field)
    

    // スタックに追加（子フィールドを持つ可能性があるため）
    // ただし、親フィールド（start=0, length=0）の場合は追加しない
    if (field.start > 0 && field.length > 0) fieldStack.push(field)
  }

  // ネストされたフィールドをフラット化
  const flattenedFields = flattenFields(fields)
  
  // 実際のフィールド定義からレコード長を計算（仕様書のレコード長が古い場合があるため）
  let calculatedRecordLength = recordLength
  if (flattenedFields.length > 0) {
    const sortedFields = [...flattenedFields].sort((a, b) => a.start - b.start)
    const lastField = sortedFields[sortedFields.length - 1]
    const lastFieldEnd = lastField.start + lastField.length - 1
    // 改行フィールドがある場合はその長さを使用、ない場合はCRLF（2バイト）を考慮
    if (lastField.name.includes('改行') || lastField.name.includes('CR') || lastField.name.includes('LF')) 
      calculatedRecordLength = lastFieldEnd
     else 
      calculatedRecordLength = lastFieldEnd + 2 // CRLF
    
  }

  return {
    metadata: {
      dataType,
      recordLength: calculatedRecordLength, // 実際のフィールド定義から計算したレコード長を使用
      specificationUrl,
      usageGuideUrl: undefined, // 仕様書からは抽出困難
      sampleUrl: undefined // 仕様書からは抽出困難
    },
    fields: flattenedFields
  }
}

/**
 * ネストされたフィールドをフラット化
 * 繰り返し項目（repeatCount > 1）の場合は、子フィールドを繰り返し展開
 */
function flattenFields(fields: ParsedField[]): ParsedField[] {
  const result: ParsedField[] = []
  
  for (const field of fields) {
    // start=0, length=0の親フィールドはスキップ
    if (field.start === 0 && field.length === 0) {
      if (field.subFields && field.subFields.length > 0) result.push(...flattenFields(field.subFields))
      continue
    }
    
    // 繰り返し項目の処理
    if (field.repeatCount && field.repeatCount > 1 && field.subFields && field.subFields.length > 0) {
      // 子フィールドの合計長さを計算
      const subFieldTotalLength = field.subFields.reduce((sum, sf) => sum + sf.length, 0)
      const itemLength = subFieldTotalLength / field.repeatCount
      
      // 子フィールドを繰り返し展開
      for (let i = 0; i < field.repeatCount; i++) 
        for (const subField of field.subFields) 
          if (subField.start > 0 && subField.length > 0) {
            // 繰り返し項目の開始位置を計算
            // 最初の子フィールドの相対位置を基準に、繰り返しごとにオフセットを追加
            const firstSubFieldStart = subField.start
            const relativeStart = firstSubFieldStart - field.start
            const repeatedStart = field.start + relativeStart + i * itemLength
            result.push({
              ...subField,
              start: repeatedStart,
              name: `${subField.name}${i + 1}`
            })
          }
        
      
      continue
    }
    
    // 実際のフィールドは追加
    if (field.subFields && field.subFields.length > 0) 
      // 親フィールド自体は追加せず、子フィールドのみ追加
      result.push(...flattenFields(field.subFields))
     else 
      // 子フィールドがない場合はそのまま追加
      result.push(field)
    
  }
  
  return result
}

/**
 * フィールド名を正規化
 */
function normalizeFieldName(name: string): string {
  return name
    .replace(/[\u3000\s]+/g, '') // 全角・半角スペースを削除
    .replace(/Ｒ/g, 'R') // 全角Rを半角に
    .replace(/[０-９]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0xFEE0)) // 全角数字を半角に
}

/**
 * TYPE文字列をJRDBFieldTypeに変換
 */
function convertTypeToJRDBFieldType(type: string): string {
  // 基本的な型
  if (type === '9') return 'JRDBFieldType.INTEGER_NINE'
  if (type === 'Z') return 'JRDBFieldType.INTEGER_ZERO_BLANK'
  if (type === 'X') return 'JRDBFieldType.STRING'
  if (type === 'F') return 'JRDBFieldType.STRING_HEX'

  // 複合型の判定
  // ZZ9.9, ZZZ9.9 など → STRING (小数点を含む場合は文字列として扱う)
  if (type.includes('.')) return 'JRDBFieldType.STRING'
  
  // 99, 999, 9999 など → INTEGER_NINE
  if (/^\d+$/.test(type)) return 'JRDBFieldType.INTEGER_NINE'
  
  // Z9, ZZ9, ZZZ9, ZZZZ9 など → INTEGER_ZERO_BLANK
  if (/^Z+9+$/.test(type)) return 'JRDBFieldType.INTEGER_ZERO_BLANK'
  
  // XX など → STRING
  if (/^X+$/.test(type)) return 'JRDBFieldType.STRING'
  
  // デフォルトはSTRING
  return 'JRDBFieldType.STRING'
}

/**
 * TypeScriptコードを生成
 */
function generateTypeScriptCode(metadata: SpecMetadata, fields: ParsedField[]): string {
  const dataTypeLower = metadata.dataType.toLowerCase()
  const description = getDataTypeDescription(metadata.dataType)
  
  let code = `import type { JRDBFormatDefinition } from '../parsers/formatParser'\n`
  code += `import { JRDBFieldType } from '../parsers/fieldParser'\n\n`
  code += `/**\n`
  code += ` * ${metadata.dataType}（${description}）のフォーマット定義\n`
  code += ` * \n`
  if (metadata.specificationUrl) code += ` * 仕様書: ${metadata.specificationUrl}\n`
  if (metadata.usageGuideUrl) code += ` * 使用説明: ${metadata.usageGuideUrl}\n`
  if (metadata.sampleUrl) code += ` * サンプル: ${metadata.sampleUrl}\n`
  code += ` * \n`
  code += ` * レコード長: ${metadata.recordLength}バイト\n`
  code += ` */\n`
  code += `export const ${dataTypeLower}Format: JRDBFormatDefinition = {\n`
  code += `  dataType: '${metadata.dataType}',\n`
  code += `  description: '${description}',\n`
  code += `  recordLength: ${metadata.recordLength},\n`
  code += `  encoding: 'ShiftJIS',\n`
  code += `  lineEnding: 'CRLF',\n`
  if (metadata.specificationUrl) code += `  specificationUrl: '${metadata.specificationUrl}',\n`
  if (metadata.usageGuideUrl) code += `  usageGuideUrl: '${metadata.usageGuideUrl}',\n`
  if (metadata.sampleUrl) code += `  sampleUrl: '${metadata.sampleUrl}',\n`
  code += `  fields: [\n`

  // 繰り返し項目を検出して処理
  const processedFields = detectAndProcessRepeatedFields(fields)
  
  for (const field of processedFields) 
    if (field.isRepeated && field.repeatCount) {
      // 繰り返し項目
      const repeatCount = field.repeatCount
      code += `    // ${field.name}（${repeatCount}個、${field.length}バイト×${repeatCount}=${field.length * repeatCount}バイト）\n`
      code += `    ...Array.from({ length: ${repeatCount} }, (_, i) => ({\n`
      code += `      name: \`${field.name}\${i + 1}\`,\n`
      code += `      start: ${field.start} + i * ${field.length},\n`
      code += `      length: ${field.length},\n`
      code += `      type: ${convertTypeToJRDBFieldType(field.type)} as const,\n`
      code += `      description: \`${field.description}\${i + 1}\`\n`
      code += `    })),\n`
    } else 
      // 通常のフィールド
      code += `    { name: '${field.name}', start: ${field.start}, length: ${field.length}, type: ${convertTypeToJRDBFieldType(field.type)}, description: '${escapeString(field.description)}' },\n`
    
  

  code += `  ]\n`
  code += `}\n`

  return code
}

/**
 * 繰り返し項目を検出
 */
function detectAndProcessRepeatedFields(fields: ParsedField[]): (ParsedField & { isRepeated?: boolean; repeatCount?: number })[] {
  const result: (ParsedField & { isRepeated?: boolean; repeatCount?: number })[] = []
  
  for (let i = 0; i < fields.length; i++) {
    const field = fields[i]
    
    // 連続する同じ長さ・型のフィールドを検出
    let repeatCount = 1
    for (let j = i + 1; j < fields.length; j++) {
      const nextField = fields[j]
      const isRepeatedField = 
        nextField.length === field.length &&
        nextField.type === field.type &&
        nextField.start === field.start + field.length * repeatCount &&
        (nextField.name.match(/^\d+$/) || nextField.name.includes('オッズ') || nextField.name.includes('タイム'))
      
      if (!isRepeatedField) break
      
      repeatCount++
    }
    
    if (repeatCount < 3) {
      result.push(field)
      continue
    }
    
    // 繰り返し項目として処理
    result.push({
      ...field,
      isRepeated: true,
      repeatCount
    })
    // スキップ
    i += repeatCount - 1
  }
  
  return result
}

/**
 * データタイプの説明を取得
 */
function getDataTypeDescription(dataType: string): string {
  const descriptions: Record<string, string> = {
    'BAC': 'JRDB番組データ（BAC）',
    'BAB': 'JRDB番組データ（BAB）',
    'KYI': 'JRDB競走馬データ（KYI）- 放牧先情報を追加（最も詳細）',
    'KYH': 'JRDB競走馬データ（KYH）- 放牧先情報なし',
    'KYG': 'JRDB競走馬データ（KYG）- 基本情報のみ',
    'KKA': 'JRDB拡張競走馬データ（KKA）',
    'SED': 'JRDB成績速報データ（SED）',
    'SEC': 'JRDB成績速報データ（SEC）',
    'ZED': 'JRDB前走データ（ZED）',
    'ZEC': 'JRDB前走データ（ZEC）',
    'TYB': 'JRDB直前情報データ（TYB）',
    'HJC': 'JRDB払戻情報データ（HJC）',
    'HJB': 'JRDB払戻情報データ（HJB）',
    'OZ': 'JRDB基準オッズデータ（OZ）- 単勝・複勝・連勝',
    'OW': 'JRDB基準オッズデータ（OW）- ワイド',
    'OU': 'JRDB基準オッズデータ（OU）- 馬単',
    'OT': 'JRDB基準オッズデータ（OT）- 3連複',
    'OV': 'JRDB基準オッズデータ（OV）- 3連単',
    'SRB': 'JRDB成績レースデータ（SRB）',
    'SRA': 'JRDB成績レースデータ（SRA）',
    'KZA': 'JRDB騎手データ（KZA）',
    'KSA': 'JRDB騎手データ（KSA）',
    'CZA': 'JRDB調教師データ（CZA）',
    'CSA': 'JRDB調教師データ（CSA）',
    'JOA': 'JRDB情報データ（JOA）',
    'UKC': 'JRDB馬基本データ（UKC）'
  }
  
  return descriptions[dataType] || `JRDBデータ（${dataType}）`
}

/**
 * 文字列をエスケープ
 */
function escapeString(str: string): string {
  return str
    .replace(/'/g, "\\'")
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
}

/**
 * 仕様書URLからファイル名を抽出
 */
function extractSpecFileName(specUrl: string): string {
  return specUrl.split('/').pop() || ''
}

/**
 * メイン処理
 */
function main() {
  // __dirnameは実行時のパスに依存するため、process.cwd()を基準にする
  const baseDir = process.cwd().includes('apps/functions') 
    ? process.cwd() 
    : path.join(process.cwd(), 'apps/functions')
  
  const specDir = path.join(baseDir, 'src/jrdb_scraper/formats/specs')
  const outputDir = path.join(baseDir, 'src/jrdb_scraper/formats')
  
  // 引数で指定されたデータ型を処理、または全データ型を処理
  const targetDataType = process.argv[2] as JRDBDataType | undefined
  
  const dataTypes = targetDataType
    ? [targetDataType]
    : getAllDataTypes()
  
  for (const dataType of dataTypes) {
    const specUrl = getSpecificationUrl(dataType)
    const specFileName = extractSpecFileName(specUrl)
    
    if (!specFileName) {
      console.error(`✗ エラー: ${dataType} に対応する仕様書URLが見つかりません`)
      continue
    }
    
    const specFile = path.join(specDir, specFileName)
    
    if (!fs.existsSync(specFile)) {
      console.error(`✗ エラー: 仕様書ファイルが見つかりません: ${specFileName}`)
      continue
    }
    
    try {
      console.log(`処理中: ${dataType} (${specFileName})`)
      
      const { metadata, fields } = parseSpecFile(specFile)
      
      // データ型を上書き（ZED/ZECなど、他の仕様書を参照する場合）
      metadata.dataType = dataType
      
      const code = generateTypeScriptCode(metadata, fields)
      
      const outputFile = path.join(outputDir, `${dataType.toLowerCase()}.ts`)
      fs.writeFileSync(outputFile, code, 'utf-8')
      
      console.log(`✓ 生成完了: ${outputFile}`)
    } catch (error) {
      console.error(`✗ エラー: ${dataType} (${specFileName})`, error instanceof Error ? error.message : String(error))
    }
  }
}

if (require.main === module) main()

