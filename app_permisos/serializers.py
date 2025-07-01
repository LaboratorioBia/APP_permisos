from rest_framework import serializers
from .models import Licencia

class LicenciaSerializer(serializers.ModelSerializer):
    area = serializers.CharField(source='area.nombre', default="")
    motivo = serializers.CharField(source='motivo_licencia.nombre', default="")
    estado = serializers.CharField(source='verificacion_licencia', default="")
    creado_por = serializers.CharField(source='creada_por.username', default="")

    class Meta:
        model = Licencia
        fields = [
            'nombre_completo',
            'cedula',
            'area',
            'fecha_inicio',
            'fecha_fin',
            'motivo',
            'estado',
            'creado_por',
        ]
