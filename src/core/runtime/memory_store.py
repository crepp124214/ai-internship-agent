"""
记忆存储：短期会话记忆（Redis）+ 长期向量记忆（ChromaDB）
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, NamedTuple, Optional

import redis as redis_lib
import chromadb

TURNS_KEY_PREFIX = "agent:turns:"
TURNS_TTL_SECONDS = 7 * 24 * 3600  # 7 days
DEFAULT_COLLECTION = "agent_memory"


class Turn(NamedTuple):
    """一次对话回合"""
    role: str
    content: str
    timestamp: str


class MemoryEntry(NamedTuple):
    """一条长期记忆"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class MemoryStore:
    """
    短期会话记忆（Redis）+ 长期向量记忆（ChromaDB）
    """

    def __init__(
        self,
        redis_client: Optional[redis_lib.Redis] = None,
        chroma_client: Optional[chromadb.PersistentClient] = None,
        collection_name: str = DEFAULT_COLLECTION,
        turns_ttl: int = TURNS_TTL_SECONDS,
    ) -> None:
        self._redis = redis_client
        self._chroma = chroma_client
        self._collection_name = collection_name
        self._turns_ttl = turns_ttl

    def _redis_key(self, session_id: str) -> str:
        return f"{TURNS_KEY_PREFIX}{session_id}"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # --- 短期会话记忆 ---

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        """往 Redis 存储一条对话"""
        if self._redis is None:
            return
        key = self._redis_key(session_id)
        turn_data = json.dumps({"role": role, "content": content, "timestamp": self._now_iso()})
        self._redis.rpush(key, turn_data)
        self._redis.expire(key, self._turns_ttl)

    def get_turns(self, session_id: str, limit: int = 20) -> list[Turn]:
        """从 Redis 取最近 N 条对话"""
        if self._redis is None:
            return []
        key = self._redis_key(session_id)
        raw = self._redis.lrange(key, -limit, -1)
        turns = []
        for item in raw:
            try:
                data = json.loads(item) if isinstance(item, str) else json.loads(item.decode())
                turns.append(Turn(
                    role=data.get("role", ""),
                    content=data.get("content", ""),
                    timestamp=data.get("timestamp", ""),
                ))
            except Exception:
                continue
        return turns

    def clear_session(self, session_id: str) -> None:
        """清除会话的所有记忆"""
        if self._redis:
            self._redis.delete(self._redis_key(session_id))

    # --- 长期向量记忆 ---

    def _get_collection(self):
        if self._chroma is None:
            return None
        return self._chroma.get_or_create_collection(
            name=self._collection_name,
            metadata={"description": "Agent long-term memory"},
        )

    def add_memory(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """往 ChromaDB 存储一条记忆，返回 memory_id"""
        collection = self._get_collection()
        if collection is None:
            return ""
        import uuid
        memory_id = str(uuid.uuid4())
        collection.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[{**(metadata or {}), "session_id": session_id}],
        )
        return memory_id

    def search_memory(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[MemoryEntry]:
        """在 ChromaDB 中检索记忆，返回相似度 >= threshold 的结果"""
        collection = self._get_collection()
        if collection is None:
            return []

        where_filter = {"session_id": session_id} if session_id else None

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
        )

        ids: List[List[str]] = results.get("ids", [])
        docs: List[List[str]] = results.get("documents", [])
        metas: List[List[Dict]] = results.get("metadatas", [])
        dists: List[List[float]] = results.get("distances", [])

        if not ids or not ids[0]:
            return []

        entries = []
        for mid, doc, meta, dist in zip(ids[0], docs[0], metas[0], dists[0]):
            # ChromaDB distances are L2 distance (0 = identical, higher = more different)
            # Convert to similarity: higher = better match
            similarity = max(0.0, 1.0 - dist)
            # Filter: similarity must be >= threshold
            if similarity >= threshold:
                entries.append(MemoryEntry(
                    id=mid,
                    content=doc,
                    metadata=meta or {},
                    score=round(similarity, 4),
                ))
        return entries

    def delete_memory(self, memory_id: str) -> None:
        """从 ChromaDB 删除一条记忆"""
        collection = self._get_collection()
        if collection:
            collection.delete(ids=[memory_id])