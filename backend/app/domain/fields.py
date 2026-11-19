import unicodedata
from dataclasses import dataclass

from app.domain.errors import InvalidDocumentFields


def normalize_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split()).casefold()


@dataclass(frozen=True, slots=True)
class DocumentFields:
    first_name: str
    last_name: str

    def normalized(self) -> DocumentFields:
        normalized = DocumentFields(
            first_name=normalize_name(self.first_name),
            last_name=normalize_name(self.last_name),
        )
        if not normalized.first_name or not normalized.last_name:
            raise InvalidDocumentFields("First name and last name must not be empty")
        return normalized
