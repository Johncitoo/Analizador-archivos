from django.db.models import Count, Sum
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .detector import detectar_tipo, obtener_extension
from .models import ArchivoAnalizado
from .serializers import ArchivoAnalizadoSerializer, SubidaArchivoSerializer


class ArchivoAnalizadoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Listar, ver el detalle, subir archivos y obtener estadísticas."""

    queryset = ArchivoAnalizado.objects.order_by("-fecha")
    serializer_class = ArchivoAnalizadoSerializer
    parser_classes = [MultiPartParser]

    @extend_schema(
        request={"multipart/form-data": SubidaArchivoSerializer},
        responses={201: ArchivoAnalizadoSerializer},
        summary="Subir y analizar un archivo",
    )
    def create(self, request):
        subida = SubidaArchivoSerializer(data=request.data)
        subida.is_valid(raise_exception=True)
        archivo = subida.validated_data["archivo"]

        # Solo se guarda el resultado del análisis, no el archivo en sí
        datos = archivo.read()
        resultado = detectar_tipo(datos)

        registro = ArchivoAnalizado.objects.create(
            nombre=archivo.name,
            extension=obtener_extension(archivo.name),
            tipo_detectado=resultado.tipo,
            mime=resultado.mime,
            tamano=archivo.size,
        )
        return Response(ArchivoAnalizadoSerializer(registro).data, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Estadísticas de archivos analizados")
    @action(detail=False)
    def estadisticas(self, request):
        archivos = ArchivoAnalizado.objects.all()
        totales = archivos.aggregate(total=Count("id"), tamano_total=Sum("tamano"))
        # GROUP BY tipo_detectado
        por_tipo = (
            archivos.values("tipo_detectado")
            .annotate(cantidad=Count("id"), tamano_total=Sum("tamano"))
            .order_by("-cantidad")
        )
        return Response({
            "total_archivos": totales["total"],
            "tamano_total": totales["tamano_total"] or 0,
            "por_tipo": list(por_tipo),
        })
