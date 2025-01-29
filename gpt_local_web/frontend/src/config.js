// API base URL
export const API_BASE_URL = 'http://localhost:8000/api'

// Configuración por defecto para los modelos
export const DEFAULT_CONFIG = {
    temperature: 0.7,
    max_tokens: 2000,
    top_p: 1,
    frequency_penalty: 0,
    presence_penalty: 0
}

// Configuración de la interfaz
export const UI_CONFIG = {
    messageMaxLength: 4000,
    historyMaxLength: 100,
    typingDelay: 50,
    streamingEnabled: true
}

// URL de conexión WebSocket
export const WS_BASE_URL = 'ws://localhost:8000/ws'

// Servicios disponibles
export const SERVICES = {
  OLLAMA: 'ollama',
  GPT4ALL: 'gpt4all'
}
