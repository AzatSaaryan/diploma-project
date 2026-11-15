# pyright: reportAny=false
import secrets
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, UploadFile, status
from fastapi.security import APIKeyHeader

from app.application.ports.clock import Clock
from app.application.ports.pdf_stamper import PdfStamper
from app.application.ports.registry import Registry
from app.application.use_cases.get_document_status import GetDocumentStatus
from app.application.use_cases.register_document import RegisterDocument
from app.application.use_cases.revoke_document import RevokeDocument
from app.application.use_cases.verify_document import VerifyDocument
from app.settings import Settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_settings(request: Request) -> Settings:
    return cast("Settings", request.app.state.settings)


def get_registry(request: Request) -> Registry:
    return cast("Registry", request.app.state.registry)


def get_stamper(request: Request) -> PdfStamper:
    return cast("PdfStamper", request.app.state.stamper)


def get_clock(request: Request) -> Clock:
    return cast("Clock", request.app.state.clock)


SettingsDep = Annotated[Settings, Depends(get_settings)]
RegistryDep = Annotated[Registry, Depends(get_registry)]
StamperDep = Annotated[PdfStamper, Depends(get_stamper)]
ClockDep = Annotated[Clock, Depends(get_clock)]


def require_api_key(
    settings: SettingsDep,
    api_key: Annotated[str | None, Depends(_api_key_header)],
) -> None:
    expected = settings.api_key.get_secret_value().encode()
    if api_key is None or not secrets.compare_digest(api_key.encode(), expected):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )


async def read_upload(file: UploadFile, settings: Settings) -> bytes:
    limit = settings.max_file_size_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"File is larger than {limit} bytes",
        )
    return data


def get_register_document(
    registry: RegistryDep, stamper: StamperDep
) -> RegisterDocument:
    return RegisterDocument(registry, stamper)


def get_verify_document(
    registry: RegistryDep, stamper: StamperDep, clock: ClockDep
) -> VerifyDocument:
    return VerifyDocument(registry, stamper, clock)


def get_document_status(registry: RegistryDep, clock: ClockDep) -> GetDocumentStatus:
    return GetDocumentStatus(registry, clock)


def get_revoke_document(registry: RegistryDep) -> RevokeDocument:
    return RevokeDocument(registry)
