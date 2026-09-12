from typing import Annotated

from app.core.config import Settings
from app.files.storage import FileStorage, LocalFileStorage
from fastapi import Depends, Request


def get_file_storage(request: Request) -> FileStorage:
    # Instantiate once per request or lazily.
    # Alternatively, attach to app.state in lifespan.
    settings: Settings = request.app.state.settings
    return LocalFileStorage(base_dir=settings.storage_dir)


FileStorageDependency = Annotated[FileStorage, Depends(get_file_storage)]
