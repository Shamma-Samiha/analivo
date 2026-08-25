from datetime import datetime

from pydantic import BaseModel


class NumericColumnProfile(BaseModel):
    mean: float | None
    median: float | None
    standard_deviation: float | None
    minimum: float | None
    percentile_25: float | None
    percentile_75: float | None
    maximum: float | None


class TopCategoricalValue(BaseModel):
    value: str | int | float | bool | None
    count: int
    percentage: float


class CategoricalColumnProfile(BaseModel):
    unique_count: int
    top_values: list[TopCategoricalValue]


class ColumnProfile(BaseModel):
    column_name: str
    pandas_dtype: str
    type_classification: str
    non_null_count: int
    missing_count: int
    missing_percentage: float
    unique_count: int
    numeric_profile: NumericColumnProfile | None = None
    categorical_profile: CategoricalColumnProfile | None = None


class HighMissingColumn(BaseModel):
    column_name: str
    missing_percentage: float


class DataQualityFlags(BaseModel):
    constant_columns: list[str]
    possible_id_columns: list[str]
    high_missing_columns: list[HighMissingColumn]


class CorrelationPair(BaseModel):
    column_1: str
    column_2: str
    correlation: float


class DatasetUploadResponse(BaseModel):
    dataset_id: str
    filename: str
    file_type: str
    number_of_rows: int
    number_of_columns: int
    column_names: list[str]
    data_types: dict[str, str]
    total_missing_values: int
    missing_values_per_column: dict[str, int]
    duplicate_row_count: int
    column_profiles: list[ColumnProfile]
    data_quality_flags: DataQualityFlags
    strongest_correlations: list[CorrelationPair]


class DatasetMetadataResponse(BaseModel):
    dataset_id: str
    filename: str
    file_type: str
    number_of_rows: int
    number_of_columns: int
    created_at: datetime


class DatasetPreviewResponse(BaseModel):
    dataset_id: str
    columns: list[str]
    rows: list[dict[str, str | int | float | bool | None]]


class DeleteDatasetResponse(BaseModel):
    dataset_id: str
    deleted: bool
    message: str
