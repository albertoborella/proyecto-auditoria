from django.contrib import admin
from .models import PreguntaPredefinida, Cliente, Auditor, Auditoria, Respuesta, Checklist

@admin.register(PreguntaPredefinida)
class PreguntaPredefinidaAdmin(admin.ModelAdmin):
    list_display = ('numero_pregunta', 'texto', 'texto_critico', 'checklist')
    list_filter = ('checklist', 'texto_critico')
    search_fields = ('texto',)
    ordering = ('checklist', 'numero_pregunta')

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

admin.site.register(Cliente)
admin.site.register(Auditor)
admin.site.register(Auditoria)
admin.site.register(Respuesta)
