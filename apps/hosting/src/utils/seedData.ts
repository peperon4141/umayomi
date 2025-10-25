import { collection, getDocs, deleteDoc, doc } from 'firebase/firestore'
import { db } from '@/config/firebase'

export async function seedRaceData() {
  try {
    console.log('🌱 サンプルデータの投入を開始...')
    console.log('⚠️ サンプルデータの投入機能は現在無効化されています')
    console.log('💡 JRAスクレイピング機能を使用してデータを取得してください')
    
    return true
  } catch (error) {
    console.error('❌ サンプルデータの投入に失敗しました:', error)
    return false
  }
}

export async function clearRaceData() {
  try {
    console.log('🗑️ レースデータの削除を開始...')
    
    const existingRaces = await getDocs(collection(db, 'races'))
    const deletePromises = existingRaces.docs.map(docSnapshot => 
      deleteDoc(doc(db, 'races', docSnapshot.id))
    )
    await Promise.all(deletePromises)
    
    console.log('✅ レースデータの削除が完了しました')
    return true
  } catch (error) {
    console.error('❌ レースデータの削除に失敗しました:', error)
    return false
  }
}
