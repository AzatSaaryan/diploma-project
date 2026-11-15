# pyright: reportUnusedParameter=false
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.application.errors import RegistryUnavailable
from app.domain.errors import DocumentNotFound, InvalidDocumentFile


def _json(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": detail})


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DocumentNotFound)
    async def _not_found(_: Request, exc: DocumentNotFound) -> JSONResponse:
        return _json(status.HTTP_404_NOT_FOUND, str(exc))

    @app.exception_handler(InvalidDocumentFile)
    async def _invalid_file(_: Request, exc: InvalidDocumentFile) -> JSONResponse:
        return _json(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc))

    @app.exception_handler(RegistryUnavailable)
    async def _unavailable(_: Request, __: RegistryUnavailable) -> JSONResponse:
        return _json(status.HTTP_503_SERVICE_UNAVAILABLE, "Registry is unavailable")
