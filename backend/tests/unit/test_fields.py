import pytest

from app.domain.errors import InvalidDocumentFields
from app.domain.fields import DocumentFields, normalize_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Bob", "bob"),
        ("  Bob  ", "bob"),
        ("Mary   Ann", "mary ann"),
        ("Mary\tAnn", "mary ann"),
        ("O'NEIL", "o'neil"),
        ("José", "josé"),
    ],
)
def test_normalize_name(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected


@pytest.mark.parametrize(("first", "last"), [("", "Smith"), ("Bob", "   ")])
def test_empty_fields_are_rejected(first: str, last: str) -> None:
    with pytest.raises(InvalidDocumentFields):
        _ = DocumentFields(first, last).normalized()
