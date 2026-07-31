import pytest

from app.firebase_service import initialize_firebase


def test_firebase_is_optional() -> None:
    assert initialize_firebase(None) is None


def test_firebase_credentials_path_must_exist(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="Firebase credentials file not found"):
        initialize_firebase(str(tmp_path / "missing.json"))
