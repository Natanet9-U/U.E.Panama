from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .models import Usuarios

@api_view(['POST'])
def login_view(request):
    
    email_recibido = request.data.get('email')
    password_recibida = request.data.get('password')

    try:
        
        usuario = Usuarios.objects.get(email=email_recibido)
                
        if check_password(password_recibida, usuario.password_hash):
            
            return Response({
                "mensaje": "¡Login exitoso!",
                "usuario": {
                    "id": str(usuario.id),
                    "nombre": usuario.nombre,
                    "apellido": usuario.apellido,
                    "email": usuario.email
                }
            }, status=200)
        else:
            return Response({"error": "Credenciales inválidas"}, status=401)

    except Usuarios.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=404)