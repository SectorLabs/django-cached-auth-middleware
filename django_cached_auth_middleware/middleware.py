import logging

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import SESSION_KEY, get_user_model
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth.models import AnonymousUser
from django.core.cache import caches
from django.db.models.signals import post_delete, post_save
from django.utils.functional import SimpleLazyObject

USER_MODEL = get_user_model()


class UserCache:
    @staticmethod
    def make_key(ref):
        return f"cached_authentication_middleware:{ref}"

    def __init__(self, cache):
        self._cache = cache
        self.timeout = getattr(settings, "DJANGO_CACHED_AUTH_TIMEOUT_SECONDS", None)

    def get(self, request):
        if not self._cache:
            return None

        try:
            key = self.make_key(request.session[SESSION_KEY])
        except KeyError:
            return AnonymousUser()

        return self._cache.get(key)

    def set(self, user):
        if not self._cache:
            return

        if user is None:
            return

        key = self.make_key(user.id)
        self._cache.set(key, user, timeout=self.timeout)

    def delete(self, user):
        if not self._cache:
            return

        if user is None:
            return

        key = self.make_key(user.id)
        self._cache.delete(key)


def cache_invalidation_factory(cache):
    def invalidate_cache(sender, instance, **kwargs):
        try:
            UserCache(cache).delete(instance)
        except Exception:
            logging.critical("Failed to invalidate cache", exc_info=True)
            return

    return invalidate_cache


def get_and_cache_user(cache, request):
    if hasattr(request, "_cached_user"):
        return request._cached_user

    user_cache = UserCache(cache)
    try:
        cached_user = user_cache.get(request)
    except Exception:
        logging.critical("Failed to get user from cache", exc_info=True)
        cached_user = None

    user = cached_user
    if not user:
        user = auth.get_user(request)

    if not cached_user:
        try:
            user_cache.set(user)
        except Exception:
            logging.critical("Failed to cache user", exc_info=True)

    request._cached_user = user
    return user


class CachedAuthenticationMiddleware(AuthenticationMiddleware):
    def __init__(self, get_request):
        self._session_cache_alias = getattr(settings, "SESSION_CACHE_ALIAS", "default")
        self._enabled = getattr(settings, "DJANGO_CACHED_AUTH_ENABLED", True)

        if self._enabled:
            self.cache = caches[self._session_cache_alias]
            self.invalidate_cache = cache_invalidation_factory(self.cache)

            post_save.connect(self.invalidate_cache, sender=USER_MODEL)
            post_delete.connect(self.invalidate_cache, sender=USER_MODEL)
        else:
            self.cache = None

        super().__init__(get_request)

    def process_request(self, request):
        assert hasattr(request, "session"), (
            "The cache authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'cache_authentication_middleware'"
        )

        request.user = SimpleLazyObject(lambda: get_and_cache_user(self.cache, request))
