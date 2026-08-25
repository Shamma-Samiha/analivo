from fastapi import APIRouter, File, Query, UploadFile

from app.schemas.dataset import (
    DatasetMetadataResponse,
    DatasetPreviewResponse,
    DatasetUploadResponse,
    DeleteDatasetResponse,
)
from app.services.dataset_service import (
    delete_stored_dataset,
    get_dataset_preview,
    get_stored_dataset_metadata,
    ingest_dataset,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> DatasetUploadResponse:
    dataset_profile = await ingest_dataset(file)
    return DatasetUploadResponse(**dataset_profile)


@router.get("/{dataset_id}", response_model=DatasetMetadataResponse)
def get_dataset(dataset_id: str) -> DatasetMetadataResponse:
    metadata = get_stored_dataset_metadata(dataset_id)
    return DatasetMetadataResponse(**metadata)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def preview_dataset(
    dataset_id: str,
    limit: int = Query(default=10, ge=1, le=100),
) -> DatasetPreviewResponse:
    preview = get_dataset_preview(dataset_id=dataset_id, limit=limit)
    return DatasetPreviewResponse(**preview)


@router.delete("/{dataset_id}", response_model=DeleteDatasetResponse)
def delete_dataset(dataset_id: str) -> DeleteDatasetResponse:
    delete_result = delete_stored_dataset(dataset_id)
    return DeleteDatasetResponse(**delete_result)
