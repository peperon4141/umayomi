# ルート管理システム

## 概要

enumベースのルート管理システムにより、型安全で保守性の高いルーティングを実現します。

## 使用方法

### 1. 基本的なルート生成

```typescript
import { generateRoute, RouteName } from '@/router/routeCalculator'

// ホームページ
const homeRoute = generateRoute(RouteName.HOME)
// 結果: '/'

// 管理画面
const adminRoute = generateRoute(RouteName.ADMIN_DASHBOARD)
// 結果: '/admin'

// レース一覧（リダイレクト用）
const racesRoute = generateRoute(RouteName.RACES)
// 結果: '/races'
```

### 2. パラメータ付きルート生成

```typescript
// レース詳細（直接アクセス）
const raceDetailRoute = generateRoute(RouteName.RACE_DETAIL_DIRECT, {
  raceId: 'race-123'
})
// 結果: '/race/race-123'

// 年別レース一覧
const yearRoute = generateRoute(RouteName.RACE_LIST_IN_YEAR, {
  year: 2024
})
// 結果: '/races/year/2024'

// 月別レース一覧
const monthRoute = generateRoute(RouteName.RACE_LIST_IN_MONTH, {
  year: 2024,
  month: 10
})
// 結果: '/races/year/2024/month/10'

// 日別レース一覧
const dayRoute = generateRoute(RouteName.RACE_LIST_IN_DAY, {
  year: 2024,
  month: 10,
  day: 15
})
// 結果: '/races/year/2024/month/10/day/15'

// 競馬場別レース一覧
const placeRoute = generateRoute(RouteName.RACE_LIST_IN_PLACE, {
  year: 2024,
  month: 10,
  placeId: 'tokyo'
})
// 結果: '/races/year/2024/month/10/place/tokyo'

// レース詳細（階層構造）
const raceDetailHierarchyRoute = generateRoute(RouteName.RACE_DETAIL, {
  year: 2024,
  month: 10,
  placeId: 'tokyo',
  raceId: 'race-123'
})
// 結果: '/races/year/2024/month/10/place/tokyo/race/race-123'
```

### 3. 便利なヘルパー関数

```typescript
import { 
  getCurrentYear,
  getCurrentMonth
} from '@/router/routeCalculator'

// 現在年
const currentYear = getCurrentYear()
// 結果: 2024 (現在年)

// 現在月
const currentMonth = getCurrentMonth()
// 結果: 10 (現在月)

// 現在年のレース一覧
const currentYearRoute = generateRoute(RouteName.RACE_LIST_IN_YEAR, { year: getCurrentYear() })
// 結果: '/races/year/2024' (現在年)

// 現在年月のレース一覧
const currentMonthRoute = generateRoute(RouteName.RACE_LIST_IN_MONTH, { 
  year: getCurrentYear(), 
  month: getCurrentMonth() 
})
// 結果: '/races/year/2024/month/10' (現在年月)

// 日付からルート生成
const dateRoute = generateRoute(RouteName.RACE_LIST_IN_MONTH, {
  year: new Date('2024-10-15').getFullYear(),
  month: new Date('2024-10-15').getMonth() + 1
})
// 結果: '/races/year/2024/month/10'
```

### 4. 使用例

```typescript
// Vue コンポーネント内での使用
import { generateRoute, RouteName, getCurrentYear } from '@/router/routeCalculator'
import { useNavigation } from '@/composables/useNavigation'

const { navigateTo } = useNavigation()

// ナビゲーション
const goToRaceList = () => {
  navigateTo(RouteName.RACE_LIST_IN_YEAR, { year: getCurrentYear() })
}

// 条件付きナビゲーション
const goToRaceDetail = (raceId: string) => {
  if (raceId) {
    navigateTo(RouteName.RACE_DETAIL_DIRECT, { raceId })
  }
}

// 直接router.pushを使う場合
const router = useRouter()
router.push(generateRoute(RouteName.RACE_LIST_IN_YEAR, { year: getCurrentYear() }))
```
## 型安全性

- ルート名はenumで定義されているため、タイポを防げます
- 必要なパラメータが不足している場合は実行時エラーが発生します
- TypeScriptの型チェックにより、コンパイル時にエラーを検出できます

## メリット

1. **型安全性**: enumによる型安全なルート名管理
2. **保守性**: ルート名の変更が一箇所で管理可能
3. **可読性**: ルートの意図が明確
4. **一貫性**: プロジェクト全体で統一されたルート生成方法
