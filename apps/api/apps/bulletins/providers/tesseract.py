"""Tesseract OCR provider — PoC MVP (Story 2.3 §T1 spike decision).

Uses pytesseract with `--psm 6 --oem 3 -l fra` for structured French bulletin
pages. HEIC files must be converted to JPEG before calling `extract()`.

Bulletin parsing heuristic:
- Lines matching `<matière>\s+<note>/20` are captured as (matiere, note) pairs.
- Lines between a matière header and the next are captured as appreciation.
- Trimestre/année are extracted from page headers.

Confidence simulation: Tesseract does not expose per-word confidence in a
structured way via pytesseract's simple mode. We use the TSOCR data mode
(`image_to_data`) to get word-level confidence and aggregate per semantic field.
"""

from __future__ import annotations

import io
import re
import time

try:
    import pytesseract
    from PIL import Image
    from pillow_heif import register_heif_opener

    register_heif_opener()
    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False

from .base import OCRExtractionResult, OCRField, OCRProvider

# Regex patterns for French bulletin lines
_NOTE_RE = re.compile(
    r"(?P<matiere>[A-Za-zÀ-ÿ'\- ]{3,50})\s+(?P<note>\d{1,2}[.,]\d{1}|\d{1,2})\s*/\s*20",
    re.IGNORECASE,
)
_TRIMESTRE_RE = re.compile(r"trimestre\s*[n°]?\s*(\d)", re.IGNORECASE)
_ANNEE_RE = re.compile(r"(?:année|an)\s*(\d{4}[-–]\d{2,4})", re.IGNORECASE)


def _tesseract_version() -> str:
    if not _TESSERACT_AVAILABLE:
        return "unavailable"
    try:
        return pytesseract.get_tesseract_version().string
    except Exception:
        return "unknown"


class TesseractProvider(OCRProvider):
    """Tesseract 5.x provider for French bulletin OCR."""

    PROVIDER_NAME = "tesseract"
    CONFIG = "--psm 6 --oem 3 -l fra"

    def extract(self, file_bytes: bytes, mime_type: str) -> OCRExtractionResult:
        if not _TESSERACT_AVAILABLE:
            raise RuntimeError(
                "pytesseract is not installed. "
                "Run: uv add pytesseract && brew install tesseract tesseract-lang-fra"
            )

        start = time.monotonic()
        image = self._load_image(file_bytes, mime_type)
        raw_text = pytesseract.image_to_string(image, config=self.CONFIG)
        word_data = pytesseract.image_to_data(
            image,
            config=self.CONFIG,
            output_type=pytesseract.Output.DICT,
        )
        processing_ms = int((time.monotonic() - start) * 1000)

        fields = self._parse_fields(raw_text, word_data)

        return OCRExtractionResult(
            fields=fields,
            raw_text=raw_text,
            language="fra",
            processing_ms=processing_ms,
            provider=self.PROVIDER_NAME,
            provider_version=_tesseract_version(),
        )

    def _load_image(self, file_bytes: bytes, mime_type: str) -> "Image.Image":
        if mime_type == "application/pdf":
            # pdf2image not installed in PoC — convert first page via Pillow PDF
            # reader or fallback to raw bytes. For MVP, store PDF as-is and let
            # Tesseract handle it via its built-in PDF reader.
            return Image.open(io.BytesIO(file_bytes))
        return Image.open(io.BytesIO(file_bytes))

    def _parse_fields(
        self, raw_text: str, word_data: dict
    ) -> list[OCRField]:
        fields: list[OCRField] = []
        lines = raw_text.splitlines()
        current_appreciation_lines: list[str] = []
        last_matiere: str | None = None

        # Build a word→confidence map from Tesseract data output
        word_conf_map = self._build_word_conf_map(word_data)

        for line in lines:
            line = line.strip()
            if not line:
                if last_matiere and current_appreciation_lines:
                    appr_text = " ".join(current_appreciation_lines).strip()
                    if appr_text:
                        conf = self._text_confidence(appr_text, word_conf_map)
                        fields.append(OCRField(key="appreciation", value=appr_text, confidence=conf))
                    current_appreciation_lines = []
                    last_matiere = None
                continue

            # Trimestre header
            m_trim = _TRIMESTRE_RE.search(line)
            if m_trim:
                fields.append(OCRField(key="trimestre", value=m_trim.group(1), confidence=0.9))
                continue

            # Année header
            m_year = _ANNEE_RE.search(line)
            if m_year:
                fields.append(OCRField(key="annee", value=m_year.group(1), confidence=0.9))
                continue

            # Matière + note line
            m_note = _NOTE_RE.search(line)
            if m_note:
                matiere = m_note.group("matiere").strip()
                note_raw = m_note.group("note").replace(",", ".")
                note_conf = self._text_confidence(note_raw, word_conf_map)
                matiere_conf = self._text_confidence(matiere, word_conf_map)

                fields.append(OCRField(key="matiere", value=matiere, confidence=matiere_conf))
                fields.append(OCRField(key="note", value=note_raw, confidence=note_conf))
                last_matiere = matiere
                current_appreciation_lines = []
            elif last_matiere:
                # Line after a matière match — likely an appreciation
                current_appreciation_lines.append(line)

        # Flush last appreciation
        if last_matiere and current_appreciation_lines:
            appr_text = " ".join(current_appreciation_lines).strip()
            if appr_text:
                conf = self._text_confidence(appr_text, word_conf_map)
                fields.append(OCRField(key="appreciation", value=appr_text, confidence=conf))

        return fields

    @staticmethod
    def _build_word_conf_map(word_data: dict) -> dict[str, float]:
        conf_map: dict[str, float] = {}
        words = word_data.get("text", [])
        confs = word_data.get("conf", [])
        for word, conf in zip(words, confs):
            if word and str(conf).lstrip("-").isdigit():
                conf_val = max(0.0, min(1.0, int(conf) / 100))
                conf_map[word.lower()] = max(conf_map.get(word.lower(), 0.0), conf_val)
        return conf_map

    @staticmethod
    def _text_confidence(text: str, word_conf_map: dict[str, float]) -> float:
        words = text.lower().split()
        if not words:
            return 0.5
        scores = [word_conf_map.get(w, 0.5) for w in words]
        return sum(scores) / len(scores)
