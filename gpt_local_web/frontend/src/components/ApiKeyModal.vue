<template>
  <div class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full">
    <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <div class="mt-3">
        <h3 class="text-lg font-medium leading-6 text-gray-900 mb-4">
          API Key Management
        </h3>

        <div v-if="error" class="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {{ error }}
        </div>

        <div v-if="loading" class="flex justify-center mb-4">
          <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500"></div>
        </div>

        <div v-if="authStore.apiKey" class="mb-4">
          <p class="text-sm text-gray-600 mb-2">Your API Key:</p>
          <div class="flex items-center space-x-2">
            <code class="bg-gray-100 p-2 rounded flex-1 break-all">
              {{ authStore.apiKey }}
            </code>
            <button
              @click="copyApiKey"
              class="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded"
            >
              Copy
            </button>
          </div>
        </div>

        <div v-if="userStatus" class="mb-4">
          <p class="text-sm text-gray-600">
            Requests today: {{ userStatus.requests_today }} / {{ userStatus.max_requests_per_day }}
          </p>
          <p class="text-sm text-gray-600">
            Created: {{ formatDate(userStatus.created_at) }}
          </p>
        </div>

        <div class="flex justify-between">
          <button
            v-if="authStore.apiKey"
            @click="clearApiKey"
            class="px-4 py-2 text-sm text-red-600 hover:text-red-800"
          >
            Clear API Key
          </button>
          <button
            v-else
            @click="generateApiKey"
            class="px-4 py-2 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
            :disabled="loading"
          >
            Generate API Key
          </button>
          <button
            @click="$emit('close')"
            class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const error = ref(null)
const loading = ref(false)
const userStatus = ref(null)

const formatDate = (dateStr) => {
  if (!dateStr) return 'Date not available'
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) {
      throw new Error('Invalid date')
    }
    return new Intl.DateTimeFormat(navigator.language, {
      dateStyle: 'medium',
      timeStyle: 'short'
    }).format(date)
  } catch (e) {
    console.error('Error formatting date:', e)
    return 'Invalid date'
  }
}

const generateApiKey = async () => {
  error.value = null
  loading.value = true
  try {
    await authStore.createTestUser()
    await checkStatus()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const checkStatus = async () => {
  error.value = null
  try {
    userStatus.value = await authStore.checkUserStatus()
  } catch (e) {
    error.value = e.message
  }
}

const clearApiKey = () => {
  authStore.clearApiKey()
  userStatus.value = null
}

const copyApiKey = () => {
  if (authStore.apiKey) {
    navigator.clipboard.writeText(authStore.apiKey)
  }
}

onMounted(async () => {
  if (authStore.apiKey) {
    await checkStatus()
  }
})
</script>
