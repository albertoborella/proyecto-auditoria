from django.contrib import admin
from .models import Auditor, Auditoria, Checklist, Cliente, Haccp, Norma, Ppr, PreguntaPredefinida, Referencia, Ref_haccp, Respuesta,  TipoNorma, TipoSeccion   

@admin.register(PreguntaPredefinida)
class PreguntaPredefinidaAdmin(admin.ModelAdmin):
    list_display = ('numero_pregunta', 'texto', 'texto_critico', 'checklist')
    list_filter = ('checklist', 'texto_critico')
    ordering = ('checklist', 'numero_pregunta')
    fields = ('numero_pregunta', 'texto', 'texto_critico', 'checklist')

class ChecklistAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

admin.site.register(Auditor)
admin.site.register(Auditoria)
admin.site.register(Checklist, ChecklistAdmin)
admin.site.register(Cliente)
admin.site.register(Haccp)
admin.site.register(Norma)
admin.site.register(Ppr)
admin.site.register(Referencia)
admin.site.register(Ref_haccp)
admin.site.register(Respuesta)
admin.site.register(TipoNorma)
admin.site.register(TipoSeccion)




