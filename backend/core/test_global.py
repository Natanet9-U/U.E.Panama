"""Tests globales de la aplicación"""
import pytest
from django.apps import apps
from django.conf import settings


@pytest.mark.django_db
class TestApplicationConfiguration:
    """Tests de configuración global de la aplicación"""

    def test_django_apps_loaded(self):
        """Verifica que todas las apps de Django están cargadas"""
        from django.apps import AppConfig
        
        apps_loaded = [app.name for app in apps.get_app_configs()]
        assert 'core' in apps_loaded
        assert 'django.contrib.auth' in apps_loaded

    def test_required_settings_exist(self):
        """Verifica que las configuraciones requeridas existen"""
        assert hasattr(settings, 'INSTALLED_APPS')
        assert hasattr(settings, 'DATABASES')
        assert hasattr(settings, 'SECRET_KEY')

    def test_core_app_is_configured(self):
        """Verifica que la app core está configurada correctamente"""
        from core import apps
        
        assert apps.CoreConfig.name == 'core'


class TestURLConfiguration:
    """Tests de configuración de URLs"""

    def test_api_urls_are_configured(self):
        """Verifica que las URLs de la API están configuradas"""
        from django.urls import reverse
        
        # Intenta resolver URLs comunes (estos fallarán si no existen)
        try:
            # reverse('health')  # Ajusta según tus nombres de URLs
            pass
        except:
            # Las URLs pueden no existir, así que esto es solo un placeholder
            pass


class TestDatabaseConfiguration:
    """Tests de configuración de base de datos"""

    def test_database_is_configured(self):
        """Verifica que la base de datos está configurada"""
        from django.db import connections
        
        databases = connections.databases
        assert 'default' in databases


# Agrega más tests globales según sea necesario
