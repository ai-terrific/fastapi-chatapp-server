# Chatting Server

A real-time chat backend built with FastAPI, Socket.IO, PostgreSQL, and Redis. PostgreSQL stores users; Redis stores chat history and publishes new messages to connected clients.

## Requirements

- Python 3.14 or later
- [uv](https://docs.astral.sh/uv/)
- PostgreSQL
- Redis

## Setup

Install the locked project dependencies:

```powershell
uv sync
```

Create a `.env` file in the project root:

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/chatting
SECRET_KEY=replace-with-a-long-random-secret
REDIS_URL=redis://localhost:6379/0
```

Make sure PostgreSQL and Redis are running and the database in `DATABASE_URL` exists. Alembic migrations run automatically when the server starts.

## Run

```powershell
uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The HTTP API is available at `http://localhost:8000`; interactive API docs are at `http://localhost:8000/docs`.

## HTTP API

| Method | Path            | Purpose             |
| ------ | --------------- | ------------------- |
| `GET`  | `/auth/`        | Health check        |
| `POST` | `/auth/sign-up` | Create a user       |
| `POST` | `/auth/sign-in` | Get an access token |

Sign-up expects `username`, `email`, `password`, and `confirm_password`. Sign-in expects `email` and `password`.

## Socket.IO

Connect to the server with a Socket.IO client. Authenticate at connection time with the access token from the sign-in API using `auth: { token: "<access_token>" }`. The `sign-in` event with email and password is also supported.

Authenticated clients can use these events:

| Event                 | Direction         | Payload or purpose                                   |
| --------------------- | ----------------- | ---------------------------------------------------- |
| `sign-in`             | Client to server  | `{ "email": "...", "password": "..." }`              |
| `sign-in-result`      | Server to client  | Sign-in result and access token                      |
| `message`             | Client to server  | `{ "text": "Hello" }` to send a chat message         |
| `message`             | Server to clients | A newly published chat message                       |
| `messages`            | Client to server  | Request recent message history                       |
| `messages`            | Server to client  | The latest 50 messages; refreshed after new messages |
| `get-connected-users` | Client to server  | Request the connected-user list                      |
| `connected-users`     | Server to clients | Connected authenticated users                        |

## Project Layout

- `app/main.py` - FastAPI application and Socket.IO ASGI entry point
- `app/routers/` - HTTP routes
- `app/services/` - Socket.IO handlers and Redis integration
- `app/models/` and `app/schemas/` - Database models and API schemas
- `alembic/` - Database migrations
- `tests/` - Test and Socket.IO client scripts
- `pyproject.toml` and `uv.lock` - Dependencies and locked versions
