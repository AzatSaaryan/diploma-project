from app.domain.hashing import compute_hash


def test_known_vector() -> None:
    assert compute_hash(b"abc").hex() == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_length_is_32_bytes() -> None:
    assert len(compute_hash(b"")) == 32
