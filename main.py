"""
To-Do List API
==============

A REST API for managing tasks, built with FastAPI.

This is a learning project, built from scratch with AI assistance to learn Swagger UI / OpenAPI
documentation. It is not intended for production use.

- Interactive documentation (Swagger UI): /docs
- OpenAPI specification:                  /openapi.json
- Run locally:                            uvicorn main:app --reload
- Authentication:                         demo API key `demo-key-123` (override with API_KEY in .env)
"""

import csv
import io
import os
from enum import Enum
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Path, Depends, Security, Response
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

# ---------- Configuration and authentication ----------

load_dotenv()  # reads the .env file, if there is one

# Demo key so the project runs with no setup. Set API_KEY in a .env file to override it.
API_KEY = os.getenv("API_KEY", "demo-key-123")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(key: str | None = Security(api_key_header)):
    """Runs before every endpoint. Rejects requests with a missing or wrong API key."""
    if key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# ---------- Reusable documentation pieces ----------

# The 401 response, defined once and added to every endpoint's documented responses
R401 = {401: {"description": "Missing or invalid API key"}}

# The task_id path parameter, defined once and reused by several endpoints
TaskId = Annotated[int, Path(ge=1, description="The id of the task", examples=[1])]

tags_metadata = [
    {"name": "Tasks", "description": "Create, read, update and delete single tasks."},
    {"name": "Reports", "description": "Statistics and exports about the task list."},
    {"name": "Bulk Actions", "description": "Operations that affect many tasks at once."},
]

# ---------- Application ----------

app = FastAPI(
    title="To-Do List API",
    description="Manage tasks: create, read, update, delete, filter, search and report. "
                "Click **Authorize** and enter the API key to use the endpoints.\n\n"
                "**Demo API key:** `demo-key-123`\n\n"
                "*A learning project, built from scratch with AI assistance to practise "
                "FastAPI and Swagger UI. Data is stored in memory and resets when the "
                "server restarts.*",
    version="3.0.0",
    openapi_tags=tags_metadata,
    dependencies=[Depends(verify_api_key)],
)

# ---------- Data models ----------


class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class TaskCreate(BaseModel):
    """Data required to create or fully replace a task."""
    title: str = Field(..., min_length=1, max_length=100,
                       description="What needs to be done", examples=["Buy milk"])
    done: bool = Field(False, description="True when the task is finished")
    priority: Priority = Field(Priority.medium, description="How important the task is")


class TaskUpdate(BaseModel):
    """Data for a partial update. Only the fields that are sent are changed."""
    title: str | None = Field(None, min_length=1, max_length=100, description="New title")
    done: bool | None = Field(None, description="New completion status")
    priority: Priority | None = Field(None, description="New priority")


class Task(BaseModel):
    """A task as returned by the API."""
    id: int = Field(..., description="Unique id assigned by the server", examples=[1])
    title: str = Field(..., description="What needs to be done", examples=["Buy milk"])
    done: bool = Field(..., description="True when the task is finished")
    priority: Priority = Field(..., description="How important the task is")


# ---------- Storage (in memory, resets when the server restarts) ----------

tasks = []
next_id = 1

# ---------- Helper functions (not endpoints) ----------


def find_task(task_id: int):
    """Returns the task with the given id, or raises 404 if it does not exist."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail="Task not found")


def check_title(title: str, ignore_id: int | None = None):
    """Trims the title and rejects blank (400) or duplicate (409) titles."""
    clean = title.strip()
    if not clean:
        raise HTTPException(status_code=400, detail="Title cannot be blank")
    for t in tasks:
        if t["title"].lower() == clean.lower() and t["id"] != ignore_id:
            raise HTTPException(status_code=409, detail="A task with this title already exists")
    return clean


# ---------- Endpoints ----------
# Route order matters: fixed paths such as /tasks/stats must be declared
# BEFORE /tasks/{task_id}, otherwise the word is read as a task id.


@app.get("/tasks", tags=["Tasks"], summary="List tasks (filter, search, paginate)",
         response_model=list[Task], responses={**R401})
def get_tasks(
    done: bool | None = Query(None, description="Filter by completion status"),
    priority: Priority | None = Query(None, description="Filter by priority"),
    search: str | None = Query(None, min_length=1, description="Text to look for in the title",
                               examples=["milk"]),
    q: str | None = Query(None, deprecated=True,
                          description="Old name for `search`. Use `search` instead."),
    skip: int = Query(0, ge=0, description="How many tasks to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of tasks to return"),
):
    """Returns tasks. All filters are optional and can be combined."""
    result = tasks
    text = search or q
    if done is not None:
        result = [t for t in result if t["done"] == done]
    if priority is not None:
        result = [t for t in result if t["priority"] == priority.value]
    if text:
        result = [t for t in result if text.lower() in t["title"].lower()]
    return result[skip: skip + limit]


@app.get("/tasks/search", tags=["Tasks"], summary="Search tasks by title",
         response_model=list[Task], responses={**R401})
def search_tasks(
    text: str = Query(..., min_length=2, max_length=50,
                      description="Text to look for in the title (required)", examples=["milk"]),
    case_sensitive: bool = Query(False, description="Match upper and lower case exactly"),
):
    """Searches titles. The `text` parameter is required."""
    if case_sensitive:
        return [t for t in tasks if text in t["title"]]
    return [t for t in tasks if text.lower() in t["title"].lower()]


@app.get("/tasks/stats", tags=["Reports"], summary="Task statistics", responses={**R401})
def get_stats():
    """Counts tasks and shows the completion rate."""
    total = len(tasks)
    done_count = len([t for t in tasks if t["done"]])
    return {
        "total": total,
        "done": done_count,
        "pending": total - done_count,
        "completion_rate": round(done_count / total * 100, 1) if total else 0,
        "by_priority": {p.value: len([t for t in tasks if t["priority"] == p.value]) for p in Priority},
    }


@app.get("/tasks/export", tags=["Reports"], summary="Export tasks as CSV",
         response_class=Response,
         responses={**R401,
                    200: {"description": "All tasks as CSV text",
                          "content": {"text/csv": {"example": "id,title,done,priority\n1,Buy milk,False,high\n"}}}})
def export_tasks():
    """Returns every task as a CSV file (a different media type from the other endpoints)."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["id", "title", "done", "priority"])
    writer.writeheader()
    writer.writerows(tasks)
    return Response(content=buffer.getvalue(), media_type="text/csv")


@app.get("/tasks/all", tags=["Tasks"], summary="Get all tasks (old version)",
         deprecated=True, response_model=list[Task], responses={**R401})
def get_all_tasks_old():
    """**Deprecated.** Use `GET /tasks` instead, which supports filtering, search and pagination.

    This endpoint still works, but it will be removed in a future version."""
    return tasks


@app.get("/tasks/{task_id}", tags=["Tasks"], summary="Get one task",
         response_model=Task, responses={**R401, 404: {"description": "Task not found"}})
def get_task(task_id: TaskId):
    """Returns a single task by its id."""
    return find_task(task_id)


@app.post("/tasks", tags=["Tasks"], summary="Add a task", status_code=201,
          response_model=Task,
          responses={**R401, 400: {"description": "Title is blank"},
                     409: {"description": "Duplicate title"}})
def create_task(task: TaskCreate):
    """Creates a task. The server assigns the id. Titles must be unique."""
    global next_id
    title = check_title(task.title)
    new_task = {"id": next_id, "title": title, "done": task.done, "priority": task.priority.value}
    tasks.append(new_task)
    next_id += 1
    return new_task


@app.put("/tasks/{task_id}", tags=["Tasks"], summary="Replace a task", response_model=Task,
         responses={**R401, 400: {"description": "Title is blank"},
                    404: {"description": "Task not found"},
                    409: {"description": "Duplicate title"}})
def update_task(task_id: TaskId, updated: TaskCreate):
    """Replaces ALL fields of a task."""
    task = find_task(task_id)
    task["title"] = check_title(updated.title, ignore_id=task_id)
    task["done"] = updated.done
    task["priority"] = updated.priority.value
    return task


@app.patch("/tasks/{task_id}", tags=["Tasks"], summary="Change part of a task", response_model=Task,
           responses={**R401, 400: {"description": "Nothing to change, or blank title"},
                      404: {"description": "Task not found"},
                      409: {"description": "Duplicate title"}})
def patch_task(task_id: TaskId, changes: TaskUpdate):
    """Changes only the fields you send. Other fields stay as they are."""
    task = find_task(task_id)
    data = changes.model_dump(exclude_unset=True, exclude_none=True, mode="json")
    if not data:
        raise HTTPException(status_code=400, detail="Send at least one field to change")
    if "title" in data:
        data["title"] = check_title(data["title"], ignore_id=task_id)
    task.update(data)
    return task


@app.delete("/tasks/completed", tags=["Bulk Actions"], summary="Delete all completed tasks",
            responses={**R401, 400: {"description": "Confirmation missing"}})
def delete_completed(
    confirm: bool = Query(..., description="Must be true to confirm the deletion (required)"),
):
    """Removes every task where done is true and tells you how many."""
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to delete completed tasks")
    remaining = [t for t in tasks if not t["done"]]
    deleted = len(tasks) - len(remaining)
    tasks.clear()
    tasks.extend(remaining)
    return {"deleted": deleted}


@app.delete("/tasks/{task_id}", tags=["Tasks"], summary="Delete a task",
            responses={**R401, 404: {"description": "Task not found"}})
def delete_task(task_id: TaskId):
    """Removes a task permanently."""
    task = find_task(task_id)
    tasks.remove(task)
    return {"message": "Task deleted"}