import os
import django

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")  # Cambia 'app' si tu settings.py está en otro lugar
django.setup()

from questions.models import Auditoria
from django.conf import settings

def verificar_pdfs():
    print("⏳ Verificando auditorías...")

    auditorias = Auditoria.objects.all()
    sin_pdf = []
    pdfs_no_existentes = []

    for a in auditorias:
        if not a.resultado_pdf:
            sin_pdf.append(a)
        else:
            ruta_absoluta = os.path.join(settings.MEDIA_ROOT, a.resultado_pdf.name)
            if not os.path.isfile(ruta_absoluta):
                pdfs_no_existentes.append((a, a.resultado_pdf.name))

    print(f"\n📄 Auditorías sin PDF asociado: {len(sin_pdf)}")
    for a in sin_pdf:
        print(f"  - ID {a.id} | {a.cliente} | {a.checklist} | {a.fecha}")

    print(f"\n🗑️ Auditorías con PDF faltante en disco: {len(pdfs_no_existentes)}")
    for a, nombre in pdfs_no_existentes:
        print(f"  - ID {a.id} | {a.cliente} | {a.checklist} | {a.fecha} | Ruta: {nombre}")

if __name__ == "__main__":
    verificar_pdfs()
