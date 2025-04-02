from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date

from .models import (
    SerieDocumental, SubserieDocumental, OficinaProductora,
    TipoDocumentoCorrespondencia, Contacto, Correspondencia,
    DistribucionInterna, AdjuntoCorrespondencia, Firma
)
from .forms import (
    ContactoForm, CorrespondenciaForm, AdjuntoCorrespondenciaForm,
    DistribucionInternaForm, RecepcionDistribucionForm, BusquedaCorrespondenciaForm,
    RadicacionForm, FirmaElectronicaForm
)

import json
import logging
from guardian.shortcuts import assign_perm, get_perms, get_objects_for_user, remove_perm
from django.contrib.auth.models import Group, User

logger = logging.getLogger(__name__)

# ============================
# VISTAS PARA ADMINISTRACIÓN DE PERMISOS
# ============================

@login_required
@permission_required('auth.change_user', raise_exception=True)
def gestionar_ventanilla_unica(request):
    """Vista para asignar usuarios como responsables de ventanilla única"""
    from django.contrib.auth.models import Group
    
    # Intentar obtener o crear el grupo de Ventanilla Única
    grupo_ventanilla, created = Group.objects.get_or_create(name='Ventanilla Única')
    
    if created:
        # Asignar permisos necesarios al grupo
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        ct_correspondencia = ContentType.objects.get_for_model(Correspondencia)
        
        permisos = [
            'add_correspondencia',
            'change_correspondencia',
            'view_correspondencia',
            'delete_correspondencia',
            'add_contacto',
            'change_contacto',
            'view_contacto',
            'distribute_correspondencia',
        ]
        
        for permiso in permisos:
            perm = Permission.objects.get(
                codename=permiso,
                content_type=ct_correspondencia
            )
            grupo_ventanilla.permissions.add(perm)
    
    # Obtener usuarios actuales en el grupo
    usuarios_ventanilla = User.objects.filter(groups=grupo_ventanilla).order_by('username')
    
    # Obtener todos los usuarios para el formulario
    todos_usuarios = User.objects.filter(is_active=True).order_by('username')
    
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        accion = request.POST.get('accion')
        
        if usuario_id and accion:
            usuario = get_object_or_404(User, id=usuario_id)
            
            if accion == 'agregar' and not usuario.groups.filter(id=grupo_ventanilla.id).exists():
                # Añadir al grupo
                grupo_ventanilla.user_set.add(usuario)
                messages.success(request, f'Usuario {usuario.username} añadido como responsable de ventanilla única.')
                
                # Dar permiso sobre toda la correspondencia existente
                for correspondencia in Correspondencia.objects.all():
                    assign_perm('view_correspondencia', usuario, correspondencia)
                    assign_perm('change_correspondencia', usuario, correspondencia)
                
            elif accion == 'quitar' and usuario.groups.filter(id=grupo_ventanilla.id).exists():
                # Quitar del grupo
                grupo_ventanilla.user_set.remove(usuario)
                messages.success(request, f'Usuario {usuario.username} eliminado como responsable de ventanilla única.')
                
                # Revocar permisos globales sobre correspondencia que no haya creado
                for correspondencia in Correspondencia.objects.exclude(creado_por=usuario):
                    remove_perm('view_correspondencia', usuario, correspondencia)
                    remove_perm('change_correspondencia', usuario, correspondencia)
        
        return redirect('gestionar_ventanilla_unica')
    
    context = {
        'usuarios_ventanilla': usuarios_ventanilla,
        'todos_usuarios': todos_usuarios,
    }
    
    return render(request, 'documentos/correspondencia/gestionar_ventanilla_unica.html', context)

# ============================
# VISTAS PARA CORRESPONDENCIA
# ============================

@login_required
def lista_correspondencia(request):
    """Vista para listar la correspondencia con filtros de búsqueda"""
    form = BusquedaCorrespondenciaForm(request.GET or None)
    
    # Base query - usamos get_objects_for_user de guardian para filtrar por permisos
    query = get_objects_for_user(
        request.user, 
        'documentos.view_correspondencia', 
        klass=Correspondencia,
        accept_global_perms=True
    ).filter(anulado=False)
    
    # Si el usuario tiene permisos para ver correspondencia por oficina
    if request.user.has_perm('documentos.view_office_correspondencia') and hasattr(request.user, 'perfil') and request.user.perfil.oficina:
        # Añadir correspondencia de su oficina (destinatario o remitente)
        oficina = request.user.perfil.oficina
        query_oficina = Correspondencia.objects.filter(
            anulado=False
        ).filter(
            Q(oficina_destinatario=oficina) | 
            Q(oficina_remitente=oficina)
        )
        
        # Combinar ambas queryset
        query = (query | query_oficina).distinct()
    
    # Aplicar filtros si se realiza una búsqueda
    if request.GET and form.is_valid():
        if radicado := form.cleaned_data.get('radicado'):
            query = query.filter(radicado__icontains=radicado)
        
        if asunto := form.cleaned_data.get('asunto'):
            query = query.filter(asunto__icontains=asunto)
        
        if tipo := form.cleaned_data.get('tipo_correspondencia'):
            query = query.filter(tipo_correspondencia=tipo)
        
        if estado := form.cleaned_data.get('estado'):
            query = query.filter(estado=estado)
        
        if prioridad := form.cleaned_data.get('prioridad'):
            query = query.filter(prioridad=prioridad)
        
        if fecha_desde := form.cleaned_data.get('fecha_desde'):
            query = query.filter(fecha_radicacion__date__gte=fecha_desde)
        
        if fecha_hasta := form.cleaned_data.get('fecha_hasta'):
            query = query.filter(fecha_radicacion__date__lte=fecha_hasta)
        
        if serie := form.cleaned_data.get('serie_documental'):
            query = query.filter(serie_documental=serie)
        
        if subserie := form.cleaned_data.get('subserie_documental'):
            query = query.filter(subserie_documental=subserie)
    
    # Ordenar resultados
    query = query.order_by('-fecha_radicacion')
    
    # Paginación
    paginator = Paginator(query, 20)  # 20 registros por página
    page_number = request.GET.get('page', 1)
    correspondencia_page = paginator.get_page(page_number)
    
    context = {
        'correspondencia_list': correspondencia_page,
        'form': form,
        'is_paginated': correspondencia_page.has_other_pages(),
        'page_obj': correspondencia_page,
        'es_ventanilla': request.user.groups.filter(name='Ventanilla Única').exists(),
    }
    
    return render(request, 'documentos/correspondencia/lista_correspondencia.html', context)


@login_required
@permission_required('documentos.add_correspondencia', raise_exception=True)
def crear_correspondencia(request):
    """Vista para crear nueva correspondencia"""
    if request.method == 'POST':
        form = CorrespondenciaForm(request.POST, usuario=request.user)
        
        if form.is_valid():
            # Guardar correspondencia
            correspondencia = form.save(commit=False)
            correspondencia.creado_por = request.user
            correspondencia.estado = 'RAD'  # Asignar estado 'Radicado' por defecto
            correspondencia.save()
            
            # Asignar permisos a nivel de objeto utilizando Django Guardian
            # Asignar permisos al creador
            assign_perm('view_correspondencia', request.user, correspondencia)
            assign_perm('change_correspondencia', request.user, correspondencia)
            assign_perm('delete_correspondencia', request.user, correspondencia)
            assign_perm('view_own_correspondencia', request.user, correspondencia)
            assign_perm('change_own_correspondencia', request.user, correspondencia)
            
            # Si el usuario pertenece a la oficina destinataria o remitente, otorgar permiso de visualización
            if hasattr(request.user, 'perfil') and request.user.perfil.oficina:
                if correspondencia.oficina_destinatario == request.user.perfil.oficina or \
                   correspondencia.oficina_remitente == request.user.perfil.oficina:
                    # Obtener todos los usuarios de la oficina
                    from django.contrib.auth.models import User
                    from documentos.models import PerfilUsuario
                    usuarios_oficina = User.objects.filter(
                        perfil__oficina=request.user.perfil.oficina
                    ).exclude(id=request.user.id)  # Excluir al creador que ya tiene permisos
                    
                    # Asignar permisos de visualización a usuarios de la misma oficina
                    for usuario in usuarios_oficina:
                        assign_perm('view_correspondencia', usuario, correspondencia)
                        assign_perm('view_office_correspondencia', usuario, correspondencia)
            
            messages.success(request, f'Correspondencia radicada con éxito. Radicado: {correspondencia.radicado}')
            return redirect('detalle_correspondencia', pk=correspondencia.pk)
    else:
        form = CorrespondenciaForm(usuario=request.user)
    
    return render(request, 'documentos/correspondencia/crear_correspondencia.html', {
        'form': form,
        'titulo': 'Crear Correspondencia',
    })


@login_required
def detalle_correspondencia(request, pk):
    """Vista para ver detalles de correspondencia y sus adjuntos/distribuciones"""
    correspondencia = get_object_or_404(Correspondencia, pk=pk)
    
    # Verificar permisos usando Guardian
    permisos_usuario = get_perms(request.user, correspondencia)
    
    # Si el usuario no tiene permiso específico para este objeto
    if 'view_correspondencia' not in permisos_usuario:
        # Verificar permisos por creador, oficina o global
        es_creador = correspondencia.creado_por == request.user
        
        # Permiso de oficina: el usuario pertenece a la oficina destinataria o remitente
        pertenece_oficina = False
        if hasattr(request.user, 'perfil') and request.user.perfil.oficina:
            pertenece_oficina = (request.user.perfil.oficina == correspondencia.oficina_destinatario) or \
                           (request.user.perfil.oficina == correspondencia.oficina_remitente)
        
        # Permiso global de administración
        permiso_global = request.user.has_perm('documentos.view_correspondencia')
        
        # Si no cumple ninguna condición, denegar acceso
        if not (es_creador or pertenece_oficina or permiso_global):
            messages.error(request, 'No tienes permisos para ver esta correspondencia.')
            return redirect('lista_correspondencia')
    
    # Si llegamos aquí, el usuario tiene permiso para ver la correspondencia
    # Formulario para nuevos adjuntos
    adjunto_form = AdjuntoCorrespondenciaForm()
    
    # Si es una solicitud POST para agregar adjunto
    if request.method == 'POST' and 'adjuntar' in request.POST:
        adjunto_form = AdjuntoCorrespondenciaForm(request.POST, request.FILES)
        if adjunto_form.is_valid():
            adjunto = adjunto_form.save(commit=False)
            adjunto.correspondencia = correspondencia
            adjunto.subido_por = request.user
            adjunto.save()
            messages.success(request, 'Archivo adjuntado correctamente.')
            return redirect('detalle_correspondencia', pk=pk)
    
    # Obtener adjuntos y distribuciones
    adjuntos = correspondencia.adjuntos.all()
    distribuciones = correspondencia.distribuciones.all().order_by('-fecha_distribucion')
    
    context = {
        'correspondencia': correspondencia,
        'adjuntos': adjuntos,
        'distribuciones': distribuciones,
        'adjunto_form': adjunto_form,
        'permisos': permisos_usuario,  # Pasamos los permisos al contexto para la plantilla
    }
    
    return render(request, 'documentos/correspondencia/detalle_correspondencia.html', context)


@login_required
def editar_correspondencia(request, pk):
    """Vista para editar correspondencia existente"""
    correspondencia = get_object_or_404(Correspondencia, pk=pk)
    
    # Verificar permisos usando Guardian
    permisos_usuario = get_perms(request.user, correspondencia)
    
    # Verificar si tiene permiso para editar a nivel de objeto
    if 'change_correspondencia' not in permisos_usuario:
        # Verificar si es el creador y tiene permiso para editar sus propias correspondencias
        es_creador = correspondencia.creado_por == request.user
        puede_editar_propias = request.user.has_perm('documentos.change_own_correspondencia')
        
        # Permiso global de administración
        permiso_global = request.user.has_perm('documentos.change_correspondencia')
        
        # Si no cumple ninguna condición, denegar acceso
        if not ((es_creador and puede_editar_propias) or permiso_global):
            messages.error(request, 'No tienes permisos para editar esta correspondencia.')
            return redirect('detalle_correspondencia', pk=pk)
    
    # No permitir editar correspondencia anulada
    if correspondencia.anulado:
        messages.error(request, 'No se puede editar una correspondencia anulada.')
        return redirect('detalle_correspondencia', pk=pk)
    
    if request.method == 'POST':
        form = CorrespondenciaForm(request.POST, instance=correspondencia, usuario=request.user)
        if form.is_valid():
            correspondencia = form.save(commit=False)
            correspondencia.modificado_por = request.user
            correspondencia.save()
            
            messages.success(request, 'Correspondencia actualizada correctamente.')
            return redirect('detalle_correspondencia', pk=pk)
    else:
        form = CorrespondenciaForm(instance=correspondencia, usuario=request.user)
    
    return render(request, 'documentos/correspondencia/editar_correspondencia.html', {
        'form': form,
        'correspondencia': correspondencia,
        'titulo': 'Editar Correspondencia',
        'permisos': permisos_usuario,  # Pasamos los permisos al contexto para la plantilla
    })


@login_required
@permission_required('documentos.change_correspondencia', raise_exception=True)
def anular_correspondencia(request, pk):
    """Vista para anular correspondencia"""
    correspondencia = get_object_or_404(Correspondencia, pk=pk)
    
    # Verificar permisos
    if not request.user.has_perm('documentos.change_correspondencia') and correspondencia.creado_por != request.user:
        messages.error(request, 'No tienes permisos para anular esta correspondencia.')
        return redirect('detalle_correspondencia', pk=pk)
    
    # Ya está anulada
    if correspondencia.anulado:
        messages.warning(request, 'Esta correspondencia ya está anulada.')
        return redirect('detalle_correspondencia', pk=pk)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo_anulacion', '').strip()
        
        if not motivo:
            messages.error(request, 'Debe proporcionar un motivo para anular la correspondencia.')
            return redirect('anular_correspondencia', pk=pk)
        
        correspondencia.anulado = True
        correspondencia.motivo_anulacion = motivo
        correspondencia.modificado_por = request.user
        correspondencia.save()
        
        messages.success(request, 'Correspondencia anulada correctamente.')
        return redirect('detalle_correspondencia', pk=pk)
    
    return render(request, 'documentos/correspondencia/anular_correspondencia.html', {
        'correspondencia': correspondencia,
    })


@login_required
@permission_required('documentos.distribute_correspondencia', raise_exception=True)
def distribuir_correspondencia(request, pk):
    """Vista para distribuir correspondencia a otra oficina"""
    correspondencia = get_object_or_404(Correspondencia, pk=pk)
    
    # No permitir distribuir correspondencia anulada
    if correspondencia.anulado:
        messages.error(request, 'No se puede distribuir una correspondencia anulada.')
        return redirect('detalle_correspondencia', pk=pk)
    
    # Verificar oficina del usuario
    if not hasattr(request.user, 'perfil') or not request.user.perfil.oficina:
        messages.error(request, 'No tienes una oficina asociada para distribuir correspondencia.')
        return redirect('detalle_correspondencia', pk=pk)
    
    oficina_origen = request.user.perfil.oficina
    
    if request.method == 'POST':
        form = DistribucionInternaForm(request.POST)
        if form.is_valid():
            distribucion = form.save(commit=False)
            distribucion.correspondencia = correspondencia
            distribucion.oficina_origen = oficina_origen
            distribucion.creado_por = request.user
            distribucion.save()
            
            # Actualizar estado de la correspondencia
            correspondencia.estado = 'DIS'  # Distribuido
            correspondencia.save()
            
            messages.success(request, 'Correspondencia distribuida correctamente.')
            return redirect('detalle_correspondencia', pk=pk)
    else:
        form = DistribucionInternaForm()
    
    return render(request, 'documentos/correspondencia/distribuir_correspondencia.html', {
        'form': form,
        'correspondencia': correspondencia,
        'oficina_origen': oficina_origen,
    })


# ============================
# VISTAS PARA DISTRIBUCIONES
# ============================

@login_required
def lista_distribuciones(request):
    """Vista para listar distribuciones de correspondencia"""
    # Verificar si el usuario tiene oficina
    if not hasattr(request.user, 'perfil') or not request.user.perfil.oficina:
        messages.error(request, 'No tienes una oficina asociada para ver distribuciones.')
        return redirect('lista_correspondencia')
    
    oficina = request.user.perfil.oficina
    
    # Aplicar filtros
    estado = request.GET.get('estado', '')
    oficina_origen_id = request.GET.get('oficina_origen', '')
    oficina_destino_id = request.GET.get('oficina_destino', '')
    
    # Solo superusuarios pueden ver todas las distribuciones
    if request.user.is_superuser:
        queryset = DistribucionInterna.objects.all()
    else:
        # Usuarios normales solo ven distribuciones relacionadas con su oficina
        queryset = DistribucionInterna.objects.filter(
            Q(oficina_origen=oficina) | Q(oficina_destino=oficina)
        )
    
    # Aplicar filtros si se proporcionan
    if estado:
        queryset = queryset.filter(estado=estado)
    if oficina_origen_id:
        queryset = queryset.filter(oficina_origen_id=oficina_origen_id)
    if oficina_destino_id:
        queryset = queryset.filter(oficina_destino_id=oficina_destino_id)
    
    # Ordenar por fecha más reciente
    queryset = queryset.order_by('-fecha_distribucion')
    
    # Obtener lista de oficinas para el filtro
    oficinas = OficinaProductora.objects.all().order_by('nombre')
    
    # Paginación
    paginator = Paginator(queryset, 20)  # 20 distribuciones por página
    page_number = request.GET.get('page', 1)
    distribuciones = paginator.get_page(page_number)
    
    context = {
        'distribuciones': distribuciones,
        'oficina': oficina,
        'oficinas': oficinas,
    }
    
    return render(request, 'documentos/correspondencia/lista_distribuciones.html', context)


@login_required
def recibir_distribucion(request, pk):
    """Vista para recibir una distribución"""
    distribucion = get_object_or_404(DistribucionInterna, pk=pk)
    
    # Verificar si el usuario pertenece a la oficina destino
    if not hasattr(request.user, 'perfil') or request.user.perfil.oficina != distribucion.oficina_destino:
        messages.error(request, 'No puedes recibir esta distribución porque no perteneces a la oficina destino.')
        return redirect('lista_distribuciones')
    
    # Verificar si ya está recibida
    if distribucion.estado != 'PEN':
        messages.warning(request, 'Esta distribución ya ha sido procesada.')
        return redirect('lista_distribuciones')
    
    if request.method == 'POST':
        form = RecepcionDistribucionForm(request.POST, instance=distribucion)
        if form.is_valid():
            distribucion = form.save(commit=False)
            distribucion.recibido_por = request.user
            distribucion.fecha_recepcion = timezone.now()
            
            # Si se cambia a TRA (trámite), cambiar el estado de la correspondencia
            if distribucion.estado == 'REC':
                distribucion.correspondencia.estado = 'TRA'  # En trámite
                distribucion.correspondencia.save()
                
            distribucion.save()
            
            messages.success(request, 'Distribución recibida correctamente.')
            return redirect('lista_distribuciones')
    else:
        form = RecepcionDistribucionForm(instance=distribucion)
    
    return render(request, 'documentos/correspondencia/recibir_distribucion.html', {
        'form': form,
        'distribucion': distribucion,
    })


@login_required
def redistribuir_correspondencia(request, pk):
    """Vista para redistribuir una correspondencia recibida a otra oficina"""
    distribucion = get_object_or_404(DistribucionInterna, pk=pk)
    
    # Verificar si el usuario pertenece a la oficina destino
    if not hasattr(request.user, 'perfil') or request.user.perfil.oficina != distribucion.oficina_destino:
        messages.error(request, 'No puedes redistribuir esta distribución porque no perteneces a la oficina destino.')
        return redirect('lista_distribuciones')
    
    # Verificar si ya está recibida
    if distribucion.estado != 'REC':
        messages.warning(request, 'Solo puedes redistribuir distribuciones que hayas recibido.')
        return redirect('lista_distribuciones')
    
    correspondencia = distribucion.correspondencia
    oficina_origen = request.user.perfil.oficina
    
    if request.method == 'POST':
        form = DistribucionInternaForm(request.POST)
        if form.is_valid():
            nueva_distribucion = form.save(commit=False)
            nueva_distribucion.correspondencia = correspondencia
            nueva_distribucion.oficina_origen = oficina_origen
            nueva_distribucion.creado_por = request.user
            nueva_distribucion.save()
            
            # Actualizar la distribución original
            distribucion.estado = 'RED'  # Redistribuido
            distribucion.save()
            
            messages.success(request, 'Correspondencia redistribuida correctamente.')
            return redirect('lista_distribuciones')
    else:
        form = DistribucionInternaForm()
    
    return render(request, 'documentos/correspondencia/redistribuir_correspondencia.html', {
        'form': form,
        'correspondencia': correspondencia,
        'distribucion_original': distribucion,
        'oficina_origen': oficina_origen,
    })


# ============================
# VISTAS PARA CONTACTOS
# ============================

@login_required
def lista_contactos(request):
    """Vista para listar y buscar contactos"""
    q = request.GET.get('q', '')
    
    if q:
        contactos = Contacto.objects.filter(
            Q(nombre__icontains=q) | 
            Q(identificacion__icontains=q) |
            Q(correo__icontains=q)
        ).filter(activo=True)
    else:
        contactos = Contacto.objects.filter(activo=True)
    
    # Paginación
    paginator = Paginator(contactos.order_by('nombre'), 20)
    page_number = request.GET.get('page', 1)
    contactos_page = paginator.get_page(page_number)
    
    return render(request, 'documentos/correspondencia/lista_contactos.html', {
        'contactos': contactos_page,
        'query': q,
        'is_paginated': contactos_page.has_other_pages(),
        'page_obj': contactos_page,
    })


@login_required
@permission_required('documentos.add_contacto', raise_exception=True)
def crear_contacto(request):
    """Vista para crear un nuevo contacto"""
    if request.method == 'POST':
        form = ContactoForm(request.POST)
        if form.is_valid():
            contacto = form.save(commit=False)
            contacto.creado_por = request.user
            contacto.save()
            
            messages.success(request, 'Contacto creado correctamente.')
            return redirect('lista_contactos')
    else:
        form = ContactoForm()
    
    return render(request, 'documentos/correspondencia/contacto_form.html', {
        'form': form,
        'titulo': 'Crear Contacto',
    })


@login_required
@permission_required('documentos.change_contacto', raise_exception=True)
def editar_contacto(request, pk):
    """Vista para editar un contacto existente"""
    contacto = get_object_or_404(Contacto, pk=pk)
    
    if request.method == 'POST':
        form = ContactoForm(request.POST, instance=contacto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contacto actualizado correctamente.')
            return redirect('lista_contactos')
    else:
        form = ContactoForm(instance=contacto)
    
    return render(request, 'documentos/correspondencia/contacto_form.html', {
        'form': form,
        'contacto': contacto,
        'titulo': 'Editar Contacto',
    })


# ============================
# VISTAS AJAX
# ============================

@login_required
def cargar_subseries_ajax(request):
    """Vista AJAX para cargar subseries según serie seleccionada"""
    serie_id = request.GET.get('serie_id')
    subseries = []
    
    if serie_id:
        subseries = list(SubserieDocumental.objects.filter(
            serie_id=serie_id
        ).values('id', 'codigo', 'nombre'))
    
    # Devolver directamente la lista de subseries para que el JS pueda procesarla más fácilmente
    return JsonResponse(subseries, safe=False)


@login_required
def buscar_contactos_ajax(request):
    """Vista AJAX para buscar contactos"""
    q = request.GET.get('term', '')
    contactos = []
    
    if q and len(q) >= 3:
        queryset = Contacto.objects.filter(
            Q(nombre__icontains=q) | 
            Q(identificacion__icontains=q)
        ).filter(activo=True)[:10]
        
        contactos = [{
            'id': c.id,
            'text': f"{c.nombre} ({c.get_tipo_identificacion_display()}: {c.identificacion})",
        } for c in queryset]
    
    return JsonResponse({'results': contactos})


@login_required
@require_POST
def crear_contacto_ajax(request):
    """Vista AJAX para crear contacto desde el formulario de correspondencia"""
    try:
        # Aceptar tanto datos JSON como datos de formulario
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            form = ContactoForm(data)
        else:
            form = ContactoForm(request.POST)
        
        if form.is_valid():
            contacto = form.save(commit=False)
            contacto.creado_por = request.user
            contacto.save()
            
            return JsonResponse({
                'success': True,
                'contacto': {
                    'id': contacto.id,
                    'nombre': contacto.nombre,
                    'identificacion': contacto.identificacion
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors.get_json_data()
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


@login_required
def actualizar_campos_tipo_correspondencia(request):
    """Vista AJAX para actualizar qué campos mostrar según el tipo de correspondencia"""
    tipo = request.GET.get('tipo', '')
    
    if tipo not in ['ENT', 'SAL', 'INT']:
        return JsonResponse({'status': 'error', 'message': 'Tipo inválido'}, status=400)
    
    campos = {
        'ENT': {
            'remitente_externo': True,
            'destinatario_externo': False,
            'oficina_remitente': False,
            'oficina_destinatario': True,
        },
        'SAL': {
            'remitente_externo': False,
            'destinatario_externo': True,
            'oficina_remitente': True,
            'oficina_destinatario': False,
        },
        'INT': {
            'remitente_externo': False,
            'destinatario_externo': False,
            'oficina_remitente': True,
            'oficina_destinatario': True,
        }
    }
    
    return JsonResponse({'campos': campos[tipo]})

@login_required
@permission_required('documentos.delete_correspondencia', raise_exception=True)
def eliminar_correspondencia(request, pk):
    correspondencia = get_object_or_404(Correspondencia, pk=pk)
    
    if request.method == 'POST':
        correspondencia.delete()
        messages.success(request, 'Correspondencia eliminada con éxito.')
        return redirect('lista_correspondencia')
    
    return render(request, 'documentos/correspondencia/confirmar_eliminar.html', {
        'objeto': correspondencia,
        'tipo_objeto': 'correspondencia'
    })

@login_required
def detalle_contacto(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)
    
    # Obtener correspondencia relacionada
    correspondencia_entrada = Correspondencia.objects.filter(remitente=contacto)
    correspondencia_salida = Correspondencia.objects.filter(destinatario=contacto)
    
    return render(request, 'documentos/correspondencia/detalle_contacto.html', {
        'contacto': contacto,
        'correspondencia_entrada': correspondencia_entrada,
        'correspondencia_salida': correspondencia_salida
    })

@login_required
@permission_required('documentos.delete_contacto', raise_exception=True)
def eliminar_contacto(request, pk):
    contacto = get_object_or_404(Contacto, pk=pk)
    
    if request.method == 'POST':
        contacto.delete()
        messages.success(request, 'Contacto eliminado con éxito.')
        return redirect('lista_contactos')
    
    return render(request, 'documentos/correspondencia/confirmar_eliminar.html', {
        'objeto': contacto,
        'tipo_objeto': 'contacto'
    })

@login_required
def finalizar_distribucion(request, pk):
    distribucion = get_object_or_404(DistribucionInterna, pk=pk)
    
    # Verificar que el usuario pertenezca a la oficina destino
    try:
        perfil = request.user.perfilusuario
        if perfil.oficina != distribucion.oficina_destino and not request.user.is_superuser:
            messages.error(request, 'No tiene permiso para finalizar esta distribución.')
            return redirect('lista_distribuciones')
    except:
        messages.error(request, 'No tiene un perfil asociado a una oficina.')
        return redirect('lista_distribuciones')
    
    distribucion.estado = 'FIN'
    distribucion.fecha_finalizacion = timezone.now()
    distribucion.usuario_finalizacion = request.user
    distribucion.save()
    
    messages.success(request, 'Distribución finalizada con éxito.')
    return redirect('lista_distribuciones')

@login_required
@permission_required('documentos.change_distribucioninterna', raise_exception=True)
def editar_distribucion(request, pk):
    distribucion = get_object_or_404(DistribucionInterna, pk=pk)
    
    if request.method == 'POST':
        form = DistribucionInternaForm(request.POST, instance=distribucion)
        if form.is_valid():
            form.save()
            messages.success(request, 'Distribución actualizada con éxito.')
            return redirect('lista_distribuciones')
    else:
        form = DistribucionInternaForm(instance=distribucion)
    
    return render(request, 'documentos/correspondencia/editar_distribucion.html', {
        'form': form,
        'distribucion': distribucion
    })

@login_required
@permission_required('documentos.delete_distribucioninterna', raise_exception=True)
def eliminar_distribucion(request, pk):
    distribucion = get_object_or_404(DistribucionInterna, pk=pk)
    
    if request.method == 'POST':
        distribucion.delete()
        messages.success(request, 'Distribución eliminada con éxito.')
        return redirect('lista_distribuciones')
    
    return render(request, 'documentos/correspondencia/confirmar_eliminar.html', {
        'objeto': distribucion,
        'tipo_objeto': 'distribución'
    })

@login_required
@permission_required('documentos.add_adjuntocorrespondencia', raise_exception=True)
def agregar_adjunto(request, pk):
    correspondencia = get_object_or_404(Correspondencia, pk=pk)
    
    if request.method == 'POST':
        form = AdjuntoCorrespondenciaForm(request.POST, request.FILES)
        if form.is_valid():
            adjunto = form.save(commit=False)
            adjunto.correspondencia = correspondencia
            adjunto.usuario_creacion = request.user
            adjunto.save()
            
            messages.success(request, 'Adjunto agregado con éxito.')
            return redirect('detalle_correspondencia', pk=correspondencia.pk)
    else:
        form = AdjuntoCorrespondenciaForm()
    
    return render(request, 'documentos/correspondencia/agregar_adjunto.html', {
        'form': form,
        'correspondencia': correspondencia
    })

@login_required
@permission_required('documentos.delete_adjuntocorrespondencia', raise_exception=True)
def eliminar_adjunto(request, pk):
    adjunto = get_object_or_404(AdjuntoCorrespondencia, pk=pk)
    correspondencia_id = adjunto.correspondencia.id
    
    if request.method == 'POST':
        adjunto.delete()
        messages.success(request, 'Adjunto eliminado con éxito.')
        return redirect('detalle_correspondencia', pk=correspondencia_id)
    
    return render(request, 'documentos/correspondencia/confirmar_eliminar.html', {
        'objeto': adjunto,
        'tipo_objeto': 'adjunto'
    })

@login_required
@permission_required('documentos.change_correspondencia', raise_exception=True)
def radicar_correspondencia(request, pk):
    """Cambia el estado de una correspondencia de 'Recibido' a 'Radicado' y asigna número de radicado."""
    correspondencia = get_object_or_404(Correspondencia, pk=pk)
    
    # Verificar que esté en estado recibido
    if correspondencia.estado != 'REC':
        messages.error(request, f'La correspondencia {correspondencia.pk} no está en estado "Recibido".')
        return redirect('detalle_correspondencia', pk=correspondencia.pk)
    
    if request.method == 'POST':
        form = RadicacionForm(request.POST)
        if form.is_valid():
            # Cambiar estado y asignar número de radicado
            correspondencia.estado = 'RAD'
            correspondencia.modificado_por = request.user
            correspondencia.save()  # Esto generará automáticamente el radicado
            
            messages.success(request, f'Correspondencia radicada correctamente con número {correspondencia.radicado}.')
            return redirect('detalle_correspondencia', pk=correspondencia.pk)
    else:
        form = RadicacionForm()
    
    context = {
        'correspondencia': correspondencia,
        'form': form,
    }
    
    return render(request, 'documentos/correspondencia/radicar_correspondencia.html', context)


@login_required
@permission_required('documentos.change_correspondencia', raise_exception=True)
def firmar_correspondencia(request, pk):
    """Cambia el estado de una correspondencia a 'Firmado' y registra firma electrónica."""
    correspondencia = get_object_or_404(Correspondencia, pk=pk)
    
    # Verificar que no esté anulada
    if correspondencia.anulado:
        messages.error(request, f'No se puede firmar una correspondencia anulada.')
        return redirect('detalle_correspondencia', pk=correspondencia.pk)
    
    if request.method == 'POST':
        form = FirmaElectronicaForm(request.POST)
        if form.is_valid():
            # Cambiar estado a firmado
            correspondencia.estado = 'FIR'
            correspondencia.modificado_por = request.user
            correspondencia.save()
            
            # Registrar evento de firma (podría extenderse con más datos)
            Firma.objects.create(
                correspondencia=correspondencia,
                usuario=request.user,
                fecha=timezone.now(),
                certificado=form.cleaned_data.get('certificado', '')
            )
            
            messages.success(request, f'Correspondencia {correspondencia.radicado} firmada electrónicamente.')
            return redirect('detalle_correspondencia', pk=correspondencia.pk)
    else:
        form = FirmaElectronicaForm()
    
    context = {
        'correspondencia': correspondencia,
        'form': form,
    }
    
    return render(request, 'documentos/correspondencia/firmar_correspondencia.html', context) 