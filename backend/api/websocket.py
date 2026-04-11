"""WebSocket connection manager for real-time job updates."""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections keyed by job_id."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, job_id: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            if job_id not in self._connections:
                self._connections[job_id] = set()
            self._connections[job_id].add(ws)
        logger.info(f"WS connected: job={job_id}, total={len(self._connections[job_id])}")

    async def disconnect(self, job_id: str, ws: WebSocket) -> None:
        async with self._lock:
            if job_id in self._connections:
                self._connections[job_id].discard(ws)
                if not self._connections[job_id]:
                    del self._connections[job_id]

    async def broadcast(self, job_id: str, payload: dict) -> None:
        """Send a JSON payload to all subscribers of this job."""
        connections = self._connections.get(job_id, set()).copy()
        dead = set()
        for ws in connections:
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                dead.add(ws)
        # Clean up dead connections
        if dead:
            async with self._lock:
                if job_id in self._connections:
                    self._connections[job_id] -= dead

    def subscriber_count(self, job_id: str) -> int:
        return len(self._connections.get(job_id, set()))


# Singleton instance shared across the app
manager = ConnectionManager()
