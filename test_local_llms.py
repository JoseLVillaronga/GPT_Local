import requests
import json
from typing import List, Dict, Optional
import os
from datetime import datetime
import pickle
import time
import markdown

class ChatStats:
    def __init__(self):
        self.total_tokens: int = 0
        self.total_messages: int = 0
        self.start_time: float = time.time()
        self.response_times: List[float] = []
    
    def add_response_time(self, seconds: float):
        """Registra el tiempo de respuesta de una interacción"""
        self.response_times.append(seconds)
    
    def add_tokens(self, count: int):
        """Registra tokens consumidos"""
        self.total_tokens += count
    
    def increment_messages(self):
        """Incrementa el contador de mensajes"""
        self.total_messages += 1
    
    def get_summary(self) -> Dict:
        """Retorna un resumen de las estadísticas"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        return {
            'total_tokens': self.total_tokens,
            'total_messages': self.total_messages,
            'average_response_time': f"{avg_response_time:.2f}s",
            'total_time': f"{(time.time() - self.start_time):.2f}s"
        }

class ChatExporter:
    CHAT_DIR = "chat_history"  # Directorio unificado para todas las conversaciones
    
    @staticmethod
    def to_markdown(history: 'ChatHistory', stats: Optional['ChatStats'] = None) -> str:
        """Exporta la conversación a formato Markdown"""
        md_content = [
            f"# Conversación con {history.model_name} ({history.service_name})",
            f"Fecha: {history.timestamp}",
            ""
        ]
        
        if stats:
            stat_summary = stats.get_summary()
            md_content.extend([
                "## Estadísticas",
                f"- Total de mensajes: {stat_summary['total_messages']}",
                f"- Total de tokens: {stat_summary['total_tokens']}",
                f"- Tiempo promedio de respuesta: {stat_summary['average_response_time']}",
                f"- Tiempo total de conversación: {stat_summary['total_time']}",
                ""
            ])
        
        md_content.append("## Conversación")
        for msg in history.messages:
            role = "Usuario" if msg['role'] == 'user' else "Asistente"
            md_content.extend([
                f"### {role}:",
                msg['content'],
                ""
            ])
        
        return "\n".join(md_content)
    
    @staticmethod
    def to_text(history: 'ChatHistory') -> str:
        """Exporta la conversación a formato texto plano"""
        lines = [
            f"Conversación con {history.model_name} ({history.service_name})",
            f"Fecha: {history.timestamp}",
            "",
            "Conversación:",
            "-" * 50
        ]
        
        for msg in history.messages:
            role = "Usuario" if msg['role'] == 'user' else "Asistente"
            lines.extend([
                f"{role}:",
                msg['content'],
                "-" * 50
            ])
        
        return "\n".join(lines)
    
    @staticmethod
    def export_conversation(history: 'ChatHistory', 
                          stats: Optional['ChatStats'] = None,
                          format: str = 'markdown') -> str:
        """Exporta la conversación al formato especificado"""
        os.makedirs(ChatExporter.CHAT_DIR, exist_ok=True)
        
        content = ChatExporter.to_markdown(history, stats) if format == 'markdown' else ChatExporter.to_text(history)
        extension = 'md' if format == 'markdown' else 'txt'
        
        filename = f"{ChatExporter.CHAT_DIR}/{history.service_name}_{history.model_name}_{history.timestamp}.{extension}"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename

class ChatConfig:
    def __init__(self):
        self.temperature: float = 0.7
        self.max_tokens: int = 200
        self.top_p: float = 0.9
        self.frequency_penalty: float = 0.0
        self.presence_penalty: float = 0.0
        
        # Configuraciones predefinidas
        self.presets = {
            'creativo': {'temperature': 0.9, 'max_tokens': 300, 'top_p': 0.95},
            'preciso': {'temperature': 0.3, 'max_tokens': 150, 'top_p': 0.8},
            'balanceado': {'temperature': 0.7, 'max_tokens': 200, 'top_p': 0.9}
        }
    
    def load_preset(self, preset_name: str):
        """Carga una configuración predefinida"""
        if preset_name in self.presets:
            preset = self.presets[preset_name]
            for key, value in preset.items():
                setattr(self, key, value)
            print(f"\nConfiguración '{preset_name}' cargada")
        else:
            print("\nPreset no encontrado")
    
    def adjust_parameters(self):
        """Permite al usuario ajustar los parámetros de generación"""
        while True:
            print("\nConfiguración actual:")
            print(f"1. Temperatura: {self.temperature}")
            print(f"2. Tokens máximos: {self.max_tokens}")
            print(f"3. Top P: {self.top_p}")
            print(f"4. Penalización por frecuencia: {self.frequency_penalty}")
            print(f"5. Penalización por presencia: {self.presence_penalty}")
            print("6. Cargar preset")
            print("7. Volver")
            
            try:
                choice = int(input("\nElige una opción (1-7): "))
                if choice == 7:
                    break
                elif choice == 6:
                    print("\nPresets disponibles:")
                    for preset in self.presets:
                        print(f"- {preset}")
                    preset_name = input("\nElige un preset: ").lower()
                    self.load_preset(preset_name)
                elif 1 <= choice <= 5:
                    if choice == 1:
                        self.temperature = float(input("Nueva temperatura (0.0-1.0): "))
                    elif choice == 2:
                        self.max_tokens = int(input("Nuevos tokens máximos: "))
                    elif choice == 3:
                        self.top_p = float(input("Nuevo Top P (0.0-1.0): "))
                    elif choice == 4:
                        self.frequency_penalty = float(input("Nueva penalización por frecuencia (-2.0-2.0): "))
                    elif choice == 5:
                        self.presence_penalty = float(input("Nueva penalización por presencia (-2.0-2.0): "))
                else:
                    print("Opción no válida")
            except ValueError:
                print("Por favor, ingresa un valor válido")

class ChatHistory:
    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.model_name: str = ""
        self.service_name: str = ""
        self.timestamp: str = ""
    
    def start_new_chat(self, model_name: str, service_name: str):
        """Inicia un nuevo chat con información del modelo"""
        self.messages = []
        self.model_name = model_name
        self.service_name = service_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def add_message(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
    
    def get_history(self) -> List[Dict[str, str]]:
        return self.messages
    
    def clear(self):
        self.messages = []
    
    def save_conversation(self):
        """Guarda la conversación en un archivo"""
        if not self.messages:
            print("No hay mensajes para guardar")
            return
            
        os.makedirs(ChatExporter.CHAT_DIR, exist_ok=True)
        filename = f"{ChatExporter.CHAT_DIR}/{self.service_name}_{self.model_name}_{self.timestamp}.pkl"
        
        with open(filename, 'wb') as f:
            pickle.dump({
                'messages': self.messages,
                'model_name': self.model_name,
                'service_name': self.service_name,
                'timestamp': self.timestamp
            }, f)
        print(f"\nConversación guardada en: {filename}")
    
    @staticmethod
    def load_conversation(filename: str) -> Optional['ChatHistory']:
        """Carga una conversación desde un archivo"""
        try:
            with open(filename, 'rb') as f:
                data = pickle.load(f)
                
            chat = ChatHistory()
            chat.messages = data['messages']
            chat.model_name = data['model_name']
            chat.service_name = data['service_name']
            chat.timestamp = data['timestamp']
            return chat
        except Exception as e:
            print(f"Error al cargar la conversación: {str(e)}")
            return None
    
    @staticmethod
    def list_saved_conversations() -> List[str]:
        """Lista todas las conversaciones guardadas"""
        if not os.path.exists(ChatExporter.CHAT_DIR):
            return []
        return sorted([f for f in os.listdir(ChatExporter.CHAT_DIR) if f.endswith(('.pkl', '.md', '.txt'))])

def get_ollama_models():
    """Obtener lista de modelos disponibles en Ollama"""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json()
            return [model['name'] for model in models['models']]
        return []
    except Exception as e:
        print(f"Error al obtener modelos de Ollama: {str(e)}")
        return []

def get_gpt4all_models():
    """Obtener lista de modelos disponibles en GPT4All"""
    try:
        from gpt4all import GPT4All
        return GPT4All.list_models()
    except Exception as e:
        print(f"Error al obtener modelos de GPT4All: {str(e)}")
        return []

def select_model(models_list, service_name):
    """Permite al usuario seleccionar un modelo de la lista disponible"""
    print(f"\nModelos disponibles para {service_name}:")
    for idx, model in enumerate(models_list, 1):
        model_name = model.get('name', model.get('id', 'Unknown'))
        print(f"{idx}. {model_name}")
    
    while True:
        try:
            choice = int(input("\nElige un modelo (número): ")) - 1
            if 0 <= choice < len(models_list):
                selected = models_list[choice]
                return selected.get('name', selected.get('id'))
            print("Opción no válida")
        except ValueError:
            print("Por favor, ingresa un número válido")

def show_help():
    """Muestra la ayuda del chat"""
    print("\nComandos disponibles:")
    print("- salir: Termina la conversación")
    print("- clear: Limpia el historial de la conversación")
    print("- save: Guarda la conversación actual")
    print("- load: Carga una conversación guardada")
    print("- config: Ajusta los parámetros de generación")
    print("- help: Muestra esta ayuda")

def view_saved_conversation():
    """Permite ver el contenido de una conversación guardada"""
    conversations = ChatHistory.list_saved_conversations()
    if not conversations:
        print("\nNo hay conversaciones guardadas")
        return
        
    print("\nConversaciones guardadas:")
    for i, conv in enumerate(conversations, 1):
        print(f"{i}. {conv}")
    
    try:
        choice = int(input("\nElige una conversación para ver (0 para volver): "))
        if choice == 0:
            return
        if 1 <= choice <= len(conversations):
            filename = os.path.join(ChatExporter.CHAT_DIR, conversations[choice-1])
            if filename.endswith('.pkl'):
                chat = ChatHistory.load_conversation(filename)
                if chat:
                    print(f"\nConversación con {chat.model_name} ({chat.service_name})")
                    print(f"Fecha: {chat.timestamp}")
                    print("\nMensajes:")
                    for msg in chat.messages:
                        role = "Usuario" if msg['role'] == 'user' else "Asistente"
                        print(f"\n{role}:")
                        print(msg['content'])
            else:  # .md o .txt
                with open(filename, 'r', encoding='utf-8') as f:
                    print(f.read())
            
            input("\nPresiona Enter para continuar...")
        else:
            print("\nOpción no válida")
    except ValueError:
        print("\nPor favor, ingresa un número válido")

def chat_with_ollama():
    """Simple chat interface for Ollama"""
    try:
        models = get_ollama_models()
        if not models:
            print("No se encontraron modelos disponibles")
            return
        
        model = select_model([{'name': model} for model in models], "Ollama")
        if not model:
            return
        
        print(f"\nIniciando chat con Ollama (modelo: {model})")
        print("Escribe 'salir' para terminar o 'clear' para limpiar el historial")
        
        history = ChatHistory()
        history.start_new_chat(model, "Ollama")
        
        config = ChatConfig()
        stats = ChatStats()
        
        while True:
            user_input = input("\nTú: ")
            
            if user_input.lower() == 'salir':
                break
            elif user_input.lower() == 'clear':
                history.clear()
                print("\nHistorial limpiado")
                continue
            elif user_input.lower() == 'config':
                config.adjust_parameters()
                continue
            elif user_input.lower() == 'save':
                history.save_conversation()
                continue
            elif user_input.lower() == 'help':
                print("\nComandos disponibles:")
                print("- salir: Terminar la conversación")
                print("- clear: Limpiar el historial")
                print("- config: Ajustar parámetros de generación")
                print("- save: Guardar la conversación actual")
                print("- help: Mostrar esta ayuda")
                continue
                
            try:
                # Agregar mensaje del usuario al historial
                history.add_message("user", user_input)
                stats.increment_messages()
                
                # Configurar el prompt para Ollama
                messages = []
                for msg in history.get_history():
                    role = "system" if msg['role'] == 'assistant' else "user"
                    messages.append({"role": role, "content": msg['content']})
                
                response = requests.post(
                    'http://127.0.0.1:11434/api/generate',
                    json={
                        'model': model,
                        'prompt': user_input,
                        'system': 'Eres un asistente amigable y servicial.',
                        'temperature': config.temperature,
                        'top_p': config.top_p,
                        'max_tokens': config.max_tokens,
                        'presence_penalty': config.presence_penalty,
                        'frequency_penalty': config.frequency_penalty,
                        'stream': False
                    }
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    if 'response' in response_data:
                        assistant_response = response_data['response']
                        print("\nModelo:", assistant_response)
                        # Agregar respuesta del asistente al historial
                        history.add_message("assistant", assistant_response)
                        stats.add_response_time(response.elapsed.total_seconds())
                    else:
                        print("No se recibió una respuesta válida del modelo")
                else:
                    if response.status_code == 400:
                        print("Error: El modelo no pudo procesar la solicitud. Intenta con un mensaje más corto o claro.")
                    else:
                        print(f"Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                print("Error: No se pudo conectar con Ollama. Asegúrate de que el servicio esté corriendo.")
            except Exception as e:
                print(f"Error: {str(e)}")
                
        # Exportar conversación
        export_filename = ChatExporter.export_conversation(history, stats)
        print(f"\nConversación exportada a: {export_filename}")

def chat_with_gpt4all():
    """Simple chat interface for GPT4All"""
    try:
        models = get_gpt4all_models()
        if not models:
            print("No se encontraron modelos disponibles")
            return
        
        model_id = select_model([{'id': model} for model in models], "GPT4All")
        print(f"\nIniciando chat con GPT4All")
        print(f"Usando modelo: {model_id}")
        print("Escribe 'salir' para terminar o 'clear' para limpiar el historial")
        
        history = ChatHistory()
        history.start_new_chat(model_id, "GPT4All")
        
        config = ChatConfig()
        stats = ChatStats()
        
        while True:
            user_input = input("\nTú: ")
            if user_input.lower() == 'salir':
                break
            elif user_input.lower() == 'clear':
                history.clear()
                print("Historial limpiado")
                continue
            elif user_input.lower() == 'save':
                history.save_conversation()
                continue
            elif user_input.lower() == 'load':
                filename = input("Ingrese el nombre del archivo de conversación: ")
                loaded_history = ChatHistory.load_conversation(filename)
                if loaded_history:
                    history = loaded_history
                    print("Conversación cargada")
                continue
            elif user_input.lower() == 'config':
                config.adjust_parameters()
                continue
            elif user_input.lower() == 'help':
                show_help()
                continue
                
            try:
                # Agregar mensaje del usuario al historial
                history.add_message("user", user_input)
                stats.increment_messages()
                
                response = requests.post(
                    'http://127.0.0.1:4891/v1/chat/completions',
                    json={
                        'model': model_id,
                        'messages': history.get_history(),
                        'temperature': config.temperature,
                        'max_tokens': config.max_tokens
                    }
                )
                
                if response.status_code == 200:
                    response_json = response.json()
                    if 'choices' in response_json and len(response_json['choices']) > 0:
                        assistant_response = response_json['choices'][0]['message']['content'].strip()
                        print("\nModelo:", assistant_response)
                        # Agregar respuesta del asistente al historial
                        history.add_message("assistant", assistant_response)
                        stats.add_response_time(response.elapsed.total_seconds())
                    else:
                        print("No se recibió una respuesta válida del modelo")
                else:
                    print(f"Error: {response.status_code}")
                    print(f"Detalles: {response.text}")
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                
        # Exportar conversación
        export_filename = ChatExporter.export_conversation(history, stats)
        print(f"\nConversación exportada a: {export_filename}")
        
    except Exception as e:
        print(f"Error al inicializar el chat: {str(e)}")

def main_menu():
    """Menú principal de la aplicación"""
    while True:
        print("\nOpciones:")
        print("1. Chat con Ollama")
        print("2. Chat con GPT4All")
        print("3. Ver conversaciones guardadas")
        print("4. Salir")
        
        try:
            choice = input("\nElige una opción: ")
            
            if choice == '1':
                chat_with_ollama()
            elif choice == '2':
                chat_with_gpt4all()
            elif choice == '3':
                view_saved_conversation()
            elif choice == '4':
                break
            else:
                print("\nOpción no válida")
        except Exception as e:
            print(f"\nError: {str(e)}")

def main():
    print("Probando conexiones a modelos locales...")
    
    # Verificar Ollama
    try:
        ollama_response = requests.get('http://127.0.0.1:11434/api/tags')
        if ollama_response.status_code == 200:
            print("Ollama API disponible!")
            print("Modelos disponibles:")
            print(json.dumps(ollama_response.json(), indent=2))
            ollama_available = True
            ollama_models = ollama_response.json().get('models', [])
        else:
            print("Ollama API no disponible")
            ollama_available = False
            ollama_models = []
    except Exception:
        print("Ollama API no disponible")
        ollama_available = False
        ollama_models = []

    # Verificar GPT4All
    try:
        gpt4all_response = requests.get('http://127.0.0.1:4891/v1/models')
        if gpt4all_response.status_code == 200:
            print("GPT4All API disponible!")
            print("Modelos disponibles:")
            print(json.dumps(gpt4all_response.json(), indent=2))
            gpt4all_available = True
        else:
            print("GPT4All API no disponible")
            gpt4all_available = False
    except Exception:
        print("GPT4All API no disponible")
        gpt4all_available = False

    main_menu()

if __name__ == "__main__":
    main()
