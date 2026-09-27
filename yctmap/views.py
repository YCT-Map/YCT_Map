from django.http import JsonResponse
from django.shortcuts import render


def csrf_failure(request, reason=""):
    """Retain a secure 403 while giving field users a recoverable next action."""
    response = render(request, "csrf_failure.html", status=403)
    response.headers["Cache-Control"] = "no-store, private"
    return response


def health_check(request):
    """Lightweight process health endpoint for the hosting platform."""
    return JsonResponse({"status": "ok"})
