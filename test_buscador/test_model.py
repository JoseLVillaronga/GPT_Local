import requests
import json
import pymongo

usuario = 'Admin'
password = 'sloch1618'
client = pymongo.MongoClient(f'mongodb://{usuario}:{password}@localhost:27017/')
db = client['GPT_Local']
collection = db.resultados
texto = collection.find_one({"titulo": " Argentina Constitution" }).get('texto', '')
system_message="Usa el siguiente texto como referencia para responder las preguntas del usuario:\n\n"
system_message += json.dumps(texto)
model="Phi-3 Mini Intruct"

def enviar_chat_completions(user_message,
                            model="Llama 3.1 8B Instruct 128k",
                            system_message=""):
    """
    Envía una solicitud a la API de GPT4All en el endpoint /v1/chat/completions.

    :param user_message: Mensaje del usuario a enviar.
    :param model: Nombre del modelo a utilizar.
    :param system_message: Mensaje del sistema que proporciona el contexto o referencia.
    :return: Respuesta en formato JSON o None en caso de error.
    """
    url = "http://localhost:4891/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 400,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Lanza una excepción si se obtuvo un error HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        print("Error al conectar con la API:", e)
        return None

def main():
    # Se solicita al usuario que ingrese su pregunta o mensaje
    user_message = input("Ingresa tu pregunta o mensaje: ")
    respuesta = enviar_chat_completions(user_message, model, system_message[:9000])
    if respuesta:
        print("Respuesta del modelo:")
        print(respuesta["choices"][0]["message"]["content"])
        #print("\n\n",json.dumps(texto),"\n")
    else:
        print("No se pudo obtener una respuesta de la API.")


if __name__ == "__main__":
    main()

print("\nCantidad de caracteres: ",len(system_message))