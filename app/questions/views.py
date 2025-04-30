from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.http import JsonResponse
from django.core.files.base import ContentFile
from django.core.paginator import Paginator 
from django.db.models import Q  # Para búsquedas flexibles
from weasyprint import HTML
import unicodedata
import re
from django.forms import modelformset_factory
from django.utils.text import slugify
from .forms import AuditoriaForm, PprForm, ReferenciaFormSet
from .models import Auditoria, PreguntaPredefinida, Respuesta, Checklist, Ppr, Referencia, Cliente

def superuser_required(view_func):
    decorated_view_func = user_passes_test(lambda user: user.is_superuser)(view_func)
    return decorated_view_func

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



@login_required
def lista_auditorias(request):
    filtro = request.GET.get('filtro')
    valor = request.GET.get('valor')
    auditorias = Auditoria.objects.all().order_by('-fecha')
    # Aplicar filtro
    if filtro == 'cliente' and valor:
        # Obtener el cliente por nombre
        try:
            cliente_id = Cliente.objects.get(nombre=valor).id
            auditorias = auditorias.filter(cliente_id=cliente_id)
        except Cliente.DoesNotExist:
            auditorias = auditorias.none()  # Si no existe el cliente, no mostrar auditorías
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
    clientes_unicos = Cliente.objects.values('nombre').distinct()
    tipos_checklist_unicos = Checklist.objects.values_list('nombre', flat=True).distinct()
    # Paginación
    paginator = Paginator(auditorias_con_puntaje, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # Total de auditorías (para numeración descendente)
    total = paginator.count
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

@superuser_required
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

@superuser_required
def crear_ppr(request):
    if request.method == 'POST':
        ppr_form = PprForm(request.POST)
        formset = ReferenciaFormSet(request.POST, prefix='referencia_set')
        if ppr_form.is_valid() and formset.is_valid():
            ppr = ppr_form.save()
            formset.instance = ppr
            formset.save()
            return redirect('lista_ppr')
    else:
        ppr_form = PprForm()
        formset = ReferenciaFormSet(prefix='referencia_set')

    return render(request, 'questions/crear_ppr.html', {
        'ppr_form': ppr_form,
        'formset': formset
    })


def lista_ppr(request):
    query = request.GET.get('q', '')  # 'q' será el nombre del input de búsqueda
    pprs = Ppr.objects.prefetch_related('referencias').all().order_by('numero')

    if query:
        pprs = pprs.filter(Q(requisito__icontains=query))

    paginator = Paginator(pprs, 5)  # 5 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,  # Para mantener el texto buscado en el input
    }

    return render(request, 'questions/lista_ppr.html', context)


@superuser_required
def editar_ppr(request, pk):
    ppr = get_object_or_404(Ppr, pk=pk)

    # Redefinimos el formset para edición con extra=0
    ReferenciaFormSetEdit = modelformset_factory(
        Referencia,
        fields=('texto',),
        extra=0,
        can_delete=True
    )

    if request.method == 'POST':
        ppr_form = PprForm(request.POST, instance=ppr)
        formset = ReferenciaFormSetEdit(request.POST, queryset=ppr.referencias.all())

        if ppr_form.is_valid() and formset.is_valid():
            ppr_form.save()
            instances = formset.save(commit=False)
            for instance in instances:
                instance.ppr = ppr
                instance.save()
            # Manejar eliminados
            for deleted in formset.deleted_objects:
                deleted.delete()
            return redirect('lista_ppr')
    else:
        ppr_form = PprForm(instance=ppr)
        formset = ReferenciaFormSetEdit(queryset=ppr.referencias.all())

    return render(request, 'questions/crear_ppr.html', {
        'ppr_form': ppr_form,
        'formset': formset,
        'editando': True,
        'ppr': ppr
    })

@superuser_required
def eliminar_ppr(request, pk):
    ppr = get_object_or_404(Ppr, pk=pk)
    if request.method == 'POST':
        ppr.delete()
        return redirect('lista_ppr')
    return render(request, 'questions/confirmar_eliminar_ppr.html', {'ppr': ppr})

