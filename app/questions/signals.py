import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from questions.models import Auditoria

@receiver(post_delete, sender=Auditoria)
def eliminar_pdf_asociado(sender, instance, **kwargs):
    if instance.resultado_pdf and instance.resultado_pdf.path:
        if os.path.isfile(instance.resultado_pdf.path):
            os.remove(instance.resultado_pdf.path)
