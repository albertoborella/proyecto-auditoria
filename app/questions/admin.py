from django.contrib import admin
from .models import PreguntaPredefinida, Cliente, Auditor, Auditoria, Respuesta

class PreguntaPredefinidaAdmin(admin.ModelAdmin):
    list_display = ('id', 'texto'
                    )
admin.site.register(PreguntaPredefinida,PreguntaPredefinidaAdmin)
admin.site.register(Cliente)
admin.site.register(Auditor)
admin.site.register(Auditoria)
admin.site.register(Respuesta)
