import shutil
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol


class FileStorage(Protocol):
    async def save_file(self, file_obj: BinaryIO, extension: str) -> tuple[str, int]:
        """Save a file and return its storage path and size in bytes."""
        ...

    async def get_file_path(self, storage_path: str) -> Path:
        """Get the absolute path to a saved file."""
        ...


class LocalFileStorage:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, file_obj: BinaryIO, extension: str) -> tuple[str, int]:
        file_name = f"{uuid.uuid4().hex}{extension}"
        # Store in subdirectories by first two chars of uuid to avoid huge directories
        sub_dir = file_name[:2]
        target_dir = self.base_dir / sub_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / file_name

        with open(target_path, "wb") as f:  # noqa: ASYNC230
            shutil.copyfileobj(file_obj, f)

        size = target_path.stat().st_size
        storage_path = f"{sub_dir}/{file_name}"
        return storage_path, size

    async def get_file_path(self, storage_path: str) -> Path:
        target_path = (self.base_dir / storage_path).resolve()
        # Security check to prevent directory traversal
        if not str(target_path).startswith(str(self.base_dir)):
            raise ValueError("Invalid storage path")
        if not target_path.exists():
            raise FileNotFoundError("File not found in storage")
        return target_path
