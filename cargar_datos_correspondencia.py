#!/usr/bin/env python
import os
import sys
import random
import datetime
from django.core.files.base import ContentFile
from datetime import timedelta

# Configuración del entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_document_management.settings')
import django
django.setup()

# Importar modelos después de configurar Django
from django.contrib.auth.models import User, Group
from documentos.models import (
    TipoDocumentoCorrespondencia, Contacto, Correspondencia, 
    DistribucionInterna, AdjuntoCorrespondencia, OficinaProductora,
    SerieDocumental, SubserieDocumental, PerfilUsuario
)
from django.utils import timezone
from guardian.shortcuts import assign_perm

def crear_contactos(num_contactos=20):
    """Crea contactos de prueba"""
    print("Creando contactos...")
    
    # Lista de nombres para generar contactos aleatorios
    nombres = ["Juan Pérez", "María García", "Pedro López", "Ana Rodríguez", "Luis González", 
               "Sofía Torres", "Carlos Ramírez", "Laura Sánchez", "Jorge Flores", "Diana Rivera", 
               "Hospital San Juan", "Clínica Santa María", "Ministerio de Salud",
               "Secretaría de Salud", "EPS Salud Total", "IPS Vida Plena", 
               "Fundación Corazón Sano", "Universidad Nacional", "Centro Médico Bienestar",
               "Laboratorio Médico Especializado", "Instituto de Salud Pública"]
    
    contactos_creados = []
    
    for i in range(num_contactos):
        nombre = nombres[i % len(nombres)]
        
        # Determinar si es persona natural o jurídica
        if "Hospital" in nombre or "Clínica" in nombre or "Ministerio" in nombre or "Secretaría" in nombre or "EPS" in nombre or "IPS" in nombre or "Fundación" in nombre or "Universidad" in nombre or "Centro" in nombre or "Laboratorio" in nombre or "Instituto" in nombre:
            tipo = "JUR"
            tipo_id = "NIT"
            identificacion = f"9{random.randint(10, 99)}{random.randint(100000, 999999)}"
        else:
            tipo = "NAT"
            tipo_id = "CC"
            identificacion = f"{random.randint(10000000, 99999999)}"
        
        telefono = f"3{random.randint(10, 99)}{random.randint(1000000, 9999999)}"
        correo = f"{nombre.split()[0].lower()}@{random.choice(['gmail.com', 'outlook.com', 'yahoo.com', 'empresa.co'])}"
        
        contacto = Contacto.objects.create(
            tipo=tipo,
            nombre=nombre,
            tipo_identificacion=tipo_id,
            identificacion=identificacion,
            direccion=f"Calle {random.randint(1, 100)} # {random.randint(1, 100)}-{random.randint(1, 100)}",
            telefono=telefono,
            correo=correo,
            ciudad=random.choice(["Bogotá", "Medellín", "Cali", "Barranquilla", "Bucaramanga"]),
            observaciones=f"Contacto de prueba generado automáticamente" if random.random() > 0.7 else "",
            creado_por=random.choice(User.objects.all()),
            activo=True
        )
        
        contactos_creados.append(contacto)
        print(f"Contacto creado: {contacto}")
    
    return contactos_creados

def crear_correspondencia(num_correspondencia=30):
    """Crea correspondencia de prueba"""
    print("Creando correspondencia...")
    
    # Obtener datos necesarios
    usuarios = User.objects.all()
    if not usuarios.exists():
        print("ERROR: No hay usuarios en el sistema. Crea al menos un usuario administrativo.")
        return []
    
    oficinas = OficinaProductora.objects.all()
    if not oficinas.exists():
        print("ERROR: No hay oficinas en el sistema. Crea oficinas primero.")
        return []
    
    tipos_documento = TipoDocumentoCorrespondencia.objects.all()
    if not tipos_documento.exists():
        print("ERROR: No hay tipos de documento. Ejecuta primero load_documentos.py")
        return []
    
    contactos = Contacto.objects.all()
    if not contactos.exists():
        print("No hay contactos, creando...")
        contactos = crear_contactos()
    
    series = SerieDocumental.objects.all()
    if not series.exists():
        print("ERROR: No hay series documentales. Crea series primero.")
        return []
    
    correspondencia_creada = []
    
    # Asuntos de ejemplo
    asuntos = [
        "Solicitud de información sobre pacientes",
        "Remisión de informes mensuales",
        "Invitación a reunión de coordinación",
        "Respuesta a requerimiento",
        "Notificación de auditoría",
        "Circular informativa sobre nuevos procedimientos",
        "Solicitud de insumos médicos",
        "Respuesta a derecho de petición",
        "Memorando sobre cambios en horarios",
        "Invitación a capacitación",
        "Remisión de historia clínica",
        "Notificación de eventos adversos",
        "Informe de gestión trimestral",
        "Solicitud de personal adicional",
        "Respuesta a queja de usuario"
    ]
    
    for i in range(num_correspondencia):
        # Elegir tipo de correspondencia
        tipo_corr = random.choice(["ENT", "SAL", "INT"])
        
        # Asignar campos según el tipo
        remitente_externo = None
        destinatario_externo = None
        oficina_remitente = None
        oficina_destinatario = None
        
        if tipo_corr == "ENT":  # Entrada (de externo a interno)
            remitente_externo = random.choice(contactos)
            oficina_destinatario = random.choice(oficinas)
        elif tipo_corr == "SAL":  # Salida (de interno a externo)
            oficina_remitente = random.choice(oficinas)
            destinatario_externo = random.choice(contactos)
        else:  # Interna (entre oficinas)
            oficina_remitente = random.choice(oficinas)
            # Asegurar que remitente y destinatario no sean iguales
            oficina_destinatario = random.choice([o for o in oficinas if o != oficina_remitente])
        
        # Crear correspondencia
        fecha_base = timezone.now() - datetime.timedelta(days=random.randint(0, 60))
        
        # Elegir una serie y subserie
        serie = random.choice(series)
        subseries = SubserieDocumental.objects.filter(serie=serie)
        subserie = random.choice(subseries) if subseries.exists() else None
        
        correspondencia = Correspondencia.objects.create(
            tipo_correspondencia=tipo_corr,
            asunto=random.choice(asuntos),
            descripcion=f"Descripción de prueba para correspondencia {i+1}. " * random.randint(1, 5),
            fecha_documento=fecha_base.date(),
            fecha_radicacion=fecha_base,
            numero_documento=f"DOC-{random.randint(1000, 9999)}" if random.random() > 0.5 else "",
            tipo_documento=random.choice(tipos_documento),
            serie_documental=serie,
            subserie_documental=subserie,
            estado=random.choice(['RAD', 'DIS', 'TRA', 'RES', 'ARC']) if not random.random() < 0.05 else 'ANU',
            prioridad=random.choice(['NOR', 'ALT', 'URG']),
            requiere_respuesta=random.random() < 0.4,  # 40% de probabilidad
            fecha_vencimiento=fecha_base.date() + datetime.timedelta(days=random.randint(10, 30)) if random.random() < 0.4 else None,
            anulado=random.random() < 0.05,  # 5% anulados
            motivo_anulacion="Anulado por duplicidad" if random.random() < 0.05 else "",
            
            # Campos según el tipo
            oficina_remitente=oficina_remitente,
            remitente_externo=remitente_externo,
            oficina_destinatario=oficina_destinatario,
            destinatario_externo=destinatario_externo,
            
            # Usuario que la crea (aleatorio)
            creado_por=random.choice(usuarios)
        )
        
        # Asignar permisos con Guardian
        for usuario in usuarios:
            if usuario.groups.filter(name='Ventanilla Única').exists() or usuario == correspondencia.creado_por:
                assign_perm('view_correspondencia', usuario, correspondencia)
                assign_perm('change_correspondencia', usuario, correspondencia)
            
            # Si el usuario pertenece a alguna de las oficinas involucradas
            if hasattr(usuario, 'perfil') and usuario.perfil.oficina:
                if (correspondencia.oficina_remitente == usuario.perfil.oficina or 
                    correspondencia.oficina_destinatario == usuario.perfil.oficina):
                    assign_perm('view_correspondencia', usuario, correspondencia)
                    assign_perm('view_office_correspondencia', usuario, correspondencia)
        
        correspondencia_creada.append(correspondencia)
        print(f"Correspondencia creada: {correspondencia.radicado} - {correspondencia.asunto}")
    
    return correspondencia_creada

def crear_distribuciones(correspondencia_list, cantidad):
    """
    Crea distribuciones internas para las correspondencias.
    """
    print("Creando distribuciones internas...")
    
    # Verificar si hay oficinas disponibles
    if not OficinaProductora.objects.exists():
        print("No hay oficinas productoras para asignar a las distribuciones")
        return []
    
    # Obtener todas las oficinas
    oficinas = list(OficinaProductora.objects.all())
    
    # Obtener todos los usuarios
    if not User.objects.exists():
        print("No hay usuarios para asignar a las distribuciones")
        return []
    
    usuarios = list(User.objects.all())
    
    # Filtrar correspondencias que sean de tipo interno o que tengan oficina_destinatario
    correspondencia_distribuible = [c for c in correspondencia_list if c.tipo_correspondencia == 'INT' or c.oficina_destinatario]
    
    if not correspondencia_distribuible:
        print("No hay correspondencias válidas para distribución")
        return []
    
    distribuciones = []
    
    # Crear distribuciones aleatorias
    for _ in range(min(cantidad, len(correspondencia_distribuible))):
        correspondencia = random.choice(correspondencia_distribuible)
        oficina_destino = random.choice(oficinas)
        usuario = random.choice(usuarios)
        
        try:
            # Determinar la oficina origen basada en el tipo de correspondencia
            if correspondencia.tipo_correspondencia == 'INT':
                # Para internas, el origen es la oficina remitente
                oficina_origen = correspondencia.oficina_remitente
            elif correspondencia.tipo_correspondencia == 'ENT':
                # Para entrantes, el origen es la oficina destinatario
                oficina_origen = correspondencia.oficina_destinatario
            elif correspondencia.tipo_correspondencia == 'SAL':
                # Para salientes, el origen es la oficina remitente
                oficina_origen = correspondencia.oficina_remitente
            else:
                # En caso de un tipo no reconocido, usar una oficina aleatoria
                oficina_origen = random.choice(oficinas)
                
            # Asegurarse que la oficina destino sea diferente a la origen
            if oficina_destino == oficina_origen:
                otras_oficinas = [o for o in oficinas if o != oficina_origen]
                if otras_oficinas:
                    oficina_destino = random.choice(otras_oficinas)
                    
            # Crear la distribución
            distribucion = DistribucionInterna.objects.create(
                correspondencia=correspondencia,
                oficina_origen=oficina_origen,
                oficina_destino=oficina_destino,
                fecha_distribucion=timezone.now() - timedelta(days=random.randint(0, 30)),
                estado=random.choice(['PEN', 'REC', 'FIN']),
                instrucciones=f"Distribución de prueba para la correspondencia {correspondencia.radicado}",
                creado_por=usuario
            )
            distribuciones.append(distribucion)
            print(f"Distribución creada para {correspondencia.radicado}")
        except Exception as e:
            print(f"Error al crear distribución para {correspondencia.radicado}: {e}")
    
    return distribuciones

def crear_adjuntos(correspondencia_list, num_adjuntos=15):
    """Crea archivos adjuntos de ejemplo para la correspondencia"""
    print("Creando adjuntos...")
    
    if not correspondencia_list:
        correspondencia_list = Correspondencia.objects.all()
    
    if not correspondencia_list:
        print("No hay correspondencia para adjuntar archivos.")
        return []
    
    usuarios = User.objects.all()
    
    adjuntos_creados = []
    
    # Contenido de texto simple para simular archivos
    contenido_ejemplo = "Este es un archivo de prueba para el módulo de correspondencia. " * 5
    
    # Tipos de archivo comunes
    tipos_archivo = ["pdf", "doc", "docx", "xls", "xlsx", "jpg", "png", "txt"]
    
    # Nombres de archivo típicos
    nombres_base = [
        "Informe", "Carta", "Memorando", "Circular", "Acta", "Registro", 
        "Presentacion", "Documento", "Reporte", "Solicitud", "Respuesta"
    ]
    
    for _ in range(num_adjuntos):
        correspondencia = random.choice(correspondencia_list)
        extension = random.choice(tipos_archivo)
        nombre_base = random.choice(nombres_base)
        nombre_archivo = f"{nombre_base}_{random.randint(1, 999)}.{extension}"
        
        # Crear un archivo falso con contenido de texto
        archivo_content = ContentFile(contenido_ejemplo.encode('utf-8'))
        
        # Crear el adjunto
        adjunto = AdjuntoCorrespondencia(
            correspondencia=correspondencia,
            nombre_original=nombre_archivo,
            descripcion=f"Archivo de prueba {extension.upper()}" if random.random() > 0.5 else "",
            subido_por=random.choice(usuarios)
        )
        
        # Guardar el archivo
        adjunto.archivo.save(nombre_archivo, archivo_content, save=False)
        adjunto.save()
        
        adjuntos_creados.append(adjunto)
        print(f"Adjunto creado: {adjunto}")
    
    return adjuntos_creados

def crear_grupo_ventanilla():
    """Crea el grupo de Ventanilla Única y asigna permisos"""
    print("Configurando grupo de Ventanilla Única...")
    
    grupo, created = Group.objects.get_or_create(name='Ventanilla Única')
    
    if created:
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Obtener tipos de contenido para los modelos relevantes
        ct_correspondencia = ContentType.objects.get_for_model(Correspondencia)
        ct_contacto = ContentType.objects.get_for_model(Contacto)
        
        # Asignar permisos al grupo
        permisos = [
            # Permisos de Correspondencia
            'add_correspondencia', 'change_correspondencia', 'view_correspondencia', 'delete_correspondencia',
            'view_own_correspondencia', 'change_own_correspondencia', 'view_office_correspondencia', 'distribute_correspondencia',
            # Permisos de Contacto
            'add_contacto', 'change_contacto', 'view_contacto', 'delete_contacto'
        ]
        
        for permiso in permisos:
            try:
                if permiso.startswith('add_') or permiso.startswith('change_') or permiso.startswith('view_') or permiso.startswith('delete_'):
                    ct = ct_correspondencia if 'correspondencia' in permiso else ct_contacto
                    perm = Permission.objects.get(codename=permiso, content_type=ct)
                    grupo.permissions.add(perm)
            except Permission.DoesNotExist:
                print(f"Permiso {permiso} no encontrado")
        
        print(f"Grupo 'Ventanilla Única' creado y configurado")
    else:
        print(f"Grupo 'Ventanilla Única' ya existía")
    
    # Asignar al menos un usuario al grupo
    admin_users = User.objects.filter(is_staff=True)
    if admin_users.exists():
        admin = admin_users.first()
        admin.groups.add(grupo)
        print(f"Usuario {admin.username} asignado al grupo 'Ventanilla Única'")
    
    return grupo

def crear_perfiles_usuario():
    """Crea perfiles de usuario y asigna oficinas a los usuarios existentes"""
    print("Asignando oficinas a usuarios...")
    
    # Obtener usuarios y oficinas
    usuarios = User.objects.filter(is_active=True)
    oficinas = OficinaProductora.objects.all()
    
    if not usuarios.exists():
        print("ERROR: No hay usuarios en el sistema.")
        return []
    
    if not oficinas.exists():
        print("ERROR: No hay oficinas en el sistema.")
        return []
    
    perfiles_creados = []
    
    # Asignar oficinas a usuarios
    for usuario in usuarios:
        # Verificar si ya tiene perfil
        if hasattr(usuario, 'perfil'):
            print(f"El usuario {usuario.username} ya tiene perfil asociado a {usuario.perfil.oficina}")
            perfiles_creados.append(usuario.perfil)
            continue
        
        # Asignar oficina aleatoria
        oficina = random.choice(oficinas)
        perfil = PerfilUsuario.objects.create(
            user=usuario,
            oficina=oficina
        )
        
        perfiles_creados.append(perfil)
        print(f"Perfil creado: {usuario.username} - {oficina.nombre}")
    
    return perfiles_creados

def main():
    """Función principal que ejecuta la carga de datos"""
    print("Iniciando carga de datos para el módulo de correspondencia...")
    
    # Crear grupo de ventanilla única
    crear_grupo_ventanilla()
    
    # Crear perfiles de usuario
    perfiles = crear_perfiles_usuario()
    
    # Crear contactos si no existen
    contactos = Contacto.objects.all()
    if not contactos.exists():
        contactos = crear_contactos(20)
    else:
        print(f"Ya existen {contactos.count()} contactos en la base de datos")
    
    # Crear correspondencia
    correspondencia = crear_correspondencia(30)
    
    # Crear distribuciones
    distribuciones = crear_distribuciones(correspondencia, 15)
    
    # Crear adjuntos
    adjuntos = crear_adjuntos(correspondencia, 20)
    
    print("Carga de datos completada!")
    print(f"Resumen: {Contacto.objects.count()} contactos, {Correspondencia.objects.count()} correspondencias, "
          f"{DistribucionInterna.objects.count()} distribuciones, {AdjuntoCorrespondencia.objects.count()} adjuntos")

if __name__ == "__main__":
    main() 