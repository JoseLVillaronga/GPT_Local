# GPT Local

![Estado](https://img.shields.io/badge/estado-beta-green)
![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-brightgreen)
![Framework](https://img.shields.io/badge/framework-GPT4All-orange)

Sistema de chat local que utiliza la API de GPT4All para interactuar con modelos de lenguaje de manera eficiente y flexible.

## 🌟 Características

- 💬 Chat interactivo con modelos locales
- 🔄 Soporte para múltiples modelos de GPT4All
- 📊 Sistema de métricas y estadísticas de uso
- 💾 Persistencia de conversaciones
- 🌐 Interfaz web moderna (Vue.js)
- 🎨 Modo oscuro/claro
- ⚙️ Configuración flexible de parámetros

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.8+
- Node.js 16+
- GPT4All instalado localmente

### Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/JoseLVillaronga/GPT_Local.git
cd GPT_Local
```

2. Instalar dependencias de Python:
```bash
pip install -r requirements.txt
```

3. Instalar dependencias del frontend:
```bash
cd gpt_local_web/frontend
npm install
```

### Ejecución

1. Iniciar el chat en consola:
```bash
python test_local_llms.py
```

2. Iniciar la aplicación web:
```bash
# Backend
cd gpt_local_web
python app.py

# Frontend (en otra terminal)
cd gpt_local_web/frontend
npm run dev
```

## 📚 Ejemplos de Uso

### Chat en Consola

```python
# Ejemplo de sesión de chat básica
python test_local_llms.py

# Con configuración específica
python test_local_llms.py --model "orca-mini-3b" --temperature 0.7

# Exportar conversación
python test_local_llms.py --export markdown
```

### Configuraciones Comunes

```python
# Configuración para respuestas creativas
{
    'temperature': 0.9,
    'max_tokens': 300,
    'top_p': 0.95
}

# Configuración para respuestas precisas
{
    'temperature': 0.3,
    'max_tokens': 150,
    'top_p': 0.8
}
```

### API Web

```javascript
// Ejemplo de llamada a la API
const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        message: "¿Cómo funciona GPT4All?",
        model: "orca-mini-3b",
        config: {
            temperature: 0.7
        }
    })
});
```

## 🔧 Troubleshooting

### Requerimientos de Sistema
- **RAM**: Mínimo 8GB, Recomendado 16GB+
- **CPU**: Procesador moderno con soporte AVX2
- **Almacenamiento**: 10GB+ para modelos y datos

### Problemas Comunes

1. **Error: Model not found**
   ```
   Solución: Verificar que el modelo está descargado en la carpeta correcta
   Por defecto: ~/.local/share/nomic.ai/GPT4All/
   ```

2. **Error: CUDA not available**
   ```
   Solución: La aceleración GPU es opcional. El sistema funciona con CPU.
   Para habilitar GPU, instalar CUDA toolkit y pytorch con soporte CUDA.
   ```

3. **Error: API connection refused**
   ```
   Solución: Verificar que el backend está corriendo en puerto 8000
   Check: netstat -tulpn | grep 8000
   ```

## 🗺️ Roadmap

### Fase Actual (Beta)
- [x] Implementación básica del chat
- [x] Interfaz web funcional
- [x] Sistema de persistencia
- [x] Métricas básicas

### Próximas Características
- [ ] Soporte para múltiples sesiones simultáneas
- [ ] Mejoras en la interfaz web
- [ ] Sistema de caché para respuestas frecuentes
- [ ] Integración con más modelos

### Investigación Futura
- [ ] Cooperación entre diferentes modelos
- [ ] Optimización de parámetros automática
- [ ] Sistema de fine-tuning local

## 🛠️ Estructura del Proyecto

```
GPT_Local/
├── test_local_llms.py      # Cliente de chat en consola
├── requirements.txt        # Dependencias Python
├── docs/                  # Documentación
├── chat_history/         # Historial de conversaciones
├── chat_exports/        # Exportaciones de chat
└── gpt_local_web/      # Aplicación web
    ├── frontend/      # Frontend Vue.js
    └── backend/      # API REST
```

## 📝 Funcionalidades Principales

### Cliente de Consola (`test_local_llms.py`)
- Selección interactiva de modelos
- Configuración de parámetros de generación
- Exportación de conversaciones
- Estadísticas de uso

### Interfaz Web
- Chat en tiempo real
- Gestión de sesiones
- Exportación de conversaciones
- Interfaz adaptativa (claro/oscuro)

## ⚙️ Configuración

Los parámetros de generación se pueden ajustar a través de presets predefinidos o manualmente:

```python
{
    'temperature': 0.7,
    'max_tokens': 2000,
    'top_p': 1,
    'frequency_penalty': 0,
    'presence_penalty': 0
}
```

## 📊 Métricas y Estadísticas

El sistema registra:
- Tokens totales consumidos
- Tiempo de respuesta promedio
- Número total de mensajes
- Duración total de la sesión

## 🔄 Estado del Proyecto

Actualmente en desarrollo activo con enfoque en:
- Optimización de la interfaz web
- Mejora del sistema de persistencia
- Evaluación de diferentes modelos
- Documentación de mejores prácticas

## 📜 Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [LICENSE](LICENSE) para más detalles.

La Licencia MIT es una licencia de software permisiva que permite:
- ✔️ Uso comercial
- ✔️ Modificación
- ✔️ Distribución
- ✔️ Uso privado

Solo requiere mantener el aviso de copyright y la licencia en cualquier copia o parte sustancial del Software.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abrir un issue para discutir cambios mayores.

## ✨ Agradecimientos

- Equipo de GPT4All por su excelente framework
- Comunidad de desarrolladores de modelos de lenguaje locales
