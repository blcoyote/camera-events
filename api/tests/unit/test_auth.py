"""Unit tests for firebase/auth.py token verification."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import HTTPException


class TestVerifyToken:
    def test_raises_401_when_token_empty(self) -> None:
        from infrastructure.firebase.auth import verify_token

        with pytest.raises(HTTPException) as exc_info:
            verify_token("")
        assert exc_info.value.status_code == 401

    def test_raises_401_when_token_none_string(self) -> None:
        from infrastructure.firebase.auth import verify_token

        with pytest.raises(HTTPException) as exc_info:
            verify_token("")
        assert exc_info.value.status_code == 401

    def test_raises_403_on_invalid_token(self) -> None:
        from infrastructure.firebase.auth import verify_token

        with patch("infrastructure.firebase.auth.auth.verify_id_token", side_effect=Exception("bad token")):
            with pytest.raises(HTTPException) as exc_info:
                verify_token("bad.token.value")
        assert exc_info.value.status_code == 403

    def test_returns_claims_on_valid_token(self) -> None:
        from infrastructure.firebase.auth import verify_token

        fake_claims = {"uid": "user-123", "email": "test@example.com"}
        with patch("infrastructure.firebase.auth.auth.verify_id_token", return_value=fake_claims):
            result = verify_token("valid.token")
        assert result == fake_claims
