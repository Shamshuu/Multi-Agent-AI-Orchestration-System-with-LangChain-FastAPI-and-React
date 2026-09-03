import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Set, Any
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("websocket_manager")


class ConnectionManager:
    def __init__(self):
        # Map task_id -> Set of active WebSockets
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        async with self._lock:
            if task_id not in self.active_connections:
                self.active_connections[task_id] = set()
            self.active_connections[task_id].add(websocket)
        logger.info(f"WebSocket client connected to task {task_id}. Total listeners: {len(self.active_connections[task_id])}")

    async def disconnect(self, websocket: WebSocket, task_id: str):
        async with self._lock:
            if task_id in self.active_connections:
                self.active_connections[task_id].discard(websocket)
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]
        logger.info(f"WebSocket client disconnected from task {task_id}.")

    async def broadcast_to_task(self, task_id: str, message: Dict[str, Any]):
        """Broadcast JSON payload to all connected clients for a specific task."""
        async with self._lock:
            sockets = list(self.active_connections.get(task_id, set()))

        if not sockets:
            return

        payload_str = json.dumps(message)
        dead_sockets = []

        for ws in sockets:
            try:
                await ws.send_text(payload_str)
            except Exception as e:
                logger.warning(f"Error sending message to client on task {task_id}: {str(e)}")
                dead_sockets.append(ws)

        if dead_sockets:
            async with self._lock:
                for ws in dead_sockets:
                    if task_id in self.active_connections:
                        self.active_connections[task_id].discard(ws)


manager = ConnectionManager()
