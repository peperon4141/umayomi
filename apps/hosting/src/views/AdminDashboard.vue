<template>
  <AppLayout>
    <div class="p-6">
      <h1 class="text-3xl font-bold text-gray-900 mb-4">管理ダッシュボード</h1>
      <p class="text-gray-600 mb-6">システム管理とCloud Functions実行</p>
      
      <!-- デバッグ情報 -->
      <div class="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <h2 class="text-lg font-bold text-yellow-800">デバッグ情報</h2>
        <p class="text-yellow-700">管理画面に正常にアクセスできています。</p>
      </div>
      
      <!-- シンプルな管理機能 -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-semibold mb-4">ユーザー管理</h3>
          <p class="text-gray-600">ユーザーの管理機能は今後実装予定です。</p>
        </div>
        
        <div class="bg-white p-6 rounded-lg shadow">
          <h3 class="text-lg font-semibold mb-4">システム管理</h3>
          <p class="text-gray-600">システムの管理機能は今後実装予定です。</p>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
// シンプルな管理画面コンポーネント
</script>