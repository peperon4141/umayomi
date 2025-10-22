import { collection, addDoc, getDocs, deleteDoc, doc } from 'firebase/firestore'
import { db } from '@/config/firebase'
import { sampleRaces } from './sampleData'

export async function seedRaceData() {
  try {
    console.log('🌱 サンプルデータの投入を開始...')
    
    // 既存のデータをクリア
    const existingRaces = await getDocs(collection(db, 'races'))
    const deletePromises = existingRaces.docs.map(docSnapshot => 
      deleteDoc(doc(db, 'races', docSnapshot.id))
    )
    await Promise.all(deletePromises)
    console.log('🗑️ 既存データをクリアしました')
    
    // サンプルデータを追加
    const addPromises = sampleRaces.map(race => 
      addDoc(collection(db, 'races'), race)
    )
    await Promise.all(addPromises)
    
    console.log('✅ サンプルデータの投入が完了しました')
    console.log(`📊 ${sampleRaces.length}件のレースデータを追加しました`)
    
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
