<template>
  <Dialog 
    :visible="visible" 
    @update:visible="$emit('update:visible', $event)"
    header="プロフィール" 
    :modal="true" 
    :closable="true"
    class="w-full max-w-md"
  >
    <div class="space-y-4">
      <div class="text-center">
        <Avatar 
          :label="user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'" 
          size="xlarge" 
          class="font-medium" 
          shape="circle" 
        />
        <h3 class="text-lg font-semibold mt-2">{{ user?.displayName || user?.email || 'ユーザー' }}</h3>
        <p class="text-gray-600">{{ user?.email }}</p>
      </div>
      
      <Divider />
      
      <div class="space-y-2">
        <div class="flex justify-between">
          <span class="text-gray-600">ユーザーID:</span>
          <span class="font-mono text-sm">{{ user?.uid }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-600">ロール:</span>
          <Badge :value="getUserRole()" :severity="isAdmin ? 'warning' : 'info'" />
        </div>
      </div>
    </div>
    
    <template #footer>
      <Button 
        label="閉じる" 
        @click="closeDialog" 
        severity="secondary" 
        class="w-full"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { useAuth } from '@/composables/useAuth'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const { user, isAdmin, getUserRole } = useAuth()

const closeDialog = () => {
  emit('update:visible', false)
}
</script>
