from django.urls import path
from django.contrib import admin
from app_permisos.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    #Main
    path('login/', Login.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('', Inicio.as_view(), name="inicio"),
    path('get_areas/', get_areas, name='get_areas'),
    path('get_days/', get_days, name='get_days'),
    path('get_days_licenses/', get_days_licenses, name='get_days_licenses'),

    #Consultas SQL
    path('obtener_nombre/', ObtenerNombre.as_view(), name='obtener_nombre'),
    
    #Permisos
    path('ver_permisos', GestionPermisos.as_view(), name='ver permisos'),
    path('ver_permisos/mostrar_archivo/<int:id_permiso>/', GestionPermisos.as_view(), name='mostrar_archivo'),
    path('update_permiso/<int:pk>/', ActualizarPermiso.as_view(), name='update_permiso'),
    path('permisos_chart/', PermisosChartView.as_view(), name='permisos_chart'),
    path('chart_cant_permisos/', chart_cant_permisos, name='chart_cant_permisos'),
    path('timeline_permiso_chart/', timeline_permiso_chart, name='timeline_permiso_chart'),
    path('actualizar_permisos_chart/<str:fecha>/', actualizar_permisos_chart, name='actualizar_permisos_chart'),
    path('actualizar_permisos_chart_area/<str:area_id>/', actualizar_permisos_chart_area, name='actualizar_permisos_chart_area'),
    path('actualizar_permisos_chart_dias/<str:fecha>/', actualizar_permisos_chart_dias, name='actualizar_permisos_chart_dias'),
    path('actualizar_permisos_chart_horas/', actualizar_permisos_chart_horas, name='actualizar_permisos_chart_horas'),
    path('actualizar_tabla_areas/<str:area_id>/', GestionPermisos.actualizar_tabla_areas, name='actualizar_tabla_areas'),

    #Licencias
    path('resumen', ResumenLicencias.as_view(), name='crear licencia'),
    path('ver_licencias',GestionLicencias.as_view(), name='ver licencias'),
    path('ver_licencias/mostrar_archivo_licencia/<int:id_licencia>/', GestionLicencias.as_view(), name='mostrar_archivo_licencia'),
    path('update_licencia/<int:pk>/', ActualizarLicencia.as_view(), name='update_licencia'),
    path('licencias_chart/', LicenciasChartView.as_view(), name='licencias_chart'),
    path('chart_cant_licencias/', chart_cant_licencias, name='chart_cant_licencias'),
    path('timeline_licencia_chart/', timeline_licencia_chart, name='timeline_licencia_chart'),
    path('actualizar_licencias_chart/<str:fecha>/',actualizar_licencias_chart, name='actualizar_licencias_chart'),
    path('actualizar_licencias_chart_horas/', actualizar_licencias_chart_horas, name='actualizar_licencias_chart_horas'),
    path('actualizar_licencias_chart_area/<str:area_id>/', actualizar_licencias_chart_area, name='actualizar_licencias_chart_area'),
    path('actualizar_licencias_chart_dias/<str:fecha>/', actualizar_licencias_chart_dias, name='actualizar_licencias_chart_dias'),
    path('actualizar_tabla_licencias_areas/<str:area_id>/', GestionLicencias.actualizar_tabla_licencias_areas, name='actualizar_tabla_licencias_areas'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

"""
Módulo de URL para la aplicación 'app_permisos'.

Este módulo define las rutas URL para las vistas de la aplicación 'app_permisos'.

Rutas:
    - 'logout/': Vista para cerrar sesión.
    - 'login/': Vista para iniciar sesión.
    - '' (inicio): Página de inicio.
    - 'ver_permisos': Vista para ver los permisos creados.
    - 'ver_permisos/mostrar_archivo/<int:id_permiso>/': Vista para mostrar archivos subidos a permisos.
    - 'ver_licencias': Vista para ver las licencias creadas.
    - 'ver_licencias/mostrar_archivo_licencia/<int:id_licencia>/': Vista para mostrar archivos subidos a licencias.
    - 'update_permiso/<int:pk>/': Vista para actualizar permisos.
    - 'update_licencia/<int:pk>/': Vista para actualizar licencias.

Uso:
    Este módulo se importa en el archivo 'urls.py' del proyecto principal.
"""