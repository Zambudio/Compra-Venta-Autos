from uuid import UUID

from app.auth.dependencies import AuthDependency, CsrfDependency, DbDependency
from app.files import schemas, service
from app.files.dependencies import FileStorageDependency
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

router = APIRouter(prefix="/files", tags=["files"])


@router.post(
    "/inspections/{inspection_id}",
    response_model=schemas.FileAttachmentPublic,
    status_code=status.HTTP_201_CREATED,
)
async def upload_inspection_file(
    auth: AuthDependency,
    csrf: CsrfDependency,
    db: DbDependency,
    storage: FileStorageDependency,
    inspection_id: UUID,
    file: UploadFile = File(...),
) -> schemas.FileAttachmentPublic:
    del auth, csrf
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    try:
        attachment = await service.create_attachment(
            db=db,
            storage=storage,
            inspection_id=inspection_id,
            file_obj=file.file,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
        )
        return schemas.FileAttachmentPublic.model_validate(attachment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/inspections/{inspection_id}", response_model=list[schemas.FileAttachmentPublic])
async def list_inspection_files(
    auth: AuthDependency,
    db: DbDependency,
    inspection_id: UUID,
) -> list[schemas.FileAttachmentPublic]:
    del auth
    attachments = await service.list_inspection_attachments(db, inspection_id)
    return [schemas.FileAttachmentPublic.model_validate(a) for a in attachments]


@router.get("/{attachment_id}/download")
async def download_file(
    auth: AuthDependency,
    db: DbDependency,
    storage: FileStorageDependency,
    attachment_id: UUID,
) -> FileResponse:
    del auth
    attachment = await service.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    try:
        file_path = await storage.get_file_path(attachment.storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File missing from storage"
        )

    return FileResponse(
        path=file_path,
        filename=attachment.file_name,
        media_type=attachment.content_type,
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    auth: AuthDependency,
    csrf: CsrfDependency,
    db: DbDependency,
    attachment_id: UUID,
) -> None:
    del auth, csrf
    success = await service.delete_attachment(db, attachment_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
