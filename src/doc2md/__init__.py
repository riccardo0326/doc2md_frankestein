"""Stable models and pure output functions for the doc2md migration."""

from .api import convert, inspect_pdf
from .config import Config
from .models import Block, ConversionResult, ConvertedDocument, PageResult, Provenance

__version__ = "0.1.0"

__all__ = [
    "Block",
    "Config",
    "convert",
    "ConversionResult",
    "ConvertedDocument",
    "PageResult",
    "Provenance",
    "inspect_pdf",
    "__version__",
]
