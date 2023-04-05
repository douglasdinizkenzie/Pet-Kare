from django.shortcuts import render
from rest_framework.views import status, Request, Response, APIView
from pets.models import Pet
from groups.models import Group
from traits.models import Trait
from rest_framework.pagination import PageNumberPagination
from pets.serializers import PetSerializer


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        pets = Pet.objects.all()
        result_pages = self.paginate_queryset(pets, request, view=self)
        serializer = PetSerializer(result_pages, many=True)
        return self.get_paginated_response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = PetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        groups = serializer.validated_data.pop("group")
        traits = serializer.validated_data.pop("traits")

        groups_obj = Group.objects.filter(
            scientific_name__iexact=groups["scientific_name"]
        ).first()

        if not groups_obj:
            groups_obj = Group.objects.create(**groups)

        pet_obj = Pet.objects.create(**serializer.validated_data, group=groups_obj)

        for trait in traits:
            traits_obj = Trait.objects.filter(name__iexact=trait["name"]).first()
            if not traits_obj:
                traits_obj = Trait.objects.create(**trait)

            pet_obj.traits.add(traits_obj)

        serializer = PetSerializer(instance=pet_obj)

        return Response(serializer.data, 201)
