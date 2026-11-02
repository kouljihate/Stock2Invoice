"""Password hashing — bcrypt stays *inside* identity, never crosses the wire."""

import bcrypt as _bcrypt


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')


def check_password(hashed: str, plain: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False
