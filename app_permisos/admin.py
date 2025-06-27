from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import(
Area, MotivoPermiso, Turno,
Permiso, Empresa, 
MotivoLicencia,
Licencia, TipoLicencia, 
Permission, CustomUser)

#Import-Export
from import_export import resources
from import_export.admin import ImportExportModelAdmin

class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'es_coordinador', 'area', 'is_active', 'is_staff', 'is_superuser']
    fieldsets = (
        (None, {'fields': ('username', 'email', 'es_coordinador', 'area', 'password','is_active', 'is_staff', 'is_superuser' )}),
        ('Permisos', {'fields': ('groups',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

admin.site.register(ContentType)
admin.site.register(Permission)

#Permisos
admin.site.register(Permiso)

# admin.site.register(TipoLicencia)

#Licencias
admin.site.register(Licencia)

# General
class AreaResources(resources.ModelResource):
      fields = {
           "id",    
           "nombre_area",
        }
      class Meta:
            model = Area
class AreaAdmin(ImportExportModelAdmin):
      resource_class = AreaResources
admin.site.register(Area,AreaAdmin)

#Permisos
class MotivoPermisoResources(resources.ModelResource):
      fields = {
           "id",
           "name_motivo" 
        }
      class Meta:
            model = MotivoPermiso
class MotivoPermisoAdmin(ImportExportModelAdmin):
      resource_class = MotivoPermisoResources
admin.site.register(MotivoPermiso,MotivoPermisoAdmin)

class TurnoResources(resources.ModelResource):
      fields = {
           "id",
           "name_turno" 
        }
      class Meta:
            model = Turno
class TurnoAdmin(ImportExportModelAdmin):
      resource_class = TurnoResources
admin.site.register(Turno,TurnoAdmin)

#Licencias
class EmpresaResources(resources.ModelResource):
      fields = {
           "id",
           "name_empresa" 
        }
      class Meta:
            model = Empresa
class EmpresaAdmin(ImportExportModelAdmin):
      resource_class = EmpresaResources
admin.site.register(Empresa,EmpresaAdmin)

class MotivoLicenciaResources(resources.ModelResource):
      fields = {
           "id",
           "name_motivo_licencia" 
        }
      class Meta:
            model = MotivoLicencia
class MotivoLicenciaAdmin(ImportExportModelAdmin):
      resource_class = MotivoLicenciaResources
admin.site.register(MotivoLicencia,MotivoLicenciaAdmin)

class TipoLicenciaResources(resources.ModelResource):
      fields = {
           "id",
           "name_tipo_licencia" 
        }
      class Meta:
            model = TipoLicencia
class TipoLicenciaAdmin(ImportExportModelAdmin):
      resource_class = TipoLicenciaResources
admin.site.register(TipoLicencia,TipoLicenciaAdmin)