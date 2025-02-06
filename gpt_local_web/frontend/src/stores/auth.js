import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_URL = 'http://localhost:8000'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    apiKey: localStorage.getItem('apiKey') || null,
    userStatus: null,
    models: [],
    error: null,
    loading: false
  }),

  getters: {
    isAuthenticated: (state) => !!state.apiKey,
  },

  actions: {
    async createTestUser() {
      this.loading = true
      this.error = null
      
      try {
        const response = await fetch(`${API_URL}/api/test-user/new`, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Error creating test user')
        }

        const data = await response.json()
        this.apiKey = data.api_key
        localStorage.setItem('apiKey', data.api_key)
        
        // Intentar obtener el estado del usuario después de crear
        try {
          await this.checkUserStatus()
          await this.fetchModels()
        } catch (statusError) {
          console.error('Error getting initial user status:', statusError)
        }
        
        return data
      } catch (error) {
        console.error('Error creating test user:', error)
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async checkUserStatus() {
      try {
        if (!this.apiKey) {
          throw new Error('No API key available')
        }

        const response = await fetch(`${API_URL}/api/test-user/status`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-API-Key': this.apiKey
          }
        })

        if (!response.ok) {
          if (response.status === 401) {
            this.clearApiKey()
            throw new Error('Invalid API key')
          }
          const error = await response.json()
          throw new Error(error.detail || 'Error checking user status')
        }

        const data = await response.json()
        this.userStatus = data
        return data
      } catch (error) {
        console.error('Error checking user status:', error)
        throw error
      }
    },

    async fetchModels() {
      try {
        const response = await fetch(`${API_URL}/api/models`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...(this.apiKey && { 'X-API-Key': this.apiKey })
          }
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Error fetching models')
        }

        const data = await response.json()
        this.models = data.models || []
        return this.models
      } catch (error) {
        console.error('Error fetching models:', error)
        throw error
      }
    },

    async createSession(model, service = 'gpt4all') {
      if (!this.apiKey) throw new Error('No API key available')
      
      try {
        const response = await fetch(`${API_URL}/api/session/new`, {
          method: 'POST',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-API-Key': this.apiKey
          },
          body: JSON.stringify({
            model,
            service
          })
        })
        
        if (!response.ok) {
          const data = await response.json()
          throw new Error(data.detail || 'Error creating session')
        }
        
        const data = await response.json()
        return data
      } catch (error) {
        console.error('Error creating session:', error)
        this.error = error.message
        throw error
      }
    },

    async fetchWithAuth(url, options = {}) {
      if (!this.apiKey) throw new Error('No API key available')
      
      const headers = {
        'Accept': 'application/json',
        ...options.headers,
        'X-API-Key': this.apiKey
      }
      
      const response = await fetch(url, {
        ...options,
        headers
      })

      if (!response.ok && response.status === 403) {
        this.logout()
        throw new Error('Not authenticated')
      }

      return response
    },

    setApiKey(key) {
      this.apiKey = key
      localStorage.setItem('apiKey', key)
    },

    clearApiKey() {
      this.apiKey = null
      this.userStatus = null
      this.models = []
      localStorage.removeItem('apiKey')
    },

    logout() {
      this.apiKey = null
      this.userStatus = null
      this.models = []
      localStorage.removeItem('apiKey')
    }
  }
})
