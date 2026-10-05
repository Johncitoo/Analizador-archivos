from rest_framework import serializers

from .detector import obtener_extension
from .models import ArchivoAnalizado

TAMANO_MAXIMO = 20 * 1024 * 1024  # 20 MB


class ArchivoAnalizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivoAnalizado
        fields = ["id", "nombre", "extension", "tipo_detectado", "mime", "tamano", "fecha"]
        read_only_fields = fields


class SubidaArchivoSerializer(serializers.Serializer):
    archivo = serializers.FileField()

    def validate_archivo(self, archivo):
        if archivo.size > TAMANO_MAXIMO:
            raise serializers.ValidationError("El archivo supera el máximo de 20 MB.")
        max_extension = ArchivoAnalizado._meta.get_field("extension").max_length
        if len(obtener_extension(archivo.name)) > max_extension:
            raise serializers.ValidationError(
                f"La extensión del archivo no puede superar {max_extension} caracteres."
            )
        return archivo
