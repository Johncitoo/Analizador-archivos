from rest_framework import serializers

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
        return archivo
