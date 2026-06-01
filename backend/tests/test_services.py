"""Tests for service layer."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import NotFoundError
from app.schemas.user import UserCreate
from app.services.user import UserService


class MockUser:
    """Mock user for testing."""

    def __init__(
        self,
        id=None,
        email="test@example.com",
        full_name="Test User",
        hashed_password="$2b$12$hashedpassword",
        is_active=True,
        role="user",
    ):
        self.id = id or str(uuid4())
        self.email = email
        self.full_name = full_name
        self.hashed_password = hashed_password
        self.is_active = is_active
        self.role = role


class TestUserServiceSQLite:
    """Tests for UserService with SQLite."""

    @pytest.fixture
    def mock_db(self) -> MagicMock:
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def user_service(self, mock_db: MagicMock) -> UserService:
        """Create UserService instance with mock db."""
        return UserService(mock_db)

    @pytest.fixture
    def mock_user(self) -> MockUser:
        """Create a mock user."""
        return MockUser()

    @pytest.mark.anyio
    async def test_get_by_id_success(self, user_service: UserService, mock_user: MockUser):
        """Test getting user by ID successfully."""
        with patch("app.services.user.user_repo") as mock_repo:
            mock_repo.get_by_id = MagicMock(return_value=mock_user)

            result = await user_service.get_by_id(mock_user.id)

            assert result == mock_user

    @pytest.mark.anyio
    async def test_get_by_id_not_found(self, user_service: UserService):
        """Test getting non-existent user raises NotFoundError."""
        with patch("app.services.user.user_repo") as mock_repo:
            mock_repo.get_by_id = MagicMock(return_value=None)

            with pytest.raises(NotFoundError):
                await user_service.get_by_id("nonexistent")

    @pytest.mark.anyio
    async def test_authenticate_success(self, user_service: UserService, mock_user: MockUser):
        """Test successful authentication."""
        with (
            patch("app.services.user.user_repo") as mock_repo,
            patch("app.services.user.verify_password", return_value=True),
        ):
            mock_repo.get_by_email = MagicMock(return_value=mock_user)

            result = await user_service.authenticate("test@example.com", "password123")

            assert result == mock_user

    @pytest.mark.anyio
    async def test_register_success(self, user_service: UserService, mock_user: MockUser):
        """Test registering a new user."""
        with (
            patch("app.services.user.user_repo") as mock_repo,
        ):
            mock_repo.get_by_email = MagicMock(return_value=None)
            mock_repo.create = MagicMock(return_value=mock_user)

            user_in = UserCreate(
                email="new@example.com",
                password="password123",
                full_name="New User",
            )
            result = await user_service.register(user_in)

            assert result == mock_user
