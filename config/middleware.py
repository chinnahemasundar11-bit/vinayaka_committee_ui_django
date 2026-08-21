import threading

_thread_locals = threading.local()

def get_current_user():
    """Return current authenticated user from thread-local storage."""
    return getattr(_thread_locals, 'user', None)

class AuditMiddleware:
    """Middleware to capture current user in thread-local storage for AuditModel save operations."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        response = self.get_response(request)
        _thread_locals.user = None
        return response
