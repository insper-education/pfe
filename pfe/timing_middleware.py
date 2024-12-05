import time
import logging

logger = logging.getLogger("django")

class TimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        response = self.get_response(request)
        end_time = time.time()
        duration = end_time - start_time

        bold_start = '\033[1m'
        bold_end = '\033[0m'
        logger.info(f"Request to {request.path} took >>>>> {bold_start}{duration:.2f} seconds{bold_end}")

        return response