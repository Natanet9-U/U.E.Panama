from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Estudiantes, Asistencias
from .serializers import EstudianteSerializer, AsistenciaSerializer

# 1. El endpoint que ya hicimos (Listar todos)
@api_view(['GET'])
def listar_estudiantes(request):
    estudiantes = Estudiantes.objects.filter(estado='activo')
    serializer = EstudianteSerializer(estudiantes, many=True)
    return Response(serializer.data)

# 2. ENDPOINT NUEVO: Filtrar por curso
@api_view(['GET'])
def estudiantes_por_curso(request, grado_id):
    # Buscamos alumnos que pertenezcan a ese grado_id (que es un UUID)
    estudiantes = Estudiantes.objects.filter(grado_id=grado_id, estado='activo')
    
    if estudiantes.exists():
        serializer = EstudianteSerializer(estudiantes, many=True)
        return Response(serializer.data)
    else:
        return Response({"mensaje": "No hay estudiantes activos en este curso"}, status=status.HTTP_404_NOT_FOUND)

# 3. ENDPOINT NUEVO: Guardar Asistencia
@api_view(['POST'])
def registrar_asistencia(request):
    # Django recibe el JSON de React y lo pasa al traductor
    serializer = AsistenciaSerializer(data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response({"mensaje": "Asistencia registrada correctamente"}, status=status.HTTP_201_CREATED)
    
    # Si falta algún dato, mostramos exactamente cuál fue el error
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)