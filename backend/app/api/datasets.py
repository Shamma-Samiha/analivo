from fastapi import APIRouter, File, UploadFile

from app.schemas.dataset import DatasetUploadResponse
from app.services.dataset_service import ingest_dataset

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(file: UploadFile = File(...)) -> DatasetUploadResponse:
    dataset_profile = await ingest_dataset(file)
    return DatasetUploadResponse(**dataset_profile)
