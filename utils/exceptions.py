class AppError(Exception):
    """Base class voor alle custom errors"""
    pass

class IngestionError(AppError):
    pass

class SourceConfigError(AppError):
    pass

class ExternalServiceError(AppError):
    pass

class AppValidationError(AppError):
    pass