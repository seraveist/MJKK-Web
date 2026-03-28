"""
Rate Limiting 모듈
- flask-limiter 미설치 시 no-op으로 동작
"""
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"], storage_uri="memory://")
except ImportError:
    # flask-limiter 미설치 시 no-op
    class _NoopLimiter:
        def init_app(self, app): pass
        def limit(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
        def shared_limit(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
    limiter = _NoopLimiter()
