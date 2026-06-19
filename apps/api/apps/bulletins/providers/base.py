"""Abstract OCRProvider interface — anti-vendor-lock (Story 2.3 §4.10).

Every provider returns a normalized `OCRExtractionResult` regardless of
the underlying SDK. Swapping Tesseract → Mindee is a single-file change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class OCRField:
    key: str  # "matiere" | "note" | "appreciation" | "trimestre" | "annee"
    value: str
    confidence: float  # 0.0–1.0
    bbox: list[int] | None = None  # [x, y, w, h] px — None when unavailable


@dataclass
class OCRExtractionResult:
    fields: list[OCRField] = field(default_factory=list)
    raw_text: str = ""
    language: str = "fra"
    processing_ms: int = 0
    provider: str = "unknown"
    provider_version: str = ""

    def to_dict(self) -> dict:
        return {
            "fields": [
                {
                    "key": f.key,
                    "value": f.value,
                    "confidence": f.confidence,
                    "bbox": f.bbox,
                }
                for f in self.fields
            ],
            "raw_text": self.raw_text,
            "language": self.language,
            "processing_ms": self.processing_ms,
            "provider": self.provider,
            "provider_version": self.provider_version,
        }

    @property
    def confidence_avg(self) -> float:
        if not self.fields:
            return 0.0
        return sum(f.confidence for f in self.fields) / len(self.fields)


class OCRProvider(ABC):
    """Base class for all OCR providers."""

    @abstractmethod
    def extract(self, file_bytes: bytes, mime_type: str) -> OCRExtractionResult:
        """Extract structured data from a bulletin image or PDF.

        Args:
            file_bytes: raw file content (HEIC already converted to JPEG upstream)
            mime_type: "application/pdf" | "image/jpeg" | "image/png"

        Returns:
            Normalized OCRExtractionResult.
        """
        ...
