from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.realtime_service import realtime_manager

router = APIRouter()

@router.websocket("/payments")
@router.websocket("/stream")
async def websocket_payments_endpoint(websocket: WebSocket):
    await realtime_manager.connect(websocket)
    try:
        # Send initial connection status confirmation event
        await realtime_manager.send_personal_message({
            "event": "connection.established",
            "message": "Connected to Quantum Fraud Detection Payment Stream",
            "active_clients": len(realtime_manager.active_connections)
        }, websocket)
        
        while True:
            # Maintain open websocket loop to receive incoming keep-alive pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        realtime_manager.disconnect(websocket)
    except Exception as e:
        realtime_manager.disconnect(websocket)
