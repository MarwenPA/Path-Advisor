"""Cross-cutting endpoints — health probe only in this story."""

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response


@extend_schema(
    summary="Liveness probe",
    description="Returns 200 when the API process is up. Used by Docker healthcheck and load balancers.",
    responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}},
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(_request: Request) -> Response:
    return Response({"status": "ok"})
