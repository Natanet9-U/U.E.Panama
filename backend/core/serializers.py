from rest_framework import serializers
from .models import Estudiantes, Asistencias

class EstudianteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Estudiantes
        fields = '__all__'

class AsistenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asistencias
        fields = '__all__'