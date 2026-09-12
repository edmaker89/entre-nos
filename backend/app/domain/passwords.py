from argon2 import PasswordHasher
from argon2.exceptions import VerificationError


hasher = PasswordHasher()


def verify_password(encoded: str, password: str) -> bool:
    try:
        return hasher.verify(encoded, password)
    except VerificationError:
        return False


def hash_password(password: str) -> str:
    return hasher.hash(password)


def validate_new_password(password: str, *, current_hash: str | None = None) -> str:
    if not isinstance(password, str) or not 15 <= len(password) <= 200:
        raise ValueError("Use uma senha de 15 a 200 caracteres.")
    if current_hash and verify_password(current_hash, password):
        raise ValueError("A nova senha deve ser diferente da senha atual.")
    return password
