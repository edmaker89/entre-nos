"""AUTH-RESET-01 AC8: shared password policy."""

import pytest

from app.domain.passwords import hash_password, validate_new_password, verify_password


def test_minimum_length_is_fifteen_characters():
    assert validate_new_password("a" * 15) == "a" * 15
    with pytest.raises(ValueError, match="15 a 200"):
        validate_new_password("a" * 14)


def test_maximum_length_is_two_hundred_characters():
    assert validate_new_password("a" * 200) == "a" * 200
    with pytest.raises(ValueError, match="15 a 200"):
        validate_new_password("a" * 201)


def test_spaces_are_preserved_and_count_toward_length():
    password = "  frase com espaços  "
    assert validate_new_password(password) == password


def test_unicode_is_accepted_without_normalization():
    password = "áβ🙂 senha longa  漢"
    assert validate_new_password(password) == password


def test_identical_current_password_is_rejected():
    current = hash_password("senha atual longa")
    with pytest.raises(ValueError, match="diferente da senha atual"):
        validate_new_password("senha atual longa", current_hash=current)


def test_different_password_is_accepted_against_current_hash():
    current = hash_password("senha atual longa")
    assert validate_new_password("senha nova bem longa", current_hash=current) == "senha nova bem longa"


def test_hash_round_trip_and_wrong_password():
    encoded = hash_password("uma senha muito longa")
    assert encoded != "uma senha muito longa"
    assert verify_password(encoded, "uma senha muito longa") is True
    assert verify_password(encoded, "outra senha também longa") is False


@pytest.mark.parametrize("invalid", [None, 123, b"fifteen-characters"])
def test_non_text_password_is_rejected(invalid):
    with pytest.raises(ValueError, match="15 a 200"):
        validate_new_password(invalid)
