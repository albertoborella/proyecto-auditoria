import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')  
django.setup()

from questions.models import Checklist, PreguntaPredefinida

# Crear un checklist
checklist, creado = Checklist.objects.get_or_create(nombre="HACCP")

# Crear preguntas asociadas
preguntas = [
    "¿Se controla la temperatura de almacenamiento?",
    "¿Los empleados usan ropa adecuada?",
    "¿Se registran las limpiezas diarias?",
]

for texto in preguntas:
    PreguntaPredefinida.objects.get_or_create(texto=texto, checklist=checklist)

print("Checklist y preguntas creadas correctamente.")