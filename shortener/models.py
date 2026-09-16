from django.core.validators import URLValidator
from django.db import models

from shortener.utils import SHORT_CODE_LENGTH

MAX_URL_LENGTH = 2048

http_url_validator = URLValidator(schemes=["http", "https"])


class ShortenedUrl(models.Model):
    code = models.CharField(primary_key=True, max_length=SHORT_CODE_LENGTH)
    url = models.URLField(max_length=MAX_URL_LENGTH, unique=True, validators=[http_url_validator])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.code} -> {self.url}"
