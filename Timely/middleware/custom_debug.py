import traceback
from django.shortcuts import render
from django.conf import settings

class CustomDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            return self.process_exception(request, e)

    def process_exception(self, request, exception):
        traceback_str = traceback.format_exc()
        error_details = {
            "exception": str(exception),
            "traceback": traceback_str,
            "path": request.path,
            "method": request.method,
            "error_code": self.get_error_code(exception, traceback_str)
        }

        if settings.DEBUG:
            return render(request, "middleware/custom_debug.html", error_details, status=500)
        else:
            return render(request, "middleware/friendly_error.html", error_details, status=500)

    def get_error_code(self, exception, traceback_str):
        if "SyntaxError" in traceback_str:
            return 420
        elif "NoReverseMatch" in str(exception) or 'Reverse' in str(exception):
            return 430
        elif "ValueError" in str(exception):
            return 440
        elif "KeyError" in str(exception):
            return 450
        elif "IndexError" in str(exception):
            return 460
        elif "AttributeError" in str(exception):
            return 470
        elif "TypeError" in str(exception):
            return 480
        elif "ImportError" in str(exception) or "ModuleNotFoundError" in str(exception):
            return 490
        elif "PermissionError" in str(exception):
            return 500
        elif "FileNotFoundError" in str(exception):
            return 510
        elif "TimeoutError" in str(exception):
            return 520
        else:
            return 599  # Default for unknown errors
