import os
import logging

from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.conf import settings

logger = logging.getLogger(__name__)

# ============================
# FUNCIONES DE UTILIDAD
# ============================

def validate_file_size(value):
    max_size = 2 * 1024 * 1024  # 2 MB
    if value.size > max_size:
        raise ValidationError(f"El archivo no puede superar los 2 MB. Tamaño actual: {value.size / (1024 * 1024):.2f} MB")

def normalize_filename(filename):
    """Normaliza el nombre del archivo eliminando caracteres especiales y espacios"""
    name, extension = os.path.splitext(filename)
    return f"{slugify(name)}{extension.lower()}"

def documento_upload_path(instance, filename):
    filename = normalize_filename(filename)

    try:
        if instance.registro.creado_por.perfil.oficina:
            oficina = slugify(instance.registro.creado_por.perfil.oficina.nombre)
        else:
            oficina = "sin_oficina"
    except (AttributeError, Exception) as e:
        logger.warning(f"Error al obtener oficina: {str(e)}")
        oficina = "sin_oficina"

    try:
        serie = slugify(instance.registro.codigo_serie.codigo)
        subserie = slugify(instance.registro.codigo_subserie.codigo) if instance.registro.codigo_subserie else "00"
        registro_id = str(instance.registro.id)
    except (AttributeError, Exception) as e:
        logger.warning(f"Error al obtener datos del registro: {str(e)}")
        serie = "serie_default"
        subserie = "subserie_default"
        registro_id = "0"

    ruta = os.path.join("documentos", oficina, f"serie_{serie}", f"subserie_{subserie}", f"registro_{registro_id}")
    ruta_completa = os.path.join(settings.MEDIA_ROOT, ruta)
    return os.path.join(ruta, filename)

# ============================
# MODELOS
# ============================

class SerieDocumental(models.Model):
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

class SubserieDocumental(models.Model):
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=255)
    serie = models.ForeignKey(SerieDocumental, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.codigo} - {self.nombre} (Serie: {self.serie.nombre})"

class EntidadProductora(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nombre

class UnidadAdministrativa(models.Model):
    nombre = models.CharField(max_length=255)
    entidad_productora = models.ForeignKey(EntidadProductora, on_delete=models.CASCADE, related_name='unidades')

    def __str__(self):
        return f"{self.nombre} ({self.entidad_productora.nombre})"

class OficinaProductora(models.Model):
    nombre = models.CharField(max_length=255)
    unidad_administrativa = models.ForeignKey(UnidadAdministrativa, on_delete=models.CASCADE, related_name='oficinas')

    def __str__(self):
        return f"{self.nombre} ({self.unidad_administrativa.nombre})"

class Objeto(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nombre

class FUID(models.Model):
    entidad_productora = models.ForeignKey(EntidadProductora, on_delete=models.SET_NULL, null=True)
    unidad_administrativa = models.ForeignKey(UnidadAdministrativa, on_delete=models.SET_NULL, null=True)
    oficina_productora = models.ForeignKey(OficinaProductora, on_delete=models.SET_NULL, null=True)
    objeto = models.ForeignKey(Objeto, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='fuids')
    registros = models.ManyToManyField('RegistroDeArchivo', related_name='fuids', blank=True)

    elaborado_por_nombre = models.CharField(max_length=255, null=True, blank=True)
    elaborado_por_cargo = models.CharField(max_length=255, null=True, blank=True)
    elaborado_por_lugar = models.CharField(max_length=255, null=True, blank=True)
    elaborado_por_fecha = models.DateField(null=True, blank=True)

    entregado_por_nombre = models.CharField(max_length=255, null=True, blank=True)
    entregado_por_cargo = models.CharField(max_length=255, null=True, blank=True)
    entregado_por_lugar = models.CharField(max_length=255, null=True, blank=True)
    entregado_por_fecha = models.DateField(null=True, blank=True)

    recibido_por_nombre = models.CharField(max_length=255, null=True, blank=True)
    recibido_por_cargo = models.CharField(max_length=255, null=True, blank=True)
    recibido_por_lugar = models.CharField(max_length=255, null=True, blank=True)
    recibido_por_fecha = models.DateField(null=True, blank=True)

    class Meta:
        permissions = [
            ("view_own_fuid", "Puede ver sus propios FUIDs"),
            ("edit_own_fuid", "Puede editar sus propios FUIDs"),
            ("delete_own_fuid", "Puede eliminar sus propios FUIDs"),
        ]

    def __str__(self):
        return f"FUID #{self.id} - {self.entidad_productora.nombre if self.entidad_productora else 'Sin Entidad'}"

class RegistroDeArchivo(models.Model):  
    Estado_archivo = models.BooleanField(default=True)
    numero_orden = models.IntegerField(default=0)
    codigo = models.CharField(max_length=50, blank=True, null=True)
    codigo_serie = models.ForeignKey(SerieDocumental, on_delete=models.CASCADE, related_name="registros")
    codigo_subserie = models.ForeignKey(SubserieDocumental, on_delete=models.CASCADE, blank=True, null=True, related_name="registros")
    unidad_documental = models.CharField(max_length=255)
    fecha_archivo = models.DateField(blank=True, null=True)
    fecha_inicial = models.DateField(blank=True, null=True)
    fecha_final = models.DateField(blank=True, null=True)
    soporte_fisico = models.BooleanField(default=False)
    soporte_electronico = models.BooleanField(default=False)
    caja = models.IntegerField(blank=True, null=True)
    carpeta = models.IntegerField(blank=True, null=True)
    tomo_legajo_libro = models.CharField(max_length=50, blank=True, null=True)
    numero_folios = models.IntegerField(blank=True, null=True)
    tipo = models.CharField(max_length=100, blank=True, null=True)
    cantidad = models.IntegerField(blank=True, null=True)
    ubicacion = models.CharField(max_length=255, null=True)
    cantidad_documentos_electronicos = models.IntegerField(null=True, blank=True)
    tamano_documentos_electronicos = models.CharField(max_length=50, null=True, blank=True)
    identificador_documento = models.IntegerField(null=True, blank=True)
    notas = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [
            ("view_own_registro", "Puede ver sus propios registros"),
            ("edit_own_registro", "Puede editar sus propios registros"),
            ("delete_own_registro", "Puede eliminar sus propios registros"),
        ]

class Documento(models.Model):
    registro = models.ForeignKey(RegistroDeArchivo, on_delete=models.CASCADE, related_name='documentos')
    archivo = models.FileField(upload_to=documento_upload_path, validators=[validate_file_size])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk and self.registro.documentos.count() >= 3:
            raise ValidationError("Solo se permiten 3 archivos por registro.")

        if self.archivo:
            ruta_destino = os.path.dirname(os.path.join(settings.MEDIA_ROOT, self.archivo.field.upload_to(self, self.archivo.name)))
            try:
                os.makedirs(ruta_destino, exist_ok=True, mode=0o755)
                logger.info(f"Directorio creado/verificado: {ruta_destino}")
            except PermissionError as e:
                logger.error(f"Error de permisos al crear directorio {ruta_destino}: {str(e)}")
                raise ValidationError("No se pueden crear los directorios necesarios debido a permisos insuficientes.")
            except Exception as e:
                logger.error(f"Error al crear directorio {ruta_destino}: {str(e)}")
                raise ValidationError(f"Error al crear directorio para almacenar el archivo: {str(e)}")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Documento para registro {self.registro.numero_orden}"

class PermisoUsuarioSerie(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    serie = models.ForeignKey(SerieDocumental, on_delete=models.CASCADE)
    permiso_crear = models.BooleanField(default=False)
    permiso_editar = models.BooleanField(default=False)
    permiso_consultar = models.BooleanField(default=True)
    permiso_eliminar = models.BooleanField(default=False)

    def __str__(self):
        return f"Permisos de {self.usuario.username} sobre {self.serie.nombre}"

class FichaPaciente(models.Model):
    consecutivo = models.AutoField(primary_key=True)
    primer_nombre = models.CharField(max_length=50)
    segundo_nombre = models.CharField(max_length=50, blank=True, null=True)
    primer_apellido = models.CharField(max_length=50)
    segundo_apellido = models.CharField(max_length=50, blank=True, null=True)
    num_identificacion = models.IntegerField(unique=True)
    fecha_nacimiento = models.DateField()
    primer_nombre_padre = models.CharField(max_length=50, blank=True, null=True)
    segundo_nombre_padre = models.CharField(max_length=50, blank=True, null=True)
    primer_apellido_padre = models.CharField(max_length=50, blank=True, null=True)
    segundo_apellido_padre = models.CharField(max_length=50, blank=True, null=True)
    Numero_historia_clinica = models.IntegerField(unique=True)
    caja = models.CharField(max_length=20)
    carpeta = models.CharField(max_length=20)
    gabeta = models.IntegerField(null=True, blank=True)
    tipo_identificacion = models.CharField(max_length=20, default='Cedula de Ciudadania')
    sexo = models.CharField(max_length=10, default='Masculino')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Ficha del paciente {self.primer_nombre} con identificacion {self.num_identificacion}"

class PerfilUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    oficina = models.ForeignKey(OficinaProductora, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.oficina.nombre}"

# ============================
# MODELOS DE CORRESPONDENCIA
# ============================

class TipoDocumentoCorrespondencia(models.Model):
    """Catálogo de tipos de documentos de correspondencia"""
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=10, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    class Meta:
        verbose_name = "Tipo de Documento de Correspondencia"
        verbose_name_plural = "Tipos de Documento de Correspondencia"
        ordering = ['codigo']


class Contacto(models.Model):
    """Entidades o personas externas que envían o reciben correspondencia"""
    TIPO_CHOICES = [
        ('NAT', 'Persona Natural'),
        ('JUR', 'Persona Jurídica'),
        ('GOB', 'Entidad Gubernamental'),
    ]
    TIPO_ID_CHOICES = [
        ('NIT', 'NIT'),
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('PAS', 'Pasaporte'),
        ('OTR', 'Otro'),
    ]
    
    tipo = models.CharField(max_length=3, choices=TIPO_CHOICES)
    nombre = models.CharField(max_length=200)
    tipo_identificacion = models.CharField(max_length=3, choices=TIPO_ID_CHOICES)
    identificacion = models.CharField(max_length=20)
    direccion = models.CharField(max_length=255, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    correo = models.EmailField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    observaciones = models.TextField(blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='contactos_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_identificacion_display()}: {self.identificacion})"
    
    class Meta:
        verbose_name = "Contacto"
        verbose_name_plural = "Contactos"
        ordering = ['nombre']
        unique_together = [['tipo_identificacion', 'identificacion']]


class Correspondencia(models.Model):
    """Modelo principal para gestionar correspondencia entrante, saliente e interna"""
    TIPO_CORRESPONDENCIA_CHOICES = [
        ('ENT', 'Entrada'),
        ('SAL', 'Salida'),
        ('INT', 'Interna'),
    ]
    ESTADO_CHOICES = [
        ('REC', 'Recibido'),
        ('RAD', 'Radicado'),
        ('DIS', 'Distribuido'),
        ('TRA', 'En Trámite'),
        ('RES', 'Respondido'),
        ('FIR', 'Firmado'),
        ('ARC', 'Archivado'),
        ('ANU', 'Anulado'),
    ]
    PRIORIDAD_CHOICES = [
        ('NOR', 'Normal'),
        ('ALT', 'Alta'),
        ('URG', 'Urgente'),
    ]
    
    # Campos básicos
    radicado = models.CharField(max_length=50, unique=True, editable=False, null=True, blank=True)
    fecha_radicacion = models.DateTimeField(null=True, blank=True)
    tipo_correspondencia = models.CharField(max_length=3, choices=TIPO_CORRESPONDENCIA_CHOICES)
    tipo_documento = models.ForeignKey(TipoDocumentoCorrespondencia, on_delete=models.PROTECT)
    asunto = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    fecha_documento = models.DateField()
    numero_documento = models.CharField(max_length=100, blank=True)
    
    # Clasificación documental
    serie_documental = models.ForeignKey(SerieDocumental, on_delete=models.PROTECT)
    subserie_documental = models.ForeignKey(SubserieDocumental, on_delete=models.PROTECT)
    
    # Campos para correspondencia entrada/salida
    remitente_externo = models.ForeignKey(Contacto, on_delete=models.PROTECT, 
                                         related_name='correspondencia_remitida',
                                         null=True, blank=True)
    destinatario_externo = models.ForeignKey(Contacto, on_delete=models.PROTECT,
                                            related_name='correspondencia_recibida',
                                            null=True, blank=True)
    
    # Campos para correspondencia interna/salida
    oficina_remitente = models.ForeignKey(OficinaProductora, on_delete=models.PROTECT,
                                         related_name='correspondencia_emitida',
                                         null=True, blank=True)
    
    # Campo para correspondencia entrada/interna
    oficina_destinatario = models.ForeignKey(OficinaProductora, on_delete=models.PROTECT,
                                           related_name='correspondencia_recibida',
                                           null=True, blank=True)
    
    # Campos adicionales
    estado = models.CharField(max_length=3, choices=ESTADO_CHOICES, default='RAD')
    prioridad = models.CharField(max_length=3, choices=PRIORIDAD_CHOICES, default='NOR')
    requiere_respuesta = models.BooleanField(default=False)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    anulado = models.BooleanField(default=False)
    motivo_anulacion = models.TextField(blank=True)
    
    # Seguimiento
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='correspondencia_creada')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    modificado_por = models.ForeignKey(User, on_delete=models.PROTECT, 
                                      related_name='correspondencia_modificada',
                                      null=True, blank=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Generar radicado automático solo si el estado es RAD y no tiene radicado
        if self.estado == 'RAD' and not self.radicado:
            from django.utils import timezone
            year = timezone.now().year
            prefix = self._get_radicado_prefix()
            
            # Obtener último consecutivo del año actual para este tipo
            ultimo_consecutivo = Correspondencia.objects.filter(
                radicado__startswith=f"{prefix}{year}"
            ).count()
            
            # Generar nuevo radicado: PREFIJO + AÑO + CONSECUTIVO (5 dígitos)
            self.radicado = f"{prefix}{year}{str(ultimo_consecutivo + 1).zfill(5)}"
            self.fecha_radicacion = timezone.now()
        
        super().save(*args, **kwargs)
    
    def _get_radicado_prefix(self):
        """Determina el prefijo según el tipo de correspondencia"""
        if self.tipo_correspondencia == 'ENT':
            return 'E'
        elif self.tipo_correspondencia == 'SAL':
            return 'S'
        else:  # Interna
            return 'I'
    
    def __str__(self):
        return f"{self.radicado} - {self.asunto}"
    
    class Meta:
        verbose_name = "Correspondencia"
        verbose_name_plural = "Correspondencia"
        ordering = ['-fecha_radicacion']
        permissions = [
            ("view_own_correspondencia", "Puede ver su propia correspondencia"),
            ("change_own_correspondencia", "Puede editar su propia correspondencia"),
            ("view_office_correspondencia", "Puede ver la correspondencia de su oficina"),
            ("distribute_correspondencia", "Puede distribuir correspondencia"),
        ]


class DistribucionInterna(models.Model):
    """Registro de distribución de correspondencia entre oficinas internas"""
    ESTADO_CHOICES = [
        ('PEN', 'Pendiente'),
        ('REC', 'Recibido'),
        ('RED', 'Redistribuido'),
        ('FIN', 'Finalizado'),
    ]
    
    correspondencia = models.ForeignKey(Correspondencia, on_delete=models.CASCADE, 
                                       related_name='distribuciones')
    oficina_origen = models.ForeignKey(OficinaProductora, on_delete=models.PROTECT, 
                                      related_name='distribuciones_enviadas')
    oficina_destino = models.ForeignKey(OficinaProductora, on_delete=models.PROTECT,
                                       related_name='distribuciones_recibidas')
    fecha_distribucion = models.DateTimeField(auto_now_add=True)
    instrucciones = models.TextField(blank=True)
    estado = models.CharField(max_length=3, choices=ESTADO_CHOICES, default='PEN')
    
    # Campos para recepción
    recibido_por = models.ForeignKey(User, on_delete=models.PROTECT, 
                                    related_name='distribuciones_recibidas',
                                    null=True, blank=True)
    fecha_recepcion = models.DateTimeField(null=True, blank=True)
    observaciones_recepcion = models.TextField(blank=True)
    
    # Seguimiento
    creado_por = models.ForeignKey(User, on_delete=models.PROTECT, 
                                  related_name='distribuciones_creadas')
    
    def __str__(self):
        return f"Distribución {self.correspondencia.radicado}: {self.oficina_origen} → {self.oficina_destino}"
    
    class Meta:
        verbose_name = "Distribución Interna"
        verbose_name_plural = "Distribuciones Internas"
        ordering = ['-fecha_distribucion']


def adjunto_correspondencia_path(instance, filename):
    """
    Define la ruta de almacenamiento para los adjuntos de correspondencia
    organizándolos por año/mes/radicado
    """
    filename = normalize_filename(filename)
    radicado = instance.correspondencia.radicado
    return os.path.join("correspondencia", radicado, filename)


class AdjuntoCorrespondencia(models.Model):
    """Archivos adjuntos a correspondencia"""
    correspondencia = models.ForeignKey(Correspondencia, on_delete=models.CASCADE, 
                                       related_name='adjuntos')
    archivo = models.FileField(upload_to=adjunto_correspondencia_path, 
                              validators=[validate_file_size])
    nombre_original = models.CharField(max_length=255)
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    subido_por = models.ForeignKey(User, on_delete=models.PROTECT)
    
    def save(self, *args, **kwargs):
        if not self.nombre_original and self.archivo:
            self.nombre_original = self.archivo.name
            
        # Crear directorio si no existe
        if self.archivo:
            ruta_destino = os.path.dirname(os.path.join(settings.MEDIA_ROOT, 
                                          adjunto_correspondencia_path(self, self.archivo.name)))
            try:
                os.makedirs(ruta_destino, exist_ok=True, mode=0o755)
                logger.info(f"Directorio creado/verificado: {ruta_destino}")
            except Exception as e:
                logger.error(f"Error al crear directorio {ruta_destino}: {str(e)}")
                raise ValidationError(f"Error al crear directorio para almacenar el archivo: {str(e)}")
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Adjunto: {self.nombre_original} ({self.correspondencia.radicado})"
    
    class Meta:
        verbose_name = "Adjunto de Correspondencia"
        verbose_name_plural = "Adjuntos de Correspondencia"
        ordering = ['correspondencia', 'fecha_carga']

class Firma(models.Model):
    """Registro de firmas electrónicas de correspondencia"""
    correspondencia = models.ForeignKey(Correspondencia, on_delete=models.CASCADE, 
                                       related_name='firmas')
    usuario = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    certificado = models.TextField(blank=True)
    hash_documento = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"Firma de {self.usuario.username} en {self.correspondencia.radicado}"
    
    class Meta:
        verbose_name = "Firma Electrónica"
        verbose_name_plural = "Firmas Electrónicas"
        ordering = ['-fecha']
