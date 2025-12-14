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

  // レースを取得（race_keyベース）
  const fetchRaces = async (startDate?: Date, endDate?: Date, filters?: RaceFilters) => {
    loading.value = true
    error.value = null

    try {
      // デフォルトの日付範囲（過去1年）
      const defaultStartDate = startDate || new Date()
      defaultStartDate.setFullYear(defaultStartDate.getFullYear() - 1)
      const defaultEndDate = endDate || new Date()

      // race_keyの形式: 場コード_年_回_日_R
      // 年の下2桁で範囲を指定
      const startYear = defaultStartDate.getFullYear() % 100
      const endYear = defaultEndDate.getFullYear() % 100
      const startYearStr = String(startYear).padStart(2, '0')
      const endYearStr = String(endYear).padStart(2, '0')
      
      // race_keyは文字列なので、範囲クエリを使用
      // 開始: 00_年_0_0_00（最小の場コード、最小の年、最小の回・日・R）
      // 終了: 99_年_9_9_99（最大の場コード、最大の年、最大の回・日・R）
      // 注意: 年が異なる場合は複数クエリが必要だが、簡易的に範囲クエリを使用
      const startRaceKey = `00_${startYearStr}_0_0_00`
      const endRaceKey = `99_${endYearStr}_9_9_99`

      const constraints: QueryConstraint[] = [
        where('race_key', '>=', startRaceKey),
        where('race_key', '<=', endRaceKey),
        orderBy('race_key', 'desc')
      ]

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

      const q = query(collection(db, 'races'), ...constraints)
      const snapshot = await getDocs(q)
      
      races.value = snapshot.docs.map(doc => {
        const data = doc.data()
        return {
          id: doc.id,
          race_key: doc.id, // ドキュメントIDがrace_key
          ...data
        } as Race
      })

    } catch (err: any) {
      error.value = err.message
      console.error('レース取得エラー:', err)
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
      // race.dateがTimestampの場合はtoDate()を使用、Dateの場合はそのまま使用
      const date = race.date instanceof Timestamp ? race.date.toDate() : race.date
      const dateStr = date.toLocaleDateString('ja-JP')
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
