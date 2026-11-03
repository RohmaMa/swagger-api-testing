# To-Do List API

A REST API for managing tasks, built with Python and [FastAPI](https://fastapi.tiangolo.com/) and documented with Swagger UI.

> **A learning project.** Built from scratch with AI assistance to Swagger UI / OpenAPI documentation. Data is stored in memory and resets when the server restarts. Not intended for production use.

## Quick start

**Requires Python 3.10 or newer** (check with `python3 --version`).

```
   git clone https://github.com/RohmaMa/swagger-api-testing.git
   cd swagger-api-testing
   bash run.sh
```

Then open **http://127.0.0.1:8000/docs**, click **Authorize**, enter the demo API key `demo-key-123`, and use **Try it out** on any endpoint.

Press `Ctrl + C` in the terminal to stop the server.

<details>
<summary>Manual setup, or on Windows</summary>

macOS / Linux:
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Windows:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
</details>

## Documentation

| Page | Address |
|---|---|
| Swagger UI (interactive docs) | http://127.0.0.1:8000/docs |
| ReDoc (read-only docs) | http://127.0.0.1:8000/redoc |
| OpenAPI specification (JSON) | http://127.0.0.1:8000/openapi.json |

## Authentication

Every endpoint needs an API key, sent in the `X-API-Key` header. In Swagger UI, click **Authorize** once and enter the key.

The default demo key is `demo-key-123`. To use your own, copy `.env.example` to `.env` and change the value of `API_KEY`, then restart the server.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/tasks` | List tasks, with filters, search and pagination |
| `GET` | `/tasks/search` | Search tasks by title |
| `GET` | `/tasks/stats` | Task counts and completion rate |
| `GET` | `/tasks/export` | Export all tasks as CSV |
| `GET` | `/tasks/{task_id}` | Get one task |
| `POST` | `/tasks` | Create a task |
| `PUT` | `/tasks/{task_id}` | Replace a task |
| `PATCH` | `/tasks/{task_id}` | Change part of a task |
| `DELETE` | `/tasks/{task_id}` | Delete a task |
| `DELETE` | `/tasks/completed` | Delete all completed tasks (requires `confirm=true`) |
| `GET` | `/tasks/all` | **Deprecated.** Use `GET /tasks` instead |

## Response codes

| Code | Meaning |
|---|---|
| `200` | Success |
| `201` | Task created |
| `400` | Valid data that is not acceptable (for example, a blank title) |
| `401` | Missing or invalid API key |
| `404` | Task not found |
| `409` | A task with this title already exists |
| `422` | Validation failed (wrong type, missing field or broken rule) |

## What this project demonstrates

- Path and query parameters, with required and optional fields
- Request validation with Pydantic, including enums and length limits
- Grouping with tags, plus summaries, descriptions and example values
- Documented error responses
- API key authentication shown through the **Authorize** button
- A deprecated endpoint and a deprecated parameter
- A non-JSON response (CSV) next to JSON ones


## Troubleshooting

| Problem | Fix |
|---|---|
| Error mentioning `str | None` or a syntax error on startup | Python is older than 3.10. Install a newer version |
| `Address already in use` | Another server is on port 8000. Stop it, or run `uvicorn main:app --reload --port 8001` |
| `401` in Swagger UI | Click **Authorize** and enter `demo-key-123` (or the value in your `.env`) |
| The task list is empty after a restart | Expected. Tasks are stored in memory |