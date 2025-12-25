from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import Optional, Protocol, Tuple

import certifi

try:
    from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore
except Exception:  # pragma: no cover
    AsyncIOMotorClient = None  # type: ignore

from core.session_state import SessionState


logger = logging.getLogger(__name__)


def _env_truthy(name: str) -> bool:
    val = os.getenv(name)
    if val is None:
        return False
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore(Protocol):
    async def get(self, session_id: str) -> Optional[SessionState]:
        ...

    async def create(self) -> Tuple[str, SessionState]:
        ...

    async def save(self, session_id: str, session: SessionState) -> None:
        ...

    async def delete(self, session_id: str) -> bool:
        ...

    async def count(self) -> int:
        ...


@dataclass
class InMemorySessionStore:
    _sessions: dict

    def __init__(self):
        self._sessions = {}

    async def get(self, session_id: str) -> Optional[SessionState]:
        return self._sessions.get(session_id)

    async def create(self) -> Tuple[str, SessionState]:
        session_id = str(uuid.uuid4())
        session = SessionState()
        self._sessions[session_id] = session
        return session_id, session

    async def save(self, session_id: str, session: SessionState) -> None:
        self._sessions[session_id] = session

    async def delete(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    async def count(self) -> int:
        return len(self._sessions)


class MongoSessionStore:
    def __init__(
        self,
        mongo_uri: str,
        db_name: str = "autonomous_tutor",
        collection_name: str = "sessions",
    ):
        if AsyncIOMotorClient is None:
            raise RuntimeError("motor is not installed; add 'motor' to requirements.txt")

        tls_allow_invalid = _env_truthy("MONGODB_TLS_ALLOW_INVALID_CERTS") or _env_truthy("MONGODB_TLS_INSECURE")

        # Fail fast on misconfigured/blocked Mongo in dev environments.
        self._client = AsyncIOMotorClient(
            mongo_uri,
            serverSelectionTimeoutMS=int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "3000")),
            connectTimeoutMS=int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "3000")),
            tls=True,
            tlsCAFile=certifi.where(),
            tlsAllowInvalidCertificates=tls_allow_invalid,
        )
        self._collection = self._client[db_name][collection_name]

    async def get(self, session_id: str) -> Optional[SessionState]:
        doc = await self._collection.find_one({"_id": session_id})
        if not doc:
            return None
        state = doc.get("state") or {}
        return SessionState.from_dict(state)

    async def create(self) -> Tuple[str, SessionState]:
        session_id = str(uuid.uuid4())
        session = SessionState()
        await self._collection.insert_one(
            {
                "_id": session_id,
                "state": session.to_dict(),
                "created_at": _utc_now_iso(),
                "updated_at": _utc_now_iso(),
            }
        )
        return session_id, session

    async def save(self, session_id: str, session: SessionState) -> None:
        await self._collection.update_one(
            {"_id": session_id},
            {
                "$set": {
                    "state": session.to_dict(),
                    "updated_at": _utc_now_iso(),
                },
                "$setOnInsert": {"created_at": _utc_now_iso()},
            },
            upsert=True,
        )

    async def delete(self, session_id: str) -> bool:
        res = await self._collection.delete_one({"_id": session_id})
        return bool(res.deleted_count)

    async def count(self) -> int:
        return int(await self._collection.count_documents({}))

    async def close(self) -> None:
        self._client.close()


def build_session_store_from_env() -> SessionStore:
    mongo_uri = (
        os.getenv("MONGODB_URI")
        or os.getenv("MONGO_URI")
        or os.getenv("MONGO_URL")
    )

    # Allow targeting a specific DB/collection without changing code.
    db_name = os.getenv("MONGODB_DB") or os.getenv("MONGO_DB") or "autonomous_tutor"
    collection_name = os.getenv("MONGODB_COLLECTION") or os.getenv("MONGO_COLLECTION") or "sessions"

    if mongo_uri:
        logger.info("Using MongoSessionStore db=%s collection=%s", db_name, collection_name)
        return MongoSessionStore(mongo_uri=mongo_uri, db_name=db_name, collection_name=collection_name)

    logger.warning("MONGODB_URI not set; falling back to InMemorySessionStore")
    return InMemorySessionStore()
