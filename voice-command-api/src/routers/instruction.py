import json
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from groq import Groq
from pydantic import BaseModel


load_dotenv()


router = APIRouter(
    tags=["Instruction"]
)


# -------------------------------------------------
# BODY QUE RECIBIMOS DEL FRONTEND
# -------------------------------------------------

class InstructionRequest(BaseModel):
    transcription: str


# -------------------------------------------------
# FORMATO QUE QUEREMOS DEVOLVER
# -------------------------------------------------

class InstructionResponse(BaseModel):
    endpoint: str
    method: str
    params: dict


# -------------------------------------------------
# CLIENTE DE GROQ
# -------------------------------------------------

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError(
        "No se encontró GROQ_API_KEY. Revisá el archivo .env"
    )


client = Groq(
    api_key=api_key
)


# -------------------------------------------------
# SYSTEM PROMPT
# -------------------------------------------------

SYSTEM_PROMPT = """
Sos un router de una API de tareas.

Tu único trabajo es convertir la instrucción del usuario
en un objeto JSON que indique qué endpoint de la API debe
usar el sistema.

Respondé ÚNICAMENTE JSON válido.

No agregues explicaciones.
No agregues Markdown.
No uses bloques de código.
No agregues texto antes ni después del JSON.

El formato SIEMPRE debe ser:

{
    "endpoint": "endpoint correspondiente",
    "method": "GET | POST | PUT | PATCH | DELETE",
    "params": {}
}

Endpoints disponibles:

1. Listar todas las tareas

GET /tasks

Respuesta esperada:

{
    "endpoint": "/tasks",
    "method": "GET",
    "params": {}
}


2. Crear una tarea

POST /tasks

Params posibles:

{
    "title": "texto de la tarea",
    "done": false
}

Si el usuario no menciona el estado, no es necesario incluir "done".


3. Reemplazar completamente una tarea

PUT /tasks/{task_id}

Debe utilizarse cuando se proporcionan los datos completos
de la tarea: title y done.

Ejemplo:

{
    "endpoint": "/tasks/3",
    "method": "PUT",
    "params": {
        "title": "Comprar pan",
        "done": false
    }
}


4. Modificar parcialmente una tarea

PATCH /tasks/{task_id}

Usalo cuando el usuario quiera cambiar solamente el título
o solamente el estado done.

Ejemplo para completar una tarea:

{
    "endpoint": "/tasks/3",
    "method": "PATCH",
    "params": {
        "done": true
    }
}

Ejemplo para cambiar el título:

{
    "endpoint": "/tasks/3",
    "method": "PATCH",
    "params": {
        "title": "Comprar pan"
    }
}


5. Eliminar una tarea

DELETE /tasks/{task_id}

Ejemplo:

{
    "endpoint": "/tasks/3",
    "method": "DELETE",
    "params": {}
}


Reglas importantes:

- Nunca inventes endpoints distintos a los indicados.
- El ID debe estar incluido dentro del endpoint cuando corresponda.
- method debe estar escrito en mayúsculas.
- params siempre debe existir.
- Para GET y DELETE, params normalmente será {}.
- Para crear una tarea usá POST.
- Para marcar una tarea como completada usá PATCH con done=true.
- Para marcar una tarea como pendiente usá PATCH con done=false.
- Para cambiar solamente el título usá PATCH.
- No ejecutes ninguna acción. Solamente devolvé el JSON de enrutamiento.
"""


# -------------------------------------------------
# POST /instruction
# -------------------------------------------------

@router.post(
    "/instruction",
    response_model=InstructionResponse
)
def process_instruction(data: InstructionRequest):

    try:

        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": data.transcription
                }
            ],
            response_format={
                "type": "json_object"
            },
            temperature=0
        )

        response_text = completion.choices[0].message.content

        parsed_response = json.loads(response_text)

        return parsed_response

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Error procesando la instrucción: {str(error)}"
        )
