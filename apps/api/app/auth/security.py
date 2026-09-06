import hashlib
import secrets

from pwdlib import PasswordHash

PASSWORD_HASH = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = PASSWORD_HASH.hash("not-a-real-user-password-for-timing-only")


def hash_password(password: str) -> str:
    return PASSWORD_HASH.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    candidate_hash = password_hash or _DUMMY_PASSWORD_HASH
    verified = PASSWORD_HASH.verify(password, candidate_hash)
    return verified and password_hash is not None


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def tokens_match(left: str, right: str) -> bool:
    return secrets.compare_digest(left, right)
