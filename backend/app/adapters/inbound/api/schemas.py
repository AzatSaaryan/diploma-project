from datetime import datetime
from typing import Annotated, ClassVar

from pydantic import AwareDatetime, BaseModel, ConfigDict, StringConstraints

from app.application.use_cases.evaluate import VerificationResult
from app.domain.fields import DocumentFields
from app.domain.status import Status

Name = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z][A-Za-z .'-]*$",
    ),
]


class FieldsIn(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        json_schema_extra={"examples": [{"first_name": "Bob", "last_name": "Smith"}]}
    )

    first_name: Name
    last_name: Name

    def to_domain(self) -> DocumentFields:
        return DocumentFields(first_name=self.first_name, last_name=self.last_name)


class RegisterRequest(FieldsIn):
    expires_at: AwareDatetime | None = None


class LookupResponse(BaseModel):
    document_id: str
    registered: bool


class VerificationResponse(BaseModel):
    status: Status
    document_id: str | None
    first_name: str | None
    last_name: str | None
    issuer: str | None
    issued_at: datetime | None
    expires_at: datetime | None

    @classmethod
    def from_result(cls, result: VerificationResult) -> VerificationResponse:
        record = result.record
        fields = result.fields
        return cls(
            status=result.status,
            document_id=result.document_id,
            first_name=fields.first_name if fields else None,
            last_name=fields.last_name if fields else None,
            issuer=record.issuer if record else None,
            issued_at=record.issued_at if record else None,
            expires_at=record.expires_at if record else None,
        )


class RevocationResponse(BaseModel):
    document_id: str
    revoked: bool
