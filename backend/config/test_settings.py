from .settings import *
import uuid

# Use SQLite with in-memory shared cache for isolated tests
# Each test gets a fresh, clean database that auto-destroys after test completion
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# Disable migrations in tests to avoid schema conflicts
# Models will be synced directly to the DB without migration history
MIGRATION_MODULES = {
    'contenttypes': None,
    'auth': None,
    'admin': None,
    'sessions': None,
    'messages': None,
    'staticfiles': None,
    'corsheaders': None,
    'rest_framework': None,
    'core': None,
}
