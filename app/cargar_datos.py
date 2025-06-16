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
    "¿Se han identificado y documentado todos los peligros potenciales en el proceso de producción?",
    "¿Se han establecido límites críticos para cada punto de control crítico (PCC)?",
    "¿Se realiza un monitoreo regular de los PCC para asegurar que se mantengan dentro de los límites críticos establecidos?",
    "¿Se cuenta con un plan de acción documentado para abordar desviaciones de los límites críticos?",
    "¿Se llevan registros adecuados de todas las actividades de monitoreo y verificación de los PCC?",
    "¿Se realizan auditorías internas periódicas para evaluar la eficacia del sistema HACCP implementado?",
    "¿Se proporciona capacitación regular al personal sobre las prácticas y principios de HACCP?"
]

for texto in preguntas:
    PreguntaPredefinida.objects.get_or_create(texto=texto, checklist=checklist)

print("Checklist y preguntas creadas correctamente.")