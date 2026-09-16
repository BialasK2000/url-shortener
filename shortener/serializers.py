from typing import Any
from urllib.parse import unquote, urlsplit

from django.urls import Resolver404, resolve, reverse
from rest_framework import serializers
from rest_framework.request import Request

from shortener.models import MAX_URL_LENGTH, ShortenedUrl, http_url_validator
from shortener.utils import ShortCode


def get_code_from_short_url(short_url: str) -> ShortCode | None:
    # host is not checked, the same app can be reached via localhost, 127.0.0.1, proxy etc.
    try:
        parts = urlsplit(short_url)
    except ValueError:  # malformed url ("http://[*]/shrt/abc1234" etc.)
        return None
    if parts.scheme not in http_url_validator.schemes or not parts.netloc:
        return None
    try:
        match = resolve(unquote(parts.path))
    except Resolver404:
        return None
    if match.view_name != "shortener:redirect":
        return None
    code: ShortCode = match.kwargs["code"]
    return code


class ShortenedUrlSerializer(serializers.ModelSerializer[ShortenedUrl]):
    # declared explicitly, otherwise ModelSerializer adds a UniqueValidator and shortening
    # already shortened url would fail with 400
    url = serializers.URLField(max_length=MAX_URL_LENGTH)
    short_url = serializers.SerializerMethodField()

    class Meta:
        model = ShortenedUrl
        fields = ("url", "short_url")

    def validate_url(self, value: str) -> str:
        # URLField in default accepts ftp:// and ftps:// too, short links we create
        # I assume are meant for web pages only.
        if urlsplit(value).scheme not in http_url_validator.schemes:
            raise serializers.ValidationError("Only http and https URLs are allowed.")
        return value

    def get_short_url(self, obj: ShortenedUrl) -> str:
        request: Request = self.context["request"]
        return request.build_absolute_uri(reverse("shortener:redirect", args=[obj.code]))


class ExpandSerializer(serializers.Serializer[None]):
    # CharField purposefully, URLField rejects hosts without TLD (testserver etc.)
    short_url = serializers.CharField(max_length=MAX_URL_LENGTH)

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        code = get_code_from_short_url(attrs["short_url"])
        if code is None:
            raise serializers.ValidationError({"short_url": "Not a valid short URL."})
        attrs["code"] = code
        return attrs
