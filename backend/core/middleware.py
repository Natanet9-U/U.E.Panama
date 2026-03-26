import time

class LogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()

        print(f"➡️ {request.method} {request.path}")

        response = self.get_response(request)

        duration = time.time() - start
        print(f"⬅️ {response.status_code} en {duration:.2f}s")

        return response
    
class ErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            from django.http import JsonResponse
            return JsonResponse({
                "error": "Error interno",
                "detalle": str(e)
            }, status=500)
"""
class AuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # rutas públicas
        if request.path == '/':
            return self.get_response(request)

        token = request.headers.get('Authorization')

        if not token:
            from django.http import JsonResponse
            return JsonResponse({'error': 'No autorizado'}, status=401)

        return self.get_response(request)
"""

