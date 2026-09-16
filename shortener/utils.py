import secrets
import string
from typing import NewType

ShortCode = NewType("ShortCode", str)

SHORT_CODE_LENGTH = 7
SHORT_CODE_CHARS = string.ascii_letters + string.digits


def generate_short_code() -> ShortCode:
    return ShortCode("".join(secrets.choice(SHORT_CODE_CHARS) for _ in range(SHORT_CODE_LENGTH)))
