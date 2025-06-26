from django.contrib import admin
from .models import PreguntaPredefinida, Cliente, Auditor, Auditoria, Respuesta, Checklist, Ppr, Referencia, Norma, TipoNorma, TipoSeccion, Haccp, Ref_haccp, NoConformidades, Ref_noconformidades, TipoAnalisisAgua, PlantaIndustrial, MuestraAgua, ResultadoAnalisisAgua

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
admin.site.register(NoConformidades)
admin.site.register(Ppr)
admin.site.register(Referencia)
admin.site.register(Ref_haccp)
admin.site.register(Ref_noconformidades)
admin.site.register(Respuesta)
admin.site.register(TipoNorma)
admin.site.register(TipoSeccion)
admin.site.register(TipoAnalisisAgua)
admin.site.register(PlantaIndustrial)
admin.site.register(MuestraAgua)
admin.site.register(ResultadoAnalisisAgua)




