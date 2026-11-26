from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()
# Позволяет проверять несуществующий логин без быстрого выхода до хэширования.
dummy_hash = password_hasher.hash("dummy-password-for-timing-comparison")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)
