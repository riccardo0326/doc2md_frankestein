class Doc2MdError(Exception):
    """Base class for expected doc2md failures."""


class ConfigError(Doc2MdError):
    """The requested operation or configuration is invalid."""


class OptionalDependencyError(Doc2MdError):
    """An optional adapter dependency is not installed."""


class UnsupportedFormat(Doc2MdError):
    """The input format is not supported."""


class SourceError(Doc2MdError):
    """The input document cannot be opened or read."""


class PageExtractionError(Doc2MdError):
    """A page extractor failed without invalidating the whole document."""


class HardExtractionError(Doc2MdError):
    """The hard-path document extractor failed."""


class HardPathHandoffError(HardExtractionError):
    """The page must be handled by the configured hard path."""


class VisionError(Doc2MdError):
    """A vision backend failed to describe or transcribe an image."""


class VisionUnavailable(VisionError):
    """The configured vision service cannot be reached or used."""


class CacheError(Doc2MdError):
    """The persistent cache could not be read or written."""


class ConversionFailed(Doc2MdError):
    """Strict conversion found one or more failed pages."""
