import os
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# Inicializar entorno Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")  # ajustá si tu settings tiene otro nombre
application = get_wsgi_application()

from questions.models import Auditoria

def limpiar_pdfs_huerfanos():
    media_path = os.path.join(settings.MEDIA_ROOT, 'auditorias')
    archivos_en_uso = set(
        Auditoria.objects.exclude(resultado_pdf='').values_list('resultado_pdf', flat=True)
    )

    eliminados = []
    for archivo in os.listdir(media_path):
        ruta_relativa = f'auditorias/{archivo}'
        if ruta_relativa not in archivos_en_uso:
            ruta_completa = os.path.join(media_path, archivo)
            os.remove(ruta_completa)
            eliminados.append(archivo)

    if eliminados:
        print("Archivos eliminados:")
        for f in eliminados:
            print(f" - {f}")
    else:
        print("No se encontraron archivos huérfanos.")

if __name__ == "__main__":
    limpiar_pdfs_huerfanos()
