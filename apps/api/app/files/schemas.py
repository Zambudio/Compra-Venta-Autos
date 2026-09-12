from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FileAttachmentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    inspection_id: UUID
    file_name: str
    content_type: str
    size_bytes: int
    # storage_path is omitted for security so frontend only uses ID
    created_at: datetime
    updated_at: datetime
