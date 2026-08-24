import math
from typing import Any

import pandas as pd
from pandas.api.types import (
    is_bool_dtype,
    is_datetime64_any_dtype,
    is_integer_dtype,
    is_numeric_dtype,
    is_string_dtype,
)

HIGH_MISSING_THRESHOLD_PERCENT = 40.0
MAX_TOP_CATEGORIES = 5
MAX_CORRELATION_PAIRS = 10
ID_COLUMN_NAME_HINTS = {"id", "uuid", "key", "code"}


def to_json_safe_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def to_json_safe_float(value: Any, digits: int = 4) -> float | None:
    if pd.isna(value):
        return None
    numeric_value = float(value)
    if not math.isfinite(numeric_value):
        return None
    return round(numeric_value, digits)


def classify_column_type(series: pd.Series) -> str:
    if is_bool_dtype(series):
        return "boolean"
    if is_datetime64_any_dtype(series):
        return "datetime"
    if is_numeric_dtype(series):
        return "numeric"
    if is_string_dtype(series) or series.dtype == "object" or series.dtype.name == "category":
        return "categorical"
    return "other"


def profile_numeric_column(series: pd.Series) -> dict | None:
    numeric_series = pd.to_numeric(series, errors="coerce")
    numeric_series = numeric_series[numeric_series.notna()]
    numeric_series = numeric_series[numeric_series.map(math.isfinite)]

    if numeric_series.empty:
        return None

    return {
        "mean": to_json_safe_float(numeric_series.mean()),
        "median": to_json_safe_float(numeric_series.median()),
        "standard_deviation": to_json_safe_float(numeric_series.std()),
        "minimum": to_json_safe_float(numeric_series.min()),
        "percentile_25": to_json_safe_float(numeric_series.quantile(0.25)),
        "percentile_75": to_json_safe_float(numeric_series.quantile(0.75)),
        "maximum": to_json_safe_float(numeric_series.max()),
    }


def profile_categorical_column(series: pd.Series, row_count: int) -> dict | None:
    value_counts = series.value_counts(dropna=True).head(MAX_TOP_CATEGORIES)

    top_values = []
    for value, count in value_counts.items():
        top_values.append(
            {
                "value": to_json_safe_value(value),
                "count": int(count),
                "percentage": round((int(count) / row_count) * 100, 2) if row_count else 0.0,
            }
        )

    return {
        "unique_count": int(series.nunique(dropna=True)),
        "top_values": top_values,
    }


def profile_columns(dataframe: pd.DataFrame) -> list[dict]:
    row_count = len(dataframe)
    profiles = []

    for column in dataframe.columns:
        series = dataframe[column]
        missing_count = int(series.isna().sum())
        simplified_type = classify_column_type(series)
        column_profile = {
            "column_name": str(column),
            "pandas_dtype": str(series.dtype),
            "type_classification": simplified_type,
            "non_null_count": int(series.notna().sum()),
            "missing_count": missing_count,
            "missing_percentage": round((missing_count / row_count) * 100, 2) if row_count else 0.0,
            "unique_count": int(series.nunique(dropna=True)),
            "numeric_profile": None,
            "categorical_profile": None,
        }

        if simplified_type == "numeric":
            column_profile["numeric_profile"] = profile_numeric_column(series)
        if simplified_type in {"categorical", "boolean"}:
            column_profile["categorical_profile"] = profile_categorical_column(series, row_count)

        profiles.append(column_profile)

    return profiles


def has_id_like_name(column_name: str) -> bool:
    normalized_name_parts = column_name.lower().replace("-", "_").split("_")
    return any(part in ID_COLUMN_NAME_HINTS for part in normalized_name_parts)


def is_possible_id_column(
    column_name: str,
    series: pd.Series,
    row_count: int,
    unique_count: int,
    missing_count: int,
) -> bool:
    if row_count == 0 or missing_count != 0 or unique_count != row_count:
        return False
    if not has_id_like_name(column_name):
        return False
    if is_bool_dtype(series) or is_datetime64_any_dtype(series):
        return False
    if is_numeric_dtype(series) and not is_integer_dtype(series):
        return False
    return True


def detect_data_quality_flags(dataframe: pd.DataFrame, column_profiles: list[dict]) -> dict:
    constant_columns = []
    possible_id_columns = []
    high_missing_columns = []
    row_count = len(dataframe)

    for profile in column_profiles:
        column_name = profile["column_name"]
        series = dataframe[column_name]

        if profile["unique_count"] <= 1:
            constant_columns.append(column_name)

        if profile["missing_percentage"] >= HIGH_MISSING_THRESHOLD_PERCENT:
            high_missing_columns.append(
                {
                    "column_name": column_name,
                    "missing_percentage": profile["missing_percentage"],
                }
            )

        if is_possible_id_column(
            column_name=column_name,
            series=series,
            row_count=row_count,
            unique_count=profile["unique_count"],
            missing_count=profile["missing_count"],
        ):
            possible_id_columns.append(column_name)

    return {
        "constant_columns": constant_columns,
        "possible_id_columns": possible_id_columns,
        "high_missing_columns": high_missing_columns,
    }


def discover_strongest_correlations(dataframe: pd.DataFrame) -> list[dict]:
    numeric_dataframe = dataframe.select_dtypes(include="number")
    usable_numeric_dataframe = numeric_dataframe.replace([math.inf, -math.inf], pd.NA).dropna(axis=1, how="all")

    if usable_numeric_dataframe.shape[1] < 2:
        return []

    correlation_matrix = usable_numeric_dataframe.corr(method="pearson")
    correlations = []
    columns = list(correlation_matrix.columns)

    for index, column_1 in enumerate(columns):
        for column_2 in columns[index + 1 :]:
            correlation = correlation_matrix.loc[column_1, column_2]
            safe_correlation = to_json_safe_float(correlation)
            if safe_correlation is None:
                continue
            correlations.append(
                {
                    "column_1": str(column_1),
                    "column_2": str(column_2),
                    "correlation": safe_correlation,
                }
            )

    correlations.sort(key=lambda item: abs(item["correlation"]), reverse=True)
    return correlations[:MAX_CORRELATION_PAIRS]


def profile_dataset(dataframe: pd.DataFrame) -> dict:
    column_profiles = profile_columns(dataframe)

    return {
        "column_profiles": column_profiles,
        "data_quality_flags": detect_data_quality_flags(dataframe, column_profiles),
        "strongest_correlations": discover_strongest_correlations(dataframe),
    }
