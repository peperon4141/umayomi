import { ref, computed } from 'vue'
import { 
  collection, 
  query, 
  where, 
  orderBy, 
  getDocs, 
  Timestamp,
  type QueryConstraint 
} from 'firebase/firestore'
import { db } from '@/config/firebase'
import type { Race, RaceFilters } from '../../../shared/race'


export function useRace() {
  const races = ref<Race[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // レースを取得（yearフィールドベース）
  const fetchRaces = async (startDate?: Date, endDate?: Date, filters?: RaceFilters) => {
    loading.value = true
    error.value = null

    try {
      // デフォルトは現在の年
      const defaultStartDate = startDate || new Date()
      const defaultEndDate = endDate || new Date()
      
      const startYear = defaultStartDate.getFullYear()
      const endYear = defaultEndDate.getFullYear()
      
      // 現在の年をデフォルトでクエリ条件に含める
      const currentYear = new Date().getFullYear()
      const targetYear = startYear === endYear ? startYear : currentYear

      const constraints: QueryConstraint[] = []

      // 日付範囲が指定されている場合は、raceDateフィールドでフィルタリング
      // yearフィールドも併用してクエリを最適化
      if (startDate && endDate) {
        const startTimestamp = Timestamp.fromDate(startDate)
        const endTimestamp = Timestamp.fromDate(endDate)
        const startYear = startDate.getFullYear()
        const endYear = endDate.getFullYear()
        
        // yearフィールドが存在する場合は、yearフィールドでもフィルタリングしてクエリを最適化
        if (startYear === endYear) {
          constraints.push(where('year', '==', startYear))
        }
        
        constraints.push(where('raceDate', '>=', startTimestamp))
        constraints.push(where('raceDate', '<=', endTimestamp))
      } else {
        // 日付範囲が指定されていない場合は、yearフィールドでフィルタリング
        constraints.push(where('year', '==', targetYear))
      }

      // ソート条件を追加
      if (startDate && endDate) {
        // 日付範囲指定時はraceDateフィールドでソート
        constraints.push(orderBy('raceDate', 'asc'))
      } else {
        // 日付範囲未指定時はrace_keyでソート
        constraints.push(orderBy('race_key', 'desc'))
      }

      // フィルター条件を追加
      if (filters?.racecourse) {
        constraints.push(where('racecourse', '==', filters.racecourse))
      }
      if (filters?.grade) {
        constraints.push(where('grade', '==', filters.grade))
      }
      if (filters?.surface) {
        constraints.push(where('surface', '==', filters.surface))
      }

      const queryForYear = async (year: number, yearStart?: Date, yearEnd?: Date) => {
        const yearConstraints: QueryConstraint[] = []
        if (yearStart && yearEnd) {
          yearConstraints.push(where('raceDate', '>=', Timestamp.fromDate(yearStart)))
          yearConstraints.push(where('raceDate', '<=', Timestamp.fromDate(yearEnd)))
          yearConstraints.push(orderBy('raceDate', 'asc'))
        } else {
          yearConstraints.push(orderBy('raceDate', 'asc'))
        }
        // filters
        if (filters?.racecourse) yearConstraints.push(where('racecourse', '==', filters.racecourse))
        if (filters?.grade) yearConstraints.push(where('grade', '==', filters.grade))
        if (filters?.surface) yearConstraints.push(where('surface', '==', filters.surface))

        const q = query(collection(db, 'racesByYear', String(year), 'races'), ...yearConstraints)
        return await getDocs(q)
      }

      let snapshots = []
      if (startDate && endDate && startYear !== endYear) {
        // 年跨ぎは年別に取得して結合
        const years = Array.from({ length: endYear - startYear + 1 }, (_, i) => startYear + i)
        snapshots = await Promise.all(years.map(y => {
          const yStart = y === startYear ? startDate : new Date(Date.UTC(y, 0, 1, 0, 0, 0, 0))
          const yEnd = y === endYear ? endDate : new Date(Date.UTC(y, 11, 31, 23, 59, 59, 999))
          return queryForYear(y, yStart, yEnd)
        }))
      } else {
        const y = startDate && endDate ? startYear : targetYear
        snapshots = [await queryForYear(y, startDate, endDate)]
      }

      races.value = snapshots.flatMap(snapshot => snapshot.docs.map(doc => {
        const data = doc.data()
        const docId = doc.id
        const storedRaceKey = (data as any).race_key
        if (storedRaceKey != null && storedRaceKey !== docId) throw new Error(`race_key mismatch: doc.id=${docId}, data.race_key=${storedRaceKey}`)
        return {
          id: docId,
          race_key: docId,
          ...data
        } as Race
      }))

    } catch (err: any) {
      error.value = err instanceof Error ? err.message : String(err)
    } finally {
      loading.value = false
    }
  }

  // 競馬場一覧を取得
  const racecourses = computed(() => {
    const unique = new Set(races.value.map((race: Race) => race.racecourse))
    return Array.from(unique).sort()
  })

  // グレード一覧を取得
  const grades = computed(() => {
    const unique = new Set(races.value.map((race: Race) => race.grade).filter(Boolean))
    return Array.from(unique).sort()
  })

  // コース一覧を取得
  const surfaces = computed(() => {
    const unique = new Set(races.value.map((race: Race) => race.surface))
    return Array.from(unique).sort()
  })

  // レースを日付でグループ化
  const racesByDate = computed(() => {
    const grouped: { [key: string]: Race[] } = {}
    
    races.value.forEach((race: Race) => {
      // race.raceDateがTimestampの場合はtoDate()を使用、Dateの場合はそのまま使用
      const raceDate = race.raceDate instanceof Timestamp ? race.raceDate.toDate() : race.raceDate
      const dateStr = raceDate.toLocaleDateString('ja-JP')
      if (!grouped[dateStr]) {
        grouped[dateStr] = []
      }
      grouped[dateStr].push(race)
    })

    return grouped
  })

  return {
    races,
    loading,
    error,
    racecourses,
    grades,
    surfaces,
    racesByDate,
    fetchRaces,
    fetchOctoberRaces: () => fetchRaces() // 後方互換性のため
  }
}
