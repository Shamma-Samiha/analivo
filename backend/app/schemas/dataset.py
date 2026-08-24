from pydantic import BaseModel


class DatasetUploadResponse(BaseModel):
    filename: str
    file_type: str
    number_of_rows: int
    number_of_columns: int
    column_names: list[str]
    data_types: dict[str, str]
    total_missing_values: int
    missing_values_per_column: dict[str, int]
    duplicate_row_count: int
