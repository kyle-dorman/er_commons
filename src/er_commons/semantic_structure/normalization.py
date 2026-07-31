"""Text normalization owned by the semantic alias contract."""

import unicodedata


def normalize_alias(value: str) -> str:
    """Normalize a target name without deleting punctuation or numbering."""
    normalized = unicodedata.normalize("NFC", value).replace("\u00a0", " ")
    return " ".join(normalized.split()).strip().casefold()
