from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
import sys
import os
import logging
import requests
import time
import uuid

# Agregar el directorio padre al path para poder importar test_local_llms
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BACKEND_DIR))
sys.path.append(PROJECT_ROOT)
from test_local_llms import ChatHistory, ChatStats, ChatConfig, ChatExporter, get_gpt4all_models

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BACKEND_DIR, 'backend.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Crear directorio de exportación si no existe
CHAT_HISTORY_DIR = os.path.join(PROJECT_ROOT, "chat_history")
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

app = FastAPI(title="GPT Local API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de datos
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    model: str
    message: str
    service: Optional[str] = "gpt4all"

class ConfigUpdate(BaseModel):
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None

# Almacenamiento en memoria de las sesiones activas
active_sessions: Dict[str, tuple[ChatHistory, ChatStats, ChatConfig]] = {}

@app.get("/api/models")
async def get_models():
    """Obtener lista de modelos disponibles de la API local"""
    try:
        logger.info("Obteniendo lista de modelos disponibles...")
        models = get_gpt4all_models()
        
        if not models:
            logger.warning("No se encontraron modelos disponibles")
            return {"error": "No se encontraron modelos disponibles"}
            
        logger.info(f"Modelos encontrados: {models}")
        
        # Formatear los modelos como lo espera el frontend
        formatted_models = []
        for model in models:
            model_name = model.get('name', model.get('id', 'Unknown'))
            formatted_models.append(model_name)
            
        return {
            "models": formatted_models
        }
    except ImportError as e:
        logger.error(f"Error al importar módulo: {str(e)}")
        return {"error": "Error al cargar el módulo de modelos"}
    except Exception as e:
        logger.error(f"Error al obtener modelos: {str(e)}")
        return {"error": f"Error al obtener modelos: {str(e)}"}

@app.post("/api/chat/{session_id}")
async def chat(session_id: str, request: ChatRequest):
    """Endpoint para chat no streaming"""
    logger.info(f"Nueva solicitud de chat - Sesión: {session_id}, Modelo: {request.model}")
    
    try:
        # Si es una nueva sesión, generar un nuevo ID
        if session_id == 'new':
            session_id = str(uuid.uuid4())
            logger.info(f"Creando nueva sesión con ID: {session_id}")
            
        # Si la sesión no existe, crearla
        if session_id not in active_sessions:
            history = ChatHistory()
            history.start_new_chat(request.model, request.service)  # Esto inicializará el timestamp
            stats = ChatStats()
            config = ChatConfig()
            # Aumentar el límite de tokens para respuestas más largas
            config.max_tokens = 2000
            active_sessions[session_id] = (history, stats, config)
        
        history, stats, config = active_sessions[session_id]
        
        # Agregar mensaje del usuario al historial
        history.add_message("user", request.message)
        stats.increment_messages()
        
        start_time = time.time()
        
        # Hacer la llamada a la API de GPT4All
        try:
            response = requests.post(
                'http://127.0.0.1:4891/v1/chat/completions',
                json={
                    'model': request.model,
                    'messages': history.get_history(),
                    'temperature': config.temperature,
                    'max_tokens': config.max_tokens
                }
            )
            
            if response.status_code == 200:
                response_json = response.json()
                if 'choices' in response_json and len(response_json['choices']) > 0:
                    assistant_response = response_json['choices'][0]['message']['content'].strip()
                    # Agregar respuesta del asistente al historial
                    history.add_message("assistant", assistant_response)
                    stats.add_response_time(time.time() - start_time)
                    
                    logger.info("Respuesta generada exitosamente")
                    return {
                        "response": assistant_response,
                        "session_id": session_id,
                        "stats": stats.get_summary()
                    }
                else:
                    raise ValueError("No se recibió una respuesta válida del modelo")
            else:
                raise ValueError(f"Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con GPT4All: {str(e)}")
            raise ValueError(f"Error de conexión con GPT4All: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error en chat: {str(e)}")
        return {"error": str(e)}

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """Endpoint para chat streaming via WebSocket"""
    await websocket.accept()
    logger.info(f"Nueva conexión WebSocket establecida - Sesión: {session_id}")
    
    try:
        if session_id not in active_sessions:
            history = ChatHistory()
            stats = ChatStats()
            config = ChatConfig()
            active_sessions[session_id] = (history, stats, config)
            logger.info(f"Nueva sesión WebSocket creada: {session_id}")
        
        history, stats, config = active_sessions[session_id]
        
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            logger.info(f"Mensaje WebSocket recibido: {request}")
            
            # Iniciar nuevo chat si es necesario
            if request.get("action") == "start":
                history.start_new_chat(request["model"], request["service"])
                await websocket.send_json({"status": "started"})
                logger.info("Nuevo chat iniciado via WebSocket")
                continue
            
            # Procesar mensaje
            try:
                if request["service"].lower() == "ollama":
                    from test_local_llms import stream_chat_with_ollama
                    logger.info("Iniciando chat streaming con Ollama...")
                    async for chunk in stream_chat_with_ollama(
                        request["model"],
                        request["message"],
                        history,
                        stats,
                        config
                    ):
                        await websocket.send_json({
                            "chunk": chunk,
                            "stats": stats.get_summary()
                        })
                else:
                    from test_local_llms import chat_with_gpt4all
                    logger.info("Iniciando chat con GPT4All...")
                    response = chat_with_gpt4all(
                        request["model"],
                        request["message"],
                        history,
                        stats,
                        config
                    )
                    await websocket.send_json({
                        "response": response,
                        "stats": stats.get_summary()
                    })
                
                logger.info("Respuesta enviada exitosamente via WebSocket")
            except Exception as e:
                logger.error(f"Error en el chat WebSocket: {str(e)}")
                await websocket.send_json({"error": str(e)})
                
    except WebSocketDisconnect:
        logger.info(f"Conexión WebSocket cerrada - Sesión: {session_id}")
        # Guardar la conversación al desconectar
        if session_id in active_sessions:
            history, stats, _ = active_sessions[session_id]
            ChatExporter.export_conversation(history, stats)
            del active_sessions[session_id]

@app.get("/api/conversations")
async def get_conversations():
    """Obtener lista de conversaciones guardadas"""
    try:
        chat_dir = os.path.join(PROJECT_ROOT, "chat_history")
        if not os.path.exists(chat_dir):
            return []
            
        conversations = []
        for filename in os.listdir(chat_dir):
            if filename.endswith('.md'):
                filepath = os.path.join(chat_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        # Leer las primeras líneas para obtener el timestamp
                        lines = f.readlines()
                        if len(lines) > 1:  # Asegurarse que hay al menos 2 líneas
                            timestamp = lines[1].replace('Fecha: ', '').strip()
                            conversations.append({
                                'id': filename[:-3],  # Remover extensión .md
                                'name': filename[:-3],  # Nombre sin extensión
                                'timestamp': timestamp  # Agregar timestamp
                            })
                except Exception as e:
                    logger.error(f"Error al leer archivo {filename}: {str(e)}")
                    continue
                    
        # Ordenar por timestamp descendente (más reciente primero)
        conversations.sort(key=lambda x: x['timestamp'], reverse=True)
        return conversations
        
    except Exception as e:
        logger.error(f"Error al listar conversaciones: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{session_id}/export")
async def export_conversation(session_id: str):
    """Exportar una conversación a archivo markdown"""
    logger.info(f"Intentando exportar conversación para sesión: {session_id}")
    
    try:
        if session_id not in active_sessions:
            logger.error(f"Sesión no encontrada: {session_id}")
            raise HTTPException(status_code=404, detail=f"Sesión no encontrada: {session_id}")
            
        history, stats, _ = active_sessions[session_id]
        logger.info(f"Exportando conversación con modelo {history.model_name} y servicio {history.service_name}")
        
        filename = ChatExporter.export_conversation(history, stats)
        logger.info(f"Conversación exportada exitosamente a: {filename}")
        
        return {"filename": os.path.basename(filename)}
    except Exception as e:
        logger.error(f"Error al exportar conversación: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al exportar conversación: {str(e)}")

@app.get("/api/conversations/{conversation_id}")
async def load_conversation(conversation_id: str):
    """Cargar una conversación guardada"""
    try:
        # El conversation_id es el nombre del archivo sin extensión
        filename = f"{conversation_id}.md"
        chat_dir = os.path.join(PROJECT_ROOT, "chat_history")
        filepath = os.path.join(chat_dir, filename)
        
        logger.info(f"Intentando cargar conversación desde: {filepath}")
        
        if not os.path.exists(filepath):
            logger.error(f"Archivo no encontrado: {filepath}")
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extraer información relevante del contenido
        lines = content.split('\n')
        model_info = lines[0].replace('# Conversación con ', '').split(' (')
        model_name = model_info[0]
        service_name = model_info[1].replace(')', '')
        
        # Extraer los mensajes
        messages = []
        current_role = None
        current_message = []
        
        for line in lines:
            if line.startswith('### Usuario:'):
                if current_role and current_message:
                    messages.append({
                        'role': 'assistant' if current_role == 'Asistente' else 'user',
                        'content': '\n'.join(current_message).strip()
                    })
                current_role = 'Usuario'
                current_message = []
            elif line.startswith('### Asistente:'):
                if current_role and current_message:
                    messages.append({
                        'role': 'assistant' if current_role == 'Asistente' else 'user',
                        'content': '\n'.join(current_message).strip()
                    })
                current_role = 'Asistente'
                current_message = []
            elif current_role and line and not line.startswith('#'):
                current_message.append(line)
                
        # Agregar el último mensaje si existe
        if current_role and current_message:
            messages.append({
                'role': 'assistant' if current_role == 'Asistente' else 'user',
                'content': '\n'.join(current_message).strip()
            })
            
        logger.info(f"Conversación cargada exitosamente: {len(messages)} mensajes")
        return {
            "messages": messages,
            "model": model_name,
            "service": service_name,
            "timestamp": lines[1].replace('Fecha: ', '')
        }
            
    except Exception as e:
        logger.error(f"Error al cargar conversación: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al cargar conversación: {str(e)}")

@app.get("/api/conversations/{session_id}/info")
async def get_session_info(session_id: str):
    """Obtener información de la sesión actual"""
    try:
        if session_id not in active_sessions:
            raise ValueError("Sesión no encontrada")
            
        history, stats, config = active_sessions[session_id]
        return {
            "model": history.model,
            "service": history.service,
            "message_count": len(history.get_history()),
            "stats": stats.get_summary()
        }
    except Exception as e:
        logger.error(f"Error al obtener información de sesión: {str(e)}")
        return {"error": str(e)}

@app.put("/api/config/{session_id}")
async def update_config(session_id: str, config_update: ConfigUpdate):
    """Actualizar configuración de una sesión"""
    logger.info(f"Actualizando configuración - Sesión: {session_id}")
    
    if session_id not in active_sessions:
        logger.error(f"Sesión no encontrada: {session_id}")
        return {"error": "Sesión no encontrada"}
    
    _, _, config = active_sessions[session_id]
    
    if config_update.temperature is not None:
        config.temperature = config_update.temperature
    if config_update.max_tokens is not None:
        config.max_tokens = config_update.max_tokens
    if config_update.top_p is not None:
        config.top_p = config_update.top_p
    if config_update.frequency_penalty is not None:
        config.frequency_penalty = config_update.frequency_penalty
    if config_update.presence_penalty is not None:
        config.presence_penalty = config_update.presence_penalty
    
    logger.info(f"Configuración actualizada: {config.__dict__}")
    return {"status": "ok", "config": config.__dict__}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
