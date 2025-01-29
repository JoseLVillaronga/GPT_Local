from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
import sys
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio padre al path para importar el módulo de chat
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from test_local_llms import ChatConfig, ChatHistory, ChatStats, ChatExporter

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
    service: str
    message: str

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
    """Obtener lista de modelos disponibles"""
    try:
        from test_local_llms import get_ollama_models, get_gpt4all_models
        
        logger.info("Obteniendo lista de modelos...")
        ollama_models = get_ollama_models()
        gpt4all_models = get_gpt4all_models()
        
        logger.info(f"Modelos Ollama encontrados: {ollama_models}")
        logger.info(f"Modelos GPT4All encontrados: {gpt4all_models}")
        
        return {
            "ollama": ollama_models,
            "gpt4all": gpt4all_models
        }
    except Exception as e:
        logger.error(f"Error al obtener modelos: {str(e)}")
        return {"error": str(e)}

@app.post("/api/chat/{session_id}")
async def chat(session_id: str, request: ChatRequest):
    """Endpoint para chat no streaming"""
    logger.info(f"Nueva solicitud de chat - Sesión: {session_id}, Modelo: {request.model}, Servicio: {request.service}")
    
    try:
        if session_id not in active_sessions:
            history = ChatHistory()
            history.start_new_chat(request.model, request.service)
            stats = ChatStats()
            config = ChatConfig()
            active_sessions[session_id] = (history, stats, config)
            logger.info(f"Nueva sesión creada: {session_id}")
        
        history, stats, config = active_sessions[session_id]
        
        # Lógica de chat según el servicio
        if request.service.lower() == "ollama":
            from test_local_llms import chat_with_ollama
            logger.info("Iniciando chat con Ollama...")
            response = chat_with_ollama(request.model, request.message, history, stats, config)
        else:
            from test_local_llms import chat_with_gpt4all
            logger.info("Iniciando chat con GPT4All...")
            response = chat_with_gpt4all(request.model, request.message, history, stats, config)
        
        logger.info("Respuesta generada exitosamente")
        return {
            "response": response,
            "stats": stats.get_summary()
        }
    except Exception as e:
        logger.error(f"Error en el chat: {str(e)}")
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
async def list_conversations():
    """Listar conversaciones guardadas"""
    try:
        logger.info("Listando conversaciones guardadas...")
        conversations = ChatHistory.list_saved_conversations()
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Error al listar conversaciones: {str(e)}")
        return {"error": str(e)}

@app.get("/api/conversations/{filename}")
async def get_conversation(filename: str):
    """Obtener contenido de una conversación"""
    try:
        logger.info(f"Obteniendo conversación: {filename}")
        filepath = os.path.join(ChatExporter.CHAT_DIR, filename)
        if filename.endswith('.pkl'):
            chat = ChatHistory.load_conversation(filepath)
            if chat:
                return {
                    "model": chat.model_name,
                    "service": chat.service_name,
                    "timestamp": chat.timestamp,
                    "messages": chat.messages
                }
        else:  # .md o .txt
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content}
    except Exception as e:
        logger.error(f"Error al obtener conversación: {str(e)}")
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
