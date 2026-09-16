from collections.abc import Iterator

import httpx
import pytest
from pytest_django.live_server_helper import LiveServer

pytestmark = [pytest.mark.e2e, pytest.mark.django_db(transaction=True)]

LONG_URL = (
    "https://en.wikipedia.org/wiki/Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch"
)
PRONUNCIATION_URL = "https://www.youtube.com/watch?v=fHxO0UdpoxM"
DRF_DOCS_URL = "https://www.django-rest-framework.org/api-guide/serializers/#modelserializer"


@pytest.fixture
def http(live_server: LiveServer) -> Iterator[httpx.Client]:
    with httpx.Client(base_url=live_server.url, timeout=5) as client:
        yield client


def shorten(http: httpx.Client, url: str) -> str:
    response = http.post("/shrt/", json={"url": url})
    assert response.status_code == 201
    short_url: str = response.json()["short_url"]
    return short_url


def test_shorten_and_expand(http: httpx.Client, live_server: LiveServer) -> None:
    short_url = shorten(http, LONG_URL)
    assert short_url.startswith(f"{live_server.url}/shrt/")

    response = http.post("/expand/", json={"short_url": short_url})

    assert response.status_code == 200
    assert response.json() == {"url": LONG_URL, "short_url": short_url}


def test_short_url_redirects(http: httpx.Client) -> None:
    short_url = shorten(http, LONG_URL)

    response = http.get(short_url)

    assert response.status_code == 302
    assert response.headers["location"] == LONG_URL


def test_same_url_returns_existing_short_url(http: httpx.Client) -> None:
    first = http.post("/shrt/", json={"url": PRONUNCIATION_URL})
    second = http.post("/shrt/", json={"url": PRONUNCIATION_URL})

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()


def test_multiple_urls(http: httpx.Client) -> None:
    urls = [LONG_URL, PRONUNCIATION_URL, DRF_DOCS_URL]
    short_urls = [shorten(http, url) for url in urls]
    assert len(set(short_urls)) == len(urls)

    for short_url, url in zip(short_urls, urls, strict=True):
        response = http.post("/expand/", json={"short_url": short_url})
        assert response.json()["url"] == url


def test_invalid_and_unknown_urls(http: httpx.Client, live_server: LiveServer) -> None:
    unknown_short_url = f"{live_server.url}/shrt/Nope404"

    assert http.post("/shrt/", json={"url": "definitely not a url"}).status_code == 400
    assert http.post("/expand/", json={"short_url": unknown_short_url}).status_code == 404
    assert http.get(unknown_short_url).status_code == 404
