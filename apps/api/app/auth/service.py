from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditEvent
from app.auth.models import AuthSession
from app.auth.security import hash_token, new_token, verify_password
from app.users.models import User


def normalize_email(email: str) -> str:
    return email.strip().casefold()


@dataclass(frozen=True, slots=True)
class AuthenticatedSession:
    user: User
    session: AuthSession
    session_token: str
    csrf_token: str


class AuthService:
    def __init__(self, db: AsyncSession, session_ttl_seconds: int) -> None:
        self.db = db
        self.session_ttl_seconds = session_ttl_seconds

    async def login(
        self,
        email: str,
        password: str,
        request_id: str,
    ) -> AuthenticatedSession | None:
        normalized_email = normalize_email(email)
        result = await self.db.execute(select(User).where(User.email == normalized_email))
        user = result.scalar_one_or_none()
        is_valid = verify_password(password, user.password_hash if user else None)

        if user is None or not user.is_active or not is_valid:
            self.db.add(
                AuditEvent(
                    actor_user_id=user.id if user else None,
                    action="failed_login",
                    entity_type="user" if user else None,
                    entity_id=str(user.id) if user else None,
                    request_id=request_id,
                    result="denied",
                    event_metadata={"reason": "invalid_credentials"},
                )
            )
            await self.db.commit()
            return None

        session_token = new_token()
        csrf_token = new_token()
        now = datetime.now(UTC)
        session = AuthSession(
            user_id=user.id,
            token_hash=hash_token(session_token),
            csrf_token_hash=hash_token(csrf_token),
            expires_at=now + timedelta(seconds=self.session_ttl_seconds),
        )
        self.db.add(session)
        self.db.add(
            AuditEvent(
                actor_user_id=user.id,
                action="login",
                entity_type="session",
                entity_id=str(session.id),
                request_id=request_id,
                result="success",
                event_metadata={},
            )
        )
        await self.db.commit()
        await self.db.refresh(session)
        return AuthenticatedSession(user, session, session_token, csrf_token)

    async def logout(self, session: AuthSession, user: User, request_id: str) -> None:
        session.revoked_at = datetime.now(UTC)
        self.db.add(
            AuditEvent(
                actor_user_id=user.id,
                action="logout",
                entity_type="session",
                entity_id=str(session.id),
                request_id=request_id,
                result="success",
                event_metadata={},
            )
        )
        await self.db.commit()
