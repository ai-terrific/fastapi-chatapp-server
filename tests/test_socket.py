from getpass import getpass

import socketio

sio = socketio.Client(
    logger=True,
    engineio_logger=True,
)


@sio.event
def connect():
    print("Connected!")
    print("Socket ID:", sio.sid)
    print("Transport:", sio.transport())

    sio.emit("sign-in", {"email": email, "password": password})


@sio.event
def disconnect():
    print("Disconnected")


@sio.on("message")
def on_message(data):
    print("New message:", data)


@sio.on("sign-in-result")
def on_sign_in_result(data):
    if not data.get("success"):
        print("Sign-in failed:", data.get("message"))
        sio.disconnect()
        return

    print("Signed in as:", data["user"]["username"])
    sio.emit("messages")
    sio.emit("get-connected-users")
    sio.emit("message", {"text": "Hello Python!"})


@sio.on("connected-users")
def on_connected_users(users):
    print("Connected users:")
    for user in users:
        print(user)


@sio.on("error")
def on_socket_error(data):
    print("Socket error:", data)


@sio.on("messages")
def on_messages(data):
    print("Chat history:")

    for message in data:
        print(message)


try:
    print("Connecting....")
    email = input("Email: ")
    password = getpass("Password: ")

    sio.connect(
        "http://127.0.0.1:5050",
        transports=["websocket"],
    )

    sio.wait()

except Exception as e:
    print("Connection error:", repr(e))
