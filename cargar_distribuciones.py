#!/usr/bin/env python
"""
Script para cargar distribuciones de prueba para el módulo de correspondencia.
"""
import os
import django
import random
from datetime import timedelta

# Configurar entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_document_management.settings')
django.setup()

from django.utils import timezone
from django.contrib.auth.models import User
from documentos.models import Correspondencia, DistribucionInterna, OficinaProductora
from django.db.models import Q

def cargar_distribuciones(cantidad=50):
    """Crear distribuciones de prueba para correspondencia existente"""
    # Obtener correspondencia existente que pueda ser distribuida (no anulada)
    correspondencia_distribuible = Correspondencia.objects.filter(
        anulado=False
    ).filter(
        Q(tipo_correspondencia='INT') | Q(oficina_destinatario__isnull=False)
    )
    
    # Verificar que haya correspondencia para distribuir
    if not correspondencia_distribuible.exists():
        print("No hay correspondencia disponible para distribuir.")
        return
    
    print(f"Correspondencia disponible para distribuir: {correspondencia_distribuible.count()}")
    
    # Obtener oficinas disponibles
    oficinas = OficinaProductora.objects.all()
    if not oficinas.exists() or oficinas.count() < 2:
        print("Se necesitan al menos 2 oficinas para crear distribuciones.")
        return
    
    print(f"Oficinas disponibles: {oficinas.count()}")
    
    # Obtener usuarios
    usuarios = User.objects.filter(is_active=True)
    if not usuarios.exists():
        print("No hay usuarios activos para asignar a las distribuciones.")
        return
    
    print(f"Usuarios disponibles: {usuarios.count()}")
    
    # Estados para las distribuciones
    estados = ['PEN', 'REC', 'FIN']
    
    # Mensajes por defecto
    mensajes_instrucciones = [
        "Favor revisar y dar trámite urgente",
        "Para su conocimiento y fines pertinentes",
        "Requiere respuesta en los próximos días",
        "Archivar según TRD",
        "Analizar y dar respuesta según lo solicitado",
        "Dar trámite según procedimiento establecido",
        "Para revisión y firma",
        "Responder al remitente con copia a esta oficina"
    ]
    
    mensajes_recepcion = [
        "Recibido conforme",
        "Documento completo y en buen estado",
        "Pendiente de revisión",
        "Se procederá según lo indicado",
        "Recibido con observaciones",
        "Se dará prioridad a este trámite",
        "Recibido para archivo",
        "En proceso de análisis"
    ]
    
    # Contadores
    distribuciones_creadas = 0
    distribuciones_existentes = 0
    
    # Crear distribuciones aleatorias
    for _ in range(cantidad):
        # Seleccionar correspondencia aleatoria
        correspondencia = random.choice(correspondencia_distribuible)
        
        # Determinar oficina de origen según tipo de correspondencia
        if correspondencia.tipo_correspondencia == 'ENT':
            # Para correspondencia de entrada, la oficina de origen es la destinataria
            oficina_origen = correspondencia.oficina_destinatario
        elif correspondencia.tipo_correspondencia == 'INT':
            # Para correspondencia interna, la oficina de origen es la remitente
            oficina_origen = correspondencia.oficina_remitente
        else:
            # Para correspondencia de salida, la oficina de origen es la remitente
            oficina_origen = correspondencia.oficina_remitente
        
        # Si no hay oficina de origen válida, continuar con la siguiente iteración
        if not oficina_origen:
            continue
        
        # Filtrar oficinas distintas de origen para destino
        posibles_destinos = oficinas.exclude(id=oficina_origen.id)
        if not posibles_destinos.exists():
            continue
        
        oficina_destino = random.choice(posibles_destinos)
        
        # Evitar crear distribuciones duplicadas para la misma correspondencia y destino
        if DistribucionInterna.objects.filter(
            correspondencia=correspondencia,
            oficina_destino=oficina_destino
        ).exists():
            distribuciones_existentes += 1
            continue
        
        # Seleccionar estado y preparar datos según el estado
        estado = random.choice(estados)
        fecha_distribucion = timezone.now() - timedelta(days=random.randint(0, 30))
        usuario_creador = random.choice(usuarios)
        
        # Crear objeto de distribución
        distribucion = DistribucionInterna(
            correspondencia=correspondencia,
            oficina_origen=oficina_origen,
            oficina_destino=oficina_destino,
            fecha_distribucion=fecha_distribucion,
            instrucciones=random.choice(mensajes_instrucciones),
            estado=estado,
            creado_por=usuario_creador
        )
        
        # Si el estado no es pendiente, agregar datos de recepción
        if estado in ['REC', 'FIN']:
            distribucion.recibido_por = random.choice(usuarios)
            distribucion.fecha_recepcion = fecha_distribucion + timedelta(days=random.randint(1, 5))
            distribucion.observaciones_recepcion = random.choice(mensajes_recepcion)
        
        # Guardar la distribución
        distribucion.save()
        distribuciones_creadas += 1
        
        # Mostrar progreso cada 10 distribuciones
        if distribuciones_creadas % 10 == 0:
            print(f"Creadas {distribuciones_creadas} distribuciones...")
    
    print(f"\nResumen de la operación:")
    print(f"- Distribuciones creadas: {distribuciones_creadas}")
    print(f"- Distribuciones existentes (no creadas): {distribuciones_existentes}")
    print(f"- Total existente actual: {DistribucionInterna.objects.count()}")

if __name__ == "__main__":
    print("Iniciando carga de distribuciones de prueba...")
    cargar_distribuciones()
    print("Proceso completado.") 