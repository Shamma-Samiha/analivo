from io import BytesIO
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile, status

MAX_UPLOAD_SIZE_BYTES = 20 * 1024 * 1024
SUPPORTED_FILE_TYPES = {".csv", ".xlsx", ".json", ".parquet"}


def get_file_extension(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def validate_supported_file_type(file_extension: str) -> None:
    if file_extension not in SUPPORTED_FILE_TYPES:
        supported_types = ", ".join(sorted(SUPPORTED_FILE_TYPES))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Supported file types are: {supported_types}.",
        )


def validate_file_size(file_content: bytes) -> None:
    if len(file_content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Uploaded file is too large. Maximum allowed size is 20 MB.",
        )


async def read_upload_file(file: UploadFile) -> bytes:
    file_content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    validate_file_size(file_content)
    return file_content


def load_dataset(file_content: bytes, file_extension: str) -> pd.DataFrame:
    buffer = BytesIO(file_content)

    try:
        if file_extension == ".csv":
            return pd.read_csv(buffer)
        if file_extension == ".xlsx":
            return pd.read_excel(buffer)
        if file_extension == ".json":
            return pd.read_json(buffer)
        if file_extension == ".parquet":
            return pd.read_parquet(buffer)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded dataset is empty or could not be read.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded dataset appears to be corrupted or unreadable.",
        ) from exc

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported file type.",
    )


def validate_non_empty_dataset(dataframe: pd.DataFrame) -> None:
    if dataframe.empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded dataset is empty.",
        )


def calculate_dataset_metadata(
    dataframe: pd.DataFrame,
    filename: str,
    file_extension: str,
) -> dict:
    missing_values = dataframe.isna().sum()

    return {
        "filename": filename,
        "file_type": file_extension.lstrip("."),
        "number_of_rows": int(dataframe.shape[0]),
        "number_of_columns": int(dataframe.shape[1]),
        "column_names": [str(column) for column in dataframe.columns],
        "data_types": {
            str(column): str(data_type)
            for column, data_type in dataframe.dtypes.items()
        },
        "total_missing_values": int(missing_values.sum()),
        "missing_values_per_column": {
            str(column): int(count)
            for column, count in missing_values.items()
        },
        "duplicate_row_count": int(dataframe.duplicated().sum()),
    }


async def ingest_dataset(file: UploadFile) -> dict:
    try:
        file_extension = get_file_extension(file.filename)
        validate_supported_file_type(file_extension)

        file_content = await read_upload_file(file)
        dataframe = load_dataset(file_content, file_extension)
        validate_non_empty_dataset(dataframe)

        return calculate_dataset_metadata(
            dataframe=dataframe,
            filename=file.filename or "uploaded_dataset",
            file_extension=file_extension,
        )
    finally:
        await file.close()
