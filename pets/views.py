from django.shortcuts import render
from rest_framework.views import status, Request, Response, APIView
from pets.models import Pet
from rest_framework.pagination import PageNumberPagination
from pets.serializers import PetSerializer


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        pets = Pet.objects.all()
        result_pages = self.paginate_queryset(pets, request, view=self)
        serializer = PetSerializer(result_pages, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        ...
