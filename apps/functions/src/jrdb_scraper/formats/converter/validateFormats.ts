import * as fs from 'fs'
import * as path from 'path'
import { getAllDataTypes } from '../../entities/jrdb'
import { getFormatDefinition } from '../../parsers/jrdbParser'
import type { JRDBFieldDefinition } from '../../parsers/formatParser'

const specsDir = path.join(__dirname, '../specs')

/**
 * 仕様書からレコード長を抽出
 */
function extractRecordLength(specContent: string): number | null {
  const match = specContent.match(/レコード長[：:]\s*(\d+)\s*BYTE/i)
  if (match) return parseInt(match[1], 10)
  return null
}

/**
 * 仕様書からフィールド定義を抽出
 */
interface SpecField {
  name: string
  start: number
  length: number
  type: string
  description: string
  indentLevel: number // 将来の階層構造チェック用
}

function extractFieldsFromSpec(specContent: string): SpecField[] {
  const lines = specContent.split('\n')
  const fields: SpecField[] = []
  let inFieldSection = false
  
  for (const line of lines) {
    // 項目名のセクション開始を検出
    if (line.includes('項目名') && line.includes('OCC')) {
      inFieldSection = true
      continue
    }
    
    // セクション終了を検出（改版履歴で終了）
    if (inFieldSection && (line.includes('改版履歴') || line.includes('特記事項'))) break
    
    // ===以下第X版で追加=== のような行はスキップ（コメント行として扱う）
    if (inFieldSection && line.includes('===以下') && line.includes('追加===')) continue
    
    if (inFieldSection) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('*')) continue
      
      // フィールド行のパターン: 項目名、OCC、BYTE、TYPE、相対、備考
      // 例: "場コード            2       99      1"
      // TYPEは9, Z, X, F, 99, 999, ZZZZ9, XXなどに対応
      const fieldMatch = trimmed.match(/^([^\s]+(?:\s+[^\s]+)*?)\s+(\d+)\s+([\dXZ.]+|F)\s+(\d+)(?:\s+(.+))?$/)
      if (fieldMatch) {
        const name = fieldMatch[1].trim()
        const byteLength = parseInt(fieldMatch[2], 10)
        const type = fieldMatch[3]
        const startPos = parseInt(fieldMatch[4], 10)
        const description = fieldMatch[5]?.trim() || ''
        
        // インデントレベルを計算（先頭のスペース数）
        const leadingSpaces = line.length - line.trimStart().length
        const currentIndentLevel = Math.floor(leadingSpaces / 2)
        
        // 親フィールド（start=0, length=0）をスキップ
        if (startPos > 0 && byteLength > 0) 
          fields.push({
            name: name.replace(/\s+/g, ' '),
            start: startPos,
            length: byteLength,
            type,
            description,
            indentLevel: currentIndentLevel // 将来の階層構造チェック用
          })
        
      }
    }
  }
  
  return fields
}

/**
 * TYPE文字列をJRDBFieldTypeに変換
 */
function convertSpecTypeToFieldType(type: string): string {
  // TYPEのパターンに応じて変換
  // 99, 9999, 9 など -> INTEGER_NINE
  // Z9, ZZ9, ZZZZ9 など -> INTEGER_ZERO_BLANK
  // F -> STRING_HEX
  // X, XX など -> STRING
  if (type.includes('F')) return 'STRING_HEX'
  if (type.includes('Z')) return 'INTEGER_ZERO_BLANK'
  if (type.includes('9')) return 'INTEGER_NINE'
  return 'STRING'
}

/**
 * フィールド型を正規化して比較
 */
function normalizeFieldType(fieldType: string | { toString(): string }): string {
  const typeStr = typeof fieldType === 'string' ? fieldType : fieldType.toString()
  // enumの値（例: "integer_nine"）を大文字に変換して比較
  return typeStr.toUpperCase().replace(/_/g, '_')
}

/**
 * フィールドの整合性をチェック
 */
function validateFieldIntegrity(fields: JRDBFieldDefinition[], recordLength: number): string[] {
  const issues: string[] = []
  
  // フィールドを開始位置でソート
  const sortedFields = [...fields].sort((a, b) => a.start - b.start)
  
  // 1. フィールドの重複チェック
  for (let i = 0; i < sortedFields.length; i++) {
    const field = sortedFields[i]
    const fieldEnd = field.start + field.length - 1
    
    for (let j = i + 1; j < sortedFields.length; j++) {
      const nextField = sortedFields[j]
      const nextFieldEnd = nextField.start + nextField.length - 1
      
      // 重複チェック
      if (field.start < nextField.start && fieldEnd >= nextField.start) issues.push(`フィールド重複: "${field.name}"(${field.start}-${fieldEnd}) と "${nextField.name}"(${nextField.start}-${nextFieldEnd})`)
    }
  }
  
  // 2. 最後のフィールドの終了位置がレコード長と一致するか
  if (sortedFields.length > 0) {
    const lastField = sortedFields[sortedFields.length - 1]
    const lastFieldEnd = lastField.start + lastField.length - 1
    
    // CRLF（2バイト）を考慮
    // 予備フィールドや改行フィールドがある場合は、それらを考慮
    const expectedEnd = lastFieldEnd + 2 // CRLF
    const tolerance = 5 // 5バイトの許容誤差（予備フィールドなど）
    
    if (Math.abs(expectedEnd - recordLength) > tolerance && Math.abs(lastFieldEnd - recordLength) > tolerance) {
      // 改行フィールドがある場合は、その長さを考慮
      const hasNewlineField = sortedFields.some(f => f.name.includes('改行') || f.name.includes('CR') || f.name.includes('LF'))
      if (!hasNewlineField) issues.push(`レコード長不一致: 最後のフィールド "${lastField.name}" の終了位置(${lastFieldEnd}) + CRLF(2) = ${expectedEnd} がレコード長(${recordLength})と一致しません`)
    }
  }
  
  // 3. フィールドの開始位置が1以上か
  for (const field of sortedFields) {
    if (field.start < 1) issues.push(`フィールド開始位置が不正: "${field.name}" の開始位置が ${field.start} (1以上である必要があります)`)
    if (field.length <= 0) issues.push(`フィールド長が不正: "${field.name}" の長さが ${field.length} (1以上である必要があります)`)
  }
  
  return issues
}

/**
 * フォーマット定義と仕様書を詳細に比較
 */
function validateFormat(dataType: string): {
  dataType: string
  hasSpec: boolean
  recordLengthMatch: boolean | null
  formatRecordLength: number
  specRecordLength: number | null
  fieldCountMatch: boolean | null
  formatFieldCount: number
  specFieldCount: number | null
  fieldDetailsMatch: boolean | null
  fieldMismatches: Array<{ field: string; issue: string }>
  integrityIssues: string[]
  issues: string[]
} {
  const format = getFormatDefinition(dataType as any)
  const issues: string[] = []
  const fieldMismatches: Array<{ field: string; issue: string }> = []
  
  if (!format) 
    return {
      dataType,
      hasSpec: false,
      recordLengthMatch: null,
      formatRecordLength: 0,
      specRecordLength: null,
      fieldCountMatch: null,
      formatFieldCount: 0,
      specFieldCount: null,
      fieldDetailsMatch: null,
      fieldMismatches: [],
      integrityIssues: [],
      issues: ['フォーマット定義が見つかりません']
    }
  
  
  // 仕様書ファイルを探す
  const specFiles = fs.readdirSync(specsDir)
  const specFile = specFiles.find(f => {
    const fLower = f.toLowerCase()
    const dtLower = dataType.toLowerCase()
    return fLower.includes(dtLower) ||
      (dataType === 'KZA' || dataType === 'KSA') && f.includes('Ks_doc') ||
      (dataType === 'CZA' || dataType === 'CSA') && f.includes('Cs_doc') ||
      (dataType === 'ZED') && f.includes('sed_doc') ||
      (dataType === 'ZEC') && f.includes('sec_doc') ||
      dataType === 'JOA' && f.includes('Jodata')
  })
  
  if (!specFile) {
    issues.push('仕様書ファイルが見つかりません')
    return {
      dataType,
      hasSpec: false,
      recordLengthMatch: null,
      formatRecordLength: format.recordLength,
      specRecordLength: null,
      fieldCountMatch: null,
      formatFieldCount: format.fields.length,
      specFieldCount: null,
      fieldDetailsMatch: null,
      fieldMismatches: [],
      integrityIssues: [],
      issues
    }
  }
  
  const specPath = path.join(specsDir, specFile)
  const specContent = fs.readFileSync(specPath, 'utf8')
  
  const specRecordLength = extractRecordLength(specContent)
  const specFields = extractFieldsFromSpec(specContent)
  
  const recordLengthMatch = specRecordLength !== null && format.recordLength === specRecordLength
  const fieldCountMatch = specFields.length > 0 && format.fields.length === specFields.length
  
  if (!recordLengthMatch && specRecordLength !== null) issues.push(`レコード長不一致: フォーマット定義=${format.recordLength}, 仕様書=${specRecordLength}`)
  
  if (!fieldCountMatch && specFields.length > 0) issues.push(`フィールド数不一致: フォーマット定義=${format.fields.length}, 仕様書=${specFields.length}`)
  
  // フィールドの詳細比較
  let fieldDetailsMatch = true
  if (specFields.length > 0 && format.fields.length > 0) {
    // 仕様書のフィールドをマップ（名前と開始位置でマッチング）
    const specFieldMap = new Map<string, SpecField>()
    for (const specField of specFields) {
      const key = `${specField.name}_${specField.start}`
      specFieldMap.set(key, specField)
    }
    
    // フォーマット定義の各フィールドを仕様書と比較
    for (const formatField of format.fields) {
      // 名前と開始位置でマッチングを試みる
      let matched = false
      for (const specField of specFields) 
        if (specField.start === formatField.start) {
          matched = true
          
          // 名前の比較（正規化：全角・半角スペース・空白を統一）
          const normalizedFormatName = formatField.name.replace(/\s+/g, ' ').trim()
          const normalizedSpecName = specField.name.replace(/\s+/g, ' ').trim()
          // 全角・半角の違いを許容（ＲとRなど）
          const formatNameForCompare = normalizedFormatName.replace(/[ＲＲ]/g, 'R').replace(/[０-９]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))
          const specNameForCompare = normalizedSpecName.replace(/[ＲＲ]/g, 'R').replace(/[０-９]/g, (c) => String.fromCharCode(c.charCodeAt(0) - 0xFEE0))
          if (formatNameForCompare !== specNameForCompare && normalizedFormatName !== normalizedSpecName) {
            fieldDetailsMatch = false
            fieldMismatches.push({
              field: formatField.name,
              issue: `フィールド名不一致: フォーマット="${normalizedFormatName}", 仕様書="${normalizedSpecName}"`
            })
          }
          
          // 長さの比較
          if (formatField.length !== specField.length) {
            fieldDetailsMatch = false
            fieldMismatches.push({
              field: formatField.name,
              issue: `フィールド長不一致: フォーマット=${formatField.length}, 仕様書=${specField.length}`
            })
          }
          
          // 型の比較（正規化して比較）
          const specFieldType = convertSpecTypeToFieldType(specField.type)
          const formatFieldType = normalizeFieldType(formatField.type)
          const normalizedSpecFieldType = specFieldType.toUpperCase()
          if (formatFieldType !== normalizedSpecFieldType) {
            fieldDetailsMatch = false
            fieldMismatches.push({
              field: formatField.name,
              issue: `フィールド型不一致: フォーマット=${formatFieldType}, 仕様書=${normalizedSpecFieldType} (TYPE=${specField.type})`
            })
          }
          
          break
        }
      
      
      if (!matched) {
        // 開始位置が一致しないフィールドを検出
        const closestSpecField = specFields.find(sf => 
          Math.abs(sf.start - formatField.start) < 5
        )
        if (closestSpecField) 
          fieldMismatches.push({
            field: formatField.name,
            issue: `開始位置不一致: フォーマット=${formatField.start}, 仕様書=${closestSpecField.start} (${closestSpecField.name})`
          })
        
      }
    }
  }
  
  // フィールドの整合性チェック
  const integrityIssues = validateFieldIntegrity(format.fields, format.recordLength)
  
  if (format.recordLength === 200 && format.fields.length === 1) issues.push('フォーマット定義が未実装（TODO状態）')
  
  return {
    dataType,
    hasSpec: true,
    recordLengthMatch,
    formatRecordLength: format.recordLength,
    specRecordLength,
    fieldCountMatch,
    formatFieldCount: format.fields.length,
    specFieldCount: specFields.length,
    fieldDetailsMatch,
    fieldMismatches,
    integrityIssues,
    issues
  }
}

/**
 * 全データタイプを検証
 */
function validateAllFormats() {
  const dataTypes = getAllDataTypes()
  const results = dataTypes.map(validateFormat)
  
  console.log('\n=== フォーマット定義と仕様書の詳細比較結果 ===\n')
  
  const issues: typeof results = []
  const ok: typeof results = []
  
  for (const result of results) {
    const hasIssues = result.issues.length > 0 || 
                     result.fieldMismatches.length > 0 || 
                     result.integrityIssues.length > 0
    if (hasIssues) 
      issues.push(result)
     else 
      ok.push(result)
    
  }
  
  console.log(`✅ 問題なし: ${ok.length}件`)
  console.log(`⚠️  問題あり: ${issues.length}件\n`)
  
  if (issues.length > 0) {
    console.log('=== 問題のあるデータタイプ ===\n')
    for (const result of issues) {
      console.log(`\n【${result.dataType}】`)
      console.log(`  レコード長: フォーマット=${result.formatRecordLength}, 仕様書=${result.specRecordLength ?? '不明'}`)
      console.log(`  フィールド数: フォーマット=${result.formatFieldCount}, 仕様書=${result.specFieldCount ?? '不明'}`)
      
      if (result.issues.length > 0) {
        console.log(`  【基本チェック】`)
        for (const issue of result.issues) 
          console.log(`    ⚠️  ${issue}`)
        
      }
      
      if (result.integrityIssues.length > 0) {
        console.log(`  【整合性チェック】`)
        for (const issue of result.integrityIssues) 
          console.log(`    ⚠️  ${issue}`)
        
      }
      
      if (result.fieldMismatches.length > 0) {
        console.log(`  【フィールド詳細不一致】`)
        for (const mismatch of result.fieldMismatches) 
          console.log(`    ⚠️  ${mismatch.field}: ${mismatch.issue}`)
        
      }
    }
  }
  
  console.log('\n=== 全データタイプの詳細 ===\n')
  for (const result of results) {
    const hasIssues = result.issues.length > 0 || 
                     result.fieldMismatches.length > 0 || 
                     result.integrityIssues.length > 0
    const status = hasIssues ? '⚠️' : '✅'
    const recordLengthStatus = result.recordLengthMatch ? '✓' : '✗'
    const fieldCountStatus = result.fieldCountMatch ? '✓' : '✗'
    const fieldDetailsStatus = result.fieldDetailsMatch !== false ? '✓' : '✗'
    const integrityStatus = result.integrityIssues.length === 0 ? '✓' : '✗'
    
    console.log(`${status} ${result.dataType.padEnd(6)} | レコード長:${recordLengthStatus} ${String(result.formatRecordLength).padStart(4)}/${String(result.specRecordLength ?? '?').padStart(4)} | フィールド数:${fieldCountStatus} ${String(result.formatFieldCount).padStart(3)}/${String(result.specFieldCount ?? '?').padStart(3)} | 詳細:${fieldDetailsStatus} | 整合性:${integrityStatus}`)
  }
  
  // 結果をJSONファイルに保存
  const outputPath = path.join(__dirname, '../../../tests/mock/jrdb/format_validation.json')
  const outputDir = path.dirname(outputPath)
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, { recursive: true })
  fs.writeFileSync(outputPath, JSON.stringify(results, null, 2), 'utf8')
  console.log(`\n詳細結果を保存しました: ${outputPath}`)
}

if (require.main === module) validateAllFormats()
