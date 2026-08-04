import sys
from wolvcapital.wsgi import application


def handler(request):
    """ASGI handler for Vercel serverless functions."""
    env = request.environ
    print(
        "VERCEL_DIAG "
        f"PATH_INFO={env.get('PATH_INFO')!r} "
        f"SCRIPT_NAME={env.get('SCRIPT_NAME')!r} "
        f"REQUEST_URI={env.get('REQUEST_URI')!r} "
        f"RAW_URI={env.get('RAW_URI')!r} "
        f"REQUEST_METHOD={env.get('REQUEST_METHOD')!r} "
        f"HTTP_X_VERCEL_ORIGINAL_PATH={env.get('HTTP_X_VERCEL_ORIGINAL_PATH')!r} "
        f"HTTP_X_NOW_ROUTE_MATCHES={env.get('HTTP_X_NOW_ROUTE_MATCHES')!r} "
        f"request.path={getattr(request, 'path', 'N/A')!r} "
        f"request.url={getattr(request, 'url', 'N/A')!r}",
        file=sys.stderr,
    )
    return application(request.environ, request.start_response)
