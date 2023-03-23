INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "tests.django",
]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}
