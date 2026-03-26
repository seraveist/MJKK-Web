"""
캐싱 서비스
- TTL 기반 인메모리 캐시 (외부 의존성 없음, Cloud Run에 적합)
- 패보 업로드 시 무효화
- 향후 Redis로 교체 가능한 인터페이스

Cloud Run 특성 고려:
- 인스턴스별 로컬 캐시 (인스턴스 간 공유 안 됨)
- 인스턴스 종료 시 캐시 소멸 → TTL 짧게 유지
- 단일 인스턴스 운영이라면 충분히 효과적
"""
import time
import logging
import hashlib
from threading import Lock

logger = logging.getLogger(__name__)


class CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value, ttl):
        self.value = value
        self.expires_at = time.monotonic() + ttl


class SimpleCache:
    """
    Thread-safe TTL 기반 인메모리 캐시.
    Flask의 멀티스레드 요청 처리에 안전.
    """

    def __init__(self, default_ttl: int = 300):
        """
        Args:
            default_ttl: 기본 캐시 유효 시간 (초). 기본 5분.
        """
        self._store: dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0}

    def get(self, key: str):
        """
        캐시에서 값 조회.
        Returns: 캐시된 값 또는 None (미스/만료)
        """
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._stats["misses"] += 1
                return None
            if time.monotonic() > entry.expires_at:
                del self._store[key]
                self._stats["misses"] += 1
                return None
            self._stats["hits"] += 1
            return entry.value

    def set(self, key: str, value, ttl: int = None):
        """캐시에 값 저장."""
        if ttl is None:
            ttl = self.default_ttl
        with self._lock:
            self._store[key] = CacheEntry(value, ttl)

    def delete(self, key: str):
        """특정 키 삭제."""
        with self._lock:
            self._store.pop(key, None)

    def invalidate_pattern(self, prefix: str):
        """
        특정 접두사로 시작하는 모든 키 무효화.
        패보 업로드 시 관련 캐시를 일괄 삭제할 때 사용.
        """
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._store[k]
            if keys_to_delete:
                logger.info("Cache invalidated: %d keys with prefix '%s'", len(keys_to_delete), prefix)

    def clear(self):
        """전체 캐시 클리어."""
        with self._lock:
            count = len(self._store)
            self._store.clear()
            logger.info("Cache cleared: %d entries removed", count)

    def cleanup_expired(self):
        """만료된 엔트리 정리 (주기적 호출 권장)."""
        now = time.monotonic()
        with self._lock:
            expired = [k for k, v in self._store.items() if now > v.expires_at]
            for k in expired:
                del self._store[k]
            return len(expired)

    @property
    def stats(self):
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        return {
            **self._stats,
            "total": total,
            "hit_rate": f"{hit_rate:.1f}%",
            "size": len(self._store),
        }


def make_cache_key(*args) -> str:
    """인자들로 캐시 키 생성."""
    raw = ":".join(str(a) for a in args)
    return hashlib.md5(raw.encode()).hexdigest()


# 글로벌 캐시 인스턴스 (앱 전체에서 공유)
cache = SimpleCache(default_ttl=300)  # 5분
