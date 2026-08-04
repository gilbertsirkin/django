from urllib.parse import parse_qs
from wolvcapital.wsgi import application as _application

def application(environ, start_response):
    # If Vercel provided the original path via __orig_path query param, use it
    qs = environ.get("QUERY_STRING", "")
    params = parse_qs(qs)
    orig = params.get("__orig_path")
    if orig:
        environ["PATH_INFO"] = orig[0]
    return _application(environ, start_response)

# Expose the WSGI callable Vercel expects
app = application
