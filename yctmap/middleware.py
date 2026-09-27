class EditorNoStoreMiddleware:
    """Prevent authenticated editor forms with rotated CSRF tokens being reused."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith("/editor/"):
            response.headers["Cache-Control"] = "no-store, private"
        return response
