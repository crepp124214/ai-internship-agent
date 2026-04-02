from fastapi import Response
import time
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware

# Metrics definitions
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)
ACTIVE_REQUESTS = Gauge("http_requests_active", "Number of active HTTP requests")


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        ACTIVE_REQUESTS.inc()
        start_time = time.time()
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        except Exception:
            status = 500
            raise
        finally:
            duration = time.time() - start_time
            endpoint = request.url.path
            REQUEST_COUNT.labels(request.method, endpoint, str(status)).inc()
            REQUEST_DURATION.labels(request.method, endpoint).observe(duration)
            ACTIVE_REQUESTS.dec()


async def metrics():
    # Expose Prometheus metrics in Prometheus text format
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
