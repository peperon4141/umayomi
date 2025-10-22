<template>
  <Card class="race-card">
    <template #header>
      <div class="race-header">
        <div class="race-info">
          <h3 class="race-name">{{ race.raceName }}</h3>
          <div class="race-details">
            <span class="racecourse">{{ race.racecourse }}</span>
            <span class="race-number">第{{ race.raceNumber }}レース</span>
            <span class="distance">{{ race.distance }}m</span>
            <span class="surface">{{ race.surface }}</span>
          </div>
        </div>
        <div class="race-grade" v-if="race.grade">
          <Badge :value="race.grade" severity="info" />
        </div>
      </div>
    </template>
    
    <template #content>
      <div class="race-results">
        <div class="results-header">
          <h4>レース結果</h4>
          <Button 
            label="詳細を見る" 
            icon="pi pi-eye" 
            size="small" 
            severity="secondary"
            @click="viewDetails"
          />
        </div>
        
        <div class="results-table" v-if="race.results && race.results.length > 0">
          <div class="result-row header">
            <div class="rank">着順</div>
            <div class="horse-number">馬番</div>
            <div class="horse-name">馬名</div>
            <div class="jockey">騎手</div>
            <div class="time">タイム</div>
            <div class="odds">オッズ</div>
          </div>
          
          <div 
            v-for="result in race.results.slice(0, 3)" 
            :key="result.horseNumber"
            class="result-row"
          >
            <div class="rank">
              <Badge 
                :value="result.rank.toString()" 
                :severity="result.rank <= 3 ? 'success' : 'secondary'"
              />
            </div>
            <div class="horse-number">{{ result.horseNumber }}</div>
            <div class="horse-name">{{ result.horseName }}</div>
            <div class="jockey">{{ result.jockey }}</div>
            <div class="time">{{ result.time }}</div>
            <div class="odds">{{ result.odds.toFixed(1) }}</div>
          </div>
        </div>
        
        <div v-else class="no-results">
          <i class="pi pi-info-circle"></i>
          <span>結果データがありません</span>
        </div>
      </div>
    </template>
    
    <template #footer>
      <div class="race-footer">
        <div class="race-date">
          <i class="pi pi-calendar"></i>
          <span>{{ formatDate(race.date) }}</span>
        </div>
        <div class="race-actions">
          <Button 
            icon="pi pi-chart-line" 
            size="small" 
            severity="secondary"
            v-tooltip="'分析を見る'"
          />
          <Button 
            icon="pi pi-bookmark" 
            size="small" 
            severity="secondary"
            v-tooltip="'ブックマーク'"
          />
        </div>
      </div>
    </template>
  </Card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { Race } from '@/types/race'

interface Props {
  race: Race
}

const props = defineProps<Props>()
const router = useRouter()

const formatDate = (timestamp: any) => {
  const date = timestamp.toDate()
  return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'long'
  })
}

const viewDetails = () => {
  router.push(`/race/${props.race.id}`)
}
</script>

<style scoped>
.race-card {
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
}

.race-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.race-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.race-info {
  flex: 1;
}

.race-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
  color: var(--p-text-color);
}

.race-details {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.race-details span {
  padding: 0.25rem 0.5rem;
  background: var(--p-surface-100);
  border-radius: 0.375rem;
}

.race-grade {
  margin-left: 1rem;
}

.race-results {
  margin-top: 1rem;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.results-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.results-table {
  border: 1px solid var(--p-surface-border);
  border-radius: 0.5rem;
  overflow: hidden;
}

.result-row {
  display: grid;
  grid-template-columns: 60px 50px 1fr 100px 80px 60px;
  gap: 0.5rem;
  padding: 0.75rem;
  align-items: center;
  border-bottom: 1px solid var(--p-surface-border);
}

.result-row.header {
  background: var(--p-surface-50);
  font-weight: 600;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.result-row:last-child {
  border-bottom: none;
}

.rank, .horse-number, .time, .odds {
  text-align: center;
}

.horse-name {
  font-weight: 500;
}

.jockey {
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.no-results {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem;
  color: var(--p-text-muted-color);
  font-style: italic;
}

.race-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid var(--p-surface-border);
}

.race-date {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  color: var(--p-text-muted-color);
}

.race-actions {
  display: flex;
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .result-row {
    grid-template-columns: 50px 40px 1fr 80px 70px 50px;
    gap: 0.25rem;
    padding: 0.5rem;
    font-size: 0.875rem;
  }
  
  .race-details {
    gap: 0.5rem;
  }
  
  .race-details span {
    font-size: 0.75rem;
  }
}
</style>
