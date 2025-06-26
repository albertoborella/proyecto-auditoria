from django import template
from questions.models import Respuesta

register = template.Library()
@register.filter
def get_item(respuestas, pregunta_id):
    # Filtra las respuestas en lugar de obtener solo una
    respuestas_filtradas = respuestas.filter(pregunta_predefinida__id=pregunta_id)
    if respuestas_filtradas.exists():
        return respuestas_filtradas.first().tipo_respuesta  # Devuelve el tipo de respuesta de la primera respuesta
    return None

@register.filter
def filter_respuestas(respuestas, pregunta_id):
    return respuestas.filter(pregunta_predefinida__id=pregunta_id)


@register.filter
def get_respuesta(respuestas, pregunta):
    respuesta = respuestas.filter(pregunta_predefinida=pregunta).first()
    return respuesta.tipo_respuesta if respuesta else ''

@register.filter
def get_observaciones(auditoria, pregunta_id):
    """
    Obtiene las observaciones de la respuesta para una pregunta específica en una auditoría.
    """
    try:
        respuesta = Respuesta.objects.get(auditoria=auditoria, pregunta_predefinida_id=pregunta_id)
        return respuesta.observaciones
    except Respuesta.DoesNotExist:
        return None
    
@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})
