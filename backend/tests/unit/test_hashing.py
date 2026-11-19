from app.domain.fields import DocumentFields
from app.domain.hashing import compute_hash, hash_document_id, hash_fields

DOC_ID = "ab" * 16


def test_known_vector() -> None:
    assert compute_hash(b"abc").hex() == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_hash_document_id_is_32_bytes_and_deterministic() -> None:
    assert len(hash_document_id(DOC_ID)) == 32
    assert hash_document_id(DOC_ID) == hash_document_id(DOC_ID)
    assert hash_document_id(DOC_ID) != hash_document_id("cd" * 16)


def test_hash_fields_ignores_case_and_spacing() -> None:
    a = hash_fields(DocumentFields("Bob", "Smith"), DOC_ID)
    b = hash_fields(DocumentFields("  bob ", "SMITH"), DOC_ID)
    assert a == b
    assert len(a) == 32


def test_id_works_as_salt() -> None:
    fields = DocumentFields("Bob", "Smith")
    assert hash_fields(fields, DOC_ID) != hash_fields(fields, "cd" * 16)


def test_swapped_fields_differ() -> None:
    a = hash_fields(DocumentFields("Bob", "Smith"), DOC_ID)
    b = hash_fields(DocumentFields("Smith", "Bob"), DOC_ID)
    assert a != b


def test_no_concatenation_ambiguity() -> None:
    a = hash_fields(DocumentFields("Bo", "bsmith"), DOC_ID)
    b = hash_fields(DocumentFields("Bob", "smith"), DOC_ID)
    assert a != b


def test_fields_hash_differs_from_id_hash() -> None:
    assert hash_fields(DocumentFields("Bob", "Smith"), DOC_ID) != hash_document_id(
        DOC_ID
    )
