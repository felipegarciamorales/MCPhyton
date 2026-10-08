import pytest

from tests.unit.application.fakes import (
    FakePasswordHasher,
    FakeTokenProvider,
    InMemoryTokenRepository,
    InMemoryUserRepository,
)


@pytest.fixture
def user_repository():
    return InMemoryUserRepository()


@pytest.fixture
def token_repository():
    return InMemoryTokenRepository()


@pytest.fixture
def password_hasher():
    return FakePasswordHasher()


@pytest.fixture
def token_provider():
    return FakeTokenProvider()
