import os
import django
import random

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_document_management.settings')
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from documentos.models import OficinaProductora, PerfilUsuario, Correspondencia

def crear_usuarios():
    # Obtener oficinas existentes
    oficinas = list(OficinaProductora.objects.all())
    
    if not oficinas:
        print("No hay oficinas disponibles. Cree oficinas primero.")
        return
    
    # Datos para los usuarios
    usuarios_datos = [
        {
            'username': 'usuario_oficina1',
            'password': 'password123',
            'email': 'usuario1@hospital.com',
            'first_name': 'Usuario',
            'last_name': 'Oficina 1',
            'is_staff': True,
        },
        {
            'username': 'usuario_oficina2',
            'password': 'password123',
            'email': 'usuario2@hospital.com',
            'first_name': 'Usuario',
            'last_name': 'Oficina 2',
            'is_staff': True,
        },
        {
            'username': 'usuario_oficina3',
            'password': 'password123',
            'email': 'usuario3@hospital.com',
            'first_name': 'Usuario',
            'last_name': 'Oficina 3',
            'is_staff': True,
        },
        {
            'username': 'usuario_oficina4',
            'password': 'password123',
            'email': 'usuario4@hospital.com',
            'first_name': 'Usuario',
            'last_name': 'Oficina 4',
            'is_staff': True,
        },
        {
            'username': 'usuario_oficina5',
            'password': 'password123',
            'email': 'usuario5@hospital.com',
            'first_name': 'Usuario',
            'last_name': 'Oficina 5',
            'is_staff': True,
        },
    ]
    
    # Crear usuarios y asignar oficinas
    print("Creando usuarios con oficinas...")
    
    for i, datos in enumerate(usuarios_datos):
        # Asignar una oficina diferente a cada usuario
        oficina = oficinas[i % len(oficinas)]
        
        # Comprobar si el usuario ya existe
        if User.objects.filter(username=datos['username']).exists():
            usuario = User.objects.get(username=datos['username'])
            print(f"El usuario {datos['username']} ya existe.")
        else:
            # Crear usuario nuevo
            usuario = User.objects.create_user(
                username=datos['username'],
                email=datos['email'],
                password=datos['password'],
                first_name=datos['first_name'],
                last_name=datos['last_name'],
            )
            usuario.is_staff = datos['is_staff']
            usuario.save()
            print(f"Usuario {datos['username']} creado.")
        
        # Comprobar si el perfil ya existe
        if hasattr(usuario, 'perfil'):
            # Actualizar la oficina si es diferente
            if usuario.perfil.oficina != oficina:
                usuario.perfil.oficina = oficina
                usuario.perfil.save()
                print(f"Actualizada oficina de {usuario.username} a {oficina.nombre}")
        else:
            # Crear perfil de usuario con la oficina asignada
            perfil = PerfilUsuario.objects.create(
                user=usuario,
                oficina=oficina
            )
            print(f"Perfil creado para {usuario.username} con oficina {oficina.nombre}")
        
        # Asignar permisos para correspondencia
        content_type = ContentType.objects.get_for_model(Correspondencia)
        permisos = Permission.objects.filter(content_type=content_type)
        
        for permiso in permisos:
            usuario.user_permissions.add(permiso)
        
        print(f"Asignados permisos de correspondencia a {usuario.username}")
    
    print("\nResumen de usuarios creados:")
    for usuario in User.objects.filter(username__startswith='usuario_oficina'):
        if hasattr(usuario, 'perfil'):
            print(f"{usuario.username} - Oficina: {usuario.perfil.oficina.nombre}")
        else:
            print(f"{usuario.username} - Sin oficina asignada")

if __name__ == "__main__":
    crear_usuarios() 