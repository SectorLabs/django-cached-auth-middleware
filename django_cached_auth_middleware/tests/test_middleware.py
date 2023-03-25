from dataclasses import dataclass, field
from typing import Dict
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import SESSION_KEY
from django.contrib.auth.models import AnonymousUser
from django.test.utils import override_settings

from django_cached_auth_middleware.middleware import CachedAuthenticationMiddleware, UserCache


@dataclass
class User:
    id: int
    name: str


CACHED_USER = User(id=1, name="User")
DB_USER = User(id=2, name="DB User")


def default_session():
    return {SESSION_KEY: 1}


@dataclass
class MockedRequest:
    session: Dict = field(default_factory=default_session)


@pytest.fixture
def mocked_cache():
    with patch("django_cached_auth_middleware.middleware.caches") as mocked_caches:
        cache = mocked_caches["default"]

        yield cache


@pytest.fixture
def mocked_get_auth_user():
    with patch("django.contrib.auth.get_user") as mocked_get_user:
        mocked_get_user.return_value = DB_USER

        yield mocked_get_user


def test_memory_cached_user(mocked_cache, mocked_get_auth_user):
    request = MockedRequest()
    request._cached_user = CACHED_USER

    CachedAuthenticationMiddleware(get_request=MagicMock()).process_request(request)

    assert request.user == CACHED_USER
    assert not mocked_cache.get.called
    assert not mocked_cache.set.called
    assert not mocked_cache.delete.called
    assert not mocked_get_auth_user.called


def test_cached_user(mocked_cache, mocked_get_auth_user):
    request = MockedRequest()

    mocked_cache.get.return_value = CACHED_USER

    CachedAuthenticationMiddleware(get_request=MagicMock()).process_request(request)

    assert request.user == CACHED_USER
    mocked_cache.get.assert_called_with(UserCache.make_key(CACHED_USER.id))
    assert not mocked_cache.set.called
    assert not mocked_cache.delete.called
    assert not mocked_get_auth_user.called


@override_settings(DJANGO_CACHED_AUTH_TIMEOUT_SECONDS=3600)
def test_user_not_cached(mocked_cache, mocked_get_auth_user):
    request = MockedRequest(session={SESSION_KEY: DB_USER.id})

    mocked_cache.get.return_value = None

    CachedAuthenticationMiddleware(get_request=MagicMock()).process_request(request)

    assert request.user == DB_USER

    mocked_cache.get.assert_called_with(UserCache.make_key(DB_USER.id))
    mocked_cache.set.assert_called_with(UserCache.make_key(DB_USER.id), DB_USER, timeout=3600)
    mocked_get_auth_user.assert_called_with(request)


def test_user_logged_out(mocked_cache, mocked_get_auth_user):
    request = MockedRequest(session=dict())

    CachedAuthenticationMiddleware(get_request=MagicMock()).process_request(request)

    assert request.user == AnonymousUser()
    assert not mocked_cache.get.called
    assert not mocked_get_auth_user.called


def test_cached_user_get_cache_exception(mocked_cache, mocked_get_auth_user):
    request = MockedRequest(session={SESSION_KEY: DB_USER.id})

    mocked_cache.get.side_effect = Exception("Oups!")

    CachedAuthenticationMiddleware(get_request=MagicMock()).process_request(request)

    assert request.user == DB_USER
    mocked_cache.get.assert_called_with(UserCache.make_key(DB_USER.id))
    mocked_cache.set.assert_called_with(UserCache.make_key(DB_USER.id), DB_USER, timeout=None)
    assert not mocked_cache.delete.called
    mocked_get_auth_user.assert_called_with(request)


def test_cached_user_set_cache_exception(mocked_cache, mocked_get_auth_user):
    request = MockedRequest(session={SESSION_KEY: DB_USER.id})

    mocked_cache.get.return_value = None
    mocked_cache.set.side_effect = Exception("Oups!")

    CachedAuthenticationMiddleware(get_request=MagicMock()).process_request(request)

    assert request.user == DB_USER

    mocked_cache.get.assert_called_with(UserCache.make_key(DB_USER.id))
    mocked_cache.set.assert_called_with(UserCache.make_key(DB_USER.id), DB_USER, timeout=None)
    mocked_get_auth_user.assert_called_with(request)
