from django.urls import path
from .views import home, crear_auditoria, checklist_auditoria, resultado_auditoria, lista_auditorias, eliminar_auditoria, resultado_auditoria_pdf, obtener_preguntas_por_checklist

urlpatterns = [
    path('', home, name='home' ),
    path('nueva_auditoria/', crear_auditoria, name='nueva_auditoria'),
    path('resultado_auditoria/<int:auditoria_id>', resultado_auditoria, name='resultado_auditoria'),
    path('lista_auditorias/', lista_auditorias, name='lista_auditorias'),
    path('auditorias/<int:auditoria_id>/checklist/', checklist_auditoria, name='checklist_auditoria'),
    path('auditorias/eliminar/<int:auditoria_id>/', eliminar_auditoria, name='eliminar_auditoria'),
    path('auditorias/pdf/<int:auditoria_id>/', resultado_auditoria_pdf, name='resultado_auditoria_pdf'),
    path('ajax/preguntas/', obtener_preguntas_por_checklist, name='ajax_preguntas_checklist'),
]