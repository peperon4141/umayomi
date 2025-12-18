/**
 * Firebase FunctionsのURLを生成するヘルパー関数
 * 環境に応じてエミュレーターまたは本番環境のURLを返す
 */
export function getFunctionUrl(functionName: string): string {
  const isEmulator = import.meta.env.VITE_USE_FIREBASE_EMULATOR === 'true' || import.meta.env.DEV
  const region = 'asia-northeast1'
  const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID
  if (!projectId) throw new Error('VITE_FIREBASE_PROJECT_ID is required (no fallback). Check your .env.* configuration.')
  
  if (isEmulator) return `http://127.0.0.1:5101/${projectId}/${region}/${functionName}`
  
  return `https://${region}-${projectId}.cloudfunctions.net/${functionName}`
}
