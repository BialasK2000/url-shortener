from django.db import IntegrityError

from shortener.models import ShortenedUrl
from shortener.utils import generate_short_code

MAX_ATTEMPTS = 10


def get_or_create_short_url(url: str) -> tuple[ShortenedUrl, bool]:
    for _ in range(MAX_ATTEMPTS):
        try:
            return ShortenedUrl.objects.get_or_create(
                url=url, defaults={"code": generate_short_code()}
            )
        except IntegrityError:
            # get_or_create handles a paralell insert of the same url
            # getting here means the generated code is already taken
            continue
    raise RuntimeError(f"Could not generate a unique short code in {MAX_ATTEMPTS} attempts")
