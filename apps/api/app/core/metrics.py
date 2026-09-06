from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "motorscope_http_requests_total",
    "HTTP requests processed",
    ("method", "status"),
)
HTTP_DURATION = Histogram(
    "motorscope_http_request_duration_seconds",
    "HTTP request duration",
    ("method",),
)
