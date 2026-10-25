from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import EventCreateSerializer, EventSerializer


class EventCreateView(APIView):
    @extend_schema(
        summary="Record a user interaction (view / search / like / save)",
        description="The weight is calculated by the server from event_type "
                    "(view=1, search=2, like=3, save=4). Any weight in the body is ignored.",
        request=EventCreateSerializer,
        responses={201: EventSerializer},
    )
    def post(self, request):
        serializer = EventCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        interaction = serializer.save()
        return Response(EventSerializer(interaction).data, status=status.HTTP_201_CREATED)
