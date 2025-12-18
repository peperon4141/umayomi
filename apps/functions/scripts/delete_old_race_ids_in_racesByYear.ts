/**
 * racesByYear/{year}/races 配下の旧docId（YYYYMMDD_...）を削除するスクリプト。
 *
 * - 現行race_key（docId）は「場コード_回_日目_R」
 * - 旧docId（誤実装/旧仕様）は「YYYYMMDD_場コード_回_日目_R」
 *
 * 使い方（エミュレータ例）:
 *   FIRESTORE_EMULATOR_HOST=127.0.0.1:8180 GCLOUD_PROJECT=umayomi-fbb2b \
 *   pnpm -F functions tsx scripts/delete_old_race_ids_in_racesByYear.ts --year=2025
 */
import { initializeApp } from 'firebase-admin/app'
import { getFirestore } from 'firebase-admin/firestore'

initializeApp()

const requireArg = (name: string): string => {
  const prefix = `--${name}=`
  const arg = process.argv.find(a => a.startsWith(prefix))
  if (!arg) throw new Error(`Missing required arg: ${prefix}...`)
  const value = arg.slice(prefix.length)
  if (!value) throw new Error(`Invalid arg (empty): ${prefix}`)
  return value
}

const requireEnv = (name: string): string => {
  const value = process.env[name]
  if (!value) throw new Error(`${name} is required (no fallback).`)
  return value
}

async function main() {
  // エミュレータ利用時は必須。誤ったプロジェクトを触らないため、fallbackはしない。
  requireEnv('GCLOUD_PROJECT')
  requireEnv('FIRESTORE_EMULATOR_HOST')

  const year = requireArg('year')
  if (!/^\d{4}$/.test(year)) throw new Error(`Invalid --year: ${year} (expected YYYY)`)

  const db = getFirestore()
  const racesRef = db.collection('racesByYear').doc(year).collection('races')
  const docRefs = await racesRef.listDocuments()

  const legacy = docRefs.filter(ref => /^\d{8}_/.test(ref.id))
  if (legacy.length === 0) {
    // eslint-disable-next-line no-console
    console.log(`No legacy docs found in racesByYear/${year}/races`)
    return
  }

  // eslint-disable-next-line no-console
  console.log(`Deleting ${legacy.length} legacy docs from racesByYear/${year}/races ...`)

  const batchSize = 500
  let deleted = 0
  for (let i = 0; i < legacy.length; i += batchSize) {
    const batch = db.batch()
    legacy.slice(i, i + batchSize).forEach(ref => batch.delete(ref))
    await batch.commit()
    deleted += Math.min(batchSize, legacy.length - i)
    // eslint-disable-next-line no-console
    console.log(`Deleted ${deleted}/${legacy.length}`)
  }
}

main().catch((e) => {
  // eslint-disable-next-line no-console
  console.error(e)
  process.exit(1)
})


