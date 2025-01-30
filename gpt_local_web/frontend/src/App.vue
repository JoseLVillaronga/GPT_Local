<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { MoonIcon, SunIcon } from '@heroicons/vue/24/outline'
import { API_BASE_URL } from './config'

const isDarkMode = ref(false)
const models = ref([])
const selectedModel = ref('')
const currentMessage = ref('')
const messages = ref([])
const isLoading = ref(false)
const error = ref(null)
const conversations = ref([])
const sessionId = ref(null)
const chatContainer = ref(null)
const isExporting = ref(false)
const exportStatus = ref('')

// Función para cargar modelos
const fetchModels = async () => {
  try {
    error.value = ''
    isLoading.value = true
    const response = await fetch(`${API_BASE_URL}/models`)
    const data = await response.json()
    
    if (data.error) {
      throw new Error(data.error)
    }
    
    models.value = data.models || []
    console.log('Modelos disponibles:', models.value)
    
    if (models.value.length === 0) {
      error.value = 'No hay modelos disponibles'
    }
  } catch (error) {
    console.error('Error al cargar modelos:', error)
    error.value = `Error al cargar modelos: ${error.message}`
  } finally {
    isLoading.value = false
  }
}

// Función para cargar conversaciones guardadas
const fetchConversations = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/conversations`)
    const data = await response.json()
    if (!data.error) {
      conversations.value = data
    }
  } catch (e) {
    console.error('Error al cargar conversaciones:', e)
  }
}

// Función para cargar una conversación
const loadConversation = async (conversationId) => {
  try {
    // Si hay una sesión activa con mensajes, preguntar si quiere guardarla
    if (sessionId.value && messages.value.length > 0) {
      if (confirm('¿Deseas exportar la conversación actual antes de cargar la histórica?')) {
        await exportConversation()
      }
    }

    // Crear una nueva sesión para la conversación histórica
    sessionId.value = 'new'
    const response = await fetch(`${API_BASE_URL}/conversations/${conversationId}`)
    const data = await response.json()
    if (!data.error) {
      messages.value = data.messages || []
      selectedModel.value = data.model || ''
      
      // Inicializar nueva sesión con el modelo correcto
      if (selectedModel.value) {
        const chatResponse = await fetch(`${API_BASE_URL}/chat/${sessionId.value}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            message: '',
            model: selectedModel.value,
            service: data.service || 'gpt4all'
          })
        })
        const chatData = await chatResponse.json()
        if (chatData.session_id) {
          sessionId.value = chatData.session_id
          console.log('Nueva sesión creada:', sessionId.value)
        }
      }
      console.log('Conversación histórica cargada:', data)
    }
  } catch (e) {
    console.error('Error al cargar conversación:', e)
    error.value = `Error al cargar conversación: ${e.message}`
  }
}

// Función para exportar la conversación actual
const exportConversation = async () => {
  console.log('Intentando exportar conversación...')
  console.log('Estado actual:', {
    sessionId: sessionId.value,
    messages: messages.value,
    selectedModel: selectedModel.value,
    isExporting: isExporting.value
  })
  
  if (!sessionId.value) {
    console.error('No hay sesión activa')
    exportStatus.value = '✗ No hay sesión activa'
    return
  }
  
  if (messages.value.length === 0) {
    console.error('No hay mensajes para exportar')
    exportStatus.value = '✗ No hay mensajes para exportar'
    return
  }
  
  try {
    isExporting.value = true
    exportStatus.value = ''
    
    console.log('Enviando petición de exportación para sesión:', sessionId.value)
    const response = await fetch(`${API_BASE_URL}/conversations/${sessionId.value}/export`, {
      method: 'POST'
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`)
    }
    
    const data = await response.json()
    console.log('Respuesta de exportación:', data)
    
    if (data.filename) {
      exportStatus.value = `✓ Conversación exportada como: ${data.filename}`
      await fetchConversations() // Actualizar lista de conversaciones
    } else {
      throw new Error('No se recibió nombre de archivo en la respuesta')
    }
  } catch (e) {
    console.error('Error al exportar conversación:', e)
    exportStatus.value = `✗ ${e.message}`
  } finally {
    isExporting.value = false
    // Limpiar mensaje de éxito después de 5 segundos
    if (exportStatus.value.startsWith('✓')) {
      setTimeout(() => {
        exportStatus.value = ''
      }, 5000)
    }
  }
}

// Función para manejar cambio de modelo
const handleModelChange = (event) => {
  selectedModel.value = event.target.value
  error.value = ''
}

// Función para enviar un mensaje
const sendMessage = async () => {
  if (!currentMessage.value.trim() || !selectedModel.value || isLoading.value) return
  
  const userMessage = currentMessage.value.trim()
  currentMessage.value = ''
  isLoading.value = true
  error.value = null
  
  // Agregar mensaje del usuario
  messages.value.push({
    role: 'user',
    content: userMessage
  })

  // Scroll to bottom
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/chat/${sessionId.value || 'new'}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: userMessage,
        model: selectedModel.value
      })
    })
    
    const data = await response.json()
    if (data.error) {
      throw new Error(data.error)
    }
    
    if (data.response) {
      // Agregar respuesta del asistente
      messages.value.push({
        role: 'assistant',
        content: data.response
      })
      
      // Actualizar ID de sesión si es nuevo
      if (!sessionId.value) {
        sessionId.value = data.session_id
      }

      // Scroll to bottom after assistant response
      await nextTick()
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    }
  } catch (e) {
    console.error('Error al enviar mensaje:', e)
    error.value = `Error: ${e.message}`
  } finally {
    isLoading.value = false
  }
}

// Función para cambiar modo oscuro
const toggleDarkMode = () => {
  isDarkMode.value = !isDarkMode.value
  document.documentElement.classList.toggle('dark')
}

// Cargar datos iniciales
onMounted(async () => {
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    isDarkMode.value = true
  }
  await fetchModels()
  await fetchConversations()
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
      <div class="mb-4">
        <label class="block text-sm font-medium mb-2">
          Modelo
        </label>
        <select 
          v-model="selectedModel"
          @change="handleModelChange"
          class="w-full p-2 rounded-lg border border-gray-300 dark:border-gray-600 
                 bg-white dark:bg-gray-700 focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Seleccionar modelo</option>
          <option v-for="model in models" :key="model" :value="model">
            {{ model }}
          </option>
        </select>
      </div>

      <!-- Conversations List -->
      <div class="mt-8">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-semibold">Conversaciones</h2>
          <div class="flex flex-col items-end">
            <button 
              @click="exportConversation" 
              class="text-sm px-2 py-1 rounded bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!sessionId || messages.length === 0 || isExporting"
            >
              <span v-if="isExporting">Exportando...</span>
              <span v-else>Exportar</span>
            </button>
            <div v-if="exportStatus" :class="[
              'text-xs mt-1',
              exportStatus.startsWith('✓') ? 'text-green-600' : 'text-red-600'
            ]">
              {{ exportStatus }}
            </div>
          </div>
        </div>
        <div class="space-y-2 max-h-[400px] overflow-y-auto">
          <button
            v-for="conv in conversations"
            :key="conv.id"
            @click="loadConversation(conv.id)"
            class="w-full p-2 text-left rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-sm"
          >
            <div class="font-medium">{{ conv.name }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">{{ conv.timestamp }}</div>
          </button>
        </div>
      </div>
    </aside>
    
    <!-- Main Content -->
    <main class="main-content">
      <!-- Chat Messages -->
      <div class="flex-1 overflow-y-auto p-4 space-y-4" ref="chatContainer">
        <template v-for="(message, index) in messages" :key="index">
          <div class="flex" :class="[
            message.role === 'user' ? 'justify-end' : 'justify-start'
          ]">
            <div :class="[
              'p-4 rounded-lg shadow-sm',
              message.role === 'user' 
                ? 'bg-blue-50 dark:bg-blue-900 dark:text-white' 
                : 'bg-gray-50 dark:bg-gray-800 dark:text-white',
              'max-w-[80%]'
            ]">
              <div class="text-xs text-gray-500 dark:text-gray-400 mb-1">
                {{ message.role === 'user' ? 'Tú' : 'Asistente' }}
              </div>
              <div class="whitespace-pre-wrap text-left">{{ message.content }}</div>
            </div>
          </div>
        </template>
        <div v-if="isLoading" class="flex justify-start">
          <div class="flex items-center space-x-2 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
            <div class="animate-pulse h-2 w-2 bg-gray-500 rounded-full"></div>
            <div class="animate-pulse h-2 w-2 bg-gray-500 rounded-full animation-delay-200"></div>
            <div class="animate-pulse h-2 w-2 bg-gray-500 rounded-full animation-delay-400"></div>
          </div>
        </div>
      </div>
      
      <!-- Input Area -->
      <div class="border-t border-gray-200 dark:border-gray-700 p-4 flex justify-center">
        <div class="flex space-x-2 min-w-[50vw] w-full max-w-3xl">
          <input 
            v-model="currentMessage"
            @keyup.enter="sendMessage"
            type="text"
            placeholder="Escribe un mensaje..."
            class="flex-1 p-2 border rounded-lg"
          />
          <button 
            @click="sendMessage"
            :disabled="!selectedModel"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50"
          >
            Enviar
          </button>
        </div>
      </div>
    </main>
  </div>
</template>
