// BACフォーマットのフィールド定義を確認し、レコード長を超えるフィールドがないかチェック

const bacFields = [
  { name: '場コード', start: 1, length: 2 },
  { name: '年', start: 3, length: 2 },
  { name: '回', start: 5, length: 1 },
  { name: '日', start: 6, length: 1 },
  { name: 'R', start: 7, length: 2 },
  { name: '年月日', start: 9, length: 8 },
  { name: '発走時間', start: 17, length: 4 },
  { name: '距離', start: 21, length: 4 },
  { name: '芝ダ障害コード', start: 25, length: 1 },
  { name: '右左', start: 26, length: 1 },
  { name: '内外', start: 27, length: 1 },
  { name: '種別', start: 28, length: 2 },
  { name: '条件', start: 30, length: 2 },
  { name: '記号', start: 32, length: 3 },
  { name: '重量', start: 35, length: 1 },
  { name: 'グレード', start: 36, length: 1 },
  { name: 'レース名', start: 37, length: 50 },
  { name: '回数', start: 87, length: 8 },
  { name: '頭数', start: 95, length: 2 },
  { name: 'コース', start: 97, length: 1 },
  { name: '開催区分', start: 98, length: 1 },
  { name: 'レース名短縮', start: 99, length: 8 },
  { name: 'レース名9文字', start: 107, length: 18 },
  { name: 'データ区分', start: 125, length: 1 },
  { name: '1着賞金', start: 126, length: 5 },
  { name: '2着賞金', start: 131, length: 5 },
  { name: '3着賞金', start: 136, length: 5 },
  { name: '4着賞金', start: 141, length: 5 },
  { name: '5着賞金', start: 146, length: 5 },
  { name: '1着算入賞金', start: 151, length: 5 },
  { name: '2着算入賞金', start: 156, length: 5 },
  { name: '単勝', start: 161, length: 1 },
  { name: '複勝', start: 162, length: 1 },
  { name: '枠連', start: 163, length: 1 },
  { name: '馬連', start: 164, length: 1 },
  { name: '馬単', start: 165, length: 1 },
  { name: 'ワイド', start: 166, length: 1 },
  { name: '３連複', start: 167, length: 1 },
  { name: '３連単', start: 168, length: 1 },
  { name: '予備', start: 169, length: 8 },
  { name: 'WIN5フラグ', start: 177, length: 1 },
  { name: '予備', start: 178, length: 5 },
  { name: '改行', start: 183, length: 2 },
];

const specRecordLength = 176;
const codeRecordLength = 184;

console.log('=== BACフォーマットのレコード長チェック ===\n');
console.log(`仕様書のレコード長: ${specRecordLength}バイト`);
console.log(`コードのレコード長: ${codeRecordLength}バイト\n`);

console.log('レコード長を超えるフィールド:');
let foundIssue = false;
for (const field of bacFields) {
  const endPos = field.start + field.length - 1;
  if (endPos > specRecordLength) {
    console.log(`  - ${field.name}: ${field.start}-${endPos}バイト目 (仕様書の${specRecordLength}バイトを超える)`);
    foundIssue = true;
  }
}

if (!foundIssue) {
  console.log('  なし');
}

console.log('\n最後のフィールド:');
const lastField = bacFields[bacFields.length - 1];
const lastFieldEnd = lastField.start + lastField.length - 1;
console.log(`  ${lastField.name}: ${lastField.start}-${lastFieldEnd}バイト目`);
console.log(`  改行(CRLF)を考慮: ${lastFieldEnd + 2}バイト目まで`);
console.log(`  実際のレコード長: ${codeRecordLength}バイト`);

console.log('\n=== 結論 ===');
if (lastFieldEnd + 2 === codeRecordLength) {
  console.log('✓ コードのレコード長(184バイト)は正しい');
} else {
  console.log('✗ コードのレコード長(184バイト)が不正');
}

if (specRecordLength < codeRecordLength) {
  console.log('⚠ 仕様書のレコード長(176バイト)が古い可能性がある');
  console.log('  → WIN5フラグが追加された第4版c以降、レコード長が184バイトに更新された可能性');
}
