import { ref } from 'vue'

export enum CloudFunctionName {
  SCRAPE_JRA_CALENDAR = 'scrapeJRACalendar',
  SCRAPE_JRA_RACE_RESULT = 'scrapeJRARaceResult',
  SCRAPE_JRA_CALENDAR_WITH_RACE_RESULTS = 'scrapeJRACalendarWithRaceResults'
}

export enum ScrapingTaskType {
  CALENDAR = 'calendar',
  RACE_RESULT = 'raceResult',
  BATCH = 'batch'
}

export interface ScrapingTaskParams {
  year: number
  month: number
  day?: number
}

export interface ScrapingTaskResult {
  success: boolean
  message: string
  racesCount?: number
  savedCount?: number
  url?: string
  executionTimeMs?: number
  error?: string
}

export function useCloudFunctions() {
  const loading = ref(false)
  const error = ref<string | null>(null)

  const callScrapingFunction = async (
    taskType: ScrapingTaskType,
    params: ScrapingTaskParams
  ): Promise<ScrapingTaskResult> => {
    loading.value = true
    error.value = null

    try {
      let functionName: CloudFunctionName
      let queryParams: Record<string, string>

      switch (taskType) {
        case ScrapingTaskType.CALENDAR:
          functionName = CloudFunctionName.SCRAPE_JRA_CALENDAR
          queryParams = {
            year: params.year.toString(),
            month: params.month.toString()
          }
          break
        case ScrapingTaskType.RACE_RESULT:
          functionName = CloudFunctionName.SCRAPE_JRA_RACE_RESULT
          queryParams = {
            year: params.year.toString(),
            month: params.month.toString(),
            day: params.day!.toString()
          }
          break
        case ScrapingTaskType.BATCH:
          functionName = CloudFunctionName.SCRAPE_JRA_CALENDAR_WITH_RACE_RESULTS
          queryParams = {
            year: params.year.toString(),
            month: params.month.toString()
          }
          break
        default:
          throw new Error('Invalid task type')
      }

      // Cloud Functionsを呼び出し（onRequest関数の場合は直接HTTPリクエスト）
      const functionUrl = `http://127.0.0.1:5101/umayomi-fbb2b/us-central1/${functionName}`
      
      const response = await fetch(functionUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(queryParams)
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result as ScrapingTaskResult
    } catch (err: any) {
      error.value = err.message
      return {
        success: false,
        message: 'Cloud Functions呼び出しに失敗しました',
        error: err.message
      }
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    callScrapingFunction
  }
}
