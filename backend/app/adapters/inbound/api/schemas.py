from datetime import datetime

from pydantic import BaseModel

from app.domain.status import Status


class VerificationResponse(BaseModel):
    status: Status
    document_id: str | None
    issuer: str | None
    issued_at: datetime | None
    expires_at: datetime | None


class RevocationResponse(BaseModel):
    document_id: str
    transaction_hash: str | None
