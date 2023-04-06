from django.shortcuts import render
from rest_framework.views import status, Request, Response, APIView
from pets.models import Pet
from groups.models import Group
from traits.models import Trait
from rest_framework.pagination import PageNumberPagination
from pets.serializers import PetSerializer


class PetView(APIView, PageNumberPagination):
    def get(self, request: Request) -> Response:
        traits = request.query_params.get("trait", None)
        if traits:
            pets = Pet.objects.filter(traits__name__iexact=traits)
        else:
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


class PetViewDetail(APIView):
    def get(self, request: Request, pet_id: int) -> Response:
        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PetSerializer(instance=pet)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request: Request, pet_id: int) -> Response:
        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        pet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def patch(self, request: Request, pet_id) -> Response:
        try:
            pet = Pet.objects.get(id=pet_id)
        except Pet.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = PetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        group_request = serializer.validated_data.pop("group", None)

        if group_request:
            try:
                group_obj = Group.objects.get(
                    scientific_name=group_request["scientific_name"]
                )
            except Group.DoesNotExist:
                group_obj = Group.objects.create(**group_request)
            pet.group = group_obj
            pet.save()

        traits_request = serializer.validated_data.pop("traits", None)

        if traits_request:
            pet.traits.clear()
            for trait_data in traits_request:
                trait = Trait.objects.filter(name__iexact=trait_data["name"]).first()
                if not trait:
                    trait = Trait.objects.create(**trait_data)
                pet.traits.add(trait)

        for key, value in serializer.validated_data.items():
            setattr(pet, key, value)

        serializer = PetSerializer(pet)
        return Response(serializer.data, status=status.HTTP_200_OK)
