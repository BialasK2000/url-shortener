from django.urls import path, register_converter

from shortener import views
from shortener.utils import SHORT_CODE_LENGTH, ShortCode


class ShortCodeConverter:
    regex = f"[a-zA-Z0-9]{{{SHORT_CODE_LENGTH}}}"

    def to_python(self, value: str) -> ShortCode:
        return ShortCode(value)

    def to_url(self, value: str) -> str:
        return value


register_converter(ShortCodeConverter, "short_code")

app_name = "shortener"

urlpatterns = [
    path("shrt/", views.ShortenView.as_view(), name="shorten"),
    path("shrt/<short_code:code>", views.RedirectShortUrlView.as_view(), name="redirect"),
    path("expand/", views.ExpandView.as_view(), name="expand"),
]
