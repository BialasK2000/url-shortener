from unittest import mock

import pytest

from shortener.models import ShortenedUrl
from shortener.services import MAX_ATTEMPTS, get_or_create_short_url

pytestmark = pytest.mark.django_db

LONG_URL = "http://example.com/very/long/url/super-uber-long-wow-long-long-url-omg"
OTHER_URL = "https://www.django-rest-framework.org/api-guide/serializers/#modelserializer"


def test_creates_short_url() -> None:
    shortened_url, created = get_or_create_short_url(LONG_URL)

    assert created
    assert ShortenedUrl.objects.get(code=shortened_url.code).url == LONG_URL


def test_returns_existing_short_url_for_same_url() -> None:
    first, _ = get_or_create_short_url(LONG_URL)
    second, created = get_or_create_short_url(LONG_URL)

    assert not created
    assert second.code == first.code
    assert ShortenedUrl.objects.count() == 1


def test_retries_when_code_is_taken() -> None:
    ShortenedUrl.objects.create(code="abc1234", url=OTHER_URL)

    with mock.patch("shortener.services.generate_short_code", side_effect=["abc1234", "xyz7890"]):
        shortened_url, created = get_or_create_short_url(LONG_URL)

    assert created
    assert shortened_url.code == "xyz7890"
    assert ShortenedUrl.objects.get(code="abc1234").url == OTHER_URL


def test_gives_up_after_max_attempts() -> None:
    ShortenedUrl.objects.create(code="abc1234", url=OTHER_URL)

    with (
        mock.patch("shortener.services.generate_short_code", return_value="abc1234") as generate,
        pytest.raises(RuntimeError),
    ):
        get_or_create_short_url(LONG_URL)

    assert generate.call_count == MAX_ATTEMPTS
