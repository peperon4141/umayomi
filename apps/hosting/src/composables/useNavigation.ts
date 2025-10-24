/**
 * enumベースのナビゲーションcomposable
 * useRouter、useRouteをラップしてenumベースの操作を提供
 */

import { useRouter as useVueRouter, useRoute as useVueRoute } from 'vue-router'
import { generateRoute, type RouteOptions, RouteName } from '@/router/routeCalculator'

export function useNavigation() {
  const router = useVueRouter()
  const route = useVueRoute()

  // enumベースのナビゲーション
  const navigateTo = (routeName: RouteName, options: RouteOptions = {}) => {
    const path = generateRoute(routeName, options)
    return router.push(path)
  }

  // 現在のルート名を取得
  const getCurrentRouteName = (): RouteName | null => {
    return route.name as RouteName || null
  }

  // 特定のパラメータを取得
  const getParam = (key: string): string | undefined => {
    return route.params[key] as string | undefined
  }

  // 特定のクエリを取得
  const getQuery = (key: string): string | string[] | undefined => {
    const value = route.query[key]
    if (value === null) return undefined
    if (Array.isArray(value)) {
      return value.filter(v => v !== null) as string[]
    }
    return value as string
  }

  // parse済みのパラメータをobject形式で取得
  const getParams = <T extends Record<string, any>>(parser?: (params: Record<string, string | undefined>) => T): T | Record<string, string | undefined> => {
    if (parser) {
      return parser(route.params as Record<string, string | undefined>)
    }
    return route.params as Record<string, string | undefined>
  }

  // 404ページへの遷移
  const navigateTo404 = () => {
    router.push({ name: 'NotFound' })
  }


  return {
    // ナビゲーション
    navigateTo,
    navigateTo404,
    
    // ルート情報取得
    getCurrentRouteName,
    getParam,
    getQuery,
    getParams,
    
    // 元のrouterとrouteへのアクセス（必要に応じて）
    router,
    route,
  }
}
