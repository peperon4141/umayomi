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
import type { Race, RaceFilters } from '@/types/race'


export function useRace() {
  const races = ref<Race[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 10月分のレースを取得
  const fetchOctoberRaces = async (filters?: RaceFilters) => {
    loading.value = true
    error.value = null

    try {
         const constraints: QueryConstraint[] = [
           where('date', '>=', Timestamp.fromDate(new Date('2024-10-01'))),
           where('date', '<=', Timestamp.fromDate(new Date('2024-10-31'))),
           orderBy('date', 'desc')
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
      
      races.value = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data()
      } as Race))

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
    fetchOctoberRaces
  }
}
