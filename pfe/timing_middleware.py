import time
import logging

logger = logging.getLogger("django")

UPLOAD_LOG_THRESHOLD_BYTES = 10 * 1024 * 1024

class TimingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        content_length_header = request.META.get("CONTENT_LENGTH")

        try:
            content_length = int(content_length_header) if content_length_header else 0
        except (TypeError, ValueError):
            content_length = 0

        should_log_upload = request.method == "POST" and content_length >= UPLOAD_LOG_THRESHOLD_BYTES

        if should_log_upload:
            logger.warning(
                "Upload request started | method=%s | path=%s | content_length=%s bytes",
                request.method,
                request.path,
                content_length,
            )

        response = self.get_response(request)
        end_time = time.time()
        duration = end_time - start_time

        bold_start = '\033[1m'
        bold_end = '\033[0m'
        logger.info(f"Request to {request.path} took >>>>> {bold_start}{duration:.2f} seconds{bold_end}")

        if should_log_upload:
            logger.warning(
                "Upload request finished | method=%s | path=%s | status=%s | content_length=%s bytes | duration=%.2f seconds",
                request.method,
                request.path,
                getattr(response, "status_code", "unknown"),
                content_length,
                duration,
            )

        return response