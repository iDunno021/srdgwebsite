import time
from django.core.cache import cache
from django.http import JsonResponse, HttpResponse
from django.conf import settings

def _get_config():
    defaults = {
        "WINDOW_SECONDS": 900,
        "MAX_REQUESTS": 100,
        "API_MAX_REQUESTS": 20,
        "LOGIN_MAX_REQUESTS": 10,
    }
    return {**defaults, **getattr(settings, "RATE_LIMIT", {})}

def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")

def _get_tier(path):
    if path.startswith("/accounts/login") or path.startswith("/admin/login"):
        return "login"
    if path.startswith("/api/"):
        return "api"
    return "general"


def _get_max_requests(tier, config):
    return {
        "login":   config["LOGIN_MAX_REQUESTS"],
        "api":     config["API_MAX_REQUESTS"],
        "general": config["MAX_REQUESTS"],
    }.get(tier, config["MAX_REQUESTS"])

class RateLimiterMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.config = _get_config()

    def __call__(self, request):
        ip = _get_client_ip(request)
        path = request.path_info
        tier = _get_tier(path)
        window = self.config["WINDOW_SECONDS"]
        max_requests = _get_max_requests(tier, self.config)

        cache_key = f"rl:{tier}:{ip}"
        now = int(time.time())
        record = cache.get(cache_key)

        if record is None:
            cache.set(cache_key, {"count": 1, "window_start": now}, timeout=window)

        elif now - record["window_start"] >= window:
            cache.set(cache_key, {"count": 1, "window_start": now}, timeout=window)

        elif record["count"] < max_requests:
            record["count"] += 1
            remaining_timeout = window - (now - record["window_start"])
            cache.set(cache_key, record, timeout=remaining_timeout)

        else:
            retry_after = window - (now - record["window_start"])
            return _build_429(request, retry_after, max_requests)

        return self.get_response(request)


def _build_429(request, retry_after, max_requests):
    """Return a 429 response — JSON for /api/ routes, plain text for pages."""
    message = f"Too many requests. Please wait {retry_after} seconds and try again."

    if request.path_info.startswith("/api/"):
        response = JsonResponse(
            {"error": "Too Many Requests", "message": message, "retry_after_seconds": retry_after},
            status=429,
        )
    else:
        response = HttpResponse(message, status=429, content_type="text/plain")

    response["Retry-After"] = str(retry_after)
    response["X-RateLimit-Limit"] = str(max_requests)
    response["X-RateLimit-Remaining"] = "0"
    return response