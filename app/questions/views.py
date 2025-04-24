from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.core.paginator import Paginator 
from weasyprint import HTML
import unicodedata
import re
from django.utils.text import slugify
from .forms import AuditoriaForm
from .models import Auditoria, PreguntaPredefinida, Respuesta, Checklist 

@login_required
def home(request):
    return render(request, 'questions/home.html')

def crear_auditoria(request):
    if request.method == 'POST':
        form = AuditoriaForm(request.POST)
        if form.is_valid():
            print("Checklist enviado:", form.cleaned_data['checklist'])
            auditoria = form.save()
            print(auditoria)
            # Crear preguntas predefinidas para la auditoria
            preguntas = PreguntaPredefinida.objects.filter(checklist=auditoria.checklist)
            for pregunta in preguntas:
                Respuesta.objects.create(
                    pregunta_predefinida=pregunta,
                    auditoria=auditoria,
                    tipo_respuesta='correcto',
                    puntaje=0
                )
            return redirect('checklist_auditoria', auditoria_id=auditoria.id,)
        else:
            print(form.errors)
    else:
        form = AuditoriaForm()
    return render(request, 'questions/nueva_auditoria.html', {'form': form})

@login_required
def checklist_auditoria(request, auditoria_id):
    auditoria = get_object_or_404(Auditoria, id=auditoria_id)
    preguntas = PreguntaPredefinida.objects.filter(checklist=auditoria.checklist)
    if request.method == 'POST':
        for pregunta in preguntas:
            tipo_respuesta = request.POST.get(f'pregunta_{pregunta.id}')
            observaciones = request.POST.get(f'observaciones-text_{pregunta.id}', '')
            if tipo_respuesta not in dict(Respuesta.OPCIONES_RESPUESTA):
                print(f"Respuesta no válida para la pregunta {pregunta.id}: {tipo_respuesta}")
                continue

            respuesta, created = Respuesta.objects.get_or_create(
                pregunta_predefinida=pregunta,
                auditoria=auditoria,
                defaults={'tipo_respuesta': tipo_respuesta, 'observaciones': observaciones}
            )
            if not created:
                respuesta.tipo_respuesta = tipo_respuesta
                respuesta.observaciones = observaciones  # Actualiza las observaciones
                respuesta.save()
        return redirect('resultado_auditoria', auditoria_id=auditoria.id)
    return render(request, 'questions/checklist_auditoria.html', {
        'auditoria': auditoria,
        'preguntas': preguntas
    })


@login_required
def resultado_auditoria(request, auditoria_id):
    auditoria = get_object_or_404(Auditoria, id=auditoria_id)
    preguntas = PreguntaPredefinida.objects.filter(checklist=auditoria.checklist)
    respuestas = Respuesta.objects.filter(auditoria=auditoria)
    resultados = Respuesta.calcular_resultados(auditoria)

    if request.method == 'POST':
        # Captura el comentario general
        comentario_general = request.POST.get('comentario_general', '')
        request.session['comentario_general'] = comentario_general  # Guardar en la sesión

        # Procesa las respuestas
        for pregunta in preguntas:
            tipo_respuesta = request.POST.get(f'pregunta_{pregunta.id}')
            if tipo_respuesta:
                respuesta, created = Respuesta.objects.get_or_create(
                    pregunta_predefinida=pregunta,
                    auditoria=auditoria,
                    defaults={'tipo_respuesta': tipo_respuesta}
                )
                if not created:
                    respuesta.tipo_respuesta = tipo_respuesta
                    respuesta.save()

        # Redirigir a la vista que genera el PDF
        return redirect('resultado_auditoria_pdf', auditoria_id=auditoria.id)

    return render(request, 'questions/resultado_auditoria.html', {
        'auditoria': auditoria,
        'preguntas': preguntas,
        'respuestas': respuestas,
        'resultados': resultados,
        'comentario_general': '',
        'usa_puntaje': auditoria.checklist.usa_puntaje,
    })


from django.db.models import Count

@login_required
def lista_auditorias(request):
    filtro = request.GET.get('filtro')
    valor = request.GET.get('valor')

    auditorias = Auditoria.objects.all().order_by('-fecha')

    # Aplicar filtro
    if filtro == 'cliente' and valor:
        auditorias = auditorias.filter(cliente=valor)
    elif filtro == 'checklist' and valor:
        auditorias = auditorias.filter(checklist__nombre=valor)

    # Procesar puntaje por auditoría
    auditorias_con_puntaje = []
    for auditoria in auditorias:
        respuestas = Respuesta.objects.filter(auditoria=auditoria)
        if auditoria.checklist and auditoria.checklist.usa_puntaje:
            puntaje_total = respuestas.aggregate(Sum('puntaje'))['puntaje__sum'] or 0
            puntaje_maximo = respuestas.count() * 1
            porcentaje = (puntaje_total / puntaje_maximo) * 100 if puntaje_maximo > 0 else 0
            resultado = "ACEPTADO" if porcentaje >= 75 else "NO ACEPTADO"
        else:
            puntaje_total = "SIN PUNTAJE"
            resultado = "INFORME DEL AUDITOR"

        auditorias_con_puntaje.append({
            'auditoria': auditoria,
            'puntaje_total': puntaje_total,
            'resultado': resultado,
            'checklist': auditoria.checklist
        })

    # Obtener listas únicas de clientes y tipos de checklist
    clientes_unicos = Auditoria.objects.values_list('cliente', flat=True).distinct()
    tipos_checklist_unicos = Checklist.objects.values_list('nombre', flat=True).distinct()

    # Paginación
    paginator = Paginator(auditorias_con_puntaje, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Total de auditorías (para numeración descendente)
    total = paginator.count

    # Agregamos índice descendente a cada auditoría
    start_index = page_obj.start_index()
    for idx, item in enumerate(page_obj, start=start_index):
        item['numero_descendente'] = total - idx + 1


    return render(request, 'questions/lista_auditorias.html', {
        'auditorias': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'clientes': clientes_unicos,
        'tipos_checklist': tipos_checklist_unicos,
        'filtro_seleccionado': filtro,
        'valor_seleccionado': valor,
    })

@login_required
def eliminar_auditoria(request, auditoria_id):
    auditoria = get_object_or_404(Auditoria, id=auditoria_id)

    if request.method == 'POST':
        auditoria.delete()
        messages.success(request, 'La auditoría ha sido eliminada exitosamente.')
        return redirect('lista_auditorias')
    return render(request, 'questions/confirmar_eliminacion.html', {'auditoria': auditoria})

def limpiar_nombre(nombre):
    # Normaliza acentos y elimina caracteres problemáticos
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', 'ignore').decode('ascii')
    nombre = re.sub(r'[^\w\s-]', '', nombre).strip().lower()
    return slugify(nombre)

@login_required
def resultado_auditoria_pdf(request, auditoria_id):
    auditoria = get_object_or_404(Auditoria, id=auditoria_id)
    respuestas = Respuesta.objects.filter(auditoria=auditoria).select_related('pregunta_predefinida')
    checklist = auditoria.checklist
    usa_puntaje = checklist.usa_puntaje
    comentario_general = request.session.get('comentario_general', '')

    resultados = Respuesta.calcular_resultados(auditoria)
    total_puntaje = resultados.get('puntaje_obtenido', 'Sin Puntaje')
    total_maximo = resultados.get('puntaje_maximo', '—')
    porcentaje = resultados.get('porcentaje_obtenido', '—')

    # Render del HTML para el PDF
    template = get_template('questions/pdf_resultado_auditoria.html')
    html_string = template.render({
        'auditoria': auditoria,
        'respuestas': respuestas,
        'usa_puntaje': usa_puntaje,
        'comentario_general': comentario_general,
        'total_puntaje': total_puntaje,
        'total_maximo': total_maximo,
        'porcentaje': porcentaje,
        'resultados': resultados,
    })

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    # Limpiar nombre del cliente y checklist
    cliente_slug = limpiar_nombre(str(auditoria.cliente))
    checklist_slug = limpiar_nombre(str(auditoria.checklist.nombre))

    nombre_archivo = f"{auditoria.fecha.strftime('%Y-%m-%d')}_{cliente_slug}_{checklist_slug}.pdf"

    # Guardar PDF en el modelo
    pdf_file = ContentFile(pdf)
    auditoria.resultado_pdf.save(nombre_archivo, pdf_file)
    auditoria.save()

    return redirect('lista_auditorias')


def obtener_preguntas_por_checklist(request):
    checklist_id = request.GET.get('checklist_id')
    print(f"ID del checklist recibido: {checklist_id}")
    preguntas = PreguntaPredefinida.objects.filter(checklist_id=checklist_id).values('id', 'texto')
    data = list(preguntas)
    print(f"Cantidad de preguntas devueltas: {len(data)}")
    return JsonResponse(data, safe=False)

def modulo_construccion(request):
    return render(request,'questions/modulo_construccion.html')
