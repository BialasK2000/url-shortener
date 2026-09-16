from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views import View
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from shortener.models import ShortenedUrl
from shortener.serializers import ExpandSerializer, ShortenedUrlSerializer
from shortener.services import get_or_create_short_url
from shortener.utils import ShortCode


class ShortenView(APIView):
    def post(self, request: Request) -> Response:
        serializer = ShortenedUrlSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shortened_url, created = get_or_create_short_url(serializer.validated_data["url"])

        output = ShortenedUrlSerializer(shortened_url, context={"request": request})
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(output.data, status=response_status)


class ExpandView(APIView):
    def post(self, request: Request) -> Response:
        serializer = ExpandSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            shortened_url = ShortenedUrl.objects.get(code=serializer.validated_data["code"])
        except ShortenedUrl.DoesNotExist:
            raise NotFound("Short URL not found.") from None

        output = ShortenedUrlSerializer(shortened_url, context={"request": request})
        return Response(output.data)


class RedirectShortUrlView(View):
    def get(self, request: HttpRequest, code: ShortCode) -> HttpResponseRedirect:
        shortened_url = get_object_or_404(ShortenedUrl, code=code)
        return HttpResponseRedirect(shortened_url.url)
