# Template:
[![<SectorLabs>](https://circleci.com/gh/SectorLabs/django-cached-auth-middleware.svg?style=svg)](https://app.circleci.com/pipelines/github/SectorLabs/django-cached-auth-middleware)


Drop-in replacement for `django.contrib.auth.middleware.AuthenticationMiddleware` with cached `request.user`

While this middleware will work with any type of cache, it only makes sense to use it with caches
that are faster than FileSystem or DB (e.g. in-memory caches such as Redis or Memcached).

When using this middleware, the code will _not_ raise any exceptions if it fails to get/set/delete from the
cache, but it will just fallback to the DB.

This plugin will use the `SESSION_CACHE_ALIAS` cache to cache the users.

## Usage

Replace `django.contrib.auth.middleware.AuthenticationMiddleware` with
`django_cached_auth_middleware.middleware.CachedAuthenticationMiddleware` in `MIDDLEWARE`.

```shell
-    "django.contrib.auth.middleware.AuthenticationMiddleware",
+    "django_cached_auth_middleware.middleware.CachedAuthenticationMiddleware",
```

Set `DJANGO_CACHED_AUTH_TIMEOUT_SECONDS` to the amount of seconds you want the sessions to be stored.
If this env var is not set, the sessions will be stored forever.

Inspired from [django-cached_authentication_middleware](https://github.com/ui/django-cached_authentication_middleware)
