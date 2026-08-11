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
