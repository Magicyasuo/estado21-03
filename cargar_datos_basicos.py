#!/usr/bin/env python
import os
import sys

# Configuración del entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_document_management.settings')
import django
django.setup()

# Importar modelos después de configurar Django
from documentos.models import SerieDocumental, SubserieDocumental, EntidadProductora, UnidadAdministrativa, OficinaProductora
from django.contrib.auth.models import User

def crear_entidades_unidades_oficinas():
    """Crea entidades, unidades administrativas y oficinas productoras"""
    print("Creando estructura organizacional...")
    
    # Crear entidades productoras
    hospital, created = EntidadProductora.objects.get_or_create(nombre="Hospital General Del Norte")
    if created:
        print(f"Entidad creada: {hospital}")
    
    # Crear unidades administrativas
    unidades = [
        "Gerencia General",
        "Dirección Financiera",
        "Dirección Administrativa",
        "Dirección Médica",
        "Dirección de Talento Humano",
        "Dirección de Calidad"
    ]
    
    unidades_creadas = []
    for nombre in unidades:
        unidad, created = UnidadAdministrativa.objects.get_or_create(
            nombre=nombre,
            entidad_productora=hospital
        )
        unidades_creadas.append(unidad)
        if created:
            print(f"Unidad creada: {unidad}")
    
    # Crear oficinas productoras
    oficinas = {
        "Gerencia General": ["Secretaría de Gerencia", "Control Interno"],
        "Dirección Financiera": ["Contabilidad", "Tesorería", "Facturación", "Cartera"],
        "Dirección Administrativa": ["Compras", "Almacén", "Mantenimiento", "Servicios Generales"],
        "Dirección Médica": ["Urgencias", "Hospitalización", "Consulta Externa", "Cirugía", "UCI"],
        "Dirección de Talento Humano": ["Gestión Humana", "Nómina", "Salud Ocupacional"],
        "Dirección de Calidad": ["Gestión de Calidad", "Atención al Usuario", "Archivo Clínico"]
    }
    
    oficinas_creadas = []
    for unidad in unidades_creadas:
        if unidad.nombre in oficinas:
            for nombre_oficina in oficinas[unidad.nombre]:
                oficina, created = OficinaProductora.objects.get_or_create(
                    nombre=nombre_oficina,
                    unidad_administrativa=unidad
                )
                oficinas_creadas.append(oficina)
                if created:
                    print(f"Oficina creada: {oficina}")
    
    return oficinas_creadas

def crear_series_subseries():
    """Crea series y subseries documentales"""
    print("Creando series y subseries documentales...")
    
    # Series y subseries
    series_subseries = {
        "ACTAS": ["Actas de Comité", "Actas de Junta Directiva", "Actas de Entrega"],
        "CONTRATOS": ["Contratos de Prestación de Servicios", "Contratos de Suministro", "Convenios Interadministrativos"],
        "HISTORIAS CLÍNICAS": ["Historias de Pacientes", "Historias Ocupacionales"],
        "CORRESPONDENCIA": ["Correspondencia Enviada", "Correspondencia Recibida", "Correspondencia Interna"],
        "INFORMES": ["Informes de Gestión", "Informes a Entes de Control", "Informes Estadísticos"],
        "MANUALES": ["Manuales de Procedimientos", "Manuales de Calidad", "Manuales Técnicos"],
        "NÓMINA": ["Nómina Administrativa", "Nómina Asistencial"],
        "PROYECTOS": ["Proyectos de Infraestructura", "Proyectos de Investigación", "Proyectos de Inversión"],
        "RESOLUCIONES": ["Resoluciones Administrativas", "Resoluciones de Personal"]
    }
    
    series_creadas = []
    
    for nombre_serie, subseries in series_subseries.items():
        serie, created = SerieDocumental.objects.get_or_create(
            codigo=nombre_serie[:3],
            nombre=nombre_serie
        )
        series_creadas.append(serie)
        if created:
            print(f"Serie creada: {serie}")
        
        for nombre_subserie in subseries:
            subserie, created = SubserieDocumental.objects.get_or_create(
                codigo=f"{serie.codigo}-{subseries.index(nombre_subserie)+1}",
                nombre=nombre_subserie,
                serie=serie
            )
            if created:
                print(f"Subserie creada: {subserie}")
    
    return series_creadas

def crear_superusuario():
    """Crea un superusuario si no existe ninguno"""
    if not User.objects.filter(is_superuser=True).exists():
        print("Creando superusuario 'admin'...")
        User.objects.create_superuser('admin', 'admin@hospital.gov.co', 'admin123')
        print("Superusuario creado con éxito")
    else:
        print("Ya existe al menos un superusuario")

def main():
    """Función principal que ejecuta la carga de datos básicos"""
    print("Iniciando carga de datos básicos para el sistema...")
    
    # Crear superusuario
    crear_superusuario()
    
    # Crear estructura organizacional
    oficinas = crear_entidades_unidades_oficinas()
    
    # Crear series y subseries
    series = crear_series_subseries()
    
    print("\nCarga de datos básicos completada!")
    print(f"Resumen: {EntidadProductora.objects.count()} entidades, {UnidadAdministrativa.objects.count()} unidades, "
          f"{OficinaProductora.objects.count()} oficinas, {SerieDocumental.objects.count()} series, "
          f"{SubserieDocumental.objects.count()} subseries")

if __name__ == "__main__":
    main() 