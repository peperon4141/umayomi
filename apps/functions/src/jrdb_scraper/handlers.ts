import { logger } from 'firebase-functions'
import { JRDBDataType, getAllDataTypes, getAnnualPackSupportedDataTypes } from './entities/jrdb'
import { fetchDailyData } from './fetchDailyData'
import { fetchAnnualData } from './fetchAnnualData'

/**
 * Request型（Firebase FunctionsのRequest型の簡易版）
 */
interface Request {
  query?: {
    url?: string
    dataType?: string
    year?: string
    month?: string
    day?: string
    racecourse?: string
    kaisaiRound?: string
    kaisaiDay?: string
    raceNumber?: string
  }
  body?: {
    url?: string
    dataType?: string
    year?: string
    file?: Buffer | string
  }
}

/**
 * Response型（Firebase FunctionsのResponse型の簡易版）
 */
interface Response {
  // eslint-disable-next-line no-unused-vars
  status: (code: number) => Response
  // eslint-disable-next-line no-unused-vars
  send: (data: unknown) => void
}

/**
 * JRDBから日単位で指定されたデータタイプを取得する処理
 * デバッグ用
 */
export async function handleFetchJRDBDailyData(request: Request, response: Response): Promise<void> {
  const startTime = Date.now()
  logger.info('Fetch JRDB daily data function called')

  try {
    // リクエストパラメータから日付情報とデータタイプを取得（queryパラメータのみ、必須）
    if (!request.query?.year || !request.query?.month || !request.query?.day || !request.query?.dataType) {
      const errorMessage = 'year, month, day, dataType parameters are required'
      logger.error(errorMessage)
      response.status(400).send({ success: false, error: errorMessage })
      return
    }

    const year = parseInt(String(request.query.year))
    const month = parseInt(String(request.query.month))
    const day = parseInt(String(request.query.day))
    const dataTypeStr = String(request.query.dataType).toUpperCase()

    // データタイプの配列を決定
    let dataTypes: JRDBDataType[]
    if (dataTypeStr === 'ALL') {
      // All指定の場合は、すべてのサポートされているデータタイプを取得
      dataTypes = Object.values(JRDBDataType)
      logger.info('Fetching JRDB data for all supported data types', {
        year,
        month,
        day,
        totalDataTypes: dataTypes.length
      })
    } else {
      // 単一のデータタイプを指定
      const dataType = Object.values(JRDBDataType).find(dt => dt.toString() === dataTypeStr) as JRDBDataType | undefined
      
      if (!dataType) {
        const errorMessage = `Invalid dataType: ${dataTypeStr}. Valid types: ALL, ${Object.values(JRDBDataType).join(', ')}`
        logger.error(errorMessage)
        response.status(400).send({ success: false, error: errorMessage })
        return
      }

      dataTypes = [dataType]
      logger.info('Fetching JRDB data for date and dataType', {
        year,
        month,
        day,
        dataType: dataTypeStr
      })
    }

    // 指定されたデータタイプ（複数可）を取得
    const results = await fetchDailyData(year, month, day, dataTypes)

    const executionTimeMs = Date.now() - startTime
    const successCount = results.filter(r => r.success).length
    const failureCount = results.filter(r => !r.success).length

    // すべて成功した場合
    if (failureCount === 0) 
      response.send({
        success: true,
        message: `${dataTypeStr === 'ALL' ? 'すべての' : dataTypeStr}データの取得が完了しました（日付: ${results[0]?.date || ''}）`,
        date: results[0]?.date || '',
        totalDataTypes: dataTypes.length,
        successCount,
        failureCount,
        results,
        executionTimeMs
      })
     else 
      // 一部またはすべてが失敗した場合
      response.status(500).send({
        success: false,
        message: `${successCount}件成功、${failureCount}件失敗しました`,
        date: results[0]?.date || '',
        totalDataTypes: dataTypes.length,
        successCount,
        failureCount,
        results,
        executionTimeMs
      })
    
    
  } catch (error) {
    const executionTimeMs = Date.now() - startTime
    const errorMessage = error instanceof Error ? error.message : String(error)
    const errorStack = error instanceof Error ? error.stack : undefined

    logger.error('Fetch JRDB daily data failed', {
      errorMessage,
      errorStack,
      executionTimeMs
    })

    response.status(500).send({
      success: false,
      error: errorMessage,
      executionTimeMs
    })
  }
}

/**
 * JRDBから年度単位で指定されたデータタイプの年度パックを取得する処理
 * 年度パックをサポートしているデータタイプのみ取得
 */
export async function handleFetchJRDBAnnualData(request: Request, response: Response): Promise<void> {
  const startTime = Date.now()
  logger.info('Fetch JRDB annual data function called')

  try {
    // リクエストパラメータから年度とデータタイプを取得（queryパラメータのみ、必須）
    if (!request.query?.year || !request.query?.dataType) {
      const errorMessage = 'year, dataType parameters are required'
      logger.error(errorMessage)
      response.status(400).send({ success: false, error: errorMessage })
      return
    }

    const year = parseInt(String(request.query.year))
    const dataTypeStr = String(request.query.dataType).toUpperCase()

    // データタイプの配列を決定
    let dataTypes: JRDBDataType[]
    if (dataTypeStr === 'ALL') {
      // All指定の場合は、年度パックをサポートしているすべてのデータタイプを取得
      dataTypes = getAnnualPackSupportedDataTypes(getAllDataTypes())
      logger.info('Fetching JRDB annual pack data for all supported data types', {
        year,
        totalDataTypes: dataTypes.length
      })
    } else {
      // 単一のデータタイプを指定
      const dataType = Object.values(JRDBDataType).find(dt => dt.toString() === dataTypeStr) as JRDBDataType | undefined
      
      if (!dataType) {
        const supportedDataTypes = getAnnualPackSupportedDataTypes(getAllDataTypes())
        const errorMessage = `Invalid dataType: ${dataTypeStr}. Valid types: ALL, ${supportedDataTypes.map((dt: JRDBDataType) => dt.toString()).join(', ')}`
        logger.error(errorMessage)
        response.status(400).send({ success: false, error: errorMessage })
        return
      }

      // 年度パックをサポートしているかチェック
      const supportedDataTypes = getAnnualPackSupportedDataTypes([dataType])
      if (supportedDataTypes.length === 0) {
        const allSupported = getAnnualPackSupportedDataTypes(getAllDataTypes())
        const errorMessage = `データタイプ ${dataTypeStr} は年度パックをサポートしていません。サポートされているデータタイプ: ${allSupported.map((dt: JRDBDataType) => dt.toString()).join(', ')}`
        logger.error(errorMessage)
        response.status(400).send({ success: false, error: errorMessage })
        return
      }

      dataTypes = [dataType]
      logger.info('Fetching JRDB annual pack data for year and dataType', {
        year,
        dataType: dataTypeStr
      })
    }

    // 指定されたデータタイプ（複数可）の年度パックを取得
    const results = await fetchAnnualData(year, dataTypes)

    const executionTimeMs = Date.now() - startTime
    const successCount = results.filter(r => r.success).length
    const failureCount = results.filter(r => !r.success).length

    // すべて成功した場合
    if (failureCount === 0) 
      response.send({
        success: true,
        message: `${dataTypeStr === 'ALL' ? 'すべての' : dataTypeStr}年度パックデータの取得が完了しました（年度: ${year}）`,
        year,
        totalDataTypes: dataTypes.length,
        successCount,
        failureCount,
        results,
        executionTimeMs
      })
     else 
      // 一部またはすべてが失敗した場合
      response.status(500).send({
        success: false,
        message: `${successCount}件成功、${failureCount}件失敗しました`,
        year,
        totalDataTypes: dataTypes.length,
        successCount,
        failureCount,
        results,
        executionTimeMs
      })
    
    
  } catch (error) {
    const executionTimeMs = Date.now() - startTime
    const errorMessage = error instanceof Error ? error.message : String(error)
    const errorStack = error instanceof Error ? error.stack : undefined

    logger.error('Fetch JRDB annual data failed', {
      errorMessage,
      errorStack,
      executionTimeMs
    })

    response.status(500).send({
      success: false,
      error: errorMessage,
      executionTimeMs
    })
  }
}

