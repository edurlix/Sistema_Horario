class NoCacheMiddleware:
    """
    Adds Cache-Control: no-store to every response served to an authenticated
    user.  This prevents the browser from serving stale protected pages from
    cache after the user logs out (back-button attack).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
