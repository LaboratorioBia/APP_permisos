from django.db import models
from django.contrib.auth.models import User, AbstractUser, Group, Permission # Importa la clase User    
import os
from django.core.validators import RegexValidator
from django.utils import timezone

# PERMISOS
class Area(models.Model):
    """
    Modelo para representar las áreas disponibles.

    Atributos:
        - nombre_area (str): Nombre del área.
    """
    nombre_area = models.CharField(max_length=50)
    def __str__(self):
        return self.nombre_area

class MotivoPermiso(models.Model):
    """
    Modelo para representar los motivos posibles para solicitar un permiso.

    Atributos:
        - name_motivo (str): Nombre del motivo.
    """
    name_motivo = models.CharField(max_length=80)
    def __str__(self):
        return self.name_motivo

class Turno(models.Model):
    """
    Modelo para representar los turnos de los empleados.

    Atributos:
        - name_turno (str): Nombre del turno.
    """
    name_turno = models.CharField(max_length=20)
    def __str__(self):
        return self.name_turno

VERIFICACION_CHOICES = [
        ("Aprobado", "Aprobado"),
        ("Rechazado", "Rechazado"),
]

COMPENSATIEMPO_CHOICES = [
    ("Si", "Si"), 
    ("No", "No"),
]

#USERS
class CustomUser(AbstractUser):
    """
    Modelo personalizado de usuarios.

    Atributos:
        - es_coordinador (bool): Indica si el usuario es coordinador.
        - area (ForeignKey): Relación con el modelo Area.
    """
    es_coordinador = models.BooleanField(default=False)
    groups = models.ManyToManyField(Group, verbose_name='grupos', blank=True, related_name='customuser_set')
    user_permissions = models.ManyToManyField(Permission, verbose_name='Permisos usuario', blank=True, related_name='customuser_set')
    area = models.ForeignKey(Area, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return self.username   

class Permiso(models.Model):
    """
    Modelo para representar la información de los permisos.

    Atributos:
        - creado (DateTimeField): Fecha y hora de creación del permiso.
        - nombre_completo (str): Nombre completo del empleado al que se le va a solicitar el permiso.
        - cedula (str): Número de cédula del empleado.
        - area (ForeignKey): Relación con el modelo Area.
        - turno (ForeignKey): Relación con el modelo Turno.
        - fecha_permiso (DateField): Fecha en que se solicita el permiso.
        - fecha_fin_permiso (DateField): Fecha de finalización del permiso (opcional).
        - hora_salida (TimeField): Hora de salida solicitada (opcional).
        - hora_llegada (TimeField): Hora de llegada solicitada (opcional).
        - motivo_permiso (ForeignKey): Relación con el modelo MotivoPermiso.
        - nombre_coordinador (str): Nombre del coordinador asignado.
        - compensa_tiempo (str): Opción para compensar tiempo (Si/No).
        - datos_adjuntos (FileField): Archivo adjunto al permiso (opcional).
        - observacion (TextField): Observaciones adicionales del permiso (opcional).
        - creado_por (ForeignKey): Usuario que creó el permiso.
        - verificacion (str): Estado de verificación del permiso (Aprobado/Rechazado).
        - estado (TextField): Información adicional del usuario que verifico el permiso.
        - verificado_por (ForeignKey): Usuario que verificó el permiso.
        - fecha_verificacion (DateTimeField): Fecha y hora de verificación.
        
    Métodos:
        - save(*args, **kwargs): Guarda la licencia en la base de datos.
        - nombre_archivo(): Devuelve el nombre del archivo adjunto de los permisos.
    """
    creado = models.DateTimeField(auto_now_add=True)
    nombre_completo = models.CharField(max_length=100)
    cedula = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex='^[0-9]*$', message='La cedula debe contener solo números.')],
    )
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE)
    fecha_permiso = models.DateField()
    fecha_fin_permiso = models.DateField(null=True)
    hora_salida = models.TimeField(blank=True, null=True)
    hora_llegada = models.TimeField(blank=True, null=True)
    motivo_permiso = models.ForeignKey(MotivoPermiso, on_delete=models.CASCADE)
    nombre_coordinador = models.CharField(max_length=50) 
    compensa_tiempo = models.CharField(max_length=3, choices=COMPENSATIEMPO_CHOICES)
    datos_adjuntos = models.FileField(upload_to='archivos_adjuntos/documento/', null=True, blank=True)
    observacion = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=None, editable=False, related_name='Permiso_Creado_Por')
    verificacion = models.CharField(max_length=20, choices=VERIFICACION_CHOICES, blank=True, null=True, editable=True)
    estado = models.TextField(blank=True, null=True, editable=True)
    verificado_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, editable=False, related_name='Permiso_Verificado_Por')
    fecha_verificacion = models.DateTimeField(null=True, blank=True, editable=False)

    def save(self, *args, **kwargs):
        """
        Guarda el objeto Permiso en la base de datos.

        Este método se encarga de realizar algunas acciones antes de guardar el objeto, como verificar y actualizar el nombre del archivo adjunto y la fecha de verificación.

        Args:
            - *args: Argumentos posicionales adicionales.
            - **kwargs: Argumentos de palabras clave adicionales.

        Return:
            None
        """
        # Verifica si ya existe el archivo y actualiza el nombre si es necesario
        if self.datos_adjuntos:
            nombre_archivo = os.path.basename(self.datos_adjuntos.name)
            if not nombre_archivo:
                # Si el nombre del archivo no está configurado, configúralo
                self.datos_adjuntos.name = f'archivos_adjuntos/documento/{self.nombre_archivo()}'

        if self.pk and self.verificado_por and self.verificado_por.groups.filter(name='Admin').exists():
            self.fecha_verificacion = timezone.now()

        super(Permiso, self).save(*args, **kwargs)

    def nombre_archivo(self):
        """
        Devuelve el nombre del archivo adjunto.

        Return:
            str: Nombre del archivo adjunto o None si no hay archivo adjunto.
        """
        if self.datos_adjuntos:
            return os.path.basename(self.datos_adjuntos.name)
        else:
            return None
# ----------------------------------------------------------------------------------------------------------------------------------------------------------#
# LICENCIAS
class Empresa(models.Model):
    """
    Modelo para representar las diferentes empresas.

    Atributos:
        - name_empresa (str): Nombre de la empresa.

    Métodos:
        - __str__(): Devuelve la representación en cadena de la empresa.
    """
    name_empresa = models.CharField(max_length=50)
    def __str__(self):
        return self.name_empresa

class MotivoLicencia(models.Model):
    """
    Modelo para representar motivos de licencia.

    Atributos:
        - name_motivo_licencia (str): Nombre del motivo de la licencia.

    Métodos:
        - __str__(): Devuelve la representación en cadena del motivo de la licencia.
    """
    name_motivo_licencia = models.CharField(max_length=80)
    def __str__(self):
        return self.name_motivo_licencia
    
class TipoLicencia(models.Model):
    """
    Modelo para representar tipos de licencia.

    Atributos:
        - name_tipo_licencia (str): Nombre del tipo de licencia.

    Métodos:
        - __str__(): Devuelve la representación en cadena del tipo de licencia.
    """
    name_tipo_licencia = models.CharField(max_length=25)
    def __str__(self):
        return self.name_tipo_licencia

MAYORIGUALDOSDIAS_CHOICES = [
    ("Si", "Si"), 
    ("No", "No"),
]

class Licencia(models.Model):
    """
    Modelo para representar licencias.

    Atributos:
        - creado (DateTimeField): Fecha y hora de creación de la licencia.
        - nombre_completo (str): Nombre completo del empleado al que se le va solicitar la licencia.
        - cedula (str): Número de cédula del empleado.
        - empresa (ForeignKey): Relación con el modelo Empresa.
        - area (ForeignKey): Relación con el modelo Area.
        - fecha_inicio (DateField): Fecha de inicio de la licencia.
        - fecha_fin (DateField): Fecha de fin de la licencia.
        - tipo_licencia (ForeignKey): Relación con el modelo TipoLicencia.
        - motivo_licencia (ForeignKey): Relación con el modelo MotivoLicencia.
        - observacion_licencia (TextField): Observaciones de la licencia.
        - nombre_coordinador (str): Nombre del coordinador responsable.
        - datos_adjuntos_licencias (FileField): Archivo adjunto a la licencia.
        - creada_por (ForeignKey): Relación con el modelo CustomUser (usuario creador).
        - verificacion_licencia (str): Estado de verificación de la licencia.
        - estado_licencia (TextField): Estado de la licencia.
        - verificada_por (ForeignKey): Relación con el modelo CustomUser (usuario verificador).
        - aprobacion_rrhh (str): Estado de aprobación de Recursos Humanos.
        - observacion_rrhh (TextField): Observaciones de Recursos Humanos.
        - verificacion_rrhh (ForeignKey): Relación con el modelo CustomUser (verificador de Recursos Humanos).
        - fecha_verificacion (DateTimeField): Fecha y hora de verificación.
        - fecha_aprobacion (DateTimeField): Fecha y hora de aprobación.

    Métodos:
        - save(*args, **kwargs): Guarda la licencia en la base de datos.
        - nombre_archivo(): Devuelve el nombre del archivo adjunto a la licencia.
    """
    creado = models.DateTimeField(auto_now_add=True)
    nombre_completo = models.CharField(max_length=100)
    cedula = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex='^[0-9]*$', message='La cedula debe contener solo números.')],
    )
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    tipo_licencia = models.ForeignKey(TipoLicencia, on_delete=models.CASCADE)
    motivo_licencia = models.ForeignKey(MotivoLicencia, on_delete=models.CASCADE)
    observacion_licencia = models.TextField(blank=True, null=True)
    nombre_coordinador = models.CharField(max_length=50)
    datos_adjuntos_licencias = models.FileField(upload_to='archivos_adjuntos_licencias/documento/', null=True, blank=True)
    creada_por = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=None, editable=False, related_name='Licencia_Creada_Por')
    verificacion_licencia = models.CharField(max_length=20, choices=VERIFICACION_CHOICES, blank=True, null=True)
    estado_licencia = models.TextField(blank=True, null=True)
    verificada_por = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, editable=False, related_name='Licencia_Verificado_Por')
    aprobacion_rrhh = models.CharField(max_length=20, choices=VERIFICACION_CHOICES, blank=True, null=True)
    observacion_rrhh = models.TextField(blank=True, null=True)
    verificacion_rrhh = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, blank=True, null=True, editable=False, related_name='Licencia_Verificada_RRHH') 
    fecha_verificacion = models.DateTimeField(null=True, blank=True, editable=False)
    fecha_aprobacion = models.DateTimeField(null=True, blank=True, editable=False)

    def save(self,*args, **kwargs):
        """
        Guarda el objeto Licencia en la base de datos.

        Este método se encarga de realizar algunas acciones antes de guardar el objeto, como verificar y actualizar el nombre del archivo adjunto y calcular si la licencia es mayor_igual_dos_dias.

        Args:
            - *args: Argumentos posicionales adicionales.
            - **kwargs: Argumentos de palabras clave adicionales.

        Return:
            - None
        """
        # Verifica si ya existe el archivo y actualiza el nombre si es necesario
        if self.datos_adjuntos_licencias:
            nombre_archivo = os.path.basename(self.datos_adjuntos_licencias.name)
            if not nombre_archivo:
                # Si el nombre del archivo no está configurado, configúralo
                self.datos_adjuntos_licencias.name = f'archivos_adjuntos_licencias/documento/{self.nombre_archivo()}'

        if (self.fecha_fin - self.fecha_inicio).days >= 2:
            self.mayor_igual_dos_dias = 'Si'
        else:
            self.mayor_igual_dos_dias = 'No'

        print('Entro al save')
            
        super(Licencia, self).save(*args, **kwargs)

    def nombre_archivo(self):
        """
        Devuelve el nombre del archivo adjunto a la licencia.

        Return:
            - str: Nombre del archivo adjunto o None si no hay archivo adjunto.
        """
        if self.datos_adjuntos_licencias:
            return os.path.basename(self.datos_adjuntos_licencias.name)
        else:
            return None