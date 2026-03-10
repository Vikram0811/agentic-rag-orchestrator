"""
Two-tier response cache:
- Per-session: keyed on (session_id, query_hash), cleared on reset
- Cross-session: keyed on query_hash, shared across sessions with TTL
"""
import hashlib
import time
from typing import Optional
from config import CACHE_TTL_SECONDS, CACHE_MAX_CROSS_SESSION


class ResponseCache:

    def __init__(self):
        self._session: dict[tuple, str] = {}
        self._cross: dict[str, tuple[str, float]] = {}  # hash → (answer, timestamp)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def get(self, session_id: str, query: str) -> Optional[tuple[str, str]]:
        """
        Returns (answer, scope) if cache hit, None if miss.
        scope is "session" or "cross_session".
        Checks per-session first, then cross-session.
        """
        key = self._make_key(query)

        # 1 — per-session check
        session_hit = self._session.get((session_id, key))
        if session_hit:
            return session_hit, "session"

        # 2 — cross-session check with TTL
        cross_hit = self._cross.get(key)
        if cross_hit:
            answer, timestamp = cross_hit
            if time.monotonic() - timestamp < CACHE_TTL_SECONDS:
                return answer, "cross_session"
            else:
                del self._cross[key]  # expired

        return None

    def set(self, session_id: str, query: str, answer: str) -> None:
        """Store answer in both per-session and cross-session caches."""
        if not answer or answer.startswith("❌") or answer.startswith("⚠️"):
            return  # never cache errors or timeouts

        skip_phrases = [
            "I can only answer questions",
            "I couldn't find any information",
            "The documents don't",
        ]
        if any(phrase in answer.lower() for phrase in skip_phrases):
            return  # never cache off-topic or empty responses

        key = self._make_key(query)

        # Per-session
        self._session[(session_id, key)] = answer

        # Cross-session with LRU eviction
        if len(self._cross) >= CACHE_MAX_CROSS_SESSION:
            # evict oldest entry
            oldest = min(self._cross.items(), key=lambda x: x[1][1])
            del self._cross[oldest[0]]

        self._cross[key] = (answer, time.monotonic())

    def clear_session(self, session_id: str) -> None:
        """Clear only per-session entries for this session — called on reset."""
        keys_to_delete = [k for k in self._session if k[0] == session_id]
        for k in keys_to_delete:
            del self._session[k]

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _make_key(query: str) -> str:
        normalized = query.strip().lower()
        return hashlib.md5(normalized.encode()).hexdigest()