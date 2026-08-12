import traceback
import sys
import datetime


def find_super_like(obj, path=""):
    hits = []
    try:
        tname = type(obj).__name__
        if tname == 'super' or repr(obj).startswith('<super'):
            hits.append((path or '<root>', obj))
            return hits
    except Exception:
        pass

    if isinstance(obj, dict):
        for k, v in obj.items():
            hits.extend(find_super_like(v, f"{path}.{k}" if path else str(k)))
    elif isinstance(obj, (list, tuple, set)):
        for i, v in enumerate(obj):
            hits.extend(find_super_like(v, f"{path}[{i}]") )
    return hits


class InspectContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            ctx = getattr(response, 'context_data', None)
            if ctx:
                hits = find_super_like(ctx)
                if hits:
                    ts = datetime.datetime.utcnow().isoformat()
                    print(f"[InspectContextMiddleware] {ts} - Found {len(hits)} super-like items for path {request.path}")
                    for p, val in hits:
                        print(f"  Context path: {p}; repr: {repr(val)}; type: {type(val)}")
                    print("Stack (most recent call last):")
                    traceback.print_stack(file=sys.stdout)
        except Exception as exc:
            print("InspectContextMiddleware error:", exc)
        return response

    def process_template_response(self, request, response):
        """Sanitize TemplateResponse.context_data to avoid un-copyable objects

        Some builtins (like `super` objects) cannot be shallow-copied by
        Django's template Context copying logic. If such an object exists
        in the response.context_data it can raise the AttributeError seen
        in your admin pages. Replace un-copyable values with their
        repr() so rendering can continue.
        """
        try:
            ctx = getattr(response, 'context_data', None)
            if ctx and isinstance(ctx, dict):
                def sanitize(obj):
                    import copy
                    # Primitive safe types
                    if obj is None or isinstance(obj, (str, int, float, bool)):
                        return obj
                    if isinstance(obj, dict):
                        return {k: sanitize(v) for k, v in obj.items()}
                    if isinstance(obj, (list, tuple, set)):
                        seq = [sanitize(v) for v in obj]
                        return type(obj)(seq)
                    try:
                        copy.copy(obj)
                        return obj
                    except Exception:
                        try:
                            return repr(obj)
                        except Exception:
                            return str(type(obj))

                safe_ctx = {k: sanitize(v) for k, v in ctx.items()}
                response.context_data = safe_ctx
        except Exception as exc:
            print('InspectContextMiddleware sanitize error:', exc)
        return response
