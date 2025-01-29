import { createApp } from 'vue'
import App from './App.vue'
import store from './store'
import './style.css'

const app = createApp(App)

// Hacer el store disponible globalmente
app.config.globalProperties.$store = store

app.mount('#app')
