from django import forms
from .models import Permiso, Licencia, Area
from django.forms.widgets import ClearableFileInput
from django.core.exceptions import ValidationError

class CustomClearableFileInput(ClearableFileInput):
    """
    Widget personalizado para la representación de archivos con opción de limpiar.
    """
    template_with_initial = (
        '%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> '
        '%(clear_template)s<br />%(input_text)s: %(input)s'
    )

    template_with_clear = '%(clear)s <label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label>'

# Permisos
class PermisoForm(forms.ModelForm):
    """
    Formulario para el modelo Permiso.

    Atributos:
    - user: Usuario asociado al formulario.
    - editing: Indica si el formulario se está utilizando para editar un objeto existente.
    """
    class Meta:
        model = Permiso
        fields = '__all__'
        labels = {
            'nombre_completo': 'Nombre Completo',
            'cedula' : 'Cedula',
            'area' : 'Area',
            'turno' : 'Turno',
            'fecha_permiso' : ' Fecha Permiso',
            'fecha_fin_permiso' : 'Fecha Fin Permiso',
            'hora_salida' : 'Hora Salida',
            'hora_llegada' : 'Hora Llegada',
            'motivo_permiso' : 'Motivo Permiso',
            'nombre_coordinador' : 'Nombre Coordinador',
            'compensa_tiempo' : 'Compensa Tiempo',
            'datos_adjuntos' : 'Datos Adjuntos',
            'observacion' : 'Observacion',
            'verificacion' : 'Verificacion',
            'estado' : 'Estado',
        }
        widgets = {
            'nombre_completo' : forms.TextInput(attrs={'class': 'form-control'}),
            'cedula' : forms.TextInput(attrs={'class' : 'form-control'}),
            'area' : forms.Select(attrs={'class' : 'form-control disable-edit'}),
            'turno' : forms.Select(attrs={'class' : 'form-control disable-edit'}),
            'fecha_permiso': forms.DateInput(attrs={'class': 'datepicker form-control disable-edit'}),
            'fecha_fin_permiso': forms.DateInput(attrs={'class': 'datepicker form-control disable-edit'}),
            'hora_salida' : forms.TimeInput(attrs={'type': 'time', 'class' : 'form-control'}),
            'hora_llegada' : forms.TimeInput(attrs={'type': 'time', 'class' : 'form-control'}),
            'motivo_permiso' : forms.Select(attrs={'class' : 'form-control disable-edit'}),
            'nombre_coordinador' : forms.TextInput(attrs={'class' : 'form-control'}),
            'compensa_tiempo' : forms.Select(attrs={'class' : 'form-control disable-edit'}),
            'datos_adjuntos': forms.FileInput(attrs={'class': 'form-control fs-8', 'id':'datos_adjuntos'}),
            'observacion' : forms.Textarea(attrs={'class' : 'form-control', 'rows' : '2', 'style' : 'resize : none;'}),
            'verificacion' : forms.Select(attrs={'class' : 'form-control'}),
            'estado' : forms.Textarea(attrs={'class' : 'form-control', 'rows' : '2', 'style' : 'resize : none;'}),
        }

    def __init__(self, *args, **kwargs):
        """
        Inicializador del formulario.

        Parámetros:
        - user: Usuario asociado al formulario.
        - editing: Indica si el formulario se está utilizando para editar un objeto existente.
        
        Notas:
        - Verifica el rol que tiene el usuario y a partir de esto, permite especificar que campos son editables.
        """
        user = kwargs.pop('user', None)
        editing = kwargs.pop('editing', False)
        self.editing = kwargs.pop('editing', False)
        self.user = kwargs.pop('user', None)
        super(PermisoForm, self).__init__(*args, **kwargs)

        if user.groups.filter(name='Lideres').exists():
            self.fields['verificacion'].widget.attrs['disabled'] = True
            self.fields['estado'].widget.attrs['disabled'] = True

        if editing and user.groups.filter(name='Admin').exists():
            for field in self.fields:
                if field not in ['verificacion', 'estado']:
                    self.fields[field].widget.attrs['readonly'] = True  

        if editing and user.groups.filter(name='Lideres').exists():
            for field in self.fields:
                if field not in ['datos_adjuntos']:
                    self.fields[field].widget.attrs['readonly'] = True  
                    
        # if user is not None:
        #     self.fields['area'].queryset = Area.objects.filter(id=user.area.id)

    def clean(self):
        """
        Método de validación personalizado.

        Realiza validaciones adicionales al formulario, como que la fecha fin no sea menor a la fecha inicio.
        """
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_permiso')
        fecha_fin = cleaned_data.get('fecha_fin_permiso')

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise ValidationError({
                'fecha_fin_permiso': ValidationError(
                    "La fecha de finalización no puede ser anterior a la fecha de inicio.",
                    code='invalid_dates'
                )
            })
        return cleaned_data

#Licencias 
class LicenciaForm(forms.ModelForm):
    """
    Formulario para el modelo Licencia.

    Atributos:
    - user: Usuario asociado al formulario.
    - editing: Indica si el formulario se está utilizando para editar un objeto existente.
    """
    class Meta: 
        model = Licencia
        fields = '__all__'
        labels = {
            'nombre_completo' : 'Nombre Completo',
            'cedula' : 'Cedula',
            'empresa' : 'Empresa',
            'area' : 'Area',
            'fecha_inicio' : 'Fecha Inicio',
            'fecha_fin' : 'Fecha Fin',
            'tipo_licencia' : 'Tipo de Licencia',
            'motivo_licencia' : 'Motivo de la licencia',
            'observacion_licencia' : 'Observaciones De Licencia',
            'nombre_coordinador' : 'Nombre Del Coordinador',
            'datos_adjuntos_licencias' : 'Datos Adjuntos Licencias',
            'verificacion_licencia' : 'Verificacion De Licencia',
            'estado_licencia' : 'Estado De Licencia',
            'aprobacion_rrhh' : 'Aprobacion BP',
            'observacion_rrhh' : 'Observaciones BP'
        }
        widgets = {
            'nombre_completo' : forms.TextInput(attrs={'class': 'form-control'}),
            'cedula' : forms.TextInput(attrs={'class' : 'form-control'}),
            'empresa' : forms.Select(attrs={'class' : 'form-control disable-edit'}),
            'area' : forms.Select(attrs={'class' : 'form-control disable-edit'}),
            'fecha_inicio' : forms.DateInput(attrs={'class': 'datepicker form-control disable-edit'}),
            'fecha_fin' : forms.DateInput(attrs={'class': 'datepicker form-control disable-edit'}),
            'tipo_licencia' : forms.Select(attrs={'class' : 'form-control disable-edit'}),
            'motivo_licencia' : forms.Select(attrs={'class' : 'form-control disable-edit'}),
            'observacion_licencia' : forms.Textarea(attrs={'class' : 'form-control', 'rows' : '2', 'style' : 'resize : none;'}),
            'nombre_coordinador' : forms.TextInput(attrs={'class' : 'form-control'}),
            'datos_adjuntos_licencias': CustomClearableFileInput(attrs={'class': 'form-control', 'id':'datos_adjuntos_licencias'}),
            'verificacion_licencia' : forms.Select(attrs={'class' : 'form-control disable-edit'}),
            'estado_licencia' : forms.Textarea(attrs={'class' : 'form-control', 'rows' : '2', 'style' : 'resize : none;'}),
            'aprobacion_rrhh' : forms.Select(attrs={'class' : 'form-control'}),
            'observacion_rrhh' : forms.Textarea(attrs={'class' : 'form-control', 'rows' : '2', 'style' : 'resize : none;'}),
        }
    def __init__(self, *args, **kwargs):
        """
        Inicializador del formulario.

        Parámetros:
        - user: Usuario asociado al formulario.
        - editing: Indica si el formulario se está utilizando para editar un objeto existente.

        Notas:
        - Verifica el rol que tiene el usuario y a partir de esto, permite especificar que campos son editables.
        """
        user = kwargs.pop('user', None)
        editing = kwargs.pop('editing', False)

        super(LicenciaForm, self).__init__(*args, **kwargs)

        self.fields['cedula'].widget.attrs['id'] = 'id_cedula_licencia'
        self.fields['nombre_completo'].widget.attrs['id'] = 'id_nombre_completo_licencia'

        if user and user.groups.filter(name='Coordinadores').exists():
            self.fields['verificacion_licencia'].widget.attrs['disabled'] = True
            self.fields['estado_licencia'].widget.attrs['disabled'] = True
            self.fields['aprobacion_rrhh'].widget.attrs['disabled'] = True
            self.fields['observacion_rrhh'].widget.attrs['disabled'] = True

        if editing and user.groups.filter(name='Admin').exists():
            for field in self.fields:
                if field not in ['verificacion_licencia','estado_licencia']:
                    self.fields[field].widget.attrs['readonly'] = True

        if editing and user.groups.filter(name='Lideres').exists():
            for field in self.fields:
                if field not in ['datos_adjuntos_licencias']:
                    self.fields[field].widget.attrs['readonly'] = True

        if editing and user.groups.filter(name='Coordinadores').exists():
            for field in self.fields:
                if field not in ['datos_adjuntos_licencias']:
                    self.fields[field].widget.attrs['readonly'] = True  

        if editing and user.groups.filter(name='BP').exists():
            for field in self.fields:
                if field not in ['aprobacion_rrhh', 'observacion_rrhh']:
                    self.fields[field].widget.attrs['readonly'] = True

        # if user is not None:
        #     self.fields['area'].queryset = Area.objects.filter(id=user.area.id)

    def clean(self):
        """
        Método de validación personalizado.

        Realiza validaciones adicionales al formulario, como que la fecha fin no sea menor a la fecha inicio.
        """
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            raise ValidationError({
                'fecha_fin': ValidationError(
                    "La fecha de finalización no puede ser anterior a la fecha de inicio.",
                    code='invalid_dates'
                )
            })
        return cleaned_data