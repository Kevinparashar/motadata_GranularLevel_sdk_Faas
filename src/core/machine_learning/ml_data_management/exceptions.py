"""
Data Management Exception Hierarchy

Exceptions specific to the ML Data Management component.
"""



from ...exceptions import SDKError


class DataManagementError(SDKError):
    """Base exception for data management errors."""

    pass


class DataLoadError(DataManagementError):
    """Raised when data loading fails."""

    pass


class DataValidationError(DataManagementError):
    """Raised when data validation fails."""

    pass


class FeatureStoreError(DataManagementError):
    """Raised when feature store operations fail."""

    pass
