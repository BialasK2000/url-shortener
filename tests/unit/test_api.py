import pytest
from rest_framework.test import APIClient

from shortener.models import MAX_URL_LENGTH, ShortenedUrl

pytestmark = pytest.mark.django_db

# village in Wales with a 58-letter name, about as long as a real URL gets I guess...
LONG_URL = (
    "https://en.wikipedia.org/wiki/Llanfairpwllgwyngyllgogerychwyrndrobwllllantysiliogogogoch"
)
SHORT_URL = "http://testserver/shrt/Wales58"
# reporter from Channel 4 News pronouncing the name of that village
PRONUNCIATION_URL = "https://www.youtube.com/watch?v=fHxO0UdpoxM"


@pytest.fixture
def shortened_url() -> ShortenedUrl:
    return ShortenedUrl.objects.create(code="Wales58", url=LONG_URL)


def test_shorten(api_client: APIClient) -> None:
    response = api_client.post("/shrt/", {"url": LONG_URL})

    assert response.status_code == 201
    code = ShortenedUrl.objects.get().code
    assert response.json() == {"url": LONG_URL, "short_url": f"http://testserver/shrt/{code}"}


def test_shorten_same_url_twice(api_client: APIClient) -> None:
    first = api_client.post("/shrt/", {"url": PRONUNCIATION_URL})
    second = api_client.post("/shrt/", {"url": PRONUNCIATION_URL})

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json() == first.json()
    assert ShortenedUrl.objects.count() == 1


@pytest.mark.parametrize(
    ("payload", "error"),
    [
        ({}, "This field is required."),
        ({"url": ""}, "This field may not be blank."),
        ({"url": "definitely not a url"}, "Enter a valid URL."),
        ({"url": "www.djangoproject.com"}, "Enter a valid URL."),
        ({"url": "javascript:alert('pwned')"}, "Enter a valid URL."),
        ({"url": "ftp://ftp.example.com/cats.zip"}, "Only http and https URLs are allowed."),
    ],
)
def test_shorten_invalid_url(api_client: APIClient, payload: dict[str, str], error: str) -> None:
    response = api_client.post("/shrt/", payload)

    assert response.status_code == 400
    assert response.json() == {"url": [error]}
    assert not ShortenedUrl.objects.exists()


def test_shorten_too_long_url(api_client: APIClient) -> None:
    too_long_url = LONG_URL + "?q=" + "a" * MAX_URL_LENGTH

    response = api_client.post("/shrt/", {"url": too_long_url})

    assert response.status_code == 400
    errors = response.json()["url"]
    assert f"Ensure this field has no more than {MAX_URL_LENGTH} characters." in errors
    assert not ShortenedUrl.objects.exists()


@pytest.mark.usefixtures("shortened_url")
def test_expand(api_client: APIClient) -> None:
    response = api_client.post("/expand/", {"short_url": SHORT_URL})

    assert response.status_code == 200
    assert response.json() == {"url": LONG_URL, "short_url": SHORT_URL}


@pytest.mark.usefixtures("shortened_url")
@pytest.mark.parametrize(
    "short_url",
    [
        "https://127.0.0.1:8000/shrt/Wales58",
        "http://testserver/shrt/Wales%358",
        "http://testserver/shrt/Wales58?utm_source=carrier_pigeon",
    ],
)
def test_expand_accepts_short_url_variants(api_client: APIClient, short_url: str) -> None:
    response = api_client.post("/expand/", {"short_url": short_url})

    assert response.status_code == 200
    assert response.json() == {"url": LONG_URL, "short_url": SHORT_URL}


@pytest.mark.usefixtures("shortened_url")
def test_expand_unknown_code(api_client: APIClient) -> None:
    response = api_client.post("/expand/", {"short_url": "http://testserver/shrt/Nope404"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Short URL not found."}


@pytest.mark.usefixtures("shortened_url")
@pytest.mark.parametrize(
    "short_url",
    [
        "",
        "definitely not a url",
        LONG_URL,
        "http://testserver/expand/",
        "http://testserver/shrt/tiny",
        "http://testserver/shrt/Wales58/",
        "http://[/shrt/Wales58",
        "/shrt/Wales58",
        "//testserver/shrt/Wales58",
        "ftp://testserver/shrt/Wales58",
        "http://testserver/shrt/Wales58;jsessionid=1337",
    ],
)
def test_expand_invalid_short_url(api_client: APIClient, short_url: str) -> None:
    response = api_client.post("/expand/", {"short_url": short_url})

    assert response.status_code == 400
    assert "short_url" in response.json()


@pytest.mark.usefixtures("shortened_url")
def test_redirect(api_client: APIClient) -> None:
    response = api_client.get("/shrt/Wales58")

    assert response.status_code == 302
    assert response["Location"] == LONG_URL


@pytest.mark.usefixtures("shortened_url")
def test_redirect_with_html_accept_header(api_client: APIClient) -> None:
    response = api_client.get("/shrt/Wales58", HTTP_ACCEPT="text/html")

    assert response.status_code == 302
    assert response["Location"] == LONG_URL


@pytest.mark.usefixtures("shortened_url")
@pytest.mark.parametrize("path", ["/shrt/Nope404", "/shrt/tiny", "/shrt/wayTooLong"])
def test_redirect_not_found(api_client: APIClient, path: str) -> None:
    response = api_client.get(path)

    assert response.status_code == 404
