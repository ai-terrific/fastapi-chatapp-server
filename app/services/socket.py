import json
import socketio
import jwt
from datetime import datetime, timezone

from app.core.security import decode_access_token
from app.core.security import create_access_token, verify_password
from app.db.database import SessionLocal
from app.models.user import User
from app.services.redis import redis_client

sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode="asgi",
)


@sio.event
async def connect(sid, environ, auth=None):
    token = auth.get("token") if isinstance(auth, dict) else None

    user_id = None
    if auth is not None:
        if not isinstance(auth, dict):
            raise socketio.exceptions.ConnectionRefusedError("Invalid credentials")
        token = auth.get("token")
        if token is not None:
            if not isinstance(token, str):
                raise socketio.exceptions.ConnectionRefusedError("Invalid credentials")
            try:
                user_id = decode_access_token(token)
            except (jwt.InvalidTokenError, RuntimeError) as exc:
                raise socketio.exceptions.ConnectionRefusedError(
                    "Invalid or expired token"
                ) from exc

    await sio.save_session(sid, {"user_id": user_id})
    print("✅ Client connected:", sid)
    if user_id is not None:
        await broadcast_connected_users()


@sio.event
async def disconnect(sid):
    print("❌ Client disconnected:", sid)
    await broadcast_connected_users()


async def broadcast_connected_users():
    user_ids = set()
    for participant_sid, _ in sio.manager.get_participants("/", None):
        try:
            session = await sio.get_session(participant_sid)
        except KeyError:
            continue
        user_id = session.get("user_id")
        if user_id is not None:
            user_ids.add(user_id)

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
        await sio.emit(
            "connected-users",
            [{"id": user.id, "username": user.username} for user in users],
        )
    finally:
        db.close()


async def require_authenticated(sid):
    session = await sio.get_session(sid)
    if session.get("user_id") is None:
        await sio.emit(
            "error",
            {"message": "Sign in required"},
            to=sid,
        )
        return False

    return True


@sio.on("sign-in")
async def sign_in(sid, credentials):
    if not isinstance(credentials, dict):
        await sio.emit(
            "sign-in-result",
            {"success": False, "message": "Email and password are required"},
            to=sid,
        )
        return

    email = credentials.get("email")
    password = credentials.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        await sio.emit(
            "sign-in-result",
            {"success": False, "message": "Email and password are required"},
            to=sid,
        )
        return

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            await sio.emit(
                "sign-in-result",
                {
                    "success": False,
                    "message": "Invalid email or password",
                },
                to=sid,
            )
            return

        if not verify_password(password, user.password):
            await sio.emit(
                "sign-in-result",
                {
                    "success": False,
                    "message": "Invalid email or password",
                },
                to=sid,
            )
            return

        token = create_access_token(user.id)

        await sio.save_session(
            sid,
            {
                "user_id": user.id,
            },
        )

        await sio.emit(
            "sign-in-result",
            {
                "success": True,
                "access_token": token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                },
            },
            to=sid,
        )

    finally:
        db.close()


@sio.on("message")
async def chat_message(sid, data):
    if not await require_authenticated(sid):
        return

    if not isinstance(data, dict) or not isinstance(data.get("text"), str):
        return

    session = await sio.get_session(sid)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == session["user_id"]).first()
        if user is None:
            return
        message = {
            "username": user.username,
            "text": data["text"].strip(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    finally:
        db.close()

    if not message["text"]:
        return

    message_id = await redis_client.xadd(
        "chat:messages",
        {"message": json.dumps(message)},
    )

    await redis_client.publish("chat", json.dumps({"id": message_id, **message}))


@sio.on("messages")
async def get_message_history(sid):
    if not await require_authenticated(sid):
        return

    messages = await load_message_history()

    await sio.emit(
        "messages",
        messages,
        to=sid,
    )


async def load_message_history():
    stream = "chat:messages"

    result = await redis_client.xrevrange(
        stream,
        count=50,
    )

    result.reverse()

    messages = []
    for message_id, data in result:
        try:
            message = json.loads(data["message"])
        except KeyError, TypeError, json.JSONDecodeError:
            continue
        messages.append({"id": message_id, **message})

    return messages


async def broadcast_message_history():
    messages = await load_message_history()

    for participant_sid, _ in sio.manager.get_participants("/", None):
        try:
            session = await sio.get_session(participant_sid)
        except KeyError:
            continue

        if session.get("user_id") is not None:
            await sio.emit("messages", messages, to=participant_sid)


@sio.on("get-connected-users")
async def get_connected_users(sid):
    if not await require_authenticated(sid):
        return
    await broadcast_connected_users()


async def redis_listener():
    pubsub = redis_client.pubsub()

    await pubsub.subscribe("chat")

    try:
        async for item in pubsub.listen():

            if item["type"] != "message":
                continue

            event = json.loads(item["data"])

            await sio.emit(
                "message",
                event,
            )
            await broadcast_message_history()

    finally:
        await pubsub.unsubscribe("chat")
        await pubsub.close()
