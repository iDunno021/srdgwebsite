import logging
from pages.utils import get_client_ip

logger = logging.getLogger('website.requests')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        ip = get_client_ip(request)
        logger.info(f"{ip} {request.method} {request.path} {response.status_code}")
        return response
