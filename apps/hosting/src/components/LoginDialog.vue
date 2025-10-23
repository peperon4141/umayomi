<template>
  <Dialog
    v-model:visible="isOpen"
    modal
    class="w-[25rem] max-w-[90vw] p-4"
    :closable="true"
    :dismissable-mask="true"
    :draggable="false"
    :resizable="false"
    @hide="closeModal"
  >
    <template #header>
      <h2 class="text-xl font-bold">馬読</h2>
    </template>

    <p class="mb-6">
      馬読は、競馬のレース結果を分析して予想精度を向上させるアプリです。
      データに基づいた競馬予想を始めましょう。
    </p>
    
    <!-- Google Login Button (Primary) - Only show when email form is hidden -->
    <Button
      v-if="!showEmailForm"
      @click="handleGoogleLogin"
      :loading="loading"
      :disabled="loading"
      class="w-full mb-4"
      severity="secondary"
      outlined
      icon="pi pi-google"
      label="Googleでログイン"
      aria-label="Googleでログイン"
    />
    
    <!-- Email Login Form (Initially Hidden) -->
    <div v-if="showEmailForm" class="space-y-4">
      <div>
        <label for="email" class="block text-sm font-medium mb-1">
          メールアドレス
        </label>
        <InputText
          id="email"
          v-model="email"
          type="email"
          placeholder="example@example.com"
          class="w-full"
          :disabled="loading"
          aria-label="メールアドレス"
        />
      </div>
      
      <div>
        <label for="password" class="block text-sm font-medium mb-1">
          パスワード
        </label>
        <Password
          id="password"
          v-model="password"
          placeholder="パスワードを入力"
          class="w-full"
          :disabled="loading"
          :feedback="false"
          toggleMask
          aria-label="パスワード"
        />
      </div>
      
      <div class="flex space-x-2">
        <Button
          @click="handleEmailLogin"
          :loading="loading"
          :disabled="loading || !email || !password"
          class="flex-1"
          severity="primary"
          label="ログイン"
          aria-label="メールでログイン"
        />
        
        <Button
          @click="handleEmailRegister"
          :loading="loading"
          :disabled="loading || !email || !password"
          class="flex-1"
          severity="secondary"
          outlined
          label="新規作成"
        />
      </div>
    </div>
    
    <!-- Error Message -->
    <Message v-if="error" severity="error" class="mt-4" >
      {{ error }}
    </Message>
    
    <!-- Footer Text -->
    <div class="mt-4 text-center">
      <Button
        v-if="!showEmailForm"
        @click="showEmailForm = true"
        text
        severity="info"
        label="Googleアカウントをお持ちでない方"
        class="text-sm"
        aria-label="メール認証に切り替え"
      />
      <Button
        v-else
        @click="showEmailForm = false"
        text
        severity="secondary"
        label="← Googleログインに戻る"
        class="text-sm"
      />
    </div>
  </Dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

interface Props {
  visible: boolean
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'login-success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const router = useRouter()
const { login, register, loginWithGoogleAuth, loading, error, clearError } = useAuth()

// Form data
const email = ref('')
const password = ref('')
const showEmailForm = ref(false)

const isOpen = computed({ get: () => props.visible, set: (value) => { if (!value) emit('update:visible', false) } })

const closeModal = () => {
  // フォームをリセット
  email.value = ''
  password.value = ''
  showEmailForm.value = false
  clearError()
  emit('update:visible', false)
}

const handleGoogleLogin = async () => {
  try {
    clearError()
    const success = await loginWithGoogleAuth()
    if (success) {
      closeModal()
      emit('login-success')
      router.push('/races')
    }
  } catch {
    // Error is handled by the composable
  }
}

const handleEmailLogin = async () => {
  try {
    clearError()
    const success = await login(email.value, password.value)
    if (success) {
      closeModal()
      emit('login-success')
      router.push('/races')
    }
  } catch {
    // Error is handled by the composable
  }
}

const handleEmailRegister = async () => {
  try {
    clearError()
    const success = await register(email.value, password.value)
    if (success) {
      closeModal()
      emit('login-success')
      router.push('/races')
    }
  } catch {
    // Error is handled by the composable
  }
}
</script>
