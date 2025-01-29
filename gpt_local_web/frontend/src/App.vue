<script setup>
import { ref, onMounted } from 'vue'
import { MoonIcon, SunIcon } from '@heroicons/vue/24/outline'
import { API_BASE_URL } from './config'

const isDarkMode = ref(false)
const currentMessage = ref('')
const selectedService = ref('')
const selectedModel = ref('')
const messages = ref([])
const models = ref({
  ollama: [],
  gpt4all: []
})
const isLoading = ref(false)

const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  document.documentElement.classList.toggle('dark')
}

const fetchModels = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/models`)
    const data = await response.json()
    if (data.error) {
      throw new Error(data.error)
    }
    models.value = data
    console.log('Modelos cargados:', data)
  } catch (error) {
    console.error('Error al cargar modelos:', error)
  }
}

const handleServiceChange = async (event) => {
  selectedService.value = event.target.value
  selectedModel.value = ''
  if (!models.value[selectedService.value]) {
    await fetchModels()
  }
}

const handleModelChange = (event) => {
  selectedModel.value = event.target.value
}

const sendMessage = async () => {
  if (!selectedModel.value || !currentMessage.value.trim()) return
  
  try {
    isLoading.value = true
    const userMessage = { role: 'user', content: currentMessage.value }
    messages.value.push(userMessage)
    
    const response = await fetch(`${API_BASE_URL}/chat/session-1`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: selectedModel.value,
        service: selectedService.value,
        message: currentMessage.value
      })
    })
    
    const data = await response.json()
    if (data.error) {
      throw new Error(data.error)
    }
    
    const assistantMessage = { role: 'assistant', content: data.response }
    messages.value.push(assistantMessage)
    currentMessage.value = ''
  } catch (error) {
    console.error('Error al enviar mensaje:', error)
    // Eliminar el mensaje del usuario si hubo un error
    messages.value.pop()
  } finally {
    isLoading.value = false
  }
}

// Cargar modelos y detectar tema al iniciar
onMounted(async () => {
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    isDarkMode.value = true
    document.documentElement.classList.add('dark')
  }
  await fetchModels()
})
</script>

<template>
  <div class="h-screen flex bg-white dark:bg-dark transition-colors duration-200">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="flex items-center justify-between mb-8">
        <h1 class="text-2xl font-bold">GPT Local</h1>
        <button @click="toggleDarkMode" class="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-dark-lighter">
          <MoonIcon v-if="!isDarkMode" class="h-6 w-6" />
          <SunIcon v-else class="h-6 w-6" />
        </button>
      </div>
      
      <!-- Model Selection -->
      <div class="mb-6">
        <h2 class="text-lg font-semibold mb-2">Modelos</h2>
        <select 
          class="input-field mb-2" 
          v-model="selectedService"
          @change="handleServiceChange"
        >
          <option value="">Seleccionar servicio</option>
          <option value="ollama">Ollama</option>
          <option value="gpt4all">GPT4All</option>
        </select>
        
        <select 
          class="input-field"
          v-model="selectedModel"
          @change="handleModelChange"
          :disabled="!selectedService || !models[selectedService]?.length"
        >
          <option value="">Seleccionar modelo</option>
          <option 
            v-for="model in models[selectedService] || []" 
            :key="model" 
            :value="model"
          >
            {{ model }}
          </option>
        </select>
      </div>
      
      <!-- Configuration -->
      <div class="mb-6">
        <h2 class="text-lg font-semibold mb-2">Configuración</h2>
        <div class="space-y-2">
          <div>
            <label class="block text-sm mb-1">Temperatura</label>
            <input 
              type="range" 
              min="0" 
              max="1" 
              step="0.1" 
              class="w-full"
              value="0.7"
            />
          </div>
          <div>
            <label class="block text-sm mb-1">Max Tokens</label>
            <input 
              type="number" 
              class="input-field"
              value="2000"
            />
          </div>
        </div>
      </div>
      
      <!-- Conversation History -->
      <div>
        <h2 class="text-lg font-semibold mb-2">Historial</h2>
        <div class="space-y-2">
          <!-- Placeholder para el historial -->
        </div>
      </div>
    </aside>
    
    <!-- Main Content -->
    <main class="main-content">
      <!-- Chat Messages -->
      <div class="chat-container">
        <div class="chat-messages">
          <div 
            v-for="(message, index) in messages" 
            :key="index"
            :class="[
              'chat-message',
              message.role === 'user' ? 'chat-message-user' : 'chat-message-assistant'
            ]"
          >
            <p class="whitespace-pre-wrap">{{ message.content }}</p>
          </div>
        </div>
      </div>
      
      <!-- Input Area -->
      <div class="input-container">
        <div class="input-wrapper">
          <input 
            type="text" 
            class="input-field flex-grow"
            placeholder="Escribe tu mensaje..."
            v-model="currentMessage"
            @keyup.enter="sendMessage"
            :disabled="!selectedModel || isLoading"
          />
          <button 
            class="btn btn-primary whitespace-nowrap"
            @click="sendMessage"
            :disabled="!selectedModel || !currentMessage.trim() || isLoading"
          >
            {{ isLoading ? 'Enviando...' : 'Enviar' }}
          </button>
        </div>
      </div>
    </main>
  </div>
</template>
