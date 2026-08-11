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
