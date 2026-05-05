class AppError(Exception):
    """
    Basis class voor alle applicatiespecifieke fouten.

    Wordt gebruikt om custom errors te groeperen en centraal te kunnen afhandelen.
    """

    pass


class IngestionError(AppError):
    """
    Fout die optreedt tijdens ingestie van data.
    """

    pass


class SourceConfigError(AppError):
    """
    Fout in bronconfiguratie of validatie van velden
    """

    pass


class ExternalServiceError(AppError):
    """
    Fout bij communicatie met externe services (bv. API's).
    """

    pass


class AppValidationError(AppError):
    """
    Fout bij validatie van gebruikserinput.
    """

    pass
