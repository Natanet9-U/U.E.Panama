#!/usr/bin/env python
"""
Test script for activities workflow
Run from: c:\Nt9\ARCHIVOS\U.E.Panama\U.E.Panama\backend
python core/management/commands/test_activities.py or python manage.py shell < test_activities_manual.py
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from uuid import uuid4
from core.models import (
    Usuarios, DocenteAsignacion, Grados, Areas, Periodos, 
    Estudiantes, Actividades, ActividadNota, DimensionesEvaluacion,
    Notas, NotaDetalle
)
from core.services.grades_service import GradesService

def test_activities_workflow():
    print("=" * 80)
    print("TESTING ACTIVITIES WORKFLOW")
    print("=" * 80)
    
    # Get or create test data
    print("\n1. Setting up test data...")
    gestion = 2024
    
    # Get existing docente
    docente = Usuarios.objects.filter(rol='docente').first()
    if not docente:
        print("ERROR: No docente found in database")
        return False
    
    # Get existing grado
    grado = Grados.objects.first()
    if not grado:
        print("ERROR: No grado found in database")
        return False
    
    # Get existing area
    area = Areas.objects.first()
    if not area:
        print("ERROR: No area found in database")
        return False
    
    # Get or create periodo
    periodo, _ = Periodos.objects.get_or_create(
        numero=1,
        gestion=gestion,
        defaults={'nombre': f'Primer Trimestre {gestion}'}
    )
    
    # Get or create docente asignacion
    asignacion, _ = DocenteAsignacion.objects.get_or_create(
        docente_id=docente.id,
        area_id=area.id,
        grado_id=grado.id,
        defaults={'periodo': periodo}
    )
    
    # Get or create estudiantes
    estudiantes = Estudiantes.objects.filter(grado_id=grado.id)[:2]
    if not estudiantes:
        print("ERROR: No estudiantes found for this grado")
        return False
    
    print(f"✓ Using grado: {grado}")
    print(f"✓ Using area: {area}")
    print(f"✓ Using docente: {docente}")
    print(f"✓ Using asignacion: {asignacion.id}")
    print(f"✓ Using {len(estudiantes)} estudiantes")
    
    # Test 1: Create activity
    print("\n2. Creating activity...")
    try:
        actividad = Actividades.objects.create(
            id=uuid4(),
            asignacion_id=asignacion.id,
            nombre="Práctica 1",
            tipo="practica",
            puntaje_maximo=100,
            descripcion="Primera práctica del trimestre",
            fecha_entrega=timezone.now().date(),
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        print(f"✓ Activity created: {actividad.nombre} (ID: {actividad.id})")
    except Exception as e:
        print(f"✗ Error creating activity: {e}")
        return False
    
    # Test 2: Add grades to activity
    print("\n3. Adding grades to activity...")
    try:
        for est in estudiantes:
            nota_obj = ActividadNota.objects.create(
                id=uuid4(),
                actividad_id=actividad.id,
                estudiante_id=est.id,
                nota=85 if est == estudiantes[0] else 90,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            print(f"✓ Grade added for {est.nombres}: {nota_obj.nota}")
    except Exception as e:
        print(f"✗ Error adding grades: {e}")
        return False
    
    # Test 3: Get activities average
    print("\n4. Computing activities average...")
    try:
        grades_service = GradesService()
        activities_avg = grades_service.get_activities_average(asignacion.id)
        print(f"✓ Activities average computed:")
        for est_id, avg in activities_avg.items():
            est_name = Estudiantes.objects.get(id=est_id).nombres
            print(f"  - {est_name}: {avg}")
    except Exception as e:
        print(f"✗ Error computing average: {e}")
        return False
    
    # Test 4: Create another activity
    print("\n5. Creating second activity...")
    try:
        actividad2 = Actividades.objects.create(
            id=uuid4(),
            asignacion_id=asignacion.id,
            nombre="Tarea 1",
            tipo="tarea",
            puntaje_maximo=50,
            descripcion="Primera tarea",
            fecha_entrega=timezone.now().date(),
            created_at=timezone.now(),
            updated_at=timezone.now(),
        )
        print(f"✓ Second activity created: {actividad2.nombre}")
        
        # Add grades with different scale (50 max)
        for est in estudiantes:
            nota_obj = ActividadNota.objects.create(
                id=uuid4(),
                actividad_id=actividad2.id,
                estudiante_id=est.id,
                nota=40 if est == estudiantes[0] else 45,
                created_at=timezone.now(),
                updated_at=timezone.now(),
            )
            print(f"✓ Grade added for {est.nombres}: {nota_obj.nota}/50")
    except Exception as e:
        print(f"✗ Error creating second activity: {e}")
        return False
    
    # Test 5: Verify average with multiple activities
    print("\n6. Computing final activities average (multiple activities)...")
    try:
        activities_avg = grades_service.get_activities_average(asignacion.id)
        print(f"✓ Final activities average (should be normalized to 100 scale):")
        for est_id, avg in activities_avg.items():
            est_name = Estudiantes.objects.get(id=est_id).nombres
            # Expected: (85 * (100/100) + 40 * (100/50)) / 2 = (85 + 80) / 2 = 82.5 ≈ 83
            # Or: (90 * (100/100) + 45 * (100/50)) / 2 = (90 + 90) / 2 = 90
            print(f"  - {est_name}: {avg}/100 (normalized average)")
    except Exception as e:
        print(f"✗ Error computing final average: {e}")
        return False
    
    # Test 6: Query activities
    print("\n7. Querying all activities for assignment...")
    try:
        todas = Actividades.objects.filter(asignacion_id=asignacion.id)
        print(f"✓ Found {len(todas)} activities:")
        for a in todas:
            count = ActividadNota.objects.filter(actividad_id=a.id).count()
            print(f"  - {a.nombre} ({a.tipo}): {count} grades")
    except Exception as e:
        print(f"✗ Error querying activities: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_activities_workflow()
    sys.exit(0 if success else 1)
