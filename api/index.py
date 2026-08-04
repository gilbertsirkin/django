import json
from wolvcapital.wsgi import application


def handler(request):
    """ASGI handler for Vercel serverless functions.

    TEMPORARY: /__diag returns raw request/environ info as the HTTP
    response body instead of invoking Django, so we can see exactly what
    Vercel hands this function without relying on log capture.
    """
    env = request.environ
    if env.get('PATH_INFO', '').rstrip('/') == '/__diag' or 'diag' in env.get('QUERY_STRING', ''):
        body = json.dumps({
            'PATH_INFO': env.get('PATH_INFO'),
            'SCRIPT_NAME': env.get('SCRIPT_NAME'),
            'REQUEST_URI': env.get('REQUEST_URI'),
            'RAW_URI': env.get('RAW_URI'),
            'REQUEST_METHOD': env.get('REQUEST_METHOD'),
            'QUERY_STRING': env.get('QUERY_STRING'),
            'HTTP_X_VERCEL_ORIGINAL_PATH': env.get('HTTP_X_VERCEL_ORIGINAL_PATH'),
            'HTTP_X_NOW_ROUTE_MATCHES': env.get('HTTP_X_NOW_ROUTE_MATCHES'),
            'request.path': getattr(request, 'path', 'N/A'),
            'request.url': getattr(request, 'url', 'N/A'),
            'request.headers': dict(getattr(request, 'headers', {}) or {}),
            'all_HTTP_env_keys': {k: v for k, v in env.items() if k.startswith('HTTP_') or k in (
                'PATH_INFO', 'SCRIPT_NAME', 'REQUEST_METHOD', 'QUERY_STRING', 'REQUEST_URI', 'RAW_URI',
            )},
        }, indent=2, default=str)
        start_response = request.start_response
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [body.encode('utf-8')]

    return application(request.environ, request.start_response)
