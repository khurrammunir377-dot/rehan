import sys
import os
import urllib.parse

# Add root directory to python path for backend package resolution
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.main import app as fastapi_app

class VercelPathMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            raw_qs = scope.get("query_string", b"").decode("latin-1")
            if "__orig_path" in raw_qs:
                params = urllib.parse.parse_qs(raw_qs, keep_blank_values=True)
                orig_path_list = params.pop("__orig_path", None)
                if orig_path_list and orig_path_list[0]:
                    target_path = orig_path_list[0]
                    scope["path"] = target_path
                    scope["raw_path"] = target_path.encode("latin-1")
                    scope["query_string"] = urllib.parse.urlencode(params, doseq=True).encode("latin-1")
        await self.inner(scope, receive, send)

app = VercelPathMiddleware(fastapi_app)
