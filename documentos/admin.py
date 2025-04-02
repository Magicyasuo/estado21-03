from django.contrib import admin
from .models import (
    SerieDocumental, SubserieDocumental, RegistroDeArchivo, PermisoUsuarioSerie, 
    EntidadProductora, UnidadAdministrativa, OficinaProductora, Objeto, FUID, FichaPaciente
)

# 1) Importaciones adicionales
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import PerfilUsuario
from .models import Documento

# Registro de modelos de correspondencia
from .models import (
    TipoDocumentoCorrespondencia, Contacto, Correspondencia,
    DistribucionInterna, AdjuntoCorrespondencia
)

# 2) Definir un inline para mostrar/editar PerfilUsuario dentro del formulario de User
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = "Perfil (Oficina)"
    fk_name = "user"

# 3) Crear un CustomUserAdmin que inyecte ese Inline
class CustomUserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)

    # Opcional: Si deseas reorganizar fieldsets o personalizar algo más, puedes hacerlo aquí.
    # Por ejemplo, para asegurarte de que no haya choques con otros inlines, etc.

# 4) Anular el registro default de User y registrar el nuevo
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)



@admin.register(SerieDocumental)
class SerieDocumentalAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('codigo', 'nombre')


@admin.register(SubserieDocumental)
class SubserieDocumentalAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'serie')
    list_filter = ('serie',)
    search_fields = ('codigo', 'nombre')


@admin.register(RegistroDeArchivo)
class RegistroDeArchivoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_orden', 'unidad_documental', 'fecha_archivo', 
        'creado_por', 'ubicacion', 'soporte_fisico', 'soporte_electronico'
    )
    list_filter = ('soporte_fisico', 'soporte_electronico', 'fecha_archivo', 'creado_por')
    search_fields = ('numero_orden', 'unidad_documental', 'ubicacion', 'notas')
    readonly_fields = ('fecha_creacion',)
    fieldsets = (
        ('Información General', {
            'fields': ('numero_orden', 'codigo_serie', 'codigo_subserie', 'unidad_documental','fecha_archivo', 
                        'fecha_inicial', 'fecha_final', 'notas', 'Estado_archivo')
        }),
        ('Soporte', {
            'fields': ('soporte_fisico', 'soporte_electronico', 'caja', 'carpeta', 
                       'tomo_legajo_libro', 'numero_folios', 'cantidad', 'ubicacion')
        }),
        ('Información Electrónica', {
            'fields': ('cantidad_documentos_electronicos', 'tamano_documentos_electronicos')
        }),
        ('Metadatos', {
            'fields': ('creado_por', 'fecha_creacion')
        }),
    )


@admin.register(PermisoUsuarioSerie)
class PermisoUsuarioSerieAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'serie', 'permiso_crear', 'permiso_editar', 'permiso_consultar', 'permiso_eliminar')
    list_filter = ('serie', 'usuario')


@admin.register(EntidadProductora)
class EntidadProductoraAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(UnidadAdministrativa)
class UnidadAdministrativaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'entidad_productora')
    list_filter = ('entidad_productora',)
    search_fields = ('nombre', 'entidad_productora__nombre')


@admin.register(OficinaProductora)
class OficinaProductoraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'unidad_administrativa')
    list_filter = ('unidad_administrativa',)
    search_fields = ('nombre', 'unidad_administrativa__nombre')


@admin.register(Objeto)
class ObjetoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


@admin.register(FUID)
class FUIDAdmin(admin.ModelAdmin):
    list_display = ('id', 'entidad_productora', 'unidad_administrativa', 'oficina_productora', 'objeto', 'creado_por', 'fecha_creacion')
    list_filter = ('entidad_productora', 'unidad_administrativa', 'oficina_productora', 'objeto', 'creado_por')
    search_fields = ('id', 'entidad_productora__nombre', 'unidad_administrativa__nombre', 'oficina_productora__nombre', 'objeto__nombre')
    filter_horizontal = ('registros',)  # Para administrar el ManyToManyField

@admin.register(FichaPaciente)
class FichaPacienteAdmin(admin.ModelAdmin):
    list_display = ('consecutivo', 'primer_nombre', 'primer_apellido', 'num_identificacion', 'Numero_historia_clinica', 'activo')
    list_filter = ('activo', 'sexo', 'tipo_identificacion')
    search_fields = ('primer_nombre', 'primer_apellido', 'num_identificacion', 'Numero_historia_clinica')




from django.contrib import admin
from django.utils.html import format_html

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        'registro', 
        'archivo', 
        'archivo_size',  
        'uploaded_at', 
        'creado_por',  
        'oficina',
    )
    search_fields = ('registro__numero_orden', 'registro__creado_por__username', 'registro__creado_por__first_name', 'registro__creado_por__last_name')
    list_filter = ('uploaded_at', 'registro__fuids__oficina_productora')

    def creado_por(self, obj):
        """ Devuelve el usuario que subió el archivo """
        return obj.registro.creado_por if hasattr(obj.registro, 'creado_por') else "Desconocido"
    creado_por.short_description = "Subido por"

    def oficina(self, obj):
        """ Devuelve la oficina a la que pertenece el registro """
        if hasattr(obj.registro, 'fuids') and obj.registro.fuids.exists():
            return obj.registro.fuids.first().oficina_productora.nombre
        return "Sin Oficina"
    oficina.short_description = "Oficina"

    def archivo_size(self, obj):
        """ Devuelve el tamaño del archivo en KB o MB """
        if obj.archivo and obj.archivo.size:
            size_kb = obj.archivo.size / 1024  # Convertir a KB
            if size_kb > 1024:
                return f"{size_kb / 1024:.2f} MB"
            return f"{size_kb:.2f} KB"
        return "Desconocido"
    archivo_size.short_description = "Tamaño"


# @admin.register(PerfilUsuario)
# class PerfilUsuarioAdmin(admin.ModelAdmin):
#     list_display = ('user', 'oficina')
#     search_fields = ('user__username', 'oficina__nombre')

@admin.register(TipoDocumentoCorrespondencia)
class TipoDocumentoCorrespondenciaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'activo')
    search_fields = ('codigo', 'nombre')
    list_filter = ('activo',)


@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'tipo_identificacion', 'identificacion', 'correo', 'activo')
    list_filter = ('tipo', 'tipo_identificacion', 'activo')
    search_fields = ('nombre', 'identificacion', 'correo')
    date_hierarchy = 'fecha_creacion'
    fieldsets = (
        ('Información básica', {
            'fields': ('tipo', 'nombre', 'tipo_identificacion', 'identificacion', 'activo')
        }),
        ('Información de contacto', {
            'fields': ('direccion', 'telefono', 'correo', 'ciudad')
        }),
        ('Información adicional', {
            'fields': ('observaciones',),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('creado_por', 'fecha_creacion')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo registro
            obj.creado_por = request.user
        obj.save()


class AdjuntoCorrespondenciaInline(admin.TabularInline):
    model = AdjuntoCorrespondencia
    extra = 1
    fields = ('archivo', 'descripcion', 'subido_por', 'fecha_carga')
    readonly_fields = ('subido_por', 'fecha_carga')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo registro
            obj.subido_por = request.user
        obj.save()


class DistribucionInternaInline(admin.TabularInline):
    model = DistribucionInterna
    extra = 1
    fields = ('oficina_origen', 'oficina_destino', 'instrucciones', 'estado', 
              'recibido_por', 'fecha_recepcion')
    readonly_fields = ('recibido_por', 'fecha_recepcion')


@admin.register(Correspondencia)
class CorrespondenciaAdmin(admin.ModelAdmin):
    list_display = ('radicado', 'asunto', 'tipo_correspondencia', 'fecha_radicacion', 'estado')
    list_filter = ('tipo_correspondencia', 'estado', 'prioridad', 'fecha_radicacion')
    search_fields = ('radicado', 'asunto', 'descripcion')
    date_hierarchy = 'fecha_radicacion'
    readonly_fields = ('radicado', 'creado_por', 'fecha_creacion', 'modificado_por', 'fecha_modificacion')
    
    fieldsets = (
        ('Información básica', {
            'fields': ('radicado', 'tipo_correspondencia', 'tipo_documento', 'asunto', 'descripcion')
        }),
        ('Documento', {
            'fields': ('fecha_documento', 'numero_documento')
        }),
        ('Clasificación documental', {
            'fields': ('serie_documental', 'subserie_documental')
        }),
        ('Remitente/Destinatario', {
            'fields': ('remitente_externo', 'destinatario_externo', 'oficina_remitente', 'oficina_destinatario')
        }),
        ('Estado y seguimiento', {
            'fields': ('estado', 'prioridad', 'requiere_respuesta', 'fecha_vencimiento', 'anulado', 'motivo_anulacion')
        }),
        ('Información de creación', {
            'fields': ('creado_por', 'fecha_creacion', 'modificado_por', 'fecha_modificacion'),
            'classes': ('collapse',),
        }),
    )
    
    inlines = [AdjuntoCorrespondenciaInline, DistribucionInternaInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo registro
            obj.creado_por = request.user
        else:
            obj.modificado_por = request.user
        obj.save()
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, AdjuntoCorrespondencia) and not instance.pk:
                instance.subido_por = request.user
            if isinstance(instance, DistribucionInterna) and not instance.pk:
                instance.creado_por = request.user
            instance.save()
        formset.save_m2m()


@admin.register(DistribucionInterna)
class DistribucionInternaAdmin(admin.ModelAdmin):
    list_display = ('correspondencia', 'oficina_origen', 'oficina_destino', 
                   'fecha_distribucion', 'estado')
    list_filter = ('estado', 'fecha_distribucion')
    search_fields = ('correspondencia__radicado', 'correspondencia__asunto', 
                     'oficina_origen__nombre', 'oficina_destino__nombre')
    date_hierarchy = 'fecha_distribucion'
    readonly_fields = ('creado_por', 'fecha_distribucion')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo registro
            obj.creado_por = request.user
        obj.save()