from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

import pandas as pd


@dataclass(frozen=True)
class StoredDatasetMetadata:
    dataset_id: str
    filename: str
    file_type: str
    number_of_rows: int
    number_of_columns: int
    created_at: datetime


_DATASETS: dict[str, pd.DataFrame] = {}
_METADATA: dict[str, StoredDatasetMetadata] = {}


def save_dataset(dataframe: pd.DataFrame, filename: str, file_type: str) -> StoredDatasetMetadata:
    dataset_id = str(uuid4())
    metadata = StoredDatasetMetadata(
        dataset_id=dataset_id,
        filename=filename,
        file_type=file_type,
        number_of_rows=int(dataframe.shape[0]),
        number_of_columns=int(dataframe.shape[1]),
        created_at=datetime.now(timezone.utc),
    )
    _DATASETS[dataset_id] = dataframe
    _METADATA[dataset_id] = metadata
    return metadata


def retrieve_dataset(dataset_id: str) -> pd.DataFrame | None:
    return _DATASETS.get(dataset_id)


def retrieve_dataset_metadata(dataset_id: str) -> StoredDatasetMetadata | None:
    return _METADATA.get(dataset_id)


def delete_dataset(dataset_id: str) -> bool:
    dataset_existed = dataset_id in _DATASETS or dataset_id in _METADATA
    _DATASETS.pop(dataset_id, None)
    _METADATA.pop(dataset_id, None)
    return dataset_existed


def dataset_exists(dataset_id: str) -> bool:
    return dataset_id in _DATASETS and dataset_id in _METADATA
