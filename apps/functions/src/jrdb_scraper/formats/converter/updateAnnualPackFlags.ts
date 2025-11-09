import { getAllDataTypes, JRDBDataType } from '../../entities/jrdb'
import { checkAnnualPackAvailabilityBatch } from './memberPageChecker'

/**
 * 全データタイプの年度パック有無を判定して、jrdb.tsのhasAnnualPackフラグを更新するスクリプト
 */
async function main() {
  console.log('年度パック有無の判定を開始します...\n')
  
  const dataTypes = getAllDataTypes()
  const results = await checkAnnualPackAvailabilityBatch(dataTypes)
  
  console.log('\n=== 判定結果 ===\n')
  
  // 結果をグループ化
  const withPack: JRDBDataType[] = []
  const withoutPack: JRDBDataType[] = []
  
  for (const [dataType, hasPack] of Object.entries(results)) 
    if (hasPack) 
      withPack.push(dataType as JRDBDataType)
     else 
      withoutPack.push(dataType as JRDBDataType)
    
  
  
  console.log(`✅ 年度パックあり: ${withPack.length}件`)
  console.log(`   ${withPack.join(', ')}\n`)
  
  console.log(`❌ 年度パックなし: ${withoutPack.length}件`)
  console.log(`   ${withoutPack.join(', ')}\n`)
  
  console.log('\n=== jrdb.tsの更新が必要なデータタイプ ===\n')
  
  // 現在の設定と比較して、更新が必要なものを表示
  const { JRDB_DATA_TYPE_INFO } = await import('../../entities/jrdb')
  
  const needsUpdate: Array<{ dataType: JRDBDataType; current: boolean; actual: boolean }> = []
  
  for (const dataType of dataTypes) {
    const current = JRDB_DATA_TYPE_INFO[dataType].hasAnnualPack
    const actual = results[dataType]
    
    if (current !== actual) needsUpdate.push({ dataType, current, actual })
  }
  
  if (needsUpdate.length === 0) 
    console.log('✅ すべてのデータタイプの設定が正しいです。\n')
   else {
    console.log(`⚠️  更新が必要: ${needsUpdate.length}件\n`)
    for (const { dataType, current, actual } of needsUpdate) 
      console.log(`   ${dataType}: ${current ? 'true' : 'false'} → ${actual ? 'true' : 'false'}`)
    
    console.log('\n以下のようにjrdb.tsを更新してください:\n')
    
    for (const { dataType, actual } of needsUpdate) {
      console.log(`  [JRDBDataType.${dataType}]: {`)
      console.log(`    // ... 他のフィールド ...`)
      console.log(`    hasAnnualPack: ${actual}`)
      console.log(`  },`)
    }
  }
  
  process.exit(0)
}

if (require.main === module) 
  main().catch((error) => {
    console.error('エラーが発生しました:', error)
    process.exit(1)
  })


