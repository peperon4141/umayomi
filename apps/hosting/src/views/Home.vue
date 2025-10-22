<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100" data-theme="light">
    <!-- Navigation -->
    <nav class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <h1 class="text-2xl font-bold text-red-600">
              馬読
            </h1>
          </div>
          <div class="flex items-center space-x-4">
            <Button
              @click="showLoginModal = true"
              label="ログイン"
              severity="primary"
              size="small"
              aria-label="ログインダイアログを開く"
            />
          </div>
        </div>
      </div>
    </nav>

    <!-- Hero Section -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
      <div class="text-center">
        <h1 class="text-4xl md:text-6xl font-bold mb-6" aria-label="メインタイトル">
          <span class="text-red-600">競馬</span>の<span class="text-red-600">データ</span>を
          <br>読み解く
        </h1>
        <p class="text-xl mb-8 max-w-3xl mx-auto text-surface-600">
          過去のレース結果を分析して、次のレースの予想精度を向上させませんか？
          <br><strong class="text-red-600">馬読なら、データに基づいた予想と結果管理ができます。</strong>
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            @click="showLoginModal = true"
            label="ログイン"
            severity="primary"
            size="large"
            aria-label="ログインダイアログを開く"
            raised
          />
          <Button 
            @click="scrollToFeatures"
            label="機能を見る"
            severity="secondary"
            size="large"
            class="text-surface-900"
            aria-label="機能を見る"
            raised
          />
        </div>
      </div>
    </div>

    <!-- Features Section -->
    <div
      id="features"
      class="py-20 bg-surface-50"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold mb-4">
            馬読の特徴
          </h2>
          <p class="text-lg text-surface-600">
            データに基づいた競馬予想と結果管理システム
          </p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-6">
          <Card class="feature-card text-center">
            <template #content>
                     <div class="flex justify-center items-center mb-4">
                       <Avatar size="xlarge" class="bg-red-100" shape="circle" style="display: flex; align-items: center; justify-content: center;">
                         <i class="pi pi-chart-line text-2xl text-red-600" />
                       </Avatar>
                     </div>
              <h3 class="text-xl font-semibold mb-3">
                レース結果分析
              </h3>
              <p class="text-surface-600 m-0">
                過去のレース結果を詳細に分析。馬の成績、騎手の実績、コースの特性をデータで把握できます。
              </p>
            </template>
          </Card>
          
          <Card class="feature-card text-center">
            <template #content>
                     <div class="flex justify-center items-center mb-4">
                       <Avatar size="xlarge" class="bg-red-100" shape="circle" style="display: flex; align-items: center; justify-content: center;">
                         <i class="pi pi-calculator text-2xl text-red-600" />
                       </Avatar>
                     </div>
              <h3 class="text-xl font-semibold mb-3">
                予想精度の向上
              </h3>
              <p class="text-surface-600 m-0">
                蓄積されたデータを活用して、より精度の高い予想を実現。的中率の向上を目指せます。
              </p>
            </template>
          </Card>
          
          <Card class="feature-card text-center">
            <template #content>
                     <div class="flex justify-center items-center mb-4">
                       <Avatar size="xlarge" class="bg-red-100" shape="circle" style="display: flex; align-items: center; justify-content: center;">
                         <i class="pi pi-database text-2xl text-red-600" />
                       </Avatar>
                     </div>
              <h3 class="text-xl font-semibold mb-3">
                結果管理
              </h3>
              <p class="text-surface-600 m-0">
                予想結果と的中率を記録・管理。自分の予想パターンを分析して改善点を見つけられます。
              </p>
            </template>
          </Card>
        </div>
      </div>
    </div>

    <!-- Highlight Section -->
    <div class="py-20 bg-surface-900">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold mb-4 text-white">
          なぜ馬読なのか？
        </h2>
        <p class="text-xl text-surface-300 mb-8 max-w-3xl mx-auto">
          従来の感覚的な予想から、データに基づいた科学的な予想へ
        </p>
        <div class="flex items-center justify-center gap-8 mb-8">
          <div class="text-center">
            <h3 class="text-xl font-semibold mb-3 text-white">感覚的な予想</h3>
            <ul class="space-y-2 text-surface-300 text-sm">
              <li>• 直感に頼った判断</li>
              <li>• 結果の再現性が低い</li>
              <li>• 改善点が不明確</li>
            </ul>
          </div>
          <div class="flex items-center justify-center">
            <i class="pi pi-arrow-right text-3xl text-white"></i>
          </div>
          <div class="text-center">
            <h3 class="text-xl font-semibold mb-3 text-white">データ分析</h3>
            <ul class="space-y-2 text-surface-300 text-sm">
              <li>• 客観的なデータ分析</li>
              <li>• 再現性の高い予想</li>
              <li>• 継続的な改善が可能</li>
            </ul>
          </div>
        </div>
      </div>
    </div>

    <!-- Timeline Section -->
    <div class="py-20 bg-surface-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold mb-4">馬予想の分析フロー</h2>
          <p class="text-lg text-surface-600">データ収集から予想まで、体系的なアプローチ</p>
        </div>
        
        <div class="max-w-2xl mx-auto">
          <Timeline :value="timelineItems" :align="'alternate'" class="customized-timeline">
            <template #marker="slotProps">
                   <span class="flex w-8 h-8 items-center justify-center text-white rounded-full z-10 shadow-sm bg-red-600">
                <i :class="slotProps.item.icon" class="text-sm"></i>
              </span>
            </template>
            <template #content="slotProps">
              <Card class="mt-4">
                <template #title>
                  {{ slotProps.item.title }}
                </template>
                <template #content>
                  <p class="text-surface-600 m-0">{{ slotProps.item.description }}</p>
                </template>
              </Card>
            </template>
          </Timeline>
        </div>
      </div>
    </div>

    <!-- Case Studies Section -->
    <div class="py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl font-bold mb-4">
            こんな悩み、ありませんか？
          </h2>
          <p class="text-lg text-surface-600">
            馬予想なら、これらの悩みを解決できます
          </p>
        </div>
        
        <div class="grid md:grid-cols-3 gap-8">
          <div class="text-center p-6 bg-surface-50 rounded-lg">
            <div class="bg-red-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <i class="pi pi-chart-bar text-2xl text-red-600" />
            </div>
            <h3 class="text-xl font-semibold mb-3">
              予想が当たらない
            </h3>
            <p class="text-surface-600 mb-4">
              「いつも感覚で予想しているけど、なかなか当たらない。何かコツがあるのかな？」
            </p>
            <div class="text-sm text-surface-500">
              <strong>馬予想の解決策：</strong><br>
              過去のデータを分析して、客観的な根拠に基づいた予想を実現
            </div>
          </div>
          
          <div class="text-center p-6 bg-surface-50 rounded-lg">
            <div class="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <i class="pi pi-book text-2xl text-blue-600" />
            </div>
            <h3 class="text-xl font-semibold mb-3">
              情報が多すぎて整理できない
            </h3>
            <p class="text-surface-600 mb-4">
              「馬の成績、騎手の実績、コース情報...情報が多すぎて何を重視すればいいかわからない」
            </p>
            <div class="text-sm text-surface-500">
              <strong>馬予想の解決策：</strong><br>
              重要な指標を自動で抽出・分析して、分かりやすく表示
            </div>
          </div>
          
          <div class="text-center p-6 bg-surface-50 rounded-lg">
            <div class="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <i class="pi pi-chart-pie text-2xl text-green-600" />
            </div>
            <h3 class="text-xl font-semibold mb-3">
              自分の予想パターンがわからない
            </h3>
            <p class="text-surface-600 mb-4">
              「どんな時に当たって、どんな時に外れるのか。自分の予想の傾向がわからない」
            </p>
            <div class="text-sm text-surface-500">
              <strong>馬予想の解決策：</strong><br>
              予想結果を記録・分析して、自分の予想パターンを可視化
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- CTA Section -->
    <div class="bg-red-600 py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl font-bold text-white mb-4">
          データに基づいた競馬予想を始めませんか？
        </h2>
        <p class="text-xl text-red-100 mb-8">
          まずは無料で始めて、予想精度の向上を実感してください。
        </p>
        <Button
          @click="showLoginModal = true"
          label="ログイン"
          size="large"
          severity="secondary"
          aria-label="ログインダイアログを開く"
          raised
        />
      </div>
    </div>

    <!-- Footer -->
    <footer class="py-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center">
          <h3 class="text-2xl font-bold mb-4">
            馬予想
          </h3>
          <p>
            データに基づいた競馬予想と結果管理
          </p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const showLoginModal = ref(false)

const scrollToFeatures = () => {
  document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
}

// Timeline data
const timelineItems = ref([
  {
    title: 'レース結果の収集',
    description: '過去のレース結果、馬の成績、騎手の実績などのデータを収集します。',
    icon: 'pi pi-download'
  },
  {
    title: 'データ分析',
    description: '収集したデータを分析して、重要な指標やパターンを抽出します。',
    icon: 'pi pi-chart-line'
  },
  {
    title: '予想の実行',
    description: '分析結果に基づいて、次のレースの予想を立てます。',
    icon: 'pi pi-lightbulb'
  },
  {
    title: '結果の記録・改善',
    description: '予想結果を記録し、的中率を分析して予想精度の向上を図ります。',
    icon: 'pi pi-check-circle'
  }
])

// Force light theme for homepage
let originalTheme = ''

onMounted(() => {
  // Store original theme
  originalTheme = document.documentElement.getAttribute('data-theme') || ''
  // Force light theme
  document.documentElement.setAttribute('data-theme', 'light')
})

onUnmounted(() => {
  // Restore original theme when leaving page
  if (originalTheme) {
    document.documentElement.setAttribute('data-theme', originalTheme)
  } else {
    document.documentElement.removeAttribute('data-theme')
  }
})
</script>

<style scoped>
.feature-card {
  transition: transform 0.2s ease-in-out;
}

.feature-card:hover {
  transform: translateY(-4px);
}

.customized-timeline .p-timeline-event-marker {
  border: 2px solid var(--p-primary-color);
  background: var(--p-primary-color);
}
</style>
