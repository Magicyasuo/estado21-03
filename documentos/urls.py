from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import FUIDCreateView, FUIDUpdateView, lista_fuids
from django.urls import path
from .views import detalle_fuid
from .views import crear_ficha_paciente
from .views import lista_fichas_paciente
from .views import EditarFichaPaciente, detalle_ficha_paciente
from .views import ListaFichasAPIView
from .views import export_fuid_to_excel
from .views import estadisticas_fuids, estadisticas_registros, estadisticas_pacientes,  pagina_estadisticas, obtener_usuarios
from django.views.generic import TemplateView
from .views import registros_api
from .views import registros_api_con_id
from .views import registros_api, ver_documento
from .views import soporte_view, panel_view, registros_fuid_json
# Importar las vistas del módulo de correspondencia
from .views_correspondencia import (
    lista_correspondencia, crear_correspondencia, detalle_correspondencia,
    editar_correspondencia, anular_correspondencia, distribuir_correspondencia,
    lista_contactos, crear_contacto, editar_contacto, detalle_contacto, eliminar_contacto,
    lista_distribuciones, recibir_distribucion, redistribuir_correspondencia,
    cargar_subseries_ajax, buscar_contactos_ajax, crear_contacto_ajax,
    actualizar_campos_tipo_correspondencia, gestionar_ventanilla_unica,
    eliminar_correspondencia, editar_distribucion, finalizar_distribucion,
    eliminar_distribucion, agregar_adjunto, eliminar_adjunto,
    radicar_correspondencia, firmar_correspondencia
)








# from .views import export_fuids_to_excel
from .views import mi_error_403
handler403 = 'documentos.views.mi_error_403'

urlpatterns = [
    path('', views.lista_registros, name='lista_registros'),  # Página principal de registros
    path('nuevo/', views.crear_registro, name='crear_registro'),
    path('<int:pk>/editar/', views.editar_registro, name='editar_registro'),
    path('<int:pk>/eliminar/', views.eliminar_registro, name='eliminar_registro'),
    path('cargar_subseries/', views.cargar_subseries, name='cargar_subseries'),
    path('cargar_series/', views.cargar_series, name='cargar_series'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registros/completo/', views.lista_completa_registros, name='lista_completa_registros'),
    path('fuids/', views.lista_fuids, name='lista_fuids'),
    path('documento/<int:registro_id>/', ver_documento, name='ver_documento'),  # <-- Agregar esta línea
    #fuids y registros
    path('fuids/<int:fuid_id>/form_registro/', views.form_registro_fuid_ajax, name='form_registro_fuid_ajax'),
    path('fuids/<int:fuid_id>/crear_registro/', views.crear_registro_fuid_ajax, name='crear_registro_fuid_ajax'),
    path('fuids/', lista_fuids, name='lista_fuids'),
    path('soporte/', soporte_view, name='soporte'),
    path('fuids/<int:fuid_id>/registros/', registros_fuid_json, name='registros_fuid_json'),

    path('fuids/create/', FUIDCreateView.as_view(), name='crear_fuid'),
    path('fuids/edit/<int:pk>/', FUIDUpdateView.as_view(), name='editar_fuid'),
    path('fuids/detalle/<int:pk>/', detalle_fuid, name='detalle_fuid'),
    path('welcome/', views.welcome_view, name='welcome'),
    path('panel/', views.panel_view, name='panel'),

    path('crear-ficha/', crear_ficha_paciente, name='crear_ficha'),
    path('lista-fichas/', lista_fichas_paciente, name='lista_fichas'),
    path('editar-ficha/<int:consecutivo>/', EditarFichaPaciente.as_view(), name='editar_ficha'),
    path('detalle-ficha/<int:consecutivo>/', detalle_ficha_paciente, name='detalle_ficha'),
    path('api/lista-fichas/', ListaFichasAPIView.as_view(), name='api_lista_fichas'),
    path('fuid/<int:pk>/export-excel/', export_fuid_to_excel, name='export_fuid_to_excel'),
    path('fuids/<int:fuid_id>/agregar_registro/', views.agregar_registro_a_fuid, name='agregar_registro_a_fuid'),
      # Otras rutas de tu app...
    path('estadisticas/pacientes/', views.estadisticas_pacientes, name='estadisticas_pacientes'),
    path('estadisticas/registros/', views.estadisticas_pacientes, name='estadisticas_pacientes'),
    path('estadisticas/fuids/', estadisticas_fuids, name='estadisticas_fuids'),
    path('estadisticas/', pagina_estadisticas, name='pagina_estadisticas'),
    path('api/usuarios/', obtener_usuarios, name='obtener_usuarios'),
    # path('adminlte/', TemplateView.as_view(template_name="admin-lte/index.html"), name="adminlte_index"),
    path('', TemplateView.as_view(template_name="adminlte/base.html"), name="home"),
    path('api/registros/', registros_api, name='registros_api'),
    path('api/registros_api_completo/', views.registros_api_completo, name='registros_api_completo'),
    path('registros_api_con_id/', registros_api_con_id, name='registros_api_con_id'),
    path('fuids/<int:fuid_id>/editar_registro/<int:registro_id>/', views.editar_registro_de_fuid, name='editar_registro_de_fuid'),

    # URLs para el módulo de correspondencia
    path('correspondencia/', lista_correspondencia, name='lista_correspondencia'),
    path('correspondencia/crear/', crear_correspondencia, name='crear_correspondencia'),
    path('correspondencia/<int:pk>/', detalle_correspondencia, name='detalle_correspondencia'),
    path('correspondencia/<int:pk>/editar/', editar_correspondencia, name='editar_correspondencia'),
    path('correspondencia/<int:pk>/anular/', anular_correspondencia, name='anular_correspondencia'),
    path('correspondencia/<int:pk>/distribuir/', distribuir_correspondencia, name='distribuir_correspondencia'),
    path('correspondencia/<int:pk>/eliminar/', eliminar_correspondencia, name='eliminar_correspondencia'),
    
    # URLs para gestión de contactos
    path('correspondencia/contactos/', lista_contactos, name='lista_contactos'),
    path('correspondencia/contactos/crear/', crear_contacto, name='crear_contacto'),
    path('correspondencia/contactos/<int:pk>/editar/', editar_contacto, name='editar_contacto'),
    path('correspondencia/contactos/<int:pk>/', detalle_contacto, name='detalle_contacto'),
    path('correspondencia/contactos/<int:pk>/eliminar/', eliminar_contacto, name='eliminar_contacto'),
    
    # URLs para distribución y recepción
    path('correspondencia/distribuciones/', lista_distribuciones, name='lista_distribuciones'),
    path('correspondencia/distribuciones/<int:pk>/recibir/', recibir_distribucion, name='recibir_distribucion'),
    path('correspondencia/distribuciones/<int:pk>/redistribuir/', redistribuir_correspondencia, name='redistribuir_correspondencia'),
    path('correspondencia/distribuciones/<int:pk>/editar/', editar_distribucion, name='editar_distribucion'),
    path('correspondencia/distribuciones/<int:pk>/finalizar/', finalizar_distribucion, name='finalizar_distribucion'),
    path('correspondencia/distribuciones/<int:pk>/eliminar/', eliminar_distribucion, name='eliminar_distribucion'),

    # URLs para adjuntos
    path('correspondencia/<int:pk>/adjuntos/agregar/', agregar_adjunto, name='agregar_adjunto'),
    path('correspondencia/adjuntos/<int:pk>/eliminar/', eliminar_adjunto, name='eliminar_adjunto'),

    # URLs para funcionalidades AJAX
    path('correspondencia/ajax/cargar-subseries/', cargar_subseries_ajax, name='cargar_subseries_ajax'),
    path('correspondencia/ajax/buscar-contactos/', buscar_contactos_ajax, name='buscar_contactos_ajax'),
    path('correspondencia/ajax/crear-contacto/', crear_contacto_ajax, name='crear_contacto_ajax'),
    path('correspondencia/ajax/actualizar-campos-tipo/', actualizar_campos_tipo_correspondencia, name='actualizar_campos_tipo_correspondencia'),

    # URLs para administración
    path('correspondencia/admin/gestionar-ventanilla/', gestionar_ventanilla_unica, name='gestionar_ventanilla_unica'),

    # URLs para radicar y firmar correspondencia
    path('correspondencia/<int:pk>/radicar/', radicar_correspondencia, name='radicar_correspondencia'),
    path('correspondencia/<int:pk>/firmar/', firmar_correspondencia, name='firmar_correspondencia'),

    







    






    
    


    # path('fuids/<int:fuid_id>/exportar/', exportar_fuid_excel, name='exportar_fuid_excel'),
    # path('export/fuids/', export_fuids_to_excel, name='export_fuids'),


   # path('login/', views.login_view, name='login'),
]
