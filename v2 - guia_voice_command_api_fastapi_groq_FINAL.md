# Voice Command API — Guía paso a paso

> **Qué se pide, en una línea:** construir una API con FastAPI que guarde tareas en una lista de Python, reciba audio desde el frontend, lo transcriba con Groq Whisper y use otro modelo de Groq para convertir esa frase en una instrucción JSON que indique qué operación CRUD ejecutar.

## Flujo general del proyecto

```text
1. USUARIO HABLA
   ↓
   "Agregá comprar leche"

2. FRONTEND GRABA EL AUDIO
   ↓
   genera un archivo de audio

3. FRONTEND
   ↓
   POST /transcribe
   ↓
   manda el archivo de audio al BACKEND

4. BACKEND → /transcribe
   ↓
   manda el audio a Groq Whisper
   ↓
   Groq lo convierte a texto

   "Agregá comprar leche"

5. /transcribe
   ↓
   pasa ese texto a la función process_instruction()
   definida en instruction.py

6. process_instruction()
   ↓
   manda el texto a Groq
   ↓
   Groq interpreta qué quiso hacer el usuario

7. GROQ DEVUELVE AL BACKEND

   {
       "endpoint": "/tasks",
       "method": "POST",
       "params": {
           "title": "Comprar leche"
       }
   }

8. /transcribe LEE ESA INSTRUCCIÓN
   ↓
   ejecuta la función CRUD correspondiente
   ↓
   crea, lista, modifica o elimina la tarea

9. BACKEND DEVUELVE TODO AL FRONTEND

   {
       "transcription": "Agregá comprar leche",
       "instruction": {
           "endpoint": "/tasks",
           "method": "POST",
           "params": {
               "title": "Comprar leche"
           }
       },
       "result": {
           "id": 1,
           "title": "Comprar leche",
           "done": false
       }
   }

10. FRONTEND
    ↓
    muestra la transcripción y el resultado final
```

> **Idea clave:** `/transcribe` entiende **qué dijo** la persona, `process_instruction()` interpreta **qué quiso hacer**, y las funciones de `/tasks` ejecutan **la acción real**.
>
> Aunque existe el endpoint `POST /instruction` para probar esa lógica de forma independiente, durante el flujo de voz `transcribe.py` llama directamente a la función Python `process_instruction()`. No hace una nueva petición HTTP a `/instruction`.

---

## 1. Abrí el proyecto

Si todavía no clonaste el repositorio:

```bash
git clone https://github.com/4GeeksAcademy/voice-command-api
cd voice-command-api
```

Abrilo con VS Code:

```bash
code .
```

Todo el backend va a quedar dentro de `src/`.

---

## 2. Creá el entorno virtual

Desde la raíz del proyecto:

```bash
python -m venv myenv
```

### Windows PowerShell

```powershell
.\myenv\Scripts\Activate.ps1
```

### Windows CMD

```cmd
myenv\Scripts\activate.bat
```

### Mac / Linux

```bash
source myenv/bin/activate
```

Cuando esté activo deberías ver algo parecido a esto:

```text
(myenv) ...
```

> Cada vez que abras una terminal nueva, volvé a activar `myenv` antes de trabajar.

Si PowerShell bloquea la activación:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Y después:

```powershell
.\myenv\Scripts\Activate.ps1
```

---

## 3. Instalá las dependencias

Con `myenv` activo:

```bash
pip install fastapi uvicorn groq python-dotenv
pip install python-multipart
```

Podés comprobarlas con:

```bash
pip list
```

---

## 4. Prepará la estructura del backend

Dentro de `src/` dejá esta estructura:

```text
src/
│
├── __init__.py
├── main.py
│
└── routers/
    ├── __init__.py
    ├── tasks.py
    ├── instruction.py
    └── transcribe.py
```

Además, en la raíz del proyecto vamos a tener:

```text
.env
.gitignore
```

Los archivos `__init__.py` pueden quedar vacíos.

---

## 5. Creá el archivo `.env`

En la raíz del proyecto:

```text
voice-command-api/
├── .env
├── .gitignore
├── frontend/
└── src/
```

Dentro de `.env` escribí:

```env
GROQ_API_KEY=TU_API_KEY_ACA
```

Todavía no tenemos la key. La vamos a buscar en el paso siguiente.

---

## 6. Conseguí una API Key de Groq

Entrá a:

```text
https://console.groq.com/keys
```

1. Iniciá sesión.
2. Entrá a **API Keys**.
3. Hacé click en **Create API Key**.
4. Poné un nombre, por ejemplo:

```text
voice-command-api
```

5. Copiá la key.
6. Pegala en el `.env`.

Ejemplo:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxx
```

> No escribas la key directamente dentro de un archivo `.py`.

---

## 7. Protegé el `.env` con `.gitignore`

Abrí o creá `.gitignore` en la raíz y agregá:

```gitignore
.env
myenv/
__pycache__/
*.pyc
```

Así la API key no termina subida a GitHub para que algún desconocido la use mientras vos dormís. Hermoso ecosistema.

---

# PARTE 1 — CRUD DE TAREAS

## 8. Creá `src/routers/tasks.py`

Pegá lo siguiente:

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


# -------------------------------------------------
# ALMACENAMIENTO EN MEMORIA
# -------------------------------------------------

tasks = []


# -------------------------------------------------
# MODELOS DE PYDANTIC
# -------------------------------------------------

class TaskCreate(BaseModel):
    title: str
    done: bool = False


class TaskReplace(BaseModel):
    title: str
    done: bool


class TaskPatch(BaseModel):
    title: str | None = None
    done: bool | None = None


# -------------------------------------------------
# FUNCIÓN AUXILIAR PARA GENERAR IDS
# -------------------------------------------------

def get_next_id():
    if len(tasks) == 0:
        return 1

    return max(task["id"] for task in tasks) + 1


# -------------------------------------------------
# GET /tasks
# -------------------------------------------------

@router.get("")
def get_tasks():
    return tasks


# -------------------------------------------------
# POST /tasks
# -------------------------------------------------

@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(data: TaskCreate):

    new_task = {
        "id": get_next_id(),
        "title": data.title,
        "done": data.done
    }

    tasks.append(new_task)

    return new_task


# -------------------------------------------------
# PUT /tasks/{task_id}
# Reemplaza título Y estado
# -------------------------------------------------

@router.put("/{task_id}")
def replace_task(task_id: int, data: TaskReplace):

    for index, task in enumerate(tasks):

        if task["id"] == task_id:

            updated_task = {
                "id": task_id,
                "title": data.title,
                "done": data.done
            }

            tasks[index] = updated_task

            return updated_task

    raise HTTPException(
        status_code=404,
        detail="Tarea no encontrada"
    )


# -------------------------------------------------
# PATCH /tasks/{task_id}
# Modifica solamente lo que llegue
# -------------------------------------------------

@router.patch("/{task_id}")
def update_task(task_id: int, data: TaskPatch):

    for task in tasks:

        if task["id"] == task_id:

            if data.title is not None:
                task["title"] = data.title

            if data.done is not None:
                task["done"] = data.done

            return task

    raise HTTPException(
        status_code=404,
        detail="Tarea no encontrada"
    )


# -------------------------------------------------
# DELETE /tasks/{task_id}
# -------------------------------------------------

@router.delete("/{task_id}")
def delete_task(task_id: int):

    for index, task in enumerate(tasks):

        if task["id"] == task_id:

            tasks.pop(index)

            return {
                "message": f"Tarea {task_id} eliminada correctamente"
            }

    raise HTTPException(
        status_code=404,
        detail="Tarea no encontrada"
    )
```

Con esto ya están los cinco endpoints pedidos:

```text
GET     /tasks
POST    /tasks
PUT     /tasks/{task_id}
PATCH   /tasks/{task_id}
DELETE  /tasks/{task_id}
```

La lista:

```python
tasks = []
```

funciona como nuestra "base de datos".

Cuando el servidor se reinicie, la lista vuelve a estar vacía. **Eso es exactamente lo que pide el proyecto.**

---

# PARTE 2 — INTERPRETAR INSTRUCCIONES

## 9. Antes de programarlo: ¿qué corno hace `/instruction`?

`/instruction` **no crea, modifica ni elimina tareas directamente**.

Su trabajo es tomar una frase ya convertida a texto y transformarla en una instrucción estructurada que el sistema pueda entender.

Por ejemplo, si recibe:

```json
{
  "transcription": "Agregá comprar leche a mi lista"
}
```

la lógica de `instruction.py` manda esa frase a Groq y espera algo parecido a:

```json
{
  "endpoint": "/tasks",
  "method": "POST",
  "params": {
    "title": "Comprar leche"
  }
}
```

Ese JSON **describe la acción**, pero todavía no es la tarea creada. Indica:

```text
endpoint → a qué recurso hay que ir
method   → qué operación hay que hacer
params   → qué datos necesita esa operación
```

Durante una prueba manual podemos llamar directamente a:

```http
POST /instruction
```

y ver solamente ese JSON de interpretación.

Durante el flujo real de voz ocurre algo distinto:

```text
Frontend manda audio
        ↓
POST /transcribe
        ↓
Whisper obtiene el texto
        ↓
transcribe.py llama directamente a process_instruction()
        ↓
Groq devuelve endpoint + method + params
        ↓
transcribe.py ejecuta la función CRUD correspondiente
        ↓
recién al final responde al frontend
```

### La idea importante

`/instruction` funciona como un **traductor de lenguaje humano a instrucciones de API**.

No queremos programar esto:

```python
if "agregá" in transcription:
    ...
```

Ni esto:

```python
if "eliminá" in transcription:
    ...
```

El proyecto pide específicamente que **Groq decida qué endpoint, método y parámetros corresponden**.

---

## 10. Creá `src/routers/instruction.py`

Pegá este código:

```python
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
```

### ¿Qué partes nuevas aparecen acá?

Solamente hay cuatro ideas importantes:

```python
load_dotenv()
```

Carga las variables guardadas en `.env`.

---

```python
os.getenv("GROQ_API_KEY")
```

Lee la API key sin escribirla directamente en el código.

---

```python
client.chat.completions.create(...)
```

Envía el texto a Groq.

---

```python
json.loads(response_text)
```

Convierte la respuesta JSON que llega como texto en un objeto de Python que FastAPI puede devolver.

Nada de magia negra. Solamente estamos usando una IA como **clasificador/traductor de instrucciones**.


# PARTE 3 — TRANSCRIBIR AUDIO Y ENCADENAR EL FLUJO

## 11. Creá `src/routers/transcribe.py`

Este archivo será el punto de entrada del flujo de voz. Recibe el audio del frontend, lo manda a Groq Whisper para obtener la transcripción, reutiliza `process_instruction()` para interpretar la intención y finalmente ejecuta la función CRUD correspondiente.

> Importante: cuando `transcribe.py` usa `process_instruction()`, **no está haciendo un POST a `/instruction`**. Está importando y ejecutando directamente esa función de Python.

```python
import os

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, Request
from groq import Groq

from src.routers.instruction import (
    process_instruction,
    InstructionRequest
)

from src.routers.tasks import (
    get_tasks,
    create_task,
    replace_task,
    update_task,
    delete_task,
    TaskCreate,
    TaskReplace,
    TaskPatch
)


load_dotenv()


router = APIRouter(
    tags=["Transcribe"]
)


client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


@router.post("/transcribe")
async def transcribe(request: Request):

    content_type = request.headers.get(
        "content-type",
        ""
    )

    # ---------------------------------------------
    # 1. SI VIENE AUDIO DEL FRONTEND
    # ---------------------------------------------

    if "multipart/form-data" in content_type:

        form = await request.form()

        audio_file = form.get("file")
        language = form.get("language")

        if audio_file is None:
            raise HTTPException(
                status_code=400,
                detail="No se recibió ningún archivo de audio"
            )

        audio_bytes = await audio_file.read()

        transcription_response = client.audio.transcriptions.create(
            file=(
                audio_file.filename or "audio.webm",
                audio_bytes
            ),
            model="whisper-large-v3-turbo",
            language=language if language else None,
            response_format="json",
            temperature=0
        )

        transcription = transcription_response.text


    # ---------------------------------------------
    # 2. SI VIENE TEXTO MANUAL DEL FRONTEND
    # ---------------------------------------------

    elif "application/json" in content_type:

        body = await request.json()

        transcription = body.get("transcription")

        if not transcription:
            raise HTTPException(
                status_code=400,
                detail="Falta transcription"
            )


    else:

        raise HTTPException(
            status_code=415,
            detail="Formato no soportado"
        )


    # ---------------------------------------------
    # 3. PASAMOS EL TEXTO A process_instruction()
    # ---------------------------------------------

    instruction = process_instruction(
        InstructionRequest(
            transcription=transcription
        )
    )


    endpoint = instruction["endpoint"]
    method = instruction["method"]
    params = instruction["params"]


    # ---------------------------------------------
    # 4. EJECUTAMOS LA ACCIÓN QUE DIJO GROQ
    # ---------------------------------------------

    if method == "GET":

        result = get_tasks()


    elif method == "POST":

        result = create_task(
            TaskCreate(**params)
        )


    elif method == "PUT":

        task_id = int(
            endpoint.split("/")[-1]
        )

        result = replace_task(
            task_id,
            TaskReplace(**params)
        )


    elif method == "PATCH":

        task_id = int(
            endpoint.split("/")[-1]
        )

        result = update_task(
            task_id,
            TaskPatch(**params)
        )


    elif method == "DELETE":

        task_id = int(
            endpoint.split("/")[-1]
        )

        result = delete_task(
            task_id
        )


    else:

        raise HTTPException(
            status_code=400,
            detail="Método no reconocido"
        )


    # ---------------------------------------------
    # 5. RESPUESTA QUE ESPERA EL FRONTEND
    # ---------------------------------------------

    return {
        "transcription": transcription,
        "instruction": instruction,
        "result": result
    }
```


---

## 12. Sobre los modelos de Groq

El README original menciona:

```text
llama3-8b-8192
```

o un modelo similar.

Para interpretar las instrucciones usamos:

```text
openai/gpt-oss-20b
```

Y para convertir el audio en texto usamos:

```text
whisper-large-v3-turbo
```

No cumplen la misma función: uno interpreta texto y el otro transcribe audio.

No cambies el nombre de los modelos por uno inventado. Groq, sorprendentemente, no acepta nombres elegidos por entusiasmo.

---

# PARTE 4 — CONECTAR TODO

## 13. Creá `src/main.py`

Pegá:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers.tasks import router as tasks_router
from src.routers.instruction import router as instruction_router
from src.routers.transcribe import router as transcribe_router

app = FastAPI()


# -------------------------------------------------
# CORS
# -------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------
# ROUTERS
# -------------------------------------------------

app.include_router(tasks_router)
app.include_router(instruction_router)
app.include_router(transcribe_router)

# -------------------------------------------------
# RUTA DE PRUEBA
# -------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Voice Command API funcionando"
    }
```

Para este proyecto local usamos:

```python
allow_origins=["*"]
```

para evitar que el frontend incluido sea bloqueado por CORS.

En un proyecto real normalmente limitaríamos los dominios permitidos.

---

# PARTE 5 — LEVANTAR Y PROBAR LA API

## 14. Iniciá el backend

Desde la **raíz del proyecto** y con `myenv` activo:

```bash
python -m uvicorn src.main:app --reload
```

Deberías ver algo parecido a:

```text
Uvicorn running on http://127.0.0.1:8000
```

Abrí:

```text
http://127.0.0.1:8000
```

Debería responder:

```json
{
  "message": "Voice Command API funcionando"
}
```

---

## 15. Abrí Swagger

Visitá:

```text
http://127.0.0.1:8000/docs
```

Antes de probar la voz, comprobá los endpoints normales.

---

# PARTE 6 — PROBAR EL CRUD

## 16. Probá `POST /tasks`

Body:

```json
{
  "title": "Comprar leche"
}
```

Respuesta esperada:

```json
{
  "id": 1,
  "title": "Comprar leche",
  "done": false
}
```

---

## 17. Probá `GET /tasks`

Respuesta:

```json
[
  {
    "id": 1,
    "title": "Comprar leche",
    "done": false
  }
]
```

---

## 18. Probá `PATCH /tasks/1`

Body:

```json
{
  "done": true
}
```

Respuesta:

```json
{
  "id": 1,
  "title": "Comprar leche",
  "done": true
}
```

---

## 19. Probá `PUT /tasks/1`

`PUT` reemplaza los datos completos de la tarea.

Body:

```json
{
  "title": "Comprar leche y pan",
  "done": false
}
```

---

## 20. Probá `DELETE /tasks/1`

Ruta:

```text
DELETE /tasks/1
```

Respuesta:

```json
{
  "message": "Tarea 1 eliminada correctamente"
}
```

---

# PARTE 7 — PROBAR `/instruction`

## 21. Probá primero `/instruction` sin usar voz

En Swagger abrí:

```text
POST /instruction
```

Body:

```json
{
  "transcription": "Agregá comprar leche a mi lista"
}
```

Deberías recibir algo similar a:

```json
{
  "endpoint": "/tasks",
  "method": "POST",
  "params": {
    "title": "Comprar leche"
  }
}
```

Importante:

Esto **todavía no crea la tarea**.

Si probamos `/instruction` directamente, solamente estamos comprobando que Groq interprete bien la frase y devuelva el JSON de enrutamiento.

En el flujo de voz completo, `transcribe.py` recibe ese resultado y ejecuta después la función CRUD correspondiente.

---

## 22. Probá distintos comandos

### Listar

Entrada:

```json
{
  "transcription": "Mostrame todas mis tareas"
}
```

Salida esperada:

```json
{
  "endpoint": "/tasks",
  "method": "GET",
  "params": {}
}
```

---

### Crear

Entrada:

```json
{
  "transcription": "Agregá estudiar FastAPI"
}
```

Salida esperada:

```json
{
  "endpoint": "/tasks",
  "method": "POST",
  "params": {
    "title": "Estudiar FastAPI"
  }
}
```

---

### Completar

Entrada:

```json
{
  "transcription": "Marcá la tarea 2 como completada"
}
```

Salida esperada:

```json
{
  "endpoint": "/tasks/2",
  "method": "PATCH",
  "params": {
    "done": true
  }
}
```

---

### Cambiar título

Entrada:

```json
{
  "transcription": "Cambiá el nombre de la tarea 2 a estudiar Python"
}
```

Salida esperada:

```json
{
  "endpoint": "/tasks/2",
  "method": "PATCH",
  "params": {
    "title": "Estudiar Python"
  }
}
```

---

### Eliminar

Entrada:

```json
{
  "transcription": "Eliminá la tarea 2"
}
```

Salida esperada:

```json
{
  "endpoint": "/tasks/2",
  "method": "DELETE",
  "params": {}
}
```

---

# PARTE 8 — PROBAR EL FLUJO COMPLETO

## 23. Iniciá el frontend incluido

Abrí **otra terminal**.

No cierres la terminal donde está corriendo Uvicorn.

Si necesitás usar Python desde esa nueva terminal, acordate otra vez de activar:

```powershell
.\myenv\Scripts\Activate.ps1
```

Entrá al frontend:

```bash
cd frontend
```

Instalá sus dependencias:

```bash
npm install
```

Antes de iniciar el frontend, dentro de `frontend/` cambiá el nombre de:

```text
.env.example
```

a:

```text
.env
```

Ese archivo contiene la URL que el frontend usará para comunicarse con la API.

Si el `package.json` de la plantilla tiene el script `dev`, iniciá con:

```bash
npm run dev
```

> El frontend viene dado por el proyecto y no debe modificarse. Si la plantilla usa otro script de inicio, ejecutá el que figure en `package.json`.

Abrí en el navegador la URL que indique la terminal del frontend.

---

## 24. Probá el flujo completo de voz

Decí algo como:

```text
Agregá comprar pan
```

El recorrido esperado es:

```text
Micrófono
→ frontend genera audio
→ POST /transcribe
→ Groq Whisper convierte audio a texto
→ transcribe.py llama a process_instruction()
→ Groq interpreta la intención
→ devuelve endpoint / method / params
→ transcribe.py ejecuta la función CRUD correspondiente
→ /transcribe devuelve transcription + instruction + result
→ frontend muestra el resultado
```

Después probá:

```text
Mostrame mis tareas
```

```text
Marcá la tarea 1 como completada
```

```text
Eliminá la tarea 1
```

Si esos casos funcionan, ya tenés cubierto el flujo principal que pide la consigna.

---

# PARTE 9 — ARCHIVOS FINALES

## 25. La estructura debería quedar parecida a esta

```text
voice-command-api/
│
├── .env
├── .gitignore
├── requirements.txt
├── frontend/
│   └── .env
│
├── myenv/
│
└── src/
    ├── __init__.py
    ├── main.py
    │
    └── routers/
        ├── __init__.py
        ├── tasks.py
        ├── instruction.py
        └── transcribe.py
```

`myenv/` y `.env` existen localmente pero **no deben subirse a GitHub**.

---

## 26. Generá `requirements.txt`

Con `myenv` activo y desde la raíz:

```bash
pip freeze > requirements.txt
```

Esto guarda las dependencias del proyecto.

---

## 27. Revisá antes de entregar

La API debe tener:

```text
GET     /tasks
POST    /tasks
PUT     /tasks/{task_id}
PATCH   /tasks/{task_id}
DELETE  /tasks/{task_id}
POST    /instruction
POST    /transcribe
```

Además:

- `tasks` debe ser una lista de Python.
- No debe haber base de datos.
- Los IDs deben ser únicos.
- `.env` debe estar ignorado por Git.
- La API key no debe aparecer escrita en Python.
- CORS debe permitir funcionar al frontend.
- `/instruction` debe llamar a Groq para interpretar el texto.
- `/transcribe` debe recibir el audio y usar Groq Whisper para convertirlo a texto.
- Groq debe devolver `endpoint`, `method` y `params` desde la lógica de instrucción.
- No debe haber detección manual con `if "agregá"`, `if "eliminá"`, etc.
- `transcribe.py` debe usar esa instrucción para ejecutar la función CRUD correspondiente.
- El frontend debe recibir al final `transcription`, `instruction` y `result`.

---

# 28. Qué tienen que entender del proyecto

No hace falta pensar que están construyendo un agente autónomo ni Skynet con una lista de supermercado.

Hay tres piezas principales:

```text
1. TRANSCRIPCIÓN
   audio → texto
   Groq Whisper

2. INTERPRETACIÓN
   texto → endpoint + method + params
   Groq LLM

3. EJECUCIÓN
   funciones CRUD de FastAPI
   crear / listar / modificar / eliminar
```

Ejemplo:

```text
"Agregá comprar leche"
```

primero se transcribe y luego se interpreta como:

```json
{
  "endpoint": "/tasks",
  "method": "POST",
  "params": {
    "title": "Comprar leche"
  }
}
```

Finalmente `transcribe.py` toma esa instrucción y llama directamente a la función CRUD correspondiente.

La idea central es:

> **Whisper entiende qué se dijo, Groq interpreta qué se quiso hacer y el CRUD ejecuta la acción.**

---

# Referencias útiles

Groq API Keys:

```text
https://console.groq.com/keys
```

Documentación de Groq:

```text
https://console.groq.com/docs
```

Documentación de FastAPI:

```text
https://fastapi.tiangolo.com/
```
