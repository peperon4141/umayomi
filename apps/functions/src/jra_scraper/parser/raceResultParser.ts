import { logger } from 'firebase-functions'
import * as cheerio from 'cheerio'

/**
 * JRAレース結果ページのHTMLをパースしてレース結果データを抽出
 */
export function parseJRARaceResult(html: string, year: number, month: number, day: number): any[] {
  const races: any[] = []

  try {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/fcefbb62-f3cd-4a1a-a659-1e87ee5897f4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'raceResultParser.ts:7',message:'parseJRARaceResult entry',data:{year,month,day,htmlLength:html.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'ALL'})}).catch(()=>{});
    // #endregion
    logger.info('Starting JRA race result HTML parsing', { htmlLength: html.length })

    const $ = cheerio.load(html)
    const raceInfo = extractRaceInfo($)

    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/fcefbb62-f3cd-4a1a-a659-1e87ee5897f4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'raceResultParser.ts:16',message:'extractRaceInfo result',data:{raceInfoCount:raceInfo.length,venues:raceInfo.map((r:any)=>r.venue)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'ALL'})}).catch(()=>{});
    // #endregion

    if (raceInfo.length > 0) {
      logger.info('Found race info', { count: raceInfo.length })

      raceInfo.forEach((race: any, index: number) => {
        try {
          const raceData = {
            raceNumber: race.raceNumber,
            raceName: race.raceName,
            venue: race.venue,
            raceDate: new Date(Date.UTC(year, month - 1, day, 0, 0, 0, 0)),
            distance: race.distance,
            surface: race.surface,
            raceStartTime: parseStartTime(year, month, day, race.startTime),
            round: race.round, // extractRoundでエラーチェック済みのため、必ず存在する
            day: race.day, // 開催日目（例: "8"）
            scrapedAt: new Date(Date.UTC(new Date().getFullYear(), new Date().getMonth(), new Date().getDate(), 0, 0, 0, 0))
          }
          races.push(raceData)
        } catch (error) {
          logger.warn('Failed to parse race info', { index, error })
          // #region agent log
          fetch('http://127.0.0.1:7243/ingest/fcefbb62-f3cd-4a1a-a659-1e87ee5897f4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'raceResultParser.ts:35',message:'Race parse error',data:{index,error:error instanceof Error?error.message:String(error)},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'ALL'})}).catch(()=>{});
          // #endregion
        }
      })
    } else {
      // レース情報が見つからない場合でも、エラーを投げずに空の配列を返す
      // （カレンダーページから取得したデータは保存されるため、その日付のデータは存在する）
      logger.warn('No race info found in HTML for this date', { year, month, day })
      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/fcefbb62-f3cd-4a1a-a659-1e87ee5897f4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'raceResultParser.ts:40',message:'No race info found',data:{year,month,day},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'ALL'})}).catch(()=>{});
      // #endregion
      // エラーを投げずに空の配列を返す（カレンダーデータは保存される）
    }

    logger.info('JRA race result parsed successfully', {
      racesCount: races.length,
      htmlLength: html.length
    })
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/fcefbb62-f3cd-4a1a-a659-1e87ee5897f4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'raceResultParser.ts:48',message:'parseJRARaceResult exit',data:{racesCount:races.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'ALL'})}).catch(()=>{});
    // #endregion

  } catch (error) {
    logger.error('Failed to parse JRA race result', { error })
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/fcefbb62-f3cd-4a1a-a659-1e87ee5897f4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'raceResultParser.ts:52',message:'parseJRARaceResult error',data:{error:error instanceof Error?error.message:String(error),stack:error instanceof Error?error.stack:undefined},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'ALL'})}).catch(()=>{});
    // #endregion
    throw error
  }

  return races
}

/**
 * レース基本情報を抽出
 */
export function extractRaceInfo($: cheerio.CheerioAPI): any[] {
  const races: any[] = []

  // 競馬場IDと競馬場名のマッピング
  const venueMapping: { [key: string]: string } = {
    'rcA': '東京',
    'rcB': '京都',
    'rcC': '中山',
    'rcD': '阪神',
    'rcE': '新潟',
    'rcF': '札幌',
    'rcG': '函館',
    'rcH': '福島',
    'rcI': '中京',
    'rcJ': '小倉'
  }

  // すべての競馬場のレース情報を抽出
  for (const [venueId, venueName] of Object.entries(venueMapping)) {
    try {
      // 以前の実装と同じように、直接セレクタで.each()を呼び出す
      const selector = `#${venueId} tbody tr`
      const raceTableCheck = $(selector)
      
      if (raceTableCheck.length === 0) {
        // この競馬場のレースがない場合はスキップ
        logger.debug(`No races found for venue ${venueName} (${venueId})`)
        continue
      }

      // 各競馬場セクション内から開催情報を抽出（重要: 競馬場ごとに異なる開催情報を持つ可能性がある）
      const venueSection = $(`#${venueId}`)
      const meeting = extractMeetingInfoForVenue($, venueSection, venueName)
      
      // 開催情報が取れない場合はこの競馬場をスキップ（他の競馬場のレースは取得する）
      if (meeting == null) {
        const pageTitle = $('title').text()
        const venueSectionText = venueSection.text().substring(0, 500)
        logger.warn(
          `Failed to extract round/day for venue ${venueName} (${venueId}) from JRA HTML. Skipping this venue. ` +
          `pageTitle: ${pageTitle}, ` +
          `venueSectionText sample: ${venueSectionText.substring(0, 200)}.`
        )
        continue // この競馬場をスキップして次の競馬場を処理
      }

    let venueRaceCount = 0
    let venueSkippedCount = 0
    const totalRows = raceTableCheck.length
    
    logger.debug(`Processing venue ${venueName} (${venueId}): found ${totalRows} rows, meeting: round=${meeting.round}, day=${meeting.day}`)
    
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/fcefbb62-f3cd-4a1a-a659-1e87ee5897f4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'raceResultParser.ts:117',message:'Starting to process rows',data:{venueId,venueName,totalRows,meeting},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
    // #endregion
    
    // 以前の実装と同じように、直接セレクタで.each()を呼び出す
    // 注意: セレクタを直接使用することで、各競馬場ごとに正しくレースを取得できる
    $(`#${venueId} tbody tr`).each((index, element) => {
      const $row = $(element)
      
      const raceNumber = parseInt($row.find('th.num').text().replace('レース', '').trim())
      const stakesName = $row.find('td.name p.stakes strong').text().trim().replace(/\s+/g, ' ') || 
                        $row.find('td.name p.stakes a strong').text().trim().replace(/\s+/g, ' ')
      const raceClassName = $row.find('td.name p.race_class').text().trim()
      
      // レース名は必須（stakesNameまたはraceClassNameのいずれかが存在する必要がある）
      if (!stakesName && !raceClassName) {
        logger.warn('Race name not found', { 
          venueId, 
          venueName, 
          rowIndex: index,
          rowText: $row.text().substring(0, 100)
        })
        venueSkippedCount++
        return // .each()内ではcontinueの代わりにreturnを使用
      }
      const raceName = stakesName || raceClassName
      const distanceText = $row.find('td.name p.race_cond span.dist').text().replace(',', '').trim()
      const distance = parseInt(distanceText)
      const surfaceText = $row.find('td.name p.race_cond span.type').text()
      // surfaceの抽出を改善：芝またはダが含まれているか確認、どちらも含まれていない場合はnull
      let surface: string | null = null
      if (surfaceText.includes('芝')) 
        surface = '芝'
       else if (surfaceText.includes('ダ')) 
        surface = 'ダ'
       else if (surfaceText.includes('障')) surface = '障'
      const startTime = $row.find('td.time').text().trim()

      // 必須フィールドの検証（raceNumber, raceName, startTimeは必須）
      if (!raceNumber || !raceName || !startTime) {
        logger.warn('Required fields missing', {
          venueId,
          venueName,
          rowIndex: index,
          raceNumber: raceNumber || null,
          raceName: raceName || null,
          startTime: startTime || null
        })
        venueSkippedCount++
        return // .each()内ではcontinueの代わりにreturnを使用
      }
      
      // distanceとsurfaceの検証（必須フィールド）
      if (isNaN(distance) || distance <= 0) 
        throw new Error(
          `Invalid distance: ${distanceText} (parsed as ${distance}). ` +
          `venue: ${venueName}, raceNumber: ${raceNumber}, raceName: ${raceName}`
        )
      
      
      if (!surface) 
        throw new Error(
          `surface is required but was null or empty. ` +
          `surfaceText: "${surfaceText}", venue: ${venueName}, raceNumber: ${raceNumber}, raceName: ${raceName}`
        )
      
      
      const finalDistance = distance
      const finalSurface = surface
      
      races.push({
        raceNumber,
        raceName,
        venue: venueName,
        distance: finalDistance,
        surface: finalSurface,
        startTime,
        round: meeting.round,
        day: meeting.day
      })
      venueRaceCount++
    })
    
      logger.info(`Venue ${venueName} (${venueId}) processing complete: ${venueRaceCount} races added, ${venueSkippedCount} skipped, ${totalRows} total rows`)
    } catch (venueError) {
      // この競馬場でエラーが発生した場合、ログを出力してスキップ（他の競馬場のレースは取得する）
      const errorMessage = venueError instanceof Error ? venueError.message : String(venueError)
      logger.warn(`Failed to process venue ${venueName} (${venueId}), skipping this venue`, {
        venueId,
        venueName,
        error: errorMessage,
        stack: venueError instanceof Error ? venueError.stack : undefined
      })
      continue // この競馬場をスキップして次の競馬場を処理
    }
  }

  // 各競馬場ごとの取得レース数を集計
  const venueCounts: { [key: string]: number } = {}
  races.forEach((r: any) => {
    venueCounts[r.venue] = (venueCounts[r.venue] || 0) + 1
  })

  logger.info('Extracted race info', {
    totalRaces: races.length,
    venues: [...new Set(races.map((r: any) => r.venue))],
    venueCounts: venueCounts
  })

  return races
}

/**
 * ページ全体から開催情報（開催回数/開催日目）を抽出（後方互換性のため残す）
 */
function extractMeetingInfo($: cheerio.CheerioAPI): { round: number; day: string } | null {
  // 「○回東京○日」のような開催情報だけを対象にする（レース名の"第○回◯◯"は対象外）
  let pageText = ''
  const found: Array<{ round: number; day: string; source: string; text: string }> = []
  
  // 1. テーブルのcaptionから抽出（最優先: 「5回東京8日」のような形式）
  $('table caption').each((_, elem) => {
    const captionText = $(elem).text().trim()
    // 例: "5回東京8日" の round=5, day=8 を抽出
    const m = captionText.match(/^(\d+)回.*?(\d+|[a-z])日/i)
    if (!m) return
    const round = parseInt(m[1])
    const day = String(m[2]).toLowerCase()
    found.push({ round, day, source: 'table caption', text: captionText })
  })
  
  // 2. ページタイトルから抽出を試みる
  const pageTitle = $('title').text()
  if (pageTitle) pageText += pageTitle + ' '
  
  // 3. ヘッダー部分を優先的に検索（JRAのレース結果ページの構造に合わせたセレクタ）
  const headerSelectors = [
    'h1', 'h2', 'h3',
    '.header', '.title', '.page-title',
    '.race_header', '.kaisai_info', '.kaisai_title',
    '.main_title', '.sub_title',
    '#main_title', '#sub_title',
    '.race_list_header', '.race_day_header',
    '.contents_header', '.header_line'
  ]
  
  for (const selector of headerSelectors) {
    const headerText = $(selector).text()
    if (headerText) pageText += headerText + ' '
  }
  
  // 5. メインコンテンツエリアから抽出を試みる
  const mainContentSelectors = [
    '.main_content', '#main_content',
    '.race_list', '#race_list',
    '.kaisai', '#kaisai',
    '#contentsBody', '.contents_body'
  ]
  
  for (const selector of mainContentSelectors) {
    const contentText = $(selector).first().text()
    if (contentText) pageText += contentText.substring(0, 2000) + ' '
  }
  
  // 6. ヘッダーから取得できなかった場合はbody全体から検索（最初の3000文字）
  if (!pageText || pageText.trim().length < 10) {
    const bodyText = $('body').text()
    pageText = bodyText.substring(0, 3000) // 最初の3000文字
  }
  
  // 2. captionで取れなかった場合は、ヘッダ/本文から「○回◯◯○日」だけを抽出
  if (found.length === 0) {
    const m = pageText.match(/(\d+)回(?:東京|中山|京都|阪神|新潟|札幌|函館|福島|中京|小倉)(\d+|[a-z])日/i)
    if (m) found.push({ round: parseInt(m[1]), day: String(m[2]).toLowerCase(), source: 'page text', text: m[0] })
  }

  if (found.length === 0) return null
  // 基本は最初の候補を採用（同一ページ内で揺れない想定）
  const chosen = found[0]
  logger.info('Meeting info extracted', { chosen, candidates: found.slice(0, 5) })
  return { round: chosen.round, day: chosen.day }
}

/**
 * 特定の競馬場セクションから開催情報（開催回数/開催日目）を抽出
 * 各競馬場ごとに異なる開催情報を持つ可能性があるため、競馬場セクション内から抽出する
 */
function extractMeetingInfoForVenue($: cheerio.CheerioAPI, venueSection: cheerio.Cheerio<any>, venueName: string): { round: number; day: string } | null {
  const found: Array<{ round: number; day: string; source: string; text: string }> = []
  
  // 競馬場名を含むパターン（重要: 競馬場名を明示的に検証）
  const venuePattern = new RegExp(`(\\d+)回${venueName}(\\d+|[a-z])日`, 'i')
  
  // 1. 競馬場セクション内のテーブルcaptionから抽出（最優先）
  // 重要: captionに競馬場名が含まれていることを確認
  venueSection.find('table caption').each((_, elem) => {
    const captionText = $(elem).text().trim()
    // 例: "4回中山5日" の round=4, day=5 を抽出（競馬場名を検証）
    const m = captionText.match(venuePattern)
    if (!m) return
    const round = parseInt(m[1])
    const day = String(m[2]).toLowerCase()
    found.push({ round, day, source: 'venue section table caption', text: captionText })
  })
  
  // 2. 競馬場セクション内のテキストから「○回◯◯○日」パターンを抽出
  const venueSectionText = venueSection.text().substring(0, 2000)
  const m = venueSectionText.match(venuePattern)
  if (m) {
    found.push({ 
      round: parseInt(m[1]), 
      day: String(m[2]).toLowerCase(), 
      source: 'venue section text', 
      text: m[0] 
    })
  }
  
  // 3. 競馬場セクション内のヘッダー要素から抽出
  const headerSelectors = ['h1', 'h2', 'h3', 'h4', '.header', '.title', '.race_header']
  for (const selector of headerSelectors) {
    const headerText = venueSection.find(selector).first().text()
    if (headerText) {
      const headerMatch = headerText.match(venuePattern)
      if (headerMatch) {
        found.push({ 
          round: parseInt(headerMatch[1]), 
          day: String(headerMatch[2]).toLowerCase(), 
          source: `venue section ${selector}`, 
          text: headerMatch[0] 
        })
      }
    }
  }

  if (found.length === 0) return null
  // 最初の候補を採用
  const chosen = found[0]
  logger.info(`Meeting info extracted for venue ${venueName}`, { chosen, candidates: found.slice(0, 3) })
  return { round: chosen.round, day: chosen.day }
}

/**
 * 発走時刻をDate型に変換（JSTからUTCに変換）
 */
function parseStartTime(year: number, month: number, day: number, timeStr: string): Date {
  // "9時50分" 形式を解析
  const timeMatch = timeStr.match(/(\d+)時(\d+)分/)
  if (!timeMatch) throw new Error(`Invalid time format: ${timeStr}`)
  
  
  const hour = parseInt(timeMatch[1])
  const minute = parseInt(timeMatch[2])
  
  // JST時刻をUTCに変換（JST = UTC + 9時間）
  const utcHour = hour - 9
  const utcDate = new Date(Date.UTC(year, month - 1, day, utcHour, minute, 0, 0))
  
  // 日付が変わる場合の処理
  if (utcHour < 0) {
    utcDate.setUTCDate(utcDate.getUTCDate() - 1)
    utcDate.setUTCHours(utcHour + 24)
  }
  
  return utcDate
}


