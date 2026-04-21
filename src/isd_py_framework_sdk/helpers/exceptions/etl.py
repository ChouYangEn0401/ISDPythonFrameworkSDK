"""
ETL (Extract-Transform-Load) exceptions — errors that occur during data pipeline
ingestion, transformation, and persistence stages.
"""


class DataExtractionError(Exception):
    """Raised when data cannot be extracted from a source (file, API, DB, stream, …)."""

    def __init__(self, source: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Failed to extract data from '{source}'"] if source else ["Data extraction failed"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.source = source
        self.reason = reason


class DataTransformationError(Exception):
    """Raised when a transformation step fails (parsing, type coercion, derivation, …)."""

    def __init__(self, step: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Transformation step '{step}' failed"] if step else ["Data transformation failed"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.step = step
        self.reason = reason


class DataLoadError(Exception):
    """Raised when data cannot be loaded/written to the target destination."""

    def __init__(self, target: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Failed to load data to '{target}'"] if target else ["Data load failed"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.target = target
        self.reason = reason


class SchemaValidationError(Exception):
    """Raised when a dataset or record does not conform to the expected schema."""

    def __init__(self, detail: str = "", message: str | None = None):
        if message is None:
            message = f"Schema validation failed: {detail}." if detail else "Schema validation failed."
        super().__init__(message)
        self.detail = detail


class MissingColumnError(Exception):
    """Raised when a required column is absent from a dataset or record."""

    def __init__(self, column: str = "", dataset: str = "", message: str | None = None):
        if message is None:
            if column and dataset:
                message = f"Required column '{column}' is missing from dataset '{dataset}'."
            elif column:
                message = f"Required column '{column}' is missing."
            else:
                message = "A required column is missing from the dataset."
        super().__init__(message)
        self.column = column
        self.dataset = dataset


class DataTypeConversionError(Exception):
    """Raised when a value cannot be converted to the target data type."""

    def __init__(self, value=None, target_type: str = "", message: str | None = None):
        if message is None:
            if value is not None and target_type:
                message = f"Cannot convert value {value!r} to type '{target_type}'."
            elif target_type:
                message = f"Type conversion to '{target_type}' failed."
            else:
                message = "Data type conversion failed."
        super().__init__(message)
        self.value = value
        self.target_type = target_type


class DuplicateRecordError(Exception):
    """Raised when a duplicate record is encountered and deduplication is required."""

    def __init__(self, key=None, message: str | None = None):
        if message is None:
            if key is not None:
                message = f"Duplicate record detected for key {key!r}."
            else:
                message = "A duplicate record was detected."
        super().__init__(message)
        self.key = key


class EmptyDatasetError(Exception):
    """Raised when a dataset or data source is unexpectedly empty."""

    def __init__(self, source: str = "", message: str | None = None):
        if message is None:
            if source:
                message = f"Dataset '{source}' is empty."
            else:
                message = "The dataset is unexpectedly empty."
        super().__init__(message)
        self.source = source


class DataCorruptionError(Exception):
    """Raised when data integrity checks fail (hash mismatch, truncated file, …)."""

    def __init__(self, source: str = "", reason: str = "", message: str | None = None):
        if message is None:
            parts = [f"Data corruption detected in '{source}'"] if source else ["Data corruption detected"]
            if reason:
                parts.append(f": {reason}")
            message = " ".join(parts) + "."
        super().__init__(message)
        self.source = source
        self.reason = reason


class PartitionError(Exception):
    """Raised when data cannot be correctly partitioned or split across shards/buckets."""

    def __init__(self, detail: str = "", message: str | None = None):
        if message is None:
            message = f"Data partitioning error: {detail}." if detail else "Data partitioning error."
        super().__init__(message)
        self.detail = detail
