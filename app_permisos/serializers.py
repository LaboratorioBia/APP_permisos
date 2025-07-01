from rest_framework import serializers
from .models import Licencia


class LicenciaSerializer(serializers.ModelSerializer):
    """Serializer para la clase Licencia."""

    motivo_licencia = serializers.CharField(
        source="motivo_licencia.name_motivo_licencia"
    )
    creada_por = serializers.CharField(source="creada_por.username")
    area = serializers.CharField(source="area.nombre_area")
    estado = serializers.CharField(source="estado_licencia")
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()

    class Meta:
        model = Licencia
        fields = [
            "nombre_completo",
            "cedula",
            "area",
            "fecha_inicio",
            "fecha_fin",
            "motivo_licencia",
            "estado",
            "creada_por",
        ]
