from django import forms
from .models import RegistroDeArchivo, SerieDocumental, SubserieDocumental
from django.utils.timezone import now
from django.forms import DateInput
from django import forms
from .models import FUID, RegistroDeArchivo
from django.utils.timezone import now, timedelta
from django.contrib.auth.models import User  # IMPORTAR User
# from .forms import FichaPacienteForm



from django import forms
from django.utils.timezone import now
from .models import RegistroDeArchivo, SubserieDocumental

from django import forms
from django.utils.timezone import now
from django.core.exceptions import ValidationError

# documentos/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from .models import RegistroDeArchivo, SubserieDocumental
from .models import Documento  # si necesitas usarlo en este archivo
from django.conf import settings

# Tu validador de tamaño
def validate_file_size(value):
    max_size = 10 * 1024 * 1024  # 10 MB
    if value.size > max_size:
        raise ValidationError("El archivo no puede superar los 10 MB.")

class RegistroDeArchivoForm(forms.ModelForm):
    # Aplica el validador al campo archivo
    archivo = forms.FileField(
        required=False,
        help_text="Sube un documento (máx 10 MB).",
        validators=[validate_file_size]
    )

    fecha_archivo = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    )

    fecha_inicial = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    )

    fecha_final = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    )

    class Meta:
        model = RegistroDeArchivo
        exclude = ['creado_por']
        widgets = {
            'Estado_archivo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Evitar que 'ubicacion' sea requerida
        self.fields['ubicacion'].required = False

        # Asignar fecha_archivo por defecto en el formulario
        if not self.instance.pk:
            self.fields['fecha_archivo'].initial = now().date()

        # Configuración dinámica de subseries
        if 'codigo_serie' in self.data:
            try:
                serie_id = int(self.data.get('codigo_serie'))
                self.fields['codigo_subserie'].queryset = SubserieDocumental.objects.filter(serie_id=serie_id)
            except (ValueError, TypeError):
                self.fields['codigo_subserie'].queryset = SubserieDocumental.objects.none()
        elif self.instance.pk and self.instance.codigo_serie:
            self.fields['codigo_subserie'].queryset = SubserieDocumental.objects.filter(serie_id=self.instance.codigo_serie.id)
        else:
            self.fields['codigo_subserie'].queryset = SubserieDocumental.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        # Si fecha_archivo está vacío, asignar la fecha actual
        if not cleaned_data.get('fecha_archivo'):
            cleaned_data['fecha_archivo'] = now().date()

        # Soporte Físico
        if not cleaned_data.get('soporte_fisico'):
            cleaned_data['caja'] = 0
            cleaned_data['carpeta'] = 0
            cleaned_data['tomo_legajo_libro'] = "N/A"
            cleaned_data['numero_folios'] = 0
            cleaned_data['tipo'] = "N/A"
            cleaned_data['cantidad'] = 0

        # Soporte Electrónico
        if not cleaned_data.get('soporte_electronico'):
            cleaned_data['ubicacion'] = "N/A"
            cleaned_data['cantidad_documentos_electronicos'] = 0
            cleaned_data['tamano_documentos_electronicos'] = "N/A"

        return cleaned_data




class FUIDForm(forms.ModelForm):
    # Campos y configuración del formulario
    usuario = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Filtrar por Usuario",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha_inicio = forms.DateField(
        required=False,
        label="Fecha Inicio",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin = forms.DateField(
        required=False,
        label="Fecha Fin",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    registros = forms.ModelMultipleChoiceField(
        queryset=RegistroDeArchivo.objects.none(),  
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Registros Asociados"
    )

    elaborado_por_nombre = forms.CharField(
        required=False,
        max_length=255,
        label="Elaborado Por (Nombre)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    elaborado_por_cargo = forms.CharField(
        required=False,
        max_length=255,
        label="Elaborado Por (Cargo)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    elaborado_por_lugar = forms.CharField(
        required=False,
        max_length=255,
        label="Elaborado Por (Lugar)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    elaborado_por_fecha = forms.DateField(
        required=False,
        label="Elaborado Por (Fecha)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    entregado_por_nombre = forms.CharField(
        required=False,
        max_length=255,
        label="Entregado Por (Nombre)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    entregado_por_cargo = forms.CharField(
        required=False,
        max_length=255,
        label="Entregado Por (Cargo)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    entregado_por_lugar = forms.CharField(
        required=False,
        max_length=255,
        label="Entregado Por (Lugar)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    entregado_por_fecha = forms.DateField(
        required=False,
        label="Entregado Por (Fecha)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    recibido_por_nombre = forms.CharField(
        required=False,
        max_length=255,
        label="Recibido Por (Nombre)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    recibido_por_cargo = forms.CharField(
        required=False,
        max_length=255,
        label="Recibido Por (Cargo)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    recibido_por_lugar = forms.CharField(
        required=False,
        max_length=255,
        label="Recibido Por (Lugar)",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    recibido_por_fecha = forms.DateField(
        required=False,
        label="Recibido Por (Fecha)",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    class Meta:
        model = FUID
        fields = [
            'entidad_productora', 'unidad_administrativa', 'oficina_productora', 'objeto',
            'registros',
            'elaborado_por_nombre', 'elaborado_por_cargo', 'elaborado_por_lugar', 'elaborado_por_fecha',
            'entregado_por_nombre', 'entregado_por_cargo', 'entregado_por_lugar', 'entregado_por_fecha',
            'recibido_por_nombre', 'recibido_por_cargo', 'recibido_por_lugar', 'recibido_por_fecha'
        ]
        widgets = {
            'entidad_productora': forms.Select(attrs={'class': 'form-select'}),
            'unidad_administrativa': forms.Select(attrs={'class': 'form-select'}),
            'oficina_productora': forms.Select(attrs={'class': 'form-select'}),
            'objeto': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # Usuario autenticado
        # No es necesario asignar self.instance aquí, ModelForm ya lo hace
        super().__init__(*args, **kwargs)

        # Configura el queryset de registros
        if self.instance and self.instance.pk:
            registros_actuales = self.instance.registros.all()
            registros_disponibles = RegistroDeArchivo.objects.filter(fuids__isnull=True)
            self.fields['registros'].queryset = registros_actuales | registros_disponibles
        else:
            self.fields['registros'].queryset = RegistroDeArchivo.objects.filter(fuids__isnull=True)
  

from django import forms
from .models import FichaPaciente

class FichaPacienteForm(forms.ModelForm):
    class Meta:
        model = FichaPaciente
        fields = '__all__'
        widgets = {
            'primer_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el primer nombre',
                'autofocus': 'autofocus',  # Enfocar este campo automáticamente
            }),
            'segundo_nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el segundo nombre (opcional)',
            }),
            'primer_apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el primer apellido',
            }),
            'segundo_apellido': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el segundo apellido (opcional)',
            }),
            'num_identificacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de identificación único',
            }),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',  # Mostrar un selector de fecha
            }),
            'primer_nombre_padre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el primer nombre del padre',
            }),
            'segundo_nombre_padre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Segundo nombre del padre (opcional)',
            }),
            'primer_apellido_padre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa el primer apellido del padre',
            }),
            'segundo_apellido_padre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Segundo apellido del padre (opcional)',
            }),
            'Numero_historia_clinica': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de historia clínica único',
            }),
            'caja': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de caja',
            }),
            'carpeta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de carpeta',

            }),
            'Activo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Estado',
                
            }),                 
        }

    def clean_Numero_historia_clinica(self):
        numero_historia_clinica = self.cleaned_data.get('Numero_historia_clinica')
        if FichaPaciente.objects.filter(Numero_historia_clinica=numero_historia_clinica).exists():
            raise forms.ValidationError("El número de historia clínica ya está registrado. Por favor, verifica los datos.")
        return numero_historia_clinica

    def clean_num_identificacion(self):
        num_identificacion = self.cleaned_data.get('num_identificacion')
        if FichaPaciente.objects.filter(num_identificacion=num_identificacion).exists():
            raise forms.ValidationError("El número de identificación ya está registrado. Por favor, verifica los datos.")
        return num_identificacion

# Formularios para el módulo de correspondencia
from .models import (
    TipoDocumentoCorrespondencia, Contacto, Correspondencia,
    DistribucionInterna, AdjuntoCorrespondencia
)


class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        exclude = ['creado_por', 'fecha_creacion']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_identificacion': forms.Select(attrs={'class': 'form-select'}),
            'identificacion': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CorrespondenciaForm(forms.ModelForm):
    """Formulario principal para la creación y edición de correspondencia"""
    
    # Campos ocultos iniciales
    estado = forms.CharField(widget=forms.HiddenInput(), required=False, initial='REC')
    
    fecha_documento = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    )
    
    fecha_vencimiento = forms.DateField(
        required=False,
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control'}
        ),
        input_formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']
    )
    
    class Meta:
        model = Correspondencia
        exclude = ['radicado', 'creado_por', 'fecha_creacion', 'modificado_por', 
                  'fecha_modificacion', 'anulado', 'motivo_anulacion', 'estado']
        widgets = {
            'tipo_correspondencia': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo_correspondencia'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'asunto': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control'}),
            'serie_documental': forms.Select(attrs={'class': 'form-select', 'id': 'id_serie_documental'}),
            'subserie_documental': forms.Select(attrs={'class': 'form-select', 'id': 'id_subserie_documental'}),
            'remitente_externo': forms.Select(attrs={'class': 'form-select', 'id': 'id_remitente_externo'}),
            'destinatario_externo': forms.Select(attrs={'class': 'form-select', 'id': 'id_destinatario_externo'}),
            'oficina_remitente': forms.Select(attrs={'class': 'form-select', 'id': 'id_oficina_remitente'}),
            'oficina_destinatario': forms.Select(attrs={'class': 'form-select', 'id': 'id_oficina_destinatario'}),
            'prioridad': forms.Select(attrs={'class': 'form-select'}),
            'requiere_respuesta': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        # Inicialmente hacemos que algunos campos no sean requeridos
        # Se validarán según el tipo de correspondencia en el clean()
        self.fields['remitente_externo'].required = False
        self.fields['destinatario_externo'].required = False
        self.fields['oficina_remitente'].required = False
        self.fields['oficina_destinatario'].required = False
        
        # Si tenemos usuario y tiene oficina asociada, la preseleccionamos como remitente
        if usuario and hasattr(usuario, 'perfil') and usuario.perfil.oficina:
            self.fields['oficina_remitente'].initial = usuario.perfil.oficina
        
        # Configuración dinámica de subseries
        if 'serie_documental' in self.data:
            try:
                serie_id = int(self.data.get('serie_documental'))
                self.fields['subserie_documental'].queryset = SubserieDocumental.objects.filter(
                    serie_id=serie_id
                )
            except (ValueError, TypeError):
                self.fields['subserie_documental'].queryset = SubserieDocumental.objects.none()
        elif self.instance.pk and self.instance.serie_documental:
            self.fields['subserie_documental'].queryset = SubserieDocumental.objects.filter(
                serie_id=self.instance.serie_documental.id
            )
        else:
            self.fields['subserie_documental'].queryset = SubserieDocumental.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_correspondencia = cleaned_data.get('tipo_correspondencia')
        
        if tipo_correspondencia == 'ENT':  # Entrada
            # Validar remitente externo y oficina destinatario
            if not cleaned_data.get('remitente_externo'):
                self.add_error('remitente_externo', 'Para correspondencia de entrada, debe especificar el remitente externo')
            if not cleaned_data.get('oficina_destinatario'):
                self.add_error('oficina_destinatario', 'Para correspondencia de entrada, debe especificar la oficina destinataria')
        
        elif tipo_correspondencia == 'SAL':  # Salida
            # Validar oficina remitente y destinatario externo
            if not cleaned_data.get('oficina_remitente'):
                self.add_error('oficina_remitente', 'Para correspondencia de salida, debe especificar la oficina remitente')
            if not cleaned_data.get('destinatario_externo'):
                self.add_error('destinatario_externo', 'Para correspondencia de salida, debe especificar el destinatario externo')
        
        elif tipo_correspondencia == 'INT':  # Interna
            # Validar oficina remitente y destinatario
            if not cleaned_data.get('oficina_remitente'):
                self.add_error('oficina_remitente', 'Para correspondencia interna, debe especificar la oficina remitente')
            if not cleaned_data.get('oficina_destinatario'):
                self.add_error('oficina_destinatario', 'Para correspondencia interna, debe especificar la oficina destinataria')
        
        return cleaned_data


class AdjuntoCorrespondenciaForm(forms.ModelForm):
    class Meta:
        model = AdjuntoCorrespondencia
        fields = ['archivo', 'descripcion']
        widgets = {
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DistribucionInternaForm(forms.ModelForm):
    class Meta:
        model = DistribucionInterna
        fields = ['oficina_destino', 'instrucciones']
        widgets = {
            'oficina_destino': forms.Select(attrs={'class': 'form-select'}),
            'instrucciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class RecepcionDistribucionForm(forms.ModelForm):
    """Formulario para registrar la recepción de una distribución"""
    class Meta:
        model = DistribucionInterna
        fields = ['estado', 'observaciones_recepcion']
        widgets = {
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'observaciones_recepcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        

class BusquedaCorrespondenciaForm(forms.Form):
    """Formulario para búsqueda avanzada de correspondencia"""
    radicado = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    asunto = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tipo_correspondencia = forms.ChoiceField(
        required=False, 
        choices=[('', '---')] + list(Correspondencia.TIPO_CORRESPONDENCIA_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha_desde = forms.DateField(
        required=False,
        label="Fecha desde",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_hasta = forms.DateField(
        required=False,
        label="Fecha hasta",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    estado = forms.ChoiceField(
        required=False, 
        choices=[('', '---')] + list(Correspondencia.ESTADO_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    prioridad = forms.ChoiceField(
        required=False, 
        choices=[('', '---')] + list(Correspondencia.PRIORIDAD_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    serie_documental = forms.ModelChoiceField(
        required=False,
        queryset=SerieDocumental.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_busqueda_serie'})
    )
    subserie_documental = forms.ModelChoiceField(
        required=False,
        queryset=SubserieDocumental.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_busqueda_subserie'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuración dinámica de subseries para búsqueda
        if 'serie_documental' in self.data:
            try:
                serie_id = int(self.data.get('serie_documental'))
                self.fields['subserie_documental'].queryset = SubserieDocumental.objects.filter(
                    serie_id=serie_id
                )
            except (ValueError, TypeError):
                self.fields['subserie_documental'].queryset = SubserieDocumental.objects.none()
        else:
            self.fields['subserie_documental'].queryset = SubserieDocumental.objects.none()


class RadicacionForm(forms.Form):
    """Formulario para radicar correspondencia"""
    observaciones = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text="Observaciones opcionales sobre la radicación"
    )


class FirmaElectronicaForm(forms.Form):
    """Formulario para firma electrónica de correspondencia"""
    certificado = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=True,
        help_text="Pegue aquí el certificado de firma digital"
    )
    
    pin = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        help_text="PIN de seguridad para la firma"
    )
    
    def clean_pin(self):
        """Validación del PIN (aquí podrías implementar la validación real)"""
        pin = self.cleaned_data.get('pin')
        # En un entorno real, aquí validarías el PIN contra un servicio de firma electrónica
        if len(pin) < 4:
            raise forms.ValidationError("El PIN debe tener al menos 4 caracteres")
        return pin
