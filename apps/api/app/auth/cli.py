import argparse
import asyncio
import sys

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import func, select

from app.auth.security import hash_password
from app.auth.service import normalize_email
from app.core.config import get_settings
from app.core.database import Database
from app.users.models import User, UserRole


async def create_owner() -> int:
    settings = get_settings()
    if settings.owner_email is None or settings.owner_password is None:
        print("OWNER_EMAIL and OWNER_PASSWORD are required.", file=sys.stderr)
        return 2
    password = settings.owner_password.get_secret_value()
    if "CHANGE_ME" in password or not 16 <= len(password) <= 128:
        print(
            "OWNER_PASSWORD must be a non-placeholder value of 16-128 characters.", file=sys.stderr
        )
        return 2
    email = normalize_email(str(TypeAdapter(EmailStr).validate_python(settings.owner_email)))
    database = Database(settings.database_url)
    try:
        async with database.session_factory() as db:
            owner_count = await db.scalar(
                select(func.count()).select_from(User).where(User.role == UserRole.OWNER)
            )
            if owner_count:
                print("An OWNER already exists; no changes made.", file=sys.stderr)
                return 1
            db.add(
                User(
                    email=email,
                    password_hash=hash_password(password),
                    role=UserRole.OWNER,
                    is_active=True,
                )
            )
            await db.commit()
        print("OWNER created successfully.")
        return 0
    finally:
        await database.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="MotorScope authentication administration")
    parser.add_argument("command", choices=["create-owner"])
    args = parser.parse_args()
    if args.command == "create-owner":
        raise SystemExit(asyncio.run(create_owner()))


if __name__ == "__main__":
    main()
