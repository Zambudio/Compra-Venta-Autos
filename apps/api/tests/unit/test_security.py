import pytest
from app.auth.rate_limit import rate_limit_key
from app.auth.security import hash_password, hash_token, new_token, tokens_match, verify_password
from app.auth.service import normalize_email


@pytest.mark.unit
def test_argon2_password_hash_round_trip_and_no_plaintext() -> None:
    password = "correct horse battery staple"
    password_hash = hash_password(password)
    assert password not in password_hash
    assert password_hash.startswith("$argon2")
    assert verify_password(password, password_hash)
    assert not verify_password("wrong password", password_hash)


@pytest.mark.unit
def test_missing_user_path_never_authenticates() -> None:
    assert not verify_password("any password at all", None)


@pytest.mark.unit
def test_tokens_have_entropy_and_are_compared_safely() -> None:
    first = new_token()
    second = new_token()
    assert len(first) >= 43
    assert first != second
    assert len(hash_token(first)) == 64
    assert tokens_match(first, first)
    assert not tokens_match(first, second)


@pytest.mark.unit
def test_normalization_and_rate_limit_key_do_not_expose_identity() -> None:
    email = normalize_email(" Owner@Example.COM ")
    key = rate_limit_key("127.0.0.1", email)
    assert email == "owner@example.com"
    assert email not in key
    assert "127.0.0.1" not in key
