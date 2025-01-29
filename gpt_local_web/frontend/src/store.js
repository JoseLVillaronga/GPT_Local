import { ref, reactive } from 'vue'
import { API_BASE_URL, DEFAULT_CONFIG } from './config'

export const useStore = () => {
  const messages = ref([])
  const models = reactive({
    ollama: [],
    gpt4all: []
  })
  const selectedService = ref('')
  const selectedModel = ref('')
  const config = reactive({ ...DEFAULT_CONFIG })
  const conversations = ref([])
  const isLoading = ref(false)
  const error = ref(null)

  const clearError = () => {
    error.value = null
  }

  // Cargar modelos disponibles
  const fetchModels = async () => {
    try {
      clearError()
      const response = await fetch(`${API_BASE_URL}/models`)
      const data = await response.json()
      
      if (data.error) {
        throw new Error(data.error)
      }
      
      if (data.ollama) models.ollama = data.ollama
      if (data.gpt4all) models.gpt4all = data.gpt4all
      
      console.log('Modelos cargados:', models)
    } catch (err) {
      error.value = `Error al cargar modelos: ${err.message}`
      console.error('Error al cargar modelos:', err)
    }
  }

  // Cargar conversaciones guardadas
  const fetchConversations = async () => {
    try {
      clearError()
      const response = await fetch(`${API_BASE_URL}/conversations`)
      const data = await response.json()
      
      if (data.error) {
        throw new Error(data.error)
      }
      
      conversations.value = data.conversations || []
    } catch (err) {
      error.value = `Error al cargar conversaciones: ${err.message}`
      console.error('Error al cargar conversaciones:', err)
    }
  }

  // Cargar una conversación específica
  const loadConversation = async (filename) => {
    try {
      clearError()
      const response = await fetch(`${API_BASE_URL}/conversations/${filename}`)
      const data = await response.json()
      
      if (data.error) {
        throw new Error(data.error)
      }
      
      if (data.messages) {
        messages.value = data.messages
        selectedModel.value = data.model
        selectedService.value = data.service
      }
    } catch (err) {
      error.value = `Error al cargar la conversación: ${err.message}`
      console.error('Error al cargar la conversación:', err)
    }
  }

  // Actualizar configuración
  const updateConfig = async (newConfig) => {
    try {
      clearError()
      Object.assign(config, newConfig)
    } catch (err) {
      error.value = `Error al actualizar la configuración: ${err.message}`
      console.error('Error al actualizar la configuración:', err)
    }
  }

  // Enviar mensaje
  const sendMessage = async (content) => {
    if (!selectedModel.value || !selectedService.value) {
      error.value = 'Por favor selecciona un modelo y servicio'
      return
    }

    try {
      clearError()
      isLoading.value = true
      
      const userMessage = { role: 'user', content }
      messages.value.push(userMessage)

      const response = await fetch(`${API_BASE_URL}/chat/session-1`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: selectedModel.value,
          service: selectedService.value,
          message: content
        })
      })

      const data = await response.json()
      
      if (data.error) {
        throw new Error(data.error)
      }

      const assistantMessage = { role: 'assistant', content: data.response }
      messages.value.push(assistantMessage)
      
      console.log('Respuesta recibida:', data)
    } catch (err) {
      error.value = `Error al enviar mensaje: ${err.message}`
      console.error('Error al enviar mensaje:', err)
      
      // Eliminar el mensaje del usuario si hubo un error
      messages.value.pop()
    } finally {
      isLoading.value = false
    }
  }

  return {
    messages,
    models,
    selectedService,
    selectedModel,
    config,
    conversations,
    isLoading,
    error,
    fetchModels,
    fetchConversations,
    loadConversation,
    updateConfig,
    sendMessage
  }
}

// Crear una única instancia del store
const store = useStore()
export default store
