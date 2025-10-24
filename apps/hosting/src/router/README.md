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

// ダッシュボード
const dashboardRoute = generateRoute(RouteName.DASHBOARD)
// 結果: '/dashboard'
```

### 2. パラメータ付きルート生成

```typescript
// レース詳細（直接アクセス）
const raceDetailRoute = generateRoute(RouteName.RACE_DETAIL_DIRECT, {
  raceId: 'race-123'
})
// 結果: '/race/race-123'

// 年別レース一覧
const yearRoute = generateRoute(RouteName.RACE_MONTH_LIST, {
  year: 2024
})
// 結果: '/races/year/2024'

// 月別レース一覧
const monthRoute = generateRoute(RouteName.RACE_DATE_LIST, {
  year: 2024,
  month: 10
})
// 結果: '/races/year/2024/month/10'

// 競馬場別レース一覧
const placeRoute = generateRoute(RouteName.RACE_LIST, {
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
  getCurrentYearRoute,
  getCurrentMonthRoute,
  getRaceYearRouteFromEnum,
  getRaceMonthRouteFromEnum,
  getRaceDateRouteFromEnum,
  getRaceDetailRouteFromEnum,
  getDirectRaceDetailRouteFromEnum
} from '@/router/routeCalculator'

// 現在年
const currentYearRoute = getCurrentYearRoute()
// 結果: '/races/year/2024' (現在年)

// 現在月
const currentMonthRoute = getCurrentMonthRoute()
// 結果: '/races/year/2024/month/10' (現在年月)

// 指定年のレース一覧
const yearRoute = getRaceYearRouteFromEnum(2024)
// 結果: '/races/year/2024'

// 指定年月のレース一覧
const monthRoute = getRaceMonthRouteFromEnum(2024, 10)
// 結果: '/races/year/2024/month/10'

// 指定年月・競馬場のレース一覧
const placeRoute = getRaceDateRouteFromEnum(2024, 10, 'tokyo')
// 結果: '/races/year/2024/month/10/place/tokyo'

// 指定レースの詳細（階層構造）
const raceDetailRoute = getRaceDetailRouteFromEnum(2024, 10, 'tokyo', 'race-123')
// 結果: '/races/year/2024/month/10/place/tokyo/race/race-123'

// 指定レースの詳細（直接アクセス）
const directRaceRoute = getDirectRaceDetailRouteFromEnum('race-123')
// 結果: '/race/race-123'
```

### 4. Vue Routerでの使用

#### 基本的な使用方法
```typescript
import { useRouter } from 'vue-router'
import { generateRoute, RouteName } from '@/router/routeCalculator'

const router = useRouter()

// ナビゲーション
router.push(generateRoute(RouteName.DASHBOARD))

// パラメータ付きナビゲーション
router.push(generateRoute(RouteName.RACE_DETAIL_DIRECT, {
  raceId: 'race-123'
}))
```


## 型安全性

- ルート名はenumで定義されているため、タイポを防げます
- 必要なパラメータが不足している場合は実行時エラーが発生します
- TypeScriptの型チェックにより、コンパイル時にエラーを検出できます

## メリット

1. **型安全性**: enumによる型安全なルート名管理
2. **保守性**: ルート名の変更が一箇所で管理可能
3. **可読性**: ルートの意図が明確
4. **拡張性**: 新しいルートの追加が容易
5. **一貫性**: 統一されたルート生成方法
