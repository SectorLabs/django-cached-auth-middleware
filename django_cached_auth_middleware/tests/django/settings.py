INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django_cached_auth_middleware.tests.django",
]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
