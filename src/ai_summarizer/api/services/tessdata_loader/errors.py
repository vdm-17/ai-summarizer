"""Tessdata loader errors."""

from ..errors import InternalServiceError


class TessdataLoaderError(InternalServiceError):
    """Tessdata loader error."""


class LanguageTrainedDataLoadingError(TessdataLoaderError):
    """Error: unable to load language trained data."""


class TrainedDataSHA256LoadingError(LanguageTrainedDataLoadingError):
    """Error: unable to load sha256 of traineddata."""


class TessdataPrefixNotSpecifiedError(TessdataLoaderError):
    """Error: Not specified TESSDATA_PREFIX env var."""
