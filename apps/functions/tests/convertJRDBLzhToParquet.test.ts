import { describe, it, expect } from 'vitest'
import { readFileSync, existsSync, unlinkSync } from 'fs'
import { join } from 'path'
import { tmpdir } from 'os'
import { convertLzhToParquet } from '../src/jrdb_scraper/converter'
// @ts-ignore - parquetjsには型定義がない
import { ParquetReader } from 'parquetjs'

describe('convertJRDBLzhToParquet', () => {
  describe('JRDB251102.lzh', () => {
    it('期待結果のParquetファイルと一致する', async () => {
      const lzhFilePath = join(__dirname, 'mock', 'jrdb', 'JRDB251102.lzh')
      const expectedParquetPath = join(__dirname, 'mock', 'jrdb', 'jrdb_data_JRDB251102.parquet')
      
      // サンプルファイルが存在することを確認
      if (!existsSync(lzhFilePath)) {
        // eslint-disable-next-line no-console
        console.warn(`サンプルファイルが見つかりません: ${lzhFilePath}`)
        // eslint-disable-next-line no-console
        console.warn('テストをスキップします')
        return
      }
      
      if (!existsSync(expectedParquetPath)) {
        // eslint-disable-next-line no-console
        console.warn(`期待結果ファイルが見つかりません: ${expectedParquetPath}`)
        // eslint-disable-next-line no-console
        console.warn('テストをスキップします')
        return
      }

      // LZHファイルを読み込む
      const lzhBuffer = readFileSync(lzhFilePath)
      expect(lzhBuffer.length).toBeGreaterThan(0)

      // 一時ファイルを作成
      const outputPath = join(tmpdir(), `test-jrdb-${Date.now()}.parquet`)

      try {
        // LZHファイルをParquetに変換
        await convertLzhToParquet(
          lzhBuffer,
          'KY',
          2025,
          outputPath
        )

        // 変換結果と期待結果のParquetファイルを読み込む
        const actualReader = await ParquetReader.openFile(outputPath)
        const expectedReader = await ParquetReader.openFile(expectedParquetPath)
        
        // 全レコードを読み込む
        const actualRecords: any[] = []
        const expectedRecords: any[] = []
        
        const actualCursor = actualReader.getCursor()
        const expectedCursor = expectedReader.getCursor()
        
        let actualRecord = null
        let expectedRecord = null
        
        while ((actualRecord = await actualCursor.next())) {
          actualRecords.push(actualRecord)
        }
        
        while ((expectedRecord = await expectedCursor.next())) {
          expectedRecords.push(expectedRecord)
        }
        
        await actualReader.close()
        await expectedReader.close()

        // レコード数が一致することを確認
        expect(actualRecords.length).toBe(expectedRecords.length)
        
        // 各レコードを比較
        for (let i = 0; i < Math.min(actualRecords.length, expectedRecords.length); i++) {
          const actual = actualRecords[i]
          const expected = expectedRecords[i]
          
          // レコード全体を比較（1つのexpectでオブジェクト全体を検証）
          expect(actual).toEqual(expected)
        }

        // eslint-disable-next-line no-console
        console.log('期待結果との比較完了:', {
          recordCount: actualRecords.length,
          matches: true
        })

      } finally {
        // 一時ファイルを削除
        if (existsSync(outputPath)) {
          unlinkSync(outputPath)
        }
      }
    }, 60000)
  })
})

