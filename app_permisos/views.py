# Redireccion
from typing import Any
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.urls import reverse

# Login
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group

# Templates
from django.views.generic import TemplateView
from django.views.generic.edit import UpdateView

# Models
from .models import Permiso, Licencia, Area

# Forms
from .forms import PermisoForm, LicenciaForm

# JSON
from django.http import HttpResponse, Http404
import os
import json

# Envio de correos
from django.contrib.auth import get_user_model
CustomUser = get_user_model()
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# Errores
from django.contrib import messages

# Fechas
from django.utils import timezone
from collections import defaultdict
from django.db.models.functions import TruncMonth
from datetime import timedelta
from datetime import datetime

# Conexion
import sqlalchemy
from sqlalchemy import text
from .utils.conections import conection_house, conection_elemental
import pandas as pd

# Consulta en SQL y envio de datos en el return
from django.views import View
from django.http import JsonResponse
import mimetypes

# Conteo de consultas a la bd
from django.db.models import Count
from collections import Counter

# Manejo de datos
import pandas as pd

# Tipos de transacciones (atomic, commit, rollback)
from django.db import transaction

"""--------------------------------  GENERAL  --------------------------------"""
# Vista del Login
class Login(LoginView):
    """
    Vista para el proceso de inicio de sesión.

    Atributos:
        - next_page (str): Página a la que se redirige al usuario después de iniciar sesión con éxito.
        - template_name (str): Nombre del template utilizado para renderizar la página de inicio de sesión.

    Metodos:
        - form_valid(form): Procesa el formulario de inicio de sesión cuando es válido.
    """
    next_page = reverse_lazy('inicio')
    template_name = 'login.html'

    def form_valid(self, form):
        """
        Procesa el formulario de inicio de sesión cuando es válido.

        Args:
            - form (AuthenticationForm): El formulario de inicio de sesión.

        Return:
            - HttpResponse: Respuesta HTTP después de un inicio de sesión exitoso.

        Notas:
            - Llama al método form_valid de la clase base para realizar la lógica estándar de inicio de sesión.
            - Obtiene el nombre de usuario del usuario autenticado.
            - Pasa el nombre de usuario al c ontexto de la página de inicio.

        Modo de uso:
            - Este método se llama automáticamente cuando el formulario de inicio de sesión es válido.
        """
        # Llama al método form_valid de la clase base
        response = super().form_valid(form)
        # Obtiene el nombre de usuario del usuario autenticado
        username = self.request.user.username
        # Pasa el nombre de usuario al contexto de la página de inicio
        self.extra_context = {'username': username}
        return response

# Vista del Logout
class CustomLogoutView(LogoutView):
    """
    Vista para el proceso de cierre de sesión.

    Atributos:
        - next_page (str): Página a la que se redirige al usuario después de cerrar sesión.

    Notas:
        - Esta vista utiliza la implementación estándar de Django para cerrar sesión.
        - La página de redirección después de cerrar sesión se establece en la página de inicio de sesión.

    Modo de uso:
        - Al acceder a esta vista, el usuario se desconecta y es redirigido a la página de inicio de sesión.
    """
    next_page = reverse_lazy('login')

# Vista del index
class Inicio(LoginRequiredMixin,TemplateView):
    """
    Vista para la página de inicio.

    Atributos:
        - login_url (str): URL a la que se redirige si el usuario no está autenticado.
        - template_name (str): Nombre del template utilizado para renderizar la página de inicio.

    Metodos:
        - get_context_data(**kwargs): Obtiene y devuelve el contexto para renderizar la página.
        - post(request, *args, **kwargs): Procesa los datos enviados mediante el formulario en la página.

    Notas:
        - Hereda de LoginRequiredMixin para asegurar que solo los usuarios autenticados pueden acceder a la página de inicio.

    Modo de uso:
        - Accede a esta vista para visualizar la página de inicio y procesar formularios de permisos y licencias.
    """
    login_url = reverse_lazy('login')
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        """
        Obtiene y devuelve el contexto para renderizar la página de inicio.

        Return:
            - dict: Un diccionario con datos para renderizar la página.

        Notas:
            - Si el usuario está autenticado, se agrega su nombre de usuario al contexto.
            - Se crean instancias de los formularios de permisos y licencias y se agregan al contexto.

        Modo de uso:
            - Este método se llama automáticamente al acceder a la página de inicio.
        """
        contexto = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # Si el usuario está autenticado, obtén su nombre de usuario - Obtiene el nombre del usuario
            username = self.request.user.username
            contexto['username'] = username

            print("Nombre de Usuario:", self.request.user.username)

            # Obtiene el grupo de permisos del usuario
            user_groups = self.request.user.groups.all()
            contexto['user_groups'] = user_groups

            # Comprueba si el usuario tiene grupos'
            contexto['es_lider'] = 'Lideres' in user_groups.values_list('name', flat=True)
            contexto['es_coordinador'] = 'Coordinadores' in user_groups.values_list('name', flat=True)
            contexto['es_admin'] = 'Admin' in user_groups.values_list('name', flat=True)
            contexto['es_BP'] = 'BP' in user_groups.values_list('name', flat=True)

            contexto['form_permisos'] = PermisoForm(user=self.request.user, editing=False) #Formulario Permisos
            contexto['form_licencias'] = LicenciaForm(user=self.request.user, editing=False) #Formulario Licencias

            # consulta_sql_marcaciones()

        return contexto

    # Envia los datos creados en los formularios para la base de datos
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        """
        Procesa los datos enviados mediante el formulario en la página.

        Args:
            - request (HttpRequest): Objeto que contiene la información de la solicitud HTTP.
            - args: Argumentos adicionales.
            - kwargs: Argumentos clave adicionales.

        Return:
            - HttpResponse: Respuesta HTTP después de procesar los datos del formulario.

        Notas:
            - Procesa formularios de permisos y licencias según la acción realizada por el usuario.
            - Envia notificaciones por correo electrónico después de crear permisos y licencias.

        Modo de uso:
            - Este método se llama automáticamente al enviar datos mediante el formulario.
        """
        contexto = self.get_context_data(**kwargs)

        if 'permiso' in request.POST:
            form_permiso = PermisoForm(request.POST, request.FILES, user=request.user)
            
            # Verificar si el usuario es un líder
            es_lider = request.user.groups.filter(name='Lideres').exists()
            if form_permiso.is_valid():
                permiso = form_permiso.save(commit=False)
                permiso.creado_por = request.user
                permiso.save()

                messages.success(request, '<i class="bi bi-check-circle"></i> El permiso se ha guardado exitosamente.')
                
                # Obtener el area del Lider
                lider_area = request.user.area

                # Obtener los usuarios con el grupo 'Coordinadores'
                coordinadores_grupo = Group.objects.get(name='Coordinadores')
                coordinadores = CustomUser.objects.filter(groups=coordinadores_grupo, area=lider_area)

                # Obtener los usuarios con el grupo 'Admin'
                admins_grupo = Group.objects.get(name='Admin')
                admins = CustomUser.objects.filter(groups=admins_grupo)

                print("Revisando coordinadores",coordinadores)

                recipient_list = [coordinador.email for coordinador in coordinadores] + [admin.email for admin in admins]

                if recipient_list:
                    #Enviar correo apenas se cree el permiso
                    html_message = render_to_string('notificaciones/notify_permisos.html', {
                    'usuario': permiso.creado_por,
                    'nombre': permiso.nombre_completo,
                    'cedula': permiso.cedula,
                    'area': permiso.area,
                    'turno': permiso.turno,
                    'fecha_permiso': permiso.fecha_permiso,
                    'hora_salida': permiso.hora_salida,
                    'hora_llegada': permiso.hora_llegada,
                    'motivo_permiso': permiso.motivo_permiso,
                    'nombre_coordinador': permiso.nombre_coordinador,
                    'compensa_tiempo': permiso.compensa_tiempo,
                    'observacion': permiso.observacion,
                    'autor': permiso.creado_por
                    })

                    # Crear una versión de texto plano del mensaje
                    plain_message = strip_tags(html_message)

                    send_mail(
                        subject='NOTIFICACION DE PERMISO',
                        message=plain_message,
                        from_email=None,
                        recipient_list=recipient_list,
                        html_message=html_message,
                        fail_silently=False,
                    ) 
                return redirect('inicio') 
            else:
                contexto = self.get_context_data(**kwargs)
                contexto['form_permisos'] = form_permiso
                messages.error(request, '<i class="bi bi-exclamation-circle"></i> Hay errores en el formulario de permisos. Por favor, diligéncielo de nuevo.')

        elif 'licencia' in request.POST:
            form_licencia = LicenciaForm(request.POST, request.FILES, user=request.user)

            if form_licencia.is_valid():
                licencia = form_licencia.save(commit=False)
                licencia.creada_por = request.user

                # Obtener todos los usuarios con el grupo 'Admin'
                admins_grupo = Group.objects.get(name='Admin')
                admins = CustomUser.objects.filter(groups=admins_grupo)

                recipient_lista = [admin.email for admin in admins]

                # Establecer el área predeterminada para los coordinadores
                if request.user.groups.filter(name='Coordinadores').exists():
                    # Reemplaza 'default_area_for_coordinators' con un valor real
                    area = licencia.area
                    default_area_for_coordinators = Licencia.area.field.related_model.objects.first()
                    licencia.area = default_area_for_coordinators
                    form_licencia.fields['area'].initial = default_area_for_coordinators

                #Verificando si la licencia es mayor o igual a dos dias 
                if (licencia.fecha_fin - licencia.fecha_inicio).days >= 2:
                    licencia.mayor_igual_dos_dias = 'Si'
                else:
                    licencia.mayor_igual_dos_dias = 'No'

                licencia.save()

                messages.success(request, '<i class="bi bi-check-circle"></i> La licencia se ha guardado exitosamente.')

                # Enviar correo apenas se cree la licencia
                html_message = render_to_string('notificaciones/notify_licencias.html', {
                'usuario': licencia.creada_por,
                'nombre': licencia.nombre_completo,
                'cedula': licencia.cedula,
                'empresa': licencia.empresa,
                'area': licencia.area,
                'fecha_inicio': licencia.fecha_inicio,
                'fecha_fin': licencia.fecha_fin,
                'mayor_igual_dos_dias': licencia.mayor_igual_dos_dias,
                'tipo_licencia': licencia.tipo_licencia,
                'motivo_licencia': licencia.motivo_licencia,
                'nombre_coordinador': licencia.nombre_coordinador,
                'observacion_licencia': licencia.observacion_licencia,
                'autor': licencia.creada_por
                })

                # Crear una versión de texto plano del mensaje
                plain_message = strip_tags(html_message)

                print("Proximo a enviar el correo 111 _________________________******************")
                send_mail(
                    subject='NOTIFICACION DE LICENCIA',
                    message=plain_message,
                    from_email='jimmy.bustamante@prebel.com.co',
                    recipient_list=recipient_lista,
                    html_message=html_message,
                    fail_silently=False,
                )

                # Verificar si se debe enviar un correo adicional
                if licencia.mayor_igual_dos_dias == "Si":
                    html_message = render_to_string('notificaciones/notify_licencias_dos_dias.html', {
                    'usuario': licencia.creada_por,
                    'nombre': licencia.nombre_completo,
                    'cedula': licencia.cedula,
                    'empresa': licencia.empresa,
                    'area': licencia.area,
                    'fecha_inicio': licencia.fecha_inicio,
                    'fecha_fin': licencia.fecha_fin,
                    'mayor_igual_dos_dias': licencia.mayor_igual_dos_dias,
                    'tipo_licencia': licencia.tipo_licencia,
                    'motivo_licencia': licencia.motivo_licencia,
                    'nombre_coordinador': licencia.nombre_coordinador,
                    'autor': licencia.creada_por
                    })

                    # Crear una versión de texto plano del mensaje
                    plain_message = strip_tags(html_message)

                    print("Proximo a enviar el correo 222 _________________________******************")
                    send_mail(
                        subject='NOTIFICACION DE LICENCIA MAYOR A DOS DIAS',
                        message=plain_message,
                        from_email='jimmy.bustamante@prebel.com.co',
                        recipient_list=['jimmy.bustamante@prebel.com.co'],
                        html_message=html_message,
                        fail_silently=False,
                    )       
                else:
                    print(form_licencia.errors)

                return redirect('inicio')
            else:
                contexto = self.get_context_data(**kwargs)
                contexto['form_licencias'] = form_licencia
                messages.error(request, '<i class="bi bi-exclamation-circle"></i> Hay errores en el formulario de licencias. Por favor, diligéncielo de nuevo.')

        return render(request, self.template_name, contexto)

#Vista para obtener las areas en el boton para filtrar los grafico y tablas
def get_areas(request):
    """
    Obtiene todas las áreas de la base de datos y las devuelve en formato JSON.
    
    Esta vista hace una solicitud GET y devuelve una lista de todas las áreas disponibles 
    en la base de datos. Cada área se representa como un diccionario con su 'id' y 'nombre_area'.
    
    Args:
        request (HttpRequest): El objeto de solicitud HTTP.

    Returns:
        JsonResponse: Una respuesta JSON que contiene una lista de diccionarios, cada uno 
        representando un área con sus claves 'id' y 'name'. En caso de error, se devuelve 
        un mensaje de error con un estado HTTP 500.
    """
    try:
        areas = Area.objects.all()
        areas_list = [{"id": area.id, "name": area.nombre_area} for area in areas]
        return JsonResponse(areas_list, safe=False)
    except Exception as e:
        print(f"Error: {e}")
        return JsonResponse({"error": str(e)}, status=500)

"""--------------------------------  CONSULTAS SQL  --------------------------------"""
# Vista para la consulta a Marcaciones (TIMESOFT)
def consulta_sql_marcaciones():
    """
    Realiza una consulta SQL a la base de datos para obtener información de los empleados.

    Return:
        - HttpResponse: Respuesta HTTP que indica que la consulta se realizó con éxito.

    Notas:
        - Establece una conexión a la base de datos mediante la función conection_house().
        - Realiza una consulta SQL para obtener información de Identificación y Nombre de los empleados.
        - Cierra la conexión después de obtener los resultados.
        - Devuelve una respuesta HTTP indicando que la consulta se realizó con éxito.

    Modo de uso:
        - Llame a esta función para obtener información de marcaciones desde la base de datos.
    """
    con = conection_house()
    #
    df = pd.read_sql(text("""
        select Identificación, Nombre from Maestro_Empleados       
    """),con)
    con.close()

    print("Revisando que vengan datos",df)

    return df

# Vista para obtener los nombres de las personas a traves de la consulta a Marcaciones
class ObtenerNombre(View):
    """
    Vista para obtener el nombre de un empleado mediante su cédula.

    Esta vista se utiliza para realizar una consulta asíncrona (AJAX) en la que se envía la cédula de un empleado
    y se devuelve el nombre y sucursal asociados si el empleado es encontrado.

    Métodos:
    - get(request, *args, **kwargs): Procesa las solicitudes GET asíncronas y devuelve una respuesta JSON con el
      nombre y la sucursal del empleado correspondiente a la cédula proporcionada.

    Ejemplo de uso en una URL de Django:
    ```
    path('obtener_nombre/', ObtenerNombre.as_view(), name='obtener_nombre'),
    ```
    """
    def get(self, request, *args, **kwargs):
        """
        Procesa las solicitudes GET asíncronas y devuelve una respuesta JSON con el nombre y la sucursal del empleado
        correspondiente a la cédula proporcionada.

        Parámetros de solicitud GET:
        - cedula (str): La cédula del empleado.

        Respuestas JSON:
        - En caso de éxito, se devuelve un diccionario con el nombre, la sucursal y un mensaje de éxito.
        - Si no se proporciona una cédula, se devuelve un diccionario con un mensaje de error.
        - Si la cédula no coincide con ningún empleado, se devuelve un diccionario con un mensaje de error.
        """
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cedula = request.GET.get("cedula")

            print("Cedula Llego",cedula)
            if cedula:
                df_empleados = consulta_sql_marcaciones()
                # print(df_empleados)
                try:
                    empleado = df_empleados[df_empleados['Identificación'] == cedula].iloc[0]
                    nombre = f"{empleado['Nombre']}"
                    mensaje = "Empleado encontrado"
                    return JsonResponse({"nombre": nombre, "mensaje": mensaje})
                except IndexError:
                    mensaje_error = "Empleado no encontrado"
                    return JsonResponse({"error": mensaje_error})
            else:
                return JsonResponse({"error": "Cédula no proporcionada"})
        else:
            return JsonResponse({"error": "Invalid request"})

"""--------------------------------  PERMISOS  --------------------------------""" 
# Vista para los graficos de Permisos
class PermisosChartView(LoginRequiredMixin, TemplateView):
    """
    Vista basada en clase para generar un gráfico de pareto de permisos.

    Esta vista requiere que el usuario esté autenticado y proporciona un contexto 
    con datos necesarios para generar un grafico pareto sobre los permisos, incluyendo tipos de permisos, 
    porcentajes acumulados y días por mes.

    Atributos:
        template_name (str): El nombre de la plantilla que se renderizará.

    Métodos:
        get_context_data(**kwargs): Obtiene el contexto para la plantilla.
    """
    template_name = 'graficos/graf_permisos.html'

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto para la plantilla.

        Esta función recopila datos de permisos, los organiza y calcula información 
        adicional necesaria para los gráficos, incluyendo el conteo de permisos por tipo,
        días por mes y porcentajes acumulados.

        Args:
            **kwargs: Argumentos adicionales para el contexto.

        Returns:
            dict: Un diccionario con los datos del contexto para la plantilla.
        """
        context = super().get_context_data(**kwargs)

        permisos = Permiso.objects.all()

        permit_date = Permiso.objects.dates('creado', 'month')

        day_per_month = defaultdict(lambda: defaultdict(int))

        for date_permit in permit_date:
            year = date_permit.year
            month = date_permit.month

            days_in_month = (date_permit.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            day_per_month[year][month] = days_in_month.day

        permission_types = {}

        for permission in permisos:
            permission_type = permission.motivo_permiso

            permission_types[permission_type.id] = permission_types.get(permission_type.id, {'id': permission_type.id, 'nombre': permission_type.name_motivo, 'count': 0})
            permission_types[permission_type.id]['count'] += 1

            month = permission.creado.month

        # Ordena los tipos de permisos por cantidad (mayor a menor)
        permission_types = dict(sorted(permission_types.items(), key=lambda item: item[1]['count'], reverse=True))

        #Porcentaje acumulado
        total_counts = sum(tipo['count'] for tipo in permission_types.values())
        accumulated_percentage = 0
        cumulative_percentages = []

        for tipo_id, tipo in permission_types.items():
            if total_counts != 0:
                accumulated_percentage += (tipo['count'] / total_counts) * 100
            else:
                accumulated_percentage = 0

            cumulative_percentages.append(accumulated_percentage)

        # Pasa los datos al contexto
        context['tipos_permisos'] = json.dumps(list(permission_types.values()))
        context['porcentajes_acumulados'] = cumulative_percentages
        context['dias_por_mes'] = day_per_month

        return context
    
# Vista para el grafico de linea de tiempo
def timeline_permiso_chart(request):
    """
    Genera datos en formato JSON para un gráfico de línea de tiempo de permisos.

    Esta vista obtiene todos los permisos de la base de datos, calcula la cantidad 
    de horas de permiso entre las fechas de inicio y fin de cada permiso, y organiza 
    estos datos en un formato adecuado para visualización en un gráfico. Además, 
    agrupa los datos por mes y motivo de permiso para calcular las horas mensuales 
    y las horas verdaderas mensuales.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP.

    Returns:
        JsonResponse: Una respuesta JSON que contiene los datos de permisos, los 
        datos agrupados por mes y las horas mensuales verdaderas.
    """
    permisos = Permiso.objects.all()

    permisos_data = []

    for i in permisos:
        fecha_permiso = pd.to_datetime(i.fecha_permiso)
        fecha_fin_permiso = pd.to_datetime(i.fecha_fin_permiso)

        dias_diferencia = (fecha_permiso - fecha_fin_permiso).days + 1
        horas_diferencia = dias_diferencia * 8

        aux = {
            'creado': i.creado,
            'fecha_permiso': i.fecha_permiso,
            'fecha_fin_permiso': i.fecha_fin_permiso,
            'motivo_permiso': i.motivo_permiso,
            'horas_entre_fechas': horas_diferencia
        }
        permisos_data.append(aux)

    data = {'id': [], 'creado': [], 'fecha_permiso': [], 'fecha_fin_permiso': [], 'motivo_permiso': [], 'month':[], 'horas_entre_fechas': [], 'horas_mensuales': []}
    
    for permisos in permisos:
        fecha_permiso = pd.to_datetime(permisos.fecha_permiso)
        fecha_fin_permiso = pd.to_datetime(permisos.fecha_fin_permiso)

        dias_diferencia = (fecha_fin_permiso - fecha_permiso).days + 1
        horas_entre_fechas = dias_diferencia * 8

        data['id'].append(permisos.id)
        data['creado'].append(permisos.creado)
        data['fecha_permiso'].append(permisos.fecha_permiso)
        data['fecha_fin_permiso'].append(permisos.fecha_fin_permiso)
        data['motivo_permiso'].append(permisos.motivo_permiso.name_motivo)
        month = permisos.creado.strftime("%Y-%m")
        data['month'].append(month)
        data['horas_entre_fechas'].append(horas_entre_fechas)
        data['horas_mensuales'].append(horas_entre_fechas)  

    month_counts = Counter(data['month'])
    month_data = [{'month': month, 'count': count} for month, count in month_counts.items()]

    permisos_df = pd.DataFrame(data)

    permisos_df['horas_mensuales'] = permisos_df.groupby('motivo_permiso')['horas_mensuales'].transform('sum')
    permisos_df['horas_mensuales_vedaderas'] = permisos_df.groupby('month')['horas_entre_fechas'].transform('sum')

    permisos_df['cantidad'] = permisos_df.groupby('motivo_permiso')['motivo_permiso'].transform('count')
    permisos_df = permisos_df.drop_duplicates('horas_mensuales_vedaderas')

    permisos_dict = json.loads(permisos_df.to_json(orient='records'))

    return JsonResponse({'permisos': permisos_dict, 'month':month_data, 'horas_mensuales_vedaderas':permisos_df['horas_mensuales_vedaderas'].to_list()})

# Vista que actuliza grafico mediante el mes elegido
def actualizar_permisos_chart(request, fecha):
    """
    Actualiza los datos del gráfico de permisos según el mes seleccionado.

    Esta vista obtiene todos los permisos de la base de datos, filtra los permisos 
    según el mes proporcionado y calcula los porcentajes acumulados para cada motivo 
    de permiso. Luego, organiza los datos en un formato adecuado para la visualización 
    en un gráfico.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP.
        fecha (int): El número del mes para el cual se deben filtrar los permisos. 
                     Si es 0, se incluirán todos los meses.

    Returns:
        JsonResponse: Una respuesta JSON que contiene los datos filtrados y calculados 
        para los permisos.
    """
    permisos = Permiso.objects.all()

    permits_data = []

    for i in permisos:

        aux = {
            'creado': i.creado,
            'fecha_permiso': i.fecha_permiso,
            'fecha_fin_permiso': i.fecha_fin_permiso,
            'motivo_permiso': i.motivo_permiso
        }
        permits_data.append(aux)

    data = {'id': [], 'creado': [] ,'fecha_permiso': [], 'fecha_fin_permiso': [], 'motivo_permiso': []}

    for permits in permisos:
        data['id'].append(permits.id)
        data['creado'].append(permits.creado)
        data['motivo_permiso'].append(permits.motivo_permiso.name_motivo)
        data['fecha_permiso'].append(permits.fecha_permiso)
        data['fecha_fin_permiso'].append(permits.fecha_fin_permiso)

    permits_df = pd.DataFrame(data)

    #Trae los registros del mes seleccionado
    mes = int(fecha)
    
    permits_df['fecha_permiso'] = pd.to_datetime(permits_df['fecha_permiso'])
    permits_df['fecha_fin_permiso'] = pd.to_datetime(permits_df['fecha_fin_permiso'])

    if mes == 0:
        filtered_df = permits_df.copy()
    else:
        filtered_df = permits_df[(permits_df['creado'].dt.month == mes) | (permits_df['creado'].dt.month == mes)]
        print(f"Cantidad de permisos para el mes {mes}: {filtered_df['id'].count()}")

    #Conteo de permisos creados por cada motivo
    filtered_df = filtered_df.groupby('motivo_permiso')['id'].count().reset_index().sort_values(by=['id'], ascending=False)

    total_percent = filtered_df['id'].sum()
    filtered_df['Porcentaje'] = (filtered_df['id'] / total_percent) * 100
    
    sumPercent = 0
    filtered_df['PorcentajeAcumulado'] = 0

    for i, row in filtered_df.iterrows():
        sumPercent += row['Porcentaje']
        filtered_df.loc[i, 'PorcentajeAcumulado'] = sumPercent

    filtered_df = filtered_df.sort_values(by=['PorcentajeAcumulado'], ascending=True, axis=0)

    print(filtered_df)

    permits_dict = json.loads(filtered_df.to_json(orient='records'))

    return JsonResponse({'permisos': permits_dict, 'motivo_permisos': filtered_df['motivo_permiso'].to_list(), 'cantidad_permisos': filtered_df['id'].to_list(), 'porcentaje_acumulado': filtered_df['PorcentajeAcumulado'].to_list()})
    
#Vista para filtrar el grafico por el area elegida
def actualizar_permisos_chart_area(request, area_id):
    """
    Actualiza los datos del gráfico de permisos según el área seleccionada.

    Esta vista obtiene los permisos de la base de datos filtrados por área y 
    calcula los porcentajes acumulados para cada motivo de permiso. Luego, organiza 
    estos datos en un formato adecuado para la visualización en un gráfico.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP.
        area_id (str): El ID del área para la cual se deben filtrar los permisos. 
                       Si es 'all', se incluyen todas las áreas.

    Returns:
        JsonResponse: Una respuesta JSON que contiene los datos filtrados y calculados 
        para los permisos, incluyendo los porcentajes acumulados y los conteos por motivo de permiso.
    """
    try:
        if area_id == 'all':
            permisos = Permiso.objects.all()
            print(f"Permisos para todas las áreas: {[permiso.id for permiso in permisos]}")
        else:
            area = Area.objects.get(id=area_id)
            permisos = Permiso.objects.filter(area=area)
            print(f"Permisos para el área {area_id} ({area.nombre_area}): {[permiso.id for permiso in permisos]}")
    except Area.DoesNotExist:
        return JsonResponse({
            'error': f'Area with id {area_id} does not exist.'
        }, status=404)

    if not permisos.exists():
        print(f"No hay permisos para el área {area_id if area_id != 'all' else 'todas las áreas'}")
        return JsonResponse({
            'permisos': [],
            'area': [],
            'motivo_permisos': [],
            'cantidad_permisos': [],
            'porcentaje_acumulado': []
        })

    data = {
        'id': [], 'creado': [], 'fecha_permiso': [], 
        'fecha_fin_permiso': [], 'motivo_permiso': [], 'area': []
    }

    for permiso in permisos:
        data['id'].append(permiso.id)
        data['creado'].append(permiso.creado)
        data['motivo_permiso'].append(permiso.motivo_permiso.name_motivo)
        data['fecha_permiso'].append(permiso.fecha_permiso)
        data['fecha_fin_permiso'].append(permiso.fecha_fin_permiso)
        data['area'].append(permiso.area.id) 
    
    permits_df = pd.DataFrame(data)

    if area_id != 'all':
        permits_df['area'] = permits_df['area'].astype(int)
        filtered_df = permits_df[permits_df['area'] == int(area_id)]
        print(f"Filtered DataFrame for area '{area_id}':", filtered_df)
    else:
        filtered_df = permits_df
        print("Filtered DataFrame for all areas:", filtered_df)

    if filtered_df.empty:
        print(f"No data found for area '{area_id if area_id != 'all' else 'todas las áreas'}")
        return JsonResponse({
            'permisos': [],
            'area': [],
            'motivo_permisos': [],
            'cantidad_permisos': [],
            'porcentaje_acumulado': []
        })

    motivo_counts = filtered_df.groupby('motivo_permiso')['id'].count().reset_index().sort_values(by=['id'], ascending=False)
    
    total_percent = motivo_counts['id'].sum()
    motivo_counts['Porcentaje'] = (motivo_counts['id'] / total_percent) * 100
    motivo_counts['PorcentajeAcumulado'] = motivo_counts['Porcentaje'].cumsum()

    print("Motivo Counts DataFrame:", motivo_counts)

    permits_dict = json.loads(motivo_counts.to_json(orient='records'))

    return JsonResponse({
        'permisos': permits_dict,
        'area': [area_id] * len(motivo_counts),
        'motivo_permisos': motivo_counts['motivo_permiso'].to_list(),
        'cantidad_permisos': motivo_counts['id'].to_list(),
        'porcentaje_acumulado': motivo_counts['PorcentajeAcumulado'].to_list()
    })

#Vista para obtener los dias de los permisos creados (para el boton que filtra el grafico por dias)
def get_days(request):
    """
    Obtiene una lista de fechas únicas de creación de permisos en formato 'dd-mm-YYYY'.

    Esta vista obtiene todas las fechas de creación de permisos, las convierte a 
    un formato específico y devuelve una lista de fechas únicas ordenadas.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP.

    Returns:
        JsonResponse: Una respuesta JSON que contiene una lista de fechas únicas 
        en formato 'dd-mm-YYYY'. En caso de error, se devuelve un mensaje de error 
        con un estado HTTP 500.
    """
    try:
        permisos = Permiso.objects.all().values_list('creado', flat=True).distinct()
        fechas = sorted(list(set([permiso.strftime('%d-%m-%Y') for permiso in permisos])))
        return JsonResponse({'fechas': fechas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#Vista para filtrar el grafico por los dias
def actualizar_permisos_chart_dias(request, fecha):
    """
    Actualiza los datos del gráfico de permisos según la fecha seleccionada.

    Esta vista obtiene los permisos de la base de datos filtrados por la fecha 
    proporcionada y calcula los porcentajes acumulados para cada motivo de permiso. 
    Luego, organiza estos datos en un formato adecuado para la visualización en un gráfico.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP.
        fecha (str): La fecha para la cual se deben filtrar los permisos en formato 'dd-mm-YYYY'. 
                     Si es 'all', se incluyen todas las fechas.

    Returns:
        JsonResponse: Una respuesta JSON que contiene los datos filtrados y calculados 
        para los permisos, incluyendo los porcentajes acumulados y los conteos por motivo de permiso.
    """
    try:
        if fecha != 'all':
            # Convierte la cadena de fecha en un objeto datetime
            fecha_obj = datetime.strptime(fecha, '%d-%m-%Y')
            dia = fecha_obj.day
            mes = fecha_obj.month
            año = fecha_obj.year
        
        permisos = Permiso.objects.all()

        # Crear el DataFrame
        data = {
            'id': [],
            'creado': [],
            'fecha_permiso': [],
            'fecha_fin_permiso': [],
            'motivo_permiso': []
        }

        for permiso in permisos:
            data['id'].append(permiso.id)
            data['creado'].append(permiso.creado)
            data['motivo_permiso'].append(permiso.motivo_permiso.name_motivo)
            data['fecha_permiso'].append(permiso.fecha_permiso)
            data['fecha_fin_permiso'].append(permiso.fecha_fin_permiso)

        permits_df = pd.DataFrame(data)

        # Convertir las fechas a datetime
        permits_df['creado'] = pd.to_datetime(permits_df['creado'])
        permits_df['fecha_permiso'] = pd.to_datetime(permits_df['fecha_permiso'])
        permits_df['fecha_fin_permiso'] = pd.to_datetime(permits_df['fecha_fin_permiso'])

        # Filtrar los registros según el día, mes y año
        if fecha != 'all':
            filtered_df = permits_df[(permits_df['creado'].dt.day == dia) &
                                    (permits_df['creado'].dt.month == mes) &
                                    (permits_df['creado'].dt.year == año)]
            print(f"Filtered DataFrame for date '{fecha}':", filtered_df)
        else:
            filtered_df = permits_df
            print("Filtered DataFrame for all days:", filtered_df)
        
        # Conteo de permisos creados por cada motivo
        filtered_df = filtered_df.groupby('motivo_permiso')['id'].count().reset_index().sort_values(by=['id'], ascending=False)

        total_percent = filtered_df['id'].sum()
        filtered_df['Porcentaje'] = (filtered_df['id'] / total_percent) * 100

        sumPercent = 0
        filtered_df['PorcentajeAcumulado'] = 0

        for i, row in filtered_df.iterrows():
            sumPercent += row['Porcentaje']
            filtered_df.loc[i, 'PorcentajeAcumulado'] = sumPercent

        filtered_df = filtered_df.sort_values(by=['PorcentajeAcumulado'], ascending=True, axis=0)

        print("Motivo Counts DataFrame:", filtered_df)

        permits_dict = json.loads(filtered_df.to_json(orient='records'))

        return JsonResponse({
            'permisos': permits_dict,
            'motivo_permisos': filtered_df['motivo_permiso'].to_list(),
            'cantidad_permisos': filtered_df['id'].to_list(),
            'porcentaje_acumulado': filtered_df['PorcentajeAcumulado'].to_list()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
#Vista para las horas muensuales de los permiso
def actualizar_permisos_chart_horas(request):
    """
    Actualiza los datos del gráfico de permisos calculando las horas totales por motivo de permiso.

    Esta vista obtiene todos los permisos de la base de datos, calcula la cantidad de horas de permiso 
    entre las fechas de inicio y fin de cada permiso, y organiza estos datos en un formato adecuado 
    para la visualización en un gráfico. Además, agrupa los datos por motivo de permiso para calcular 
    las horas mensuales y los porcentajes acumulados.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP.

    Returns:
        JsonResponse: Una respuesta JSON que contiene los datos filtrados y calculados para los permisos, 
        incluyendo los porcentajes acumulados, los conteos por motivo de permiso y las horas mensuales.
    """
    permisos = Permiso.objects.all()

    datos_permisos = []

    for i in permisos:
        fecha_permiso = pd.to_datetime(i.fecha_permiso)
        fecha_fin_permiso = pd.to_datetime(i.fecha_fin_permiso)

        dias_diferencia = (fecha_permiso - fecha_fin_permiso).days + 1
        horas_diferencia = dias_diferencia * 8

        aux = {
            'creado': i.creado,
            'fecha_permiso': i.fecha_permiso,
            'fecha_fin_permiso': i.fecha_fin_permiso,
            'motivo_permiso': i.motivo_permiso,
            'horas_entre_fechas': horas_diferencia
        }
        datos_permisos.append(aux)

    datos = {'id': [], 'creado': [], 'fecha_permiso': [], 'fecha_fin_permiso': [], 'motivo_permiso': [], 'horas_entre_fechas': [], 'horas_mensuales': []}

    for permiso in permisos:
        fecha_permiso = pd.to_datetime(permiso.fecha_permiso)
        fecha_fin_permiso = pd.to_datetime(permiso.fecha_fin_permiso)

        dias_diferencia = (fecha_fin_permiso - fecha_permiso).days + 1
        horas_entre_fechas = dias_diferencia * 8

        datos['id'].append(permiso.id)
        datos['creado'].append(permiso.creado)
        datos['motivo_permiso'].append(permiso.motivo_permiso.name_motivo)
        datos['fecha_permiso'].append(permiso.fecha_permiso)
        datos['fecha_fin_permiso'].append(permiso.fecha_fin_permiso)
        datos['horas_entre_fechas'].append(horas_entre_fechas)
        datos['horas_mensuales'].append(horas_entre_fechas)  

    per_df = pd.DataFrame(datos)

    per_df['horas_mensuales'] = per_df.groupby('motivo_permiso')['horas_mensuales'].transform('sum')

    per_df['count'] = per_df.groupby('motivo_permiso')['motivo_permiso'].transform('count')

    per_df = per_df.sort_values(by=['horas_mensuales'], ascending=False, axis=0)
    per_df = per_df.drop_duplicates('motivo_permiso')

    total_porcentaje = per_df['count'].sum()
    per_df['Porcentaje'] = (per_df['count'] / total_porcentaje) * 100

    sumaPorcentaje = 0
    per_df['PorcentajeAcumulado'] = 0 

    for i, row in per_df.iterrows():
        sumaPorcentaje += row['Porcentaje']
        per_df.loc[i, 'PorcentajeAcumulado'] = sumaPorcentaje

    per_df = per_df.sort_values(by=['PorcentajeAcumulado'], ascending=True, axis=0)

    per_dict = per_df.to_dict(orient='records')

    return JsonResponse({'Per': per_dict, 'motivos_permisos': per_df['motivo_permiso'].tolist(), 'cantidad_permisos': per_df['count'].tolist(), 'horas_mensuales': per_df['horas_mensuales'].tolist(), 'porcentaje_acumulado': per_df['PorcentajeAcumulado'].tolist()})

#Vista para el cuadro con personas que más piden permisos
def chart_cant_permisos(request):
    """
    Genera datos para una tabla sobre la cantidad de permisos por motivo y persona.

    Esta vista obtiene todos los permisos de la base de datos, calcula la cantidad de 
    permisos por motivo y por persona, y organiza estos datos en un formato adecuado 
    para la visualización en una tabla. Además, selecciona las cinco personas con la 
    mayor cantidad de permisos.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP.

    Returns:
        JsonResponse: Una respuesta JSON que contiene los datos filtrados y calculados 
        para los permisos, incluyendo los nombres completos, los motivos de permiso y 
        las cantidades de permisos.
    """
    permisos = Permiso.objects.all()

    datos_permisos = []

    for i in permisos:
        aux = {
            'creado': i.creado,
            'nombre_completo': i.nombre_completo,
            'motivo_permiso': i.motivo_permiso,
        }
        datos_permisos.append(aux)

    datos = {'id': [], 'creado': [], 'nombre_completo': [], 'motivo_permiso': []}

    for permiso in permisos:
        datos['id'].append(permiso.id)
        datos['creado'].append(permiso.creado)
        datos['nombre_completo'].append(permiso.nombre_completo)
        datos['motivo_permiso'].append(permiso.motivo_permiso.name_motivo)

    df_permisos = pd.DataFrame(datos)

    df_permisos['cantidad'] = df_permisos.groupby(['nombre_completo','motivo_permiso'])['id'].transform('count')
    df_permisos = df_permisos.drop_duplicates('nombre_completo')
    df_permisos = df_permisos.sort_values(by=['cantidad'], ascending=False)
    df_permisos = df_permisos.nlargest(5, 'cantidad')

    dict_perm = df_permisos.to_dict(orient='records')

    return JsonResponse({'Per': dict_perm, 'nombre_completo':df_permisos['nombre_completo'].to_list(), 'motivo_permiso':df_permisos['motivo_permiso'].to_list(), 'cantidad':df_permisos['cantidad'].to_list()})

# Vista para ver permisos
class GestionPermisos(LoginRequiredMixin, TemplateView):
    """
    Vista para ver los permisos creados de los empleados.

    Atributos:
        - template_name (str): Nombre del template utilizado para renderizar la página de gestión de permisos.

    Metodos:
        - get_context_data(**kwargs): Obtiene y devuelve el contexto para renderizar la página.
        - dispatch(request, *args, **kwargs): Controla la dirección de la solicitud según los parámetros.
        - post(request, *args, **kwargs): Procesa los datos enviados mediante el formulario en la página.
        - mostrar_archivo(request, id_permiso): Muestra el archivo adjunto correspondiente a un permiso.

    Notas:
        - Hereda de LoginRequiredMixin para asegurar que solo los usuarios autenticados pueden acceder a la página de gestión de permisos.
        - Utiliza el atributo 'template_name' para especificar el template a utilizar.

    Modo de uso:
        - Accede a esta vista para visualizar los permisos de los empleados.
    """
    template_name = 'permisos_gestion.html'

    @staticmethod
    def actualizar_tabla_areas(request, area_id):
        """
        Actualiza los datos de la tabla de permisos según el área seleccionada.

        Este método obtiene los permisos de la base de datos filtrados por área y 
        organiza estos datos en un formato adecuado para su visualización en una tabla. 
        Si se selecciona 'all', se incluyen todos los permisos.

        Args:
            request (HttpRequest): El objeto de solicitud HTTP.
            area_id (str): El ID del área para la cual se deben filtrar los permisos. 
                           Si es 'all', se incluyen todas las áreas.

        Returns:
            JsonResponse: Una respuesta JSON que contiene los datos filtrados para los permisos.
        """
        try:
            if area_id == 'all':
                permisos = Permiso.objects.all().order_by('-creado')
                print(f"Permisos para todas las áreas: {[permiso.id for permiso in permisos]}")
            else:
                area = Area.objects.get(id=area_id)
                permisos = Permiso.objects.filter(area=area).order_by('-creado')
                print(f"Permisos para el área {area_id} ({area.nombre_area}): {[permiso.id for permiso in permisos]}")

            permisos_data = []
            for permiso in permisos:
                permisos_data.append({
                    'creado': permiso.creado.strftime('%Y-%m-%d'),
                    'nombre_completo': permiso.nombre_completo,
                    'cedula': permiso.cedula,
                    'area': permiso.area.nombre_area,
                    'turno': str(permiso.turno), 
                    'fecha_permiso': permiso.fecha_permiso.strftime('%Y-%m-%d'),
                    'fecha_fin_permiso': permiso.fecha_fin_permiso.strftime('%Y-%m-%d'),
                    'hora_salida': permiso.hora_salida,
                    'hora_llegada': permiso.hora_llegada,
                    'motivo_permiso': permiso.motivo_permiso.name_motivo,
                    'nombre_coordinador': permiso.nombre_coordinador,
                    'compensa_tiempo': permiso.compensa_tiempo,
                    'datos_adjuntos': permiso.datos_adjuntos.url if permiso.datos_adjuntos else '',
                    'observacion': permiso.observacion,
                    'creado_por': permiso.creado_por.username, 
                    'verificacion': permiso.verificacion,
                    'estado': permiso.estado,
                    'verificado_por': permiso.verificado_por.username if permiso.verificado_por else '',
                    'fecha_verificacion': permiso.fecha_verificacion.strftime('%Y-%m-%d') if permiso.fecha_verificacion else '',
                    'edit_url': reverse('update_permiso', args=[permiso.id]) 
                })

            return JsonResponse({'permisos': permisos_data})

        except Area.DoesNotExist:
            return JsonResponse({'error': f'Area with id {area_id} does not exist.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
    def get_context_data(self, **kwargs):
        """
        Obtiene y devuelve el contexto para renderizar la página.

        Return:
            - dict: Un diccionario con datos para renderizar la página.

        Notas:
            - Verifica si el usuario es líder o tiene otra función, filtra la lista de permisos en consecuencia.

        Modo de uso:
            - Este método se llama automáticamente al acceder a la página de gestión de permisos.
        """
        contexto = super().get_context_data(**kwargs)
        user = self.request.user

        es_superusuario = user.groups.filter(name='SuperUser').exists()

        if es_superusuario:
        # Si el usuario es superusuario, se le muestran todos los permisos
            contexto['lista_permisos'] = Permiso.objects.all()
        else:
            area = user.customuser.area if hasattr(user, 'customuser') and user.customuser else None

            # print(f"Nombre de usuario: {user.username}")
            # print(f"Área del area: {user.area}")
            # print(f"Grupos de permisos: {user.groups.all()}")

            es_admin = user.groups.filter(name='Admin').exists()
            es_lider = user.groups.filter(name='Lideres').exists()
            # es_BP = user.groups.filter(name='BP').exists()

            if es_admin:
                contexto['lista_permisos'] = Permiso.objects.all()
            elif area:
                # Si hay un área, filtra los permisos por esa área
                contexto['lista_permisos'] = Permiso.objects.filter(area=area)
            else:
                area = user.area
                contexto['lista_permisos'] = Permiso.objects.filter(area=area)

        # verificación del grupo de permisos
        grupo_admin = Group.objects.get(name='Admin')
        es_admin = grupo_admin in user.groups.all()

        grupo_lideres = Group.objects.get(name='Lideres')
        es_lider = grupo_lideres in user.groups.all()

        # grupo_BP = Group.objects.get(name='BP')
        # es_BP = grupo_GH in user.groups.all()

        contexto['es_admin'] = es_admin
        contexto['es_lider'] = es_lider
        contexto['es_superusuario'] = es_superusuario

        # contexto['es_BP'] = es_BP
        return contexto
    
    def dispatch(self, request, *args, **kwargs):
        """
        Controla la dirección de la solicitud según los parámetros.

        Args:
            - request (HttpRequest): Objeto que contiene la información de la solicitud HTTP.
            - args: Argumentos adicionales.
            - kwargs: Argumentos clave adicionales.

        Return:
            - HttpResponse: Respuesta HTTP después de procesar la solicitud.

        Notas:
            - Si se proporciona 'id_permiso' en los parámetros, llama al método 'mostrar_archivo'.
            - De lo contrario, llama al método 'dispatch' de la clase base.

        Modo de uso:
            - Este método se llama automáticamente al procesar una solicitud.
        """
        if 'id_permiso' in kwargs:
            return self.mostrar_archivo(request, kwargs['id_permiso'])
        else:
            return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Procesa los datos enviados mediante el formulario en la página.

        Args:
            - request (HttpRequest): Objeto que contiene la información de la solicitud HTTP.
            - args: Argumentos adicionales.
            - kwargs: Argumentos clave adicionales.

        Return:
            - HttpResponse: Respuesta HTTP después de procesar los datos del formulario.

        Notas:
            - Procesa el formulario de permisos y guarda la información si es válido.

        Modo de uso:
            - Este método se llama automáticamente al enviar datos mediante el formulario.
        """
        form = PermisoForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('inicio')
        else:
            return render(request, self.template_name, {'form':form})
        
    def mostrar_archivo(self, request, id_permiso):
        """
        Muestra el archivo adjunto correspondiente a un permiso.

        Args:
            - request (HttpRequest): Objeto que contiene la información de la solicitud HTTP.
            - id_permiso (int): Id del permiso para el cual se muestra el archivo adjunto.

        Return:
            - HttpResponse: Respuesta HTTP que muestra el archivo adjunto.

        Notas:
            - Verifica el tipo de archivo y muestra el contenido si es compatible.

        Modo de uso:
            - Este método se llama automáticamente al acceder a la visualización de un archivo adjunto.
        """
        permiso = Permiso.objects.get(pk=id_permiso)
        if permiso.datos_adjuntos:
            archivo_path = permiso.datos_adjuntos.path
            mime_type, _ = mimetypes.guess_type(archivo_path)
            if mime_type:
                with open(archivo_path, 'rb') as file:
                    response = HttpResponse(file.read(), content_type=mime_type)
                    response['Content-Disposition'] = 'inline; filename=' + os.path.basename(archivo_path)
                    return response
            else:
                return HttpResponse("El tipo de archivo no es compatible.")
        else:
            return HttpResponse("No hay archivo adjunto.")

# Vista para la edicion de permisos
class ActualizarPermiso(UpdateView, LoginRequiredMixin):
    """
    Vista para actualizar un permiso existente.

    Atributos:
        - model (Permiso): Modelo de datos asociado a la vista.
        - form_class (PermisoForm): Clase de formulario utilizada para la actualización.
        - template_name (str): Nombre del template utilizado para renderizar la página de actualización.
        - success_url (str): URL a la que se redirige después de una actualización exitosa.

    Metodos:
        - get_context_data(**kwargs): Obtiene y devuelve el contexto para renderizar la página.
        - get_form_kwargs(): Obtiene y devuelve los argumentos para inicializar el formulario.
        - form_valid(form): Procesa el formulario después de una validación exitosa.

    Notas:
        - Hereda de UpdateView y LoginRequiredMixin.
        - Utiliza el modelo Permiso y el formulario PermisoForm.

    Modo de uso:
        - Accede a esta vista para actualizar un permiso existente.
    """
    model = Permiso
    form_class = PermisoForm
    template_name = 'update_temp/update_permisos.html'
    success_url = reverse_lazy('ver permisos')

    def get_context_data(self, **kwargs):
        """
        Obtiene y devuelve el contexto para renderizar la página.

        Return:
            - dict: Un diccionario con datos para renderizar la página.

        Notas:
            - Filtra la lista de permisos.
            - Verifica si el usuario es coordinador y agrega la información al contexto.

        Modo de uso:
            - Este método se llama automáticamente al acceder a la página de actualización.
        """
        contexto = super().get_context_data(**kwargs)
        contexto['lista_permisos'] = Permiso.objects.all()

        #Es Admin o no
        grupo_admin = Group.objects.get(name='Admin')
        es_admin = grupo_admin in self.request.user.groups.all()
        contexto['es_admin'] = es_admin

        #Es superusuario o no
        grupo_superusuario = Group.objects.get(name='SuperUser')
        es_superusuario = grupo_superusuario in self.request.user.groups.all()
        contexto['es_superusuario'] = es_superusuario

        contexto['campos_editables'] = ['verificacion', 'estado']
        return contexto
    
    def get_form_kwargs(self):
        """
        Obtiene y devuelve los argumentos para inicializar el formulario.

        Return:
            - dict: Un diccionario con argumentos para inicializar el formulario.

        Notas:
            - Agrega el usuario actual y la bandera de edición al formulario.

        Modo de uso:
            - Este método se llama automáticamente al inicializar el formulario.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['editing'] = True
        return kwargs
    
    def form_valid(self, form):
        """
        Procesa el formulario después de una validación exitosa.

        Args:
            - form (PermisoForm): Formulario de permiso con datos validados.

        Return:
            - HttpResponse: Respuesta HTTP después de procesar el formulario.

        Notas:
            - Asigna el usuario actual al campo 'verificado_por'.
            - Actualiza la fecha de verificación si el usuario es coordinador.
            - Envía un correo electrónico si el permiso es rechazado.

        Modo de uso:
            Este método se llama automáticamente después de una validación exitosa del formulario.
        """
        user = self.request.user # Obtiene el usuario actual

        if user.is_superuser:
            form.instance.verificado_por = user
            form.instance.fecha_verificacion = timezone.now()

        form.instance.verificado_por = CustomUser.objects.get(username=user.username) # Asigna el usuario actual al campo verificado_por
        
        if user.groups.filter(name='Admin').exists() and self.object:
            form.instance.fecha_verificacion = timezone.now()

        #Envio del correo cuando el permiso es rechazado
        if form.instance.verificacion == 'Rechazado':
            html_message = render_to_string('notificaciones/notify_permiso_rechazado.html', {
            'usuario': form.instance.creado_por,
            'nombre': form.instance.nombre_completo,
            'cedula': form.instance.cedula,
            'area': form.instance.area,
            'turno': form.instance.turno,
            'fecha_permiso': form.instance.fecha_permiso,
            'fecha_fin_permiso': form.instance.fecha_fin_permiso,
            'hora_salida': form.instance.hora_salida,
            'hora_llegada': form.instance.hora_llegada,
            'motivo_permiso:': form.instance.motivo_permiso,
            'nombre_coordinador': form.instance.nombre_coordinador,
            'compensa_tiempo': form.instance.compensa_tiempo,
            'verificacion': form.instance.verificacion,
            'estado': form.instance.estado,
            'autor': form.instance.verificado_por
            })

            # Crear una versión de texto plano del mensaje
            plain_message = strip_tags(html_message)

            send_mail(
                subject='NOTIFICACION DE PERMISO RECHAZADA',
                message=plain_message,
                from_email=None,
                recipient_list=[''],
                html_message=html_message,
                fail_silently=False,
            )
        print("Processing form_valid")
        # print(form.cleaned_data)
        response = super().form_valid(form)
        print("Form successfully processed")
        return response

"""--------------------------------  LICENCIAS  --------------------------------"""
#Vista para los graficos de Licencias
class LicenciasChartView(LoginRequiredMixin,TemplateView):
    """
    Vista basada en clase para generar un gráfico de pareto de licencias.

    Esta vista requiere que el usuario esté autenticado y proporciona un contexto 
    con datos necesarios para generar un gráfico de pareto de licencias, incluyendo tipos de licencias, 
    porcentajes acumulados y días por mes.

    Atributos:
        template_name (str): El nombre de la plantilla que se renderizará.

    Métodos:
        get_context_data(**kwargs): Obtiene el contexto para la plantilla.
    """
    template_name = 'graficos/graf_licencias.html'
    template_name = 'graficos/graf_licencias.html'

    def get_context_data(self, **kwargs):
        """
        Obtiene el contexto para la plantilla.

        Esta función recopila datos de licencias, los organiza y calcula información 
        adicional necesaria para los gráficos, incluyendo el conteo de licencias por tipo,
        días por mes y porcentajes acumulados.

        Args:
            **kwargs: Argumentos adicionales para el contexto.

        Returns:
            dict: Un diccionario con los datos del contexto para la plantilla.
        """
        context = super().get_context_data(**kwargs)

        licencias = Licencia.objects.all()

        fechas_licencias = Licencia.objects.dates('creado', 'month')

        dias_por_mes = defaultdict(lambda: defaultdict(int))

        for fecha_licencia in fechas_licencias:
            year = fecha_licencia.year
            month = fecha_licencia.month

            # Calcula la cantidad de días en el mes
            dias_en_mes = (fecha_licencia.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)

            dias_por_mes[year][month] = dias_en_mes.day

        tipos_licencias = {}

        for licencia in licencias:
            tipo_licencia = licencia.motivo_licencia

            tipos_licencias[tipo_licencia.id] = tipos_licencias.get(tipo_licencia.id, {'id': tipo_licencia.id, 'nombre': tipo_licencia.name_motivo_licencia, 'count': 0})
            tipos_licencias[tipo_licencia.id]['count'] += 1

            month = licencia.creado.month

        # Ordena de mayor a menor
        tipos_licencias = dict(sorted(tipos_licencias.items(), key=lambda item: item[1]['count'], reverse=True))

        # Calcula el porcentaje acumulado
        total_counts = sum(tipo['count'] for tipo in tipos_licencias.values())
        porcentaje_acumulado = 0
        porcentajes_acumulados = []

        for tipo_id, tipo in tipos_licencias.items():
            if total_counts != 0:
                porcentaje_acumulado += (tipo['count'] / total_counts) * 100
            else:
                porcentaje_acumulado = 0

            porcentajes_acumulados.append(porcentaje_acumulado)

        context['tipos_licencias'] = json.dumps(list(tipos_licencias.values()))
        context['porcentajes_acumulados'] = porcentajes_acumulados
        context['dias_por_mes'] = dias_por_mes

        return context

#Vista para el cuadro con personas que más piden licencias
def chart_cant_licencias(request):
    """
    Vista que devuelve un JSON con los datos de las licencias más frecuentes por empleado.
    
    Args:
        request (HttpRequest): La solicitud HTTP recibida por la vista.

    Returns:
        JsonResponse: Un objeto JSON que contiene la lista de las licencias más frecuentes por empleado,
                     junto con sus nombres y cantidad de licencias.

    Funcionamiento:
        1. Obtiene todas las instancias de Licencia desde la base de datos.
        2. Crea un DataFrame de pandas con los datos de las licencias.
        3. Calcula la cantidad de licencias por nombre completo y motivo de licencia.
        4. Selecciona los 5 empleados con más licencias y los ordena por cantidad descendente.
        5. Retorna un JsonResponse con la lista de las licencias más frecuentes, el nombre completo del empleado,
           el motivo de la licencia y la cantidad de licencias.
    """
    licencias = Licencia.objects.all()

    datos_lic = []

    for i in licencias:
        aux = {
            'creado': i.creado,
            'nombre_completo': i.nombre_completo,
            'motivo_licencia': i.motivo_licencia,
        }
        datos_lic.append(aux)

    datos = {'id': [], 'creado': [], 'nombre_completo': [], 'motivo_licencia': []}

    for licencia in licencias:
        datos['id'].append(licencia.id)
        datos['creado'].append(licencia.creado)
        datos['nombre_completo'].append(licencia.nombre_completo)
        datos['motivo_licencia'].append(licencia.motivo_licencia.name_motivo_licencia)

    df_licencias = pd.DataFrame(datos)

    df_licencias['cantidad'] = df_licencias.groupby(['nombre_completo', 'motivo_licencia'])['id'].transform('count')
    df_licencias = df_licencias.drop_duplicates('nombre_completo')
    df_licencias = df_licencias.sort_values(by=['cantidad'], ascending=False)
    df_licencias = df_licencias.nlargest(5, 'cantidad')
    
    dict_lic = df_licencias.to_dict(orient='records')

    return JsonResponse({'Lic': dict_lic, 'nombre_completo':df_licencias['nombre_completo'].to_list(), 'motivo_licencia':df_licencias['motivo_licencia'].to_list(), 'cantidad':df_licencias['cantidad'].to_list()})

#Vista para el grafico de linea de tiempo (licencias)
def timeline_licencia_chart(request):
    """
    Vista que devuelve un JSON con datos estadísticos sobre las licencias basadas en el tiempo y el motivo para
    usarse en un grafico de linea de tiempo.

    Args:
        request (HttpRequest): La solicitud HTTP recibida por la vista.

    Returns:
        JsonResponse: Un objeto JSON que contiene estadísticas mensuales de horas de licencia,
                     junto con detalles mensuales y totales de licencias por motivo.

    Funcionamiento:
        1. Obtiene todas las instancias de Licencia desde la base de datos.
        2. Calcula la diferencia en horas entre la fecha de inicio y la fecha de fin de cada licencia.
        3. Agrupa y procesa los datos para obtener estadísticas mensuales de horas de licencia por motivo.
        4. Calcula y agrega estadísticas mensuales y totales de licencias por motivo.
        5. Retorna un JsonResponse con datos estructurados sobre las horas mensuales de licencia,
           detalles mensuales de licencias y totales de licencias por motivo.
    """
    licenses = Licencia.objects.all()

    licenses_data = []

    for i in licenses:

        fecha_inicio = pd.to_datetime(i.fecha_inicio)
        fecha_fin = pd.to_datetime(i.fecha_fin)

        diff_days = (fecha_inicio - fecha_fin).days + 1
        diff_hours = diff_days * 8

        aux = {
            'creado': i.creado,
            'fecha_inicio': i.fecha_inicio,
            'fecha_fin': i.fecha_fin,
            'motivo_licencia': i.motivo_licencia.name_motivo_licencia,
            'hours_between': diff_hours
        }
        licenses_data.append(aux)

    data = {'id': [], 'creado': [], 'fecha_inicio': [], 'fecha_fin': [], 'motivo_licencia': [], 'month':[], 'hours_between': [], 'monthly_hours': []}

    for license in licenses:
        fecha_inicio = pd.to_datetime(license.fecha_inicio)
        fecha_fin = pd.to_datetime(license.fecha_fin)

        diff_days = (fecha_fin - fecha_inicio).days + 1
        hours_between = diff_days * 8

        data['id'].append(license.id)
        data['creado'].append(license.creado)
        data['fecha_inicio'].append(license.fecha_inicio)
        data['fecha_fin'].append(license.fecha_fin)
        data['motivo_licencia'].append(license.motivo_licencia.name_motivo_licencia)
        month = license.creado.strftime("%Y-%m")
        data['month'].append(month)
        data['hours_between'].append(hours_between)
        data['monthly_hours'].append(hours_between)

    month_counts = Counter(data['month'])
    month_data = [{'month': month, 'count': count} for month, count in month_counts.items()]

    licenses_df = pd.DataFrame(data)

    licenses_df['monthly_hours'] = licenses_df.groupby('motivo_licencia')['monthly_hours'].transform('sum')
    licenses_df['true_monthly_hours'] = licenses_df.groupby('month')['hours_between'].transform('sum')
    licenses_df = licenses_df.drop_duplicates('true_monthly_hours')

    licenses_df['quantity'] = licenses_df.groupby('motivo_licencia')['motivo_licencia'].transform('count')
    licenses_df = licenses_df.drop_duplicates('motivo_licencia')

    licenses_dict = json.loads(licenses_df.to_json(orient='records'))
    return JsonResponse({'Licenses':licenses_dict, 'month':month_data, 'true_monthly_hours':licenses_df['true_monthly_hours'].to_list()})

#Vista que actuliza grafico mediante el mes elegido
def actualizar_licencias_chart(request, fecha):
    """
    Vista que devuelve un JSON con estadísticas actualizadas de licencias filtradas por mes.

    Args:
        request (HttpRequest): La solicitud HTTP recibida por la vista.
        fecha (str): El mes seleccionado como filtro para las licencias (formato numérico).

    Returns:
        JsonResponse: Un objeto JSON que contiene estadísticas de licencias filtradas por motivo,
                     cantidad de licencias, y porcentaje acumulado por motivo.

    Funcionamiento:
        1. Obtiene todas las instancias de Licencia desde la base de datos.
        2. Crea un DataFrame de pandas con los datos de las licencias, incluyendo el motivo y fechas.
        3. Filtra el DataFrame para seleccionar solo las licencias del mes especificado.
        4. Agrupa y cuenta las licencias por motivo, calcula el porcentaje de cada motivo respecto al total.
        5. Calcula el porcentaje acumulado de los motivos y ordena el DataFrame por este porcentaje.
        6. Retorna un JsonResponse con los datos estructurados de las estadísticas de licencias filtradas por mes.
    """
    licencias = Licencia.objects.all()

    datos_licencias = []

    for i in licencias:
        
        aux = {
            'creado': i.creado,
            'nombre_completo': i.nombre_completo,
            'cedula': i.cedula,
            'fecha_inicio' : i.fecha_inicio,
            'fecha_fin' : i.fecha_fin,
            'motivo_licencia': i.motivo_licencia.name_motivo_licencia,
        }
        datos_licencias.append(aux)

    data = {'id': [], 'creado': [] ,'motivo_licencia': [], 'fecha_inicio': [], 'fecha_fin': []}

    for licencia in licencias:
        data['id'].append(licencia.id)
        data['creado'].append(licencia.creado)
        data['motivo_licencia'].append(licencia.motivo_licencia.name_motivo_licencia)
        data['fecha_inicio'].append(licencia.fecha_inicio)
        data['fecha_fin'].append(licencia.fecha_fin)

    licencias_df = pd.DataFrame(data)

    # trae los registros del mes seleccionado
    mes = int(fecha)

    licencias_df['fecha_inicio'] = pd.to_datetime(licencias_df['fecha_inicio'])
    licencias_df['fecha_fin'] = pd.to_datetime(licencias_df['fecha_fin'])

    if mes == 0:
        df_filtrado = licencias_df.copy()
    else:
        df_filtrado = licencias_df[(licencias_df['creado'].dt.month == mes) | (licencias_df['creado'].dt.month == mes)]
        print(f"Cantidad de licencias para el mes {mes}: {df_filtrado['id'].count()}")

    #Conteo licencias creados por cada motivo
    df_filtrado = df_filtrado.groupby('motivo_licencia')['id'].count().reset_index().sort_values(by=['id'], ascending=False)
    
    total_porcentaje = df_filtrado['id'].sum()
    df_filtrado['Porcentaje'] = (df_filtrado['id'] / total_porcentaje) * 100

    sumaPorcentaje = 0
    df_filtrado['PorcentajeAcumulado'] = 0 

    for i, row in df_filtrado.iterrows():
        sumaPorcentaje += row['Porcentaje']
        df_filtrado.loc[i, 'PorcentajeAcumulado'] = sumaPorcentaje

    df_filtrado = df_filtrado.sort_values(by=['PorcentajeAcumulado'], ascending=True, axis=0)

    # print(df_filtrado)

    # dataFrame a diccionario
    licencias_dict = json.loads(df_filtrado.to_json(orient='records'))

    return JsonResponse({'licencias':licencias_dict, "motivos_licencias":df_filtrado['motivo_licencia'].to_list(),"cantidad_licencias":df_filtrado['id'].to_list() ,"PorcentajeAcumulado":df_filtrado['PorcentajeAcumulado'].to_list()})

#Vista para horas mensuales de las licencias
def actualizar_licencias_chart_horas(request):
    """
    Vista que devuelve un JSON con estadísticas actualizadas de licencias, calculando las horas entre fechas.

    Args:
        request (HttpRequest): La solicitud HTTP recibida por la vista.

    Returns:
        JsonResponse: Un objeto JSON que contiene estadísticas de licencias agrupadas por motivo,
                     incluyendo horas mensuales, cantidad de licencias, y porcentaje acumulado.

    Funcionamiento:
        1. Obtiene todas las instancias de Licencia desde la base de datos.
        2. Calcula la diferencia en horas entre la fecha de inicio y la fecha de fin de cada licencia.
        3. Crea un DataFrame de pandas con los datos de las licencias, incluyendo las horas calculadas.
        4. Agrupa y suma las horas de licencias por motivo, y cuenta el número de licencias por motivo.
        5. Calcula el porcentaje y el porcentaje acumulado de licencias por motivo.
        6. Ordena y elimina duplicados del DataFrame para obtener las estadísticas finales.
        7. Retorna un JsonResponse con los datos estructurados de las estadísticas de licencias, incluyendo horas mensuales, cantidad de licencias y porcentaje acumulado.
    """
    licencias = Licencia.objects.all()

    datos_licencias = []

    for i in licencias:
        fecha_inicio = pd.to_datetime(i.fecha_inicio)
        fecha_fin = pd.to_datetime(i.fecha_fin)

        dias_diferencia = (fecha_fin - fecha_inicio).days + 1
        horas_diferencia = dias_diferencia * 8
        
        aux = {
            'creado': i.creado,
            'fecha_inicio' : i.fecha_inicio,
            'fecha_fin' : i.fecha_fin,
            'motivo_licencia': i.motivo_licencia.name_motivo_licencia,
            'horas_entre_fechas': horas_diferencia,
        }
        datos_licencias.append(aux)

    data = {'id': [], 'creado': [] ,'motivo_licencia': [], 'fecha_inicio': [], 'fecha_fin': [], 'horas_entre_fechas':[], 'horas_mensuales': []}

    for licencia in licencias:
        fecha_inicio = pd.to_datetime(licencia.fecha_inicio)
        fecha_fin = pd.to_datetime(licencia.fecha_fin)

        dias_diferencia = (fecha_fin - fecha_inicio).days + 1
        horas_entre_fechas = dias_diferencia * 8
        horas_mensuales = horas_entre_fechas / 24 * 8

        data['id'].append(licencia.id)
        data['creado'].append(licencia.creado)
        data['motivo_licencia'].append(licencia.motivo_licencia.name_motivo_licencia)
        data['fecha_inicio'].append(licencia.fecha_inicio)
        data['fecha_fin'].append(licencia.fecha_fin)
        data['horas_entre_fechas'].append(horas_entre_fechas)
        data['horas_mensuales'].append(horas_mensuales)  

    lic_df = pd.DataFrame(data)

    lic_df['horas_mensuales'] = lic_df.groupby('motivo_licencia')['horas_entre_fechas'].transform('sum')
    lic_df['count'] = lic_df.groupby('motivo_licencia')['motivo_licencia'].transform('count')

    lic_df = lic_df.sort_values(by=['horas_mensuales'], ascending=False, axis=0)
    lic_df = lic_df.drop_duplicates('motivo_licencia')

    total_porcentaje = lic_df['count'].sum()
    lic_df['Porcentaje'] = (lic_df['count'] / total_porcentaje) * 100

    sumaPorcentaje = 0
    lic_df['PorcentajeAcumulado'] = 0 

    for i, row in lic_df.iterrows():
        sumaPorcentaje += row['Porcentaje']
        lic_df.loc[i, 'PorcentajeAcumulado'] = sumaPorcentaje

    lic_df = lic_df.sort_values(by=['PorcentajeAcumulado'], ascending=True, axis=0)

    lic_dict = lic_df.to_dict(orient='records')

    return JsonResponse({'Lic': lic_dict, 'motivos_licencias': lic_df['motivo_licencia'].tolist(), 'cantidad_licencias': lic_df['count'].tolist(), 'horas_mensuales': lic_df['horas_mensuales'].tolist(), 'porcentaje_acumulado': lic_df['PorcentajeAcumulado'].tolist()})

#Vista para obtener los dias de creacion de las licencias
def get_days_licenses(request):
    """
    Obtiene una lista de fechas únicas de creación de licencias en formato 'dd-mm-YYYY'.

    Esta vista obtiene todas las fechas de creación de licencias, las convierte a 
    un formato específico y devuelve una lista de fechas únicas ordenadas.

    Args:
        request (HttpRequest): El objeto de solicitud HTTP.

    Returns:
        JsonResponse: Una respuesta JSON que contiene una lista de fechas únicas 
        en formato 'dd-mm-YYYY'. En caso de error, se devuelve un mensaje de error 
        con un estado HTTP 500.
    """
    try:
        licencias = Licencia.objects.all().values_list('creado', flat=True).distinct()
        fechas = sorted(list(set([licencia.strftime('%d-%m-%Y') for licencia in licencias])))
        return JsonResponse({'fechas': fechas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#Vista para filtrar el grafico por los dias
def actualizar_licencias_chart_dias(request, fecha):
    """
    Vista que devuelve un JSON con estadísticas de licencias filtradas por día específico o todas las fechas.

    Args:
        request (HttpRequest): La solicitud HTTP recibida por la vista.
        fecha (str): La fecha específica para filtrar las licencias en formato 'dd-mm-aaaa'. Use 'all' para incluir todas las fechas.

    Returns:
        JsonResponse: Un objeto JSON que contiene estadísticas de licencias agrupadas por motivo,
                      cantidad de licencias y porcentaje acumulado.

    Funcionamiento:
        1. Si la fecha no es 'all', convierte la cadena de fecha en un objeto datetime y extrae el día, mes y año.
        2. Obtiene todas las instancias de Licencia desde la base de datos.
        3. Crea un DataFrame de pandas con los datos de las licencias.
        4. Convierte las columnas de fechas a objetos datetime.
        5. Filtra el DataFrame según el día, mes y año especificados, o incluye todas las fechas si 'all' es especificado.
        6. Agrupa y cuenta las licencias por motivo, calcula el porcentaje de cada motivo respecto al total.
        7. Calcula el porcentaje acumulado de los motivos y ordena el DataFrame por este porcentaje.
        8. Retorna un JsonResponse con los datos estructurados de las estadísticas de licencias filtradas.
        9. Maneja cualquier excepción y devuelve un JsonResponse con el error.
    """
    try:
        if fecha != 'all':
            # Convierte la cadena de fecha en un objeto datetime
            fecha_obj = datetime.strptime(fecha, '%d-%m-%Y')
            dia = fecha_obj.day
            mes = fecha_obj.month
            año = fecha_obj.year
        
        licencias = Licencia.objects.all()

        # Crear el DataFrame
        data = {
            'id': [],
            'creado': [],
            'fecha_inicio': [],
            'fecha_fin': [],
            'motivo_licencia': []
        }

        for licencia in licencias:
            data['id'].append(licencia.id)
            data['creado'].append(licencia.creado)
            data['motivo_licencia'].append(licencia.motivo_licencia.name_motivo_licencia)
            data['fecha_inicio'].append(licencia.fecha_inicio)
            data['fecha_fin'].append(licencia.fecha_fin)

        licenses_df = pd.DataFrame(data)

        # Convertir las fechas a datetime
        licenses_df['creado'] = pd.to_datetime(licenses_df['creado'])
        licenses_df['fecha_inicio'] = pd.to_datetime(licenses_df['fecha_inicio'])
        licenses_df['fecha_fin'] = pd.to_datetime(licenses_df['fecha_fin'])

        # Filtrar los registros según el día, mes y año
        if fecha != 'all':
            filtered_df = licenses_df[(licenses_df['creado'].dt.day == dia) &
                                    (licenses_df['creado'].dt.month == mes) &
                                    (licenses_df['creado'].dt.year == año)]
            print(f"Filtered DataFrame for date '{fecha}':", filtered_df)
        else:
            filtered_df = licenses_df
            print("Filtered DataFrame for all days:", filtered_df)
        
        # Conteo de permisos creados por cada motivo
        filtered_df = filtered_df.groupby('motivo_licencia')['id'].count().reset_index().sort_values(by=['id'], ascending=False)

        total_percent = filtered_df['id'].sum()
        filtered_df['Porcentaje'] = (filtered_df['id'] / total_percent) * 100

        sumPercent = 0
        filtered_df['PorcentajeAcumulado'] = 0

        for i, row in filtered_df.iterrows():
            sumPercent += row['Porcentaje']
            filtered_df.loc[i, 'PorcentajeAcumulado'] = sumPercent

        filtered_df = filtered_df.sort_values(by=['PorcentajeAcumulado'], ascending=True, axis=0)

        print("Motivo Counts DataFrame:", filtered_df)

        licenses_dict = json.loads(filtered_df.to_json(orient='records'))

        return JsonResponse({
            'licencias': licenses_dict,
            'motivo_licencia': filtered_df['motivo_licencia'].to_list(),
            'cantidad_licencias': filtered_df['id'].to_list(),
            'porcentaje_acumulado': filtered_df['PorcentajeAcumulado'].to_list()
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

#Vista para filtrar el grafico por el area elegida
def actualizar_licencias_chart_area(request, area_id):
    """
    Vista que devuelve un JSON con estadísticas de licencias filtradas por área específica o todas las áreas.

    Args:
        request (HttpRequest): La solicitud HTTP recibida por la vista.
        area_id (str): El ID del área para filtrar las licencias. Use 'all' para incluir todas las áreas.

    Returns:
        JsonResponse: Un objeto JSON que contiene estadísticas de licencias agrupadas por motivo,
                      cantidad de licencias y porcentaje acumulado.

    Funcionamiento:
        1. Si area_id es 'all', obtiene todas las instancias de Licencia desde la base de datos.
           De lo contrario, filtra las licencias por el área especificada.
        2. Crea un DataFrame de pandas con los datos de las licencias.
        3. Filtra el DataFrame según el área especificada, o incluye todas las áreas si 'all' es especificado.
        4. Agrupa y cuenta las licencias por motivo, calcula el porcentaje de cada motivo respecto al total.
        5. Calcula el porcentaje acumulado de los motivos y ordena el DataFrame por este porcentaje.
        6. Retorna un JsonResponse con los datos estructurados de las estadísticas de licencias filtradas.
        7. Maneja cualquier excepción y devuelve un JsonResponse con el error.
    """
    try:
        if area_id == 'all':
            licencias = Licencia.objects.all()
            print(f"Licencias para todas las áreas: {[licencia.id for licencia in licencias]}")
        else:
            area = Area.objects.get(id=area_id)
            licencias = Licencia.objects.filter(area=area)
            print(f"Licencias para el área {area_id} ({area.nombre_area}): {[licencia.id for licencia in licencias]}")
    except Area.DoesNotExist:
        return JsonResponse({
            'error': f'Area with id {area_id} does not exist.'
        }, status=404)

    if not licencias.exists():
        print(f"No hay licencias para el área {area_id if area_id != 'all' else 'todas las áreas'}")
        return JsonResponse({
            'licencias': [],
            'area': [],
            'motivo_licencia': [],
            'cantidad_licencias': [],
            'porcentaje_acumulado': []
        })

    data = {
        'id': [], 'creado': [], 'fecha_inicio': [], 
        'fecha_fin': [], 'motivo_licencia': [], 'area': []
    }

    for licencia in licencias:
        data['id'].append(licencia.id)
        data['creado'].append(licencia.creado)
        data['motivo_licencia'].append(licencia.motivo_licencia.name_motivo_licencia)
        data['fecha_inicio'].append(licencia.fecha_inicio)
        data['fecha_fin'].append(licencia.fecha_fin)
        data['area'].append(licencia.area.id) 
    
    licenses_df = pd.DataFrame(data)

    if area_id != 'all':
        licenses_df['area'] = licenses_df['area'].astype(int)
        filtered_df = licenses_df[licenses_df['area'] == int(area_id)]
        print(f"Filtered DataFrame for area '{area_id}':", filtered_df)
    else:
        filtered_df = licenses_df
        print("Filtered DataFrame for all areas:", filtered_df)

    if filtered_df.empty:
        print(f"No data found for area '{area_id if area_id != 'all' else 'todas las áreas'}")
        return JsonResponse({
            'permisos': [],
            'area': [],
            'motivo_licencia': [],
            'cantidad_licencias': [],
            'porcentaje_acumulado': []
        })

    motivo_counts = filtered_df.groupby('motivo_licencia')['id'].count().reset_index().sort_values(by=['id'], ascending=False)
    
    total_percent = motivo_counts['id'].sum()
    motivo_counts['Porcentaje'] = (motivo_counts['id'] / total_percent) * 100
    motivo_counts['PorcentajeAcumulado'] = motivo_counts['Porcentaje'].cumsum()

    print("Motivo Counts DataFrame:", motivo_counts)

    licenses_dict = json.loads(motivo_counts.to_json(orient='records'))

    return JsonResponse({
        'licencias': licenses_dict,
        'area': [area_id] * len(motivo_counts),
        'motivo_licencia': motivo_counts['motivo_licencia'].to_list(),
        'cantidad_licencias': motivo_counts['id'].to_list(),
        'porcentaje_acumulado': motivo_counts['PorcentajeAcumulado'].to_list()
    })

# Vista para ver licencias
class GestionLicencias(LoginRequiredMixin, TemplateView):
    """
    Vista para gestionar licencias de empleados.

    Atributos:
        - template_name (str): Nombre del template utilizado para renderizar la página de gestión de licencias.

    Metodos:
        - get_context_data(**kwargs): Obtiene y devuelve el contexto para renderizar la página.
        - dispatch(request, *args, **kwargs): Controla la dirección de la solicitud según los parámetros.
        - post(request, *args, **kwargs): Procesa los datos enviados mediante el formulario en la página.
        - mostrar_archivo_licencia(request, id_licencia): Muestra el archivo adjunto correspondiente a una licencia.

    Notas:
        - Hereda de LoginRequiredMixin para asegurar que solo los usuarios autenticados pueden acceder a la página de gestión de licencias.
        - Utiliza el atributo 'template_name' para especificar el template a utilizar.

    Modo de uso:
        - Accede a esta vista para gestionar y visualizar las licencias de los empleados.
    """
    template_name = 'licencias_gestion.html'

    @staticmethod
    def actualizar_tabla_licencias_areas(request, area_id):
        """
        Vista que devuelve un JSON con los detalles de las licencias filtradas por área específica o todas las áreas.

        Args:
            request (HttpRequest): La solicitud HTTP recibida por la vista.
            area_id (str): El ID del área para filtrar las licencias. Use 'all' para incluir todas las áreas.

        Returns:
            JsonResponse: Un objeto JSON que contiene una lista de diccionarios con detalles de las licencias filtradas.

        Funcionamiento:
            1. Si area_id es 'all', obtiene todas las instancias de Licencia desde la base de datos ordenadas por fecha de creación. De lo contrario, filtra las licencias por el área especificada y las ordena por fecha de creación.
            2. Crea una lista de diccionarios con los datos de las licencias, incluyendo detalles como fechas, área, empresa, tipo de licencia, motivo, observaciones, estado y enlaces para editar.
            3. Retorna un JsonResponse con los datos estructurados de las licencias filtradas.
            4. Maneja las excepciones relacionadas con áreas no existentes y cualquier otro error, devolviendo un JsonResponse con el error.
        """
        try:
            if area_id == 'all':
                licencias = Licencia.objects.all().order_by('-creado')
                print(f"Licencias para todas las áreas: {[licencia.id for licencia in licencias]}")
            else:
                area = Area.objects.get(id=area_id)
                licencias = Licencia.objects.filter(area=area).order_by('-creado')
                print(f"Licencias para el área {area_id} ({area.nombre_area}): {[licencia.id for licencia in licencias]}")

            licencias_data = []

            for licencia in licencias:
                licencias_data.append({
                    'creado': licencia.creado.strftime('%Y-%m-%d'),
                    'nombre_completo': licencia.nombre_completo,
                    'cedula': licencia.cedula,
                    'area': licencia.area.nombre_area,
                    'empresa': licencia.empresa.name_empresa,
                    'fecha_inicio': licencia.fecha_inicio.strftime('%Y-%m-%d'),
                    'fecha_fin': licencia.fecha_fin.strftime('%Y-%m-%d'),
                    'tipo_licencia': licencia.tipo_licencia.name_tipo_licencia,
                    'motivo_licencia': licencia.motivo_licencia.name_motivo_licencia,
                    'observacion_licencia': licencia.observacion_licencia,
                    'nombre_coordinador': licencia.nombre_coordinador,
                    'datos_adjuntos_licencias': licencia.datos_adjuntos_licencias.url if licencia.datos_adjuntos_licencias else '',
                    'creada_por': licencia.creada_por.username,
                    'verificacion_licencia': licencia.verificacion_licencia,
                    'estado_licencia': licencia.estado_licencia,
                    'verificada_por': licencia.verificada_por.username if licencia.verificada_por else '',
                    'aprobacion_rrhh': licencia.aprobacion_rrhh,
                    'observacion_rrhh': licencia.observacion_rrhh,
                    'verificacion_rrhh': licencia.verificacion_rrhh.username if licencia.verificacion_rrhh else '',
                    'fecha_verificacion': licencia.fecha_verificacion.strftime('%Y-%m-%d') if licencia.fecha_verificacion else '',
                    'fecha_aprobacion': licencia.fecha_aprobacion.strftime('%Y-%m-%d') if licencia.fecha_aprobacion else '',
                    'edit_url': reverse('update_licencia', args=[licencia.id]) 
                })

            return JsonResponse({'licencias': licencias_data})

        except Area.DoesNotExist:
            return JsonResponse({'error': f'Area with id {area_id} does not exist.'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    def get_context_data(self, **kwargs):
        """
        Obtiene y devuelve el contexto para renderizar la página.

        Return:
            - dict: Un diccionario con datos para renderizar la página.

        Notas:
            - Verifica si el usuario es coordinador, Gestión Humana u otro, y filtra la lista de licencias en consecuencia.

        Modo de uso:
            - Este método se llama automáticamente al acceder a la página de gestión de licencias.
        """
        contexto = super().get_context_data(**kwargs)
        user = self.request.user

        es_superusuario = user.groups.filter(name='SuperUser').exists()

        if es_superusuario:
        # Si el usuario es superusuario, se le muestran todos los permisos
            contexto['lista_licencias'] = Licencia.objects.all()
        else:
            area = user.customuser.area if hasattr(user, 'customuser') and user.customuser else None

            # print(f"Nombre de usuario: {user.username}")
            # print(f"Área del area: {user.area}")
            # print(f"Grupos de permisos: {user.groups.all()}")

            es_coordinador = user.groups.filter(name='Coordinadores').exists()
            es_admin = user.groups.filter(name='Admin').exists()
            es_BP = user.groups.filter(name='BP').exists()

            if es_admin or es_BP:
                contexto['lista_licencias'] = Licencia.objects.all()
            elif area:
                # Si hay un área, filtra los permisos por esa área
                contexto['lista_licencias'] = Licencia.objects.filter(area=area)
            else:
                area = user.area
                contexto['lista_licencias'] = Licencia.objects.filter(area=area)
            
        grupo_coordinadores = Group.objects.get(name='Coordinadores')
        es_coordinador = grupo_coordinadores in user.groups.all()

        grupo_admin = Group.objects.get(name='Admin')
        es_admin = grupo_admin in user.groups.all()

        grupo_BP = Group.objects.get(name='BP')
        es_BP = grupo_BP in user.groups.all()

        contexto['es_coordinador'] = es_coordinador
        contexto['es_admin'] = es_admin
        contexto['es_superusuario'] = es_superusuario
        contexto['es_BP'] = es_BP
        return contexto

    def dispatch(self, request, *args, **kwargs):
        """
        Controla la dirección de la solicitud según los parámetros.

        Args:
            - request (HttpRequest): Objeto que contiene la información de la solicitud HTTP.
            - args: Argumentos adicionales.
            - kwargs: Argumentos clave adicionales.

        Return:
            - HttpResponse: Respuesta HTTP después de procesar la solicitud.

        Notas:
            - Si se proporciona 'id_licencia' en los parámetros, llama al método 'mostrar_archivo_licencia'.
            - De lo contrario, llama al método 'dispatch' de la clase base.

        Modo de uso:
            - Este método se llama automáticamente al procesar una solicitud.
        """
        if 'id_licencia' in kwargs:
            return self.mostrar_archivo_licencia(request, kwargs['id_licencia'])
        else:
            return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        Procesa los datos enviados mediante el formulario en la página.

        Args:
            - request (HttpRequest): Objeto que contiene la información de la solicitud HTTP.
            - args: Argumentos adicionales.
            - kwargs: Argumentos clave adicionales.

        Return:
            - HttpResponse: Respuesta HTTP después de procesar los datos del formulario.

        Notas:
            - Procesa el formulario de licencias y guarda la información si es válido.

        Modo de uso:
            - Este método se llama automáticamente al enviar datos mediante el formulario.
        """
        form = LicenciaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('inicio')
        else:
            return render(request, self.template_name, {'form':form})

    def mostrar_archivo_licencia(self, request, id_licencia):
        """
        Muestra el archivo adjunto correspondiente a una licencia.

        Args:
            - request (HttpRequest): Objeto que contiene la información de la solicitud HTTP.
            - id_licencia (int): ID de la licencia para la cual se muestra el archivo adjunto.

        Return:
            - HttpResponse: Respuesta HTTP que muestra el archivo adjunto.

        Notas:
            - Verifica el tipo de archivo y muestra el contenido si es compatible.

        Modo de uso:
            - Este método se llama automáticamente al acceder a la visualización de un archivo adjunto.
        """

        licencia = Licencia.objects.get(pk=id_licencia)
        if licencia.datos_adjuntos_licencias:
            archivo_path = licencia.datos_adjuntos_licencias.path

            if not os.path.exists(archivo_path):
                raise Http404("El archivo no existe.")

            extension = os.path.splitext(archivo_path)[1].lower()
            allowed_extensions = ['.pdf', '.docx', '.png', '.jpg', '.jpeg', '.gif']

            if extension in allowed_extensions:
                mime_type, _ = mimetypes.guess_type(archivo_path)
                if mime_type is None:
                    mime_type = 'application/octet-stream'
                with open(archivo_path, 'rb') as file:
                    response = HttpResponse(file.read(), content_type=mime_type)
                    response['Content-Disposition'] = f'inline; filename={os.path.basename(archivo_path)}'
                    return response
            else:
                return HttpResponse("El tipo de archivo no es compatible.")
        else:
            return HttpResponse("No hay archivo adjunto.")
        
# Vista para la edicion de Licencias
class ActualizarLicencia(UpdateView, LoginRequiredMixin):
    """
    Vista para actualizar una licencia existente.

    Atributos:
        - model (Licencia): Modelo de datos asociado a la vista.
        - form_class (LicenciaForm): Clase de formulario utilizada para la actualización.
        - template_name (str): Nombre del template utilizado para renderizar la página de actualización.
        - success_url (str): URL a la que se redirige después de una actualización exitosa.

    Metodos:
        - get_context_data(**kwargs): Obtiene y devuelve el contexto para renderizar la página.
        - get_form_kwargs(): Obtiene y devuelve los argumentos para inicializar el formulario.
        - form_valid(form): Procesa el formulario después de una validación exitosa.

    Notas:
        - Hereda de UpdateView y LoginRequiredMixin.
        - Utiliza el modelo Licencia y el formulario LicenciaForm.

    Modo de uso:
        - Accede a esta vista para actualizar una licencia existente.
    """
    model = Licencia
    form_class = LicenciaForm
    template_name = 'update_temp/update_licencias.html'
    success_url = reverse_lazy('ver licencias')

    def get_context_data(self, **kwargs):
        """
        Obtiene y devuelve el contexto para renderizar la página.

        Return:
            - dict: Un diccionario con datos para renderizar la página.

        Notas:
            - Filtra la lista de licencias.
            - Verifica si el usuario es coordinador y agrega la información al contexto.

        Modo de uso:
            - Este método se llama automáticamente al acceder a la página de actualización.
        """
        contexto = super().get_context_data(**kwargs)
        contexto['lista_licencias'] = Licencia.objects.all() 
        
        #Es Admin o no
        grupo_admin = Group.objects.get(name='Admin')
        es_admin = grupo_admin in self.request.user.groups.all()
        contexto['es_admin'] = es_admin

        #Es superusuario o no
        grupo_superusuario = Group.objects.get(name='SuperUser')
        es_superusuario = grupo_superusuario in self.request.user.groups.all()
        contexto['es_superusuario'] = es_superusuario

        contexto['campos_editables'] = ['verificacion_licencia', 'estado_licencia']

        #Es BP
        grupo_BP = Group.objects.get(name='BP')
        es_BP = grupo_BP in self.request.user.groups.all()
        contexto['es_BP'] = es_BP

        contexto['campos_BP'] = ['aprobacion_rrhh', 'observacion_rrhh']

        return contexto
    
    def get_form_kwargs(self):
        """
        Obtiene y devuelve los argumentos para inicializar el formulario.

        Return:
            - dict: Un diccionario con argumentos para inicializar el formulario.

        Notas:
            - Agrega el usuario actual y la bandera de edición al formulario.

        Modo de uso:
            Este método se llama automáticamente al inicializar el formulario.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['editing'] = True
        return kwargs
    
    def form_valid(self, form):
        """
        Procesa el formulario después de una validación exitosa.

        Args:
            - form (LicenciaForm): Formulario de licencia con datos validados.

        Return:
            - HttpResponse: Respuesta HTTP después de procesar el formulario.

        Notas:
            - Actualiza campos específicos según el rol del usuario.
            - Envía correos electrónicos cuando se rechaza la licencia.

        Modo de uso:
            Este método se llama automáticamente después de una validación exitosa del formulario.
        """
        user = self.request.user # Obtiene el usuario actual

        # Si el usuario es superusuario, actualiza 'verificada_por' y 'fecha_verificacion'
        if user.groups.filter(name='SuperUser').exists() or user.is_superuser:
            form.instance.verificada_por = user
            form.instance.fecha_verificacion = timezone.now()

        if user.groups.filter(name='Admin').exists():
            form.instance.fecha_verificacion = timezone.now()
            form.instance.verificada_por = CustomUser.objects.get(username=user.username) 
            print('Modifico los campos de Admin')

        if user.groups.filter(name='BP').exists():
            form.instance.fecha_aprobacion = timezone.now()
            form.instance.verificacion_rrhh = CustomUser.objects.get(username=user.username) 
            print('Modifico los campos de los Bussiness Partner')

            # Enviar correo cuando Gestion Humana rechaza la licencia
            if form.instance.aprobacion_rrhh == 'Rechazado':
                html_message = render_to_string('notificaciones/notify_licencia_rechazada_RH.html', {
                    'usuario': form.instance.creada_por,
                    'nombre': form.instance.nombre_completo,
                    'cedula': form.instance.cedula,
                    'empresa': form.instance.empresa,
                    'area': form.instance.area,
                    'fecha_inicio': form.instance.fecha_inicio,
                    'fecha_fin': form.instance.fecha_fin,
                    'tipo_licencia': form.instance.tipo_licencia,
                    'motivo_licencia': form.instance.motivo_licencia,
                    'nombre_coordinador': form.instance.nombre_coordinador,
                    'aprobacion_rrhh': form.instance.aprobacion_rrhh,
                    'observacion_rrhh': form.instance.observacion_rrhh,
                    'autor': form.instance.verificada_por
                })

                # Crear una versión de texto plano del mensaje
                plain_message = strip_tags(html_message)

                send_mail(
                    subject='NOTIFICACION DE LICENCIA: RECHAZADA POR GESTIÓN HUMANA',
                    message=plain_message,
                    from_email=None,
                    recipient_list=['jimmy.bustamante@prebel.com.co'],
                    html_message=html_message,
                    fail_silently=False,
                )

        # Enviar correo cuando se rechaza la licencia
        if form.instance.verificacion_licencia == 'Rechazado':
            html_message = render_to_string('notificaciones/notify_licencia_rechazada.html', {
                'usuario': form.instance.creada_por,
                'nombre': form.instance.nombre_completo,
                'cedula': form.instance.cedula,
                'empresa': form.instance.empresa,
                'area': form.instance.area,
                'fecha_inicio': form.instance.fecha_inicio,
                'fecha_fin': form.instance.fecha_fin,
                'tipo_licencia': form.instance.tipo_licencia,
                'motivo_licencia': form.instance.motivo_licencia,
                'nombre_coordinador': form.instance.nombre_coordinador,
                'verificacion_licencia': form.instance.verificacion_licencia,
                'estado_licencia': form.instance.estado_licencia,
                'autor': form.instance.verificada_por
            })

            # Crear una versión de texto plano del mensaje
            plain_message = strip_tags(html_message)

            send_mail(
                subject='NOTIFICACION DE LICENCIA RECHAZADA',
                message=plain_message,
                from_email=None,
                # recipient_list=['sara.pena@prebel.com.co', 'diego.gallego@prebel.com.co'],
                recipient_list=['jimmy.bustamante@prebel.com.co'],
                html_message=html_message,
                fail_silently=False,
            )
        print("Processing form_valid")
        response = super().form_valid(form)
        print("Form successfully processed")
        return response