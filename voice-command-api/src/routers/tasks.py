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
