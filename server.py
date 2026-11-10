from aiohttp import web, WSMsgType
import json

connected_clients = {}


async def home(request):
    return web.Response(text="Crash Detector server is running")

async def receiver_page(request):
    return web.FileResponse("receiver.html")

async def sender_page(request):
    return web.FileResponse("sender.html")


async def websocket_handler(request):
    websocket = web.WebSocketResponse()
    await websocket.prepare(request)

    device_id = None
    role = None

    print("New client connected")

    try:
        async for message in websocket:

            if message.type == WSMsgType.TEXT:
                try:
                    data = json.loads(message.data)
                except json.JSONDecodeError:
                    print("Invalid JSON received")
                    continue

                message_type = data.get("type")

                if message_type == "register":
                    device_id = data.get("device_id")
                    role = data.get("role")

                    connected_clients[device_id] = {
                        "websocket": websocket,
                        "role": role
                    }

                    print(f"{role} registered: {device_id}")

                    await websocket.send_json({
                        "type": "registration_success",
                        "device_id": device_id
                    })

                elif message_type == "crash_alert":
                    print("Crash alert received:")
                    print(data)

                    for client_id, client in list(connected_clients.items()):
                        if client["role"] == "receiver":
                            try:
                                await client["websocket"].send_json(data)
                                print(f"Alert sent to {client_id}")
                            except Exception as error:
                                print(f"Could not send alert to {client_id}: {error}")

                elif message_type == "ack":
                    print(f"ACK received from {data.get('device_id')}")

            elif message.type == WSMsgType.ERROR:
                print("WebSocket error:", websocket.exception())

    finally:
        if device_id in connected_clients:
            del connected_clients[device_id]

        print(f"Client disconnected: {device_id}")

    return websocket


app = web.Application()

app.router.add_get("/", home)
app.router.add_get("/ws", websocket_handler)
app.router.add_get("/sender", sender_page)
app.router.add_get("/receiver", receiver_page)

print("Starting Crash Detector server...")
web.run_app(app, host="0.0.0.0", port=8080)