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
      logger.warn('No race info found in HTML')
      // #region agent log
      fetch('http://127.0.0.1:7243/ingest/fcefbb62-f3cd-4a1a-a659-1e87ee5897f4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'raceResultParser.ts:40',message:'No race info found',data:{year,month,day},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'ALL'})}).catch(()=>{});
      // #endregion
      throw new Error('No race info found in HTML')
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

  // ページ全体から開催回数を抽出（ページヘッダーなどから）
  const round = extractRound($)
  
  // roundがnullの場合はエラーを投げる（fallbackを禁止）
  if (round == null) {
    const pageTitle = $('title').text()
    const pageText = $('body').text().substring(0, 1000)
    throw new Error(
      `Failed to extract round from JRA HTML. ` +
      `pageTitle: ${pageTitle}, ` +
      `pageText sample: ${pageText.substring(0, 200)}. ` +
      `Please check the HTML structure and update extractRound function.`
    )
  }

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
    // 以前の実装と同じように、直接セレクタで.each()を呼び出す
    const selector = `#${venueId} tbody tr`
    const raceTableCheck = $(selector)
    
    if (raceTableCheck.length === 0) {
      // この競馬場のレースがない場合はスキップ
      logger.debug(`No races found for venue ${venueName} (${venueId})`)
      continue
    }

    let venueRaceCount = 0
    let venueSkippedCount = 0
    const totalRows = raceTableCheck.length
    
    logger.debug(`Processing venue ${venueName} (${venueId}): found ${totalRows} rows`)
    
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/fcefbb62-f3cd-4a1a-a659-1e87ee5897f4',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'raceResultParser.ts:117',message:'Starting to process rows',data:{venueId,venueName,totalRows},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'})}).catch(()=>{});
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
      if (surfaceText.includes('芝')) {
        surface = '芝'
      } else if (surfaceText.includes('ダ')) {
        surface = 'ダ'
      } else if (surfaceText.includes('障')) {
        surface = '障' // 障害レース
      }
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
      if (isNaN(distance) || distance <= 0) {
        throw new Error(
          `Invalid distance: ${distanceText} (parsed as ${distance}). ` +
          `venue: ${venueName}, raceNumber: ${raceNumber}, raceName: ${raceName}`
        )
      }
      
      if (!surface) {
        throw new Error(
          `surface is required but was null or empty. ` +
          `surfaceText: "${surfaceText}", venue: ${venueName}, raceNumber: ${raceNumber}, raceName: ${raceName}`
        )
      }
      
      const finalDistance = distance
      const finalSurface = surface
      
      races.push({
        raceNumber,
        raceName,
        venue: venueName,
        distance: finalDistance,
        surface: finalSurface,
        startTime,
        round: round
      })
      venueRaceCount++
    })
    
    logger.info(`Venue ${venueName} (${venueId}) processing complete: ${venueRaceCount} races added, ${venueSkippedCount} skipped, ${totalRows} total rows`)
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
 * ページから開催回数を抽出
 */
function extractRound($: cheerio.CheerioAPI): number | null {
  // ページタイトルやヘッダー、レース名から「第○回」の形式を抽出
  let pageText = ''
  const foundRounds: number[] = []
  
  // 1. ページタイトルから抽出を試みる
  const pageTitle = $('title').text()
  if (pageTitle) {
    pageText += pageTitle + ' '
  }
  
  // 2. ヘッダー部分を優先的に検索（JRAのレース結果ページの構造に合わせたセレクタ）
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
    if (headerText) {
      pageText += headerText + ' '
    }
  }
  
  // 3. レース名から「第○回」を抽出（レース名の中に開催回数が含まれる場合がある）
  $('.stakes strong, .stakes a strong, p.stakes strong, p.stakes a strong').each((_, elem) => {
    const raceName = $(elem).text()
    const roundMatch = raceName.match(/第(\d+)回/)
    if (roundMatch) {
      const round = parseInt(roundMatch[1])
      if (!foundRounds.includes(round)) {
        foundRounds.push(round)
      }
    }
  })
  
  // 4. メインコンテンツエリアから抽出を試みる
  const mainContentSelectors = [
    '.main_content', '#main_content',
    '.race_list', '#race_list',
    '.kaisai', '#kaisai',
    '#contentsBody', '.contents_body'
  ]
  
  for (const selector of mainContentSelectors) {
    const contentText = $(selector).first().text()
    if (contentText) {
      pageText += contentText.substring(0, 2000) + ' ' // 最初の2000文字
    }
  }
  
  // 5. ヘッダーから取得できなかった場合はbody全体から検索（最初の3000文字）
  if (!pageText || pageText.trim().length < 10) {
    const bodyText = $('body').text()
    pageText = bodyText.substring(0, 3000) // 最初の3000文字
  }
  
  logger.info('Extracting round', { 
    pageTitle, 
    pageTextLength: pageText.length,
    pageTextSample: pageText.substring(0, 500),
    foundRoundsInRaceNames: foundRounds
  })
  
  // 「第○回」のパターンを検索
  const roundPatterns = [
    /第(\d+)回/,           // 第○回
    /(\d+)回目/,           // ○回目
    /回数[：:]\s*(\d+)/,   // 回数：○
    /回[：:]\s*(\d+)/      // 回：○
  ]
  
  let round: number | null = null
  
  // まず、レース名から見つかった開催回数を使用（最も頻繁に出現するものを採用）
  if (foundRounds.length > 0) {
    // 最も頻繁に出現する回数を採用
    const roundCounts: { [key: number]: number } = {}
    foundRounds.forEach(r => {
      roundCounts[r] = (roundCounts[r] || 0) + 1
    })
    const mostFrequentRound = Object.keys(roundCounts).reduce((a, b) => 
      roundCounts[parseInt(a)] > roundCounts[parseInt(b)] ? a : b
    )
    round = parseInt(mostFrequentRound)
    logger.info('Round extracted from race names', { round, allRounds: foundRounds })
  }
  
  // レース名から取得できなかった場合は、ページ全体から検索
  if (!round) {
    for (const pattern of roundPatterns) {
      const roundMatch = pageText.match(pattern)
      if (roundMatch) {
        round = parseInt(roundMatch[1])
        break
      }
    }
  }
  
  logger.info('Extracted round', { 
    round, 
    pageTextSample: pageText.substring(0, 500),
    extractedFrom: round && foundRounds.includes(round) ? 'race names' : (pageText.length > 0 ? 'page content' : 'empty')
  })
  
  return round
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


