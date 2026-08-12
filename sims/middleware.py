from django.utils.deprecation import MiddlewareMixin


class NoCacheMiddleware(MiddlewareMixin):
    """Middleware to prevent browser caching of authenticated pages.

    This ensures that after a user logs out, using the browser back button
    will not show a cached dashboard for the previous user.
    """

    def process_response(self, request, response):
        try:
            # Apply strict no-cache headers for authenticated responses
            if getattr(request, 'user', None) and request.user.is_authenticated:
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0, private'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
        except Exception:
            # Never let middleware errors break the response
            pass
        return response
