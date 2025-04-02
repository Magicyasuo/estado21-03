from documentos.models import TipoDocumentoCorrespondencia

# Crear tipos de documentos comunes
tipos = [
    {'codigo': 'OFI', 'nombre': 'Oficio', 'descripcion': 'Comunicación escrita de carácter oficial'},
    {'codigo': 'MEM', 'nombre': 'Memorando', 'descripcion': 'Comunicación escrita de carácter interno'},
    {'codigo': 'CIR', 'nombre': 'Circular', 'descripcion': 'Comunicación interna o externa dirigida a varias personas'},
    {'codigo': 'RES', 'nombre': 'Resolución', 'descripcion': 'Acto administrativo con carácter obligatorio'},
    {'codigo': 'CIT', 'nombre': 'Citación', 'descripcion': 'Documento para citar a una reunión o evento'},
    {'codigo': 'INF', 'nombre': 'Informe', 'descripcion': 'Documento que contiene información detallada sobre un tema'},
]

for tipo in tipos:
    TipoDocumentoCorrespondencia.objects.get_or_create(
        codigo=tipo['codigo'],
        defaults={'nombre': tipo['nombre'], 'descripcion': tipo['descripcion']}
    )
    print(f'Tipo de documento {tipo["codigo"]} creado o existente') 