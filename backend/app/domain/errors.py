class DomainError(Exception):
    """Base class for domain errors."""


class DocumentNotFound(DomainError):
    document_id: str

    def __init__(self, document_id: str) -> None:
        super().__init__(f"Document {document_id} is not registered")
        self.document_id = document_id


class InvalidDocumentFile(DomainError):
    """The uploaded file is not a valid PDF document."""
