from django.urls import path
from .views import (home, crear_auditoria, checklist_auditoria, resultado_auditoria,
                    lista_auditorias, eliminar_auditoria, resultado_auditoria_pdf, 
                    obtener_preguntas_por_checklist, modulo_construccion, 
                    lista_ppr, crear_ppr, eliminar_ppr, 
                    listado_normas, agregar_norma,
                    lista_haccp, crear_haccp, eliminar_haccp, 
                    lista_nc, crear_nc, eliminar_nc,
                    listar_analisis, crear_y_editar_muestra_agua,
                    crear_unidad_productiva, listar_unidades_productivas,
                    editar_unidad_productiva, eliminar_unidad_productiva,
                    registro_muestra, detalle_muestra, editar_analito, listado_analisis,
                    registrar_ingreso_leche, listado_ingresos, editar_ingreso_leche,
                    )

urlpatterns = [
    path('', home, name='home' ),
    path('nueva_auditoria/', crear_auditoria, name='nueva_auditoria'),
    path('resultado_auditoria/<int:auditoria_id>', resultado_auditoria, name='resultado_auditoria'),
    path('lista_auditorias/', lista_auditorias, name='lista_auditorias'),
    path('auditorias/<int:auditoria_id>/checklist/', checklist_auditoria, name='checklist_auditoria'),
    path('auditorias/eliminar/<int:auditoria_id>/', eliminar_auditoria, name='eliminar_auditoria'),
    path('auditorias/pdf/<int:auditoria_id>/', resultado_auditoria_pdf, name='resultado_auditoria_pdf'),
    path('ajax/preguntas/', obtener_preguntas_por_checklist, name='ajax_preguntas_checklist'),
    path('normas_listar/', listado_normas, name='normas_listar'),
    path('normas_agregar/', agregar_norma, name='normas_agregar'),
    path('construccion/', modulo_construccion, name='construccion'),
    path('ppr/lista/', lista_ppr, name='lista_ppr'),
    path('ppr/crear/', crear_ppr, name='crear_ppr'),
    path('ppr/<int:pk>/eliminar/', eliminar_ppr, name='eliminar_ppr'),
    path('haccp/lista/', lista_haccp, name='lista_haccp'),
    path('haccp/crear/', crear_haccp, name='crear_haccp'),
    path('haccp/<int:pk>/eliminar/', eliminar_haccp, name='eliminar_haccp'),
    path('nc/lista/', lista_nc, name='lista_nc'),
    path('nc/crear/', crear_nc, name='crear_nc'),
    path('nc/<int:pk>/eliminar/', eliminar_nc, name='eliminar_nc'),
    
    path('listar_analisis_agua/', listar_analisis, name='listar_analisis_agua'),
    path('muestra_agua/', crear_y_editar_muestra_agua, name='crear_muestra_agua'),
    path('muestra_agua_editar/<int:muestra_id>/', crear_y_editar_muestra_agua, name='editar_muestra_agua'),
    
    path('crearUnidadProductiva/', crear_unidad_productiva, name='crear_unidad_productiva'),
    path('listarUnidadesProductivas/', listar_unidades_productivas, name='listar_unidades_productivas'),
    path('editarUnidadProductiva/<int:pk>/', editar_unidad_productiva, name='editar_unidad_productiva'),
    path('eliminarUnidadProductiva/<int:pk>', eliminar_unidad_productiva, name='eliminar_unidad_productiva'),

    path('registro/', registro_muestra, name='registro_muestra'),
    path('registro/<int:muestra_id>/', registro_muestra, name='registro_muestra'),
    path('muestras/<int:pk>/', detalle_muestra, name='detalle_muestra'),
    path('analito/<int:pk>/editar/', editar_analito, name='editar_analito'),
    path('analisis/listado/', listado_analisis, name='listado_analisis'),

    path('ingreso_leche/', registrar_ingreso_leche,  name='ingreso_leche'),
    path('ingreso_leche/listado/', listado_ingresos, name='listado_ingresos'),
    path('ingresos/<int:ingreso_id>/editar/', editar_ingreso_leche, name='editar_ingreso'),

]

