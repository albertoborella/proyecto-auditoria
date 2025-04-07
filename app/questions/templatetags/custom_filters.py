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