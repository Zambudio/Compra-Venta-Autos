from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from app.files import models
from app.files.storage import FileStorage
from app.inspections.models import Inspection
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def create_attachment(
    db: AsyncSession,
    storage: FileStorage,
    inspection_id: UUID,
    file_obj: BinaryIO,
    filename: str,
    content_type: str,
) -> models.FileAttachment:
    # Verify inspection exists
    stmt = select(Inspection).where(Inspection.id == inspection_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise ValueError("Inspection not found")

    extension = Path(filename).suffix
    storage_path, size_bytes = await storage.save_file(file_obj, extension)

    attachment = models.FileAttachment(
        inspection_id=inspection_id,
        file_name=filename,
        content_type=content_type,
        size_bytes=size_bytes,
        storage_path=storage_path,
    )

    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)
    return attachment


async def get_attachment(db: AsyncSession, attachment_id: UUID) -> models.FileAttachment | None:
    stmt = select(models.FileAttachment).where(models.FileAttachment.id == attachment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_inspection_attachments(
    db: AsyncSession, inspection_id: UUID
) -> list[models.FileAttachment]:
    stmt = select(models.FileAttachment).where(models.FileAttachment.inspection_id == inspection_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_attachment(db: AsyncSession, attachment_id: UUID) -> bool:
    attachment = await get_attachment(db, attachment_id)
    if not attachment:
        return False
    await db.delete(attachment)
    await db.commit()
    # Note: physical file deletion is omitted here or can be done asynchronously to keep DB fast
    return True
