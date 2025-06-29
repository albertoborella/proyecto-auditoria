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
from django.utils import timezone
from django.utils.text import slugify
from .forms import (
    AuditoriaForm,
    PprForm,
    ReferenciaFormSet,
    NormaForm,
    HaccpForm,
    RefHaccpFormSet,  # ✅ formset correcto para Ref_haccp
    RefNcFormSet,     # ✅ formset correcto para Ref_noconformidades
    NcForm,
    Ref_noconformidadesForm,
    UnidadProductivaForm,
    MuestraAguaForm, ResultadoAnalisisAguaForm,
    MuestraLecheForm, InvestigacionAnaliticaForm
)

from .models import (Auditoria, PreguntaPredefinida, Respuesta, Checklist,
                     Ppr, Referencia, Cliente, Norma, TipoSeccion, 
                     Haccp, Ref_haccp, NoConformidades, Ref_noconformidades, 
                     MuestraAgua, ResultadoAnalisisAgua, PlantaIndustrial, TipoAnalisisAgua,
                     UnidadProductiva, MuestraLeche, Analito, InvestigacionAnalitica)


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

@superuser_required
def eliminar_auditoria(request, auditoria_id):
    auditoria = get_object_or_404(Auditoria, id=auditoria_id)

    if request.method == 'POST':
        auditoria.delete()
        messages.success(request, 'La auditoría ha sido eliminada exitosamente.')
        return redirect('lista_auditorias')
    return render(request, 'questions/confirmar_eliminacion.html', {'auditoria': auditoria})

def modulo_construccion(request):
    return render(request,'questions/modulo_construccion.html')

# views para Prerrequisitos
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

@login_required
def listado_normas(request):
    normas = Norma.objects.all()
    secciones = TipoSeccion.objects.all()

    filtro_seleccionado = request.GET.get('filtro')
    valor_seleccionado = None  # inicializamos

    if filtro_seleccionado == 'seccion':
        valor_seleccionado = request.GET.get('valor_seccion')
        if valor_seleccionado:
            normas = normas.filter(seccion_id=valor_seleccionado)
    elif filtro_seleccionado == 'numero':
        valor_seleccionado = request.GET.get('valor_numero')
        if valor_seleccionado:
            normas = normas.filter(numero_norma__icontains=valor_seleccionado)

    context = {
        'normas': normas,
        'secciones': secciones,
        'filtro_seleccionado': filtro_seleccionado,
        'valor_seleccionado': valor_seleccionado,
    }
    return render(request, 'normas/listado_normas.html', context)


@login_required
def agregar_norma(request):
    if request.method == 'POST':
        form = NormaForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Norma agregada exitosamente.')
            return redirect('normas_listar')
    else:
        form = NormaForm()
    return render(request, 'normas/agregar_norma.html', {'form': form})

def lista_haccp(request):
    query = request.GET.get('q', '')  # 'q' será el nombre del input de búsqueda
    haccp_list = Haccp.objects.prefetch_related('ref_haccp').all().order_by('numero')

    if query:
        haccp_list = Haccp.objects.filter(Q(principio__icontains=query))
    else:
        haccp_list = Haccp.objects.all()

    paginator = Paginator(haccp_list, 5)  # 5 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,  # Para mantener el texto buscado en el input
    }

    return render(request, 'questions/lista_haccp.html', context)

@superuser_required
def crear_haccp(request):
    if request.method == 'POST':
        haccp_form = HaccpForm(request.POST)
        formset = RefHaccpFormSet(request.POST, prefix='referencia_set')  # 👈 corrección aquí
        if haccp_form.is_valid() and formset.is_valid():
            haccp = haccp_form.save()
            for ref_form in formset:
                if ref_form.cleaned_data and ref_form.cleaned_data.get('texto'):
                    ref = ref_form.save(commit=False)
                    ref.haccp_list = haccp
                    ref.save()
                    print(f"Referencia guardada: {ref.texto}")
            return redirect('lista_haccp')
        else:
            print("Errores en formularios:")
            print(haccp_form.errors)
            print(formset.errors)
    else:
        haccp_form = HaccpForm()
        formset = RefHaccpFormSet(queryset=Ref_haccp.objects.none(), prefix='referencia_set')

    return render(request, 'questions/crear_haccp.html', {
        'haccp_form': haccp_form,
        'formset': formset
    })

@superuser_required
def eliminar_haccp(request, pk):
    haccp = get_object_or_404(Haccp, pk=pk)
    if request.method == 'POST':
        haccp.delete()
        return redirect('lista_haccp')
    return render(request, 'questions/confirmar_eliminacion_haccp.html', {'haccp': haccp})

#Views No Conformidades
@superuser_required
def crear_nc(request):
    if request.method == 'POST':
        nc_form = NcForm(request.POST)
        formset = RefNcFormSet(request.POST, prefix='referencia_set')
        if nc_form.is_valid() and formset.is_valid():
            nc = nc_form.save()
            for ref_form in formset:
                if ref_form.cleaned_data and ref_form.cleaned_data.get('texto'):
                    ref = ref_form.save(commit=False)
                    ref.nc_lista = nc
                    ref.save()
                    print(f"Referencia guardada: {ref.texto}")  # Para depuración
            return redirect('lista_nc')
        else:
            print("Errores en formularios:")
            print(nc_form.errors)
            print(formset.errors)
    else:
        nc_form = NcForm()
        formset = RefNcFormSet(queryset=Ref_noconformidades.objects.none(), prefix='referencia_set')
    return render(request, 'questions/crear_nc.html', {
        'nc_form': nc_form,
        'formset': formset
    })



def lista_nc(request):
    query = request.GET.get('q', '')
    if query:
        nc_lista = NoConformidades.objects.filter(Q(seccion__icontains=query) | Q(nc__icontains=query)).prefetch_related('ref_noconformidades')
    else:
        nc_lista = NoConformidades.objects.all().prefetch_related('ref_noconformidades')

    paginator = Paginator(nc_lista, 5)  # 5 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'query': query,  # Para mantener el texto buscado en el input
    }

    return render(request, 'questions/lista_nc.html', context)

@superuser_required
def eliminar_nc(request, pk):
    nc = get_object_or_404(NoConformidades, pk=pk)
    if request.method == 'POST':
        nc.delete()
        return redirect('lista_nc')
    return render(request, 'questions/confirmar_eliminacion_nc.html', {'nc': nc})

# Funciones de Análisis de agua
def crear_y_editar_muestra_agua(request, muestra_id=None):
    muestra = get_object_or_404(MuestraAgua, id=muestra_id) if muestra_id else None
    resultado = ResultadoAnalisisAgua.objects.filter(acta_id=muestra).first() if muestra else None

    if request.method == 'POST':
        form = MuestraAguaForm(request.POST, request.FILES, instance=muestra)
        resultado_form = ResultadoAnalisisAguaForm(request.POST, request.FILES, instance=resultado)

        if form.is_valid():
            muestra = form.save()

    # Solo procesar resultado si se completaron datos
            if any([
                request.POST.get('resultado'),
                request.POST.get('observaciones'),
                request.FILES.get('protocolo_pdf'),
            ]):
                if resultado_form.is_valid():
                    resultado_data = resultado_form.cleaned_data
                    resultado = resultado_form.save(commit=False)
                    resultado.acta_id = muestra
                    resultado.save()

            return redirect('listar_analisis_agua')  # Redirige al listado si todo va bien

        else:
            print("Errores en el formulario:")
            print(form.errors)
            print(resultado_form.errors)

    else:
        form = MuestraAguaForm(instance=muestra)
        resultado_form = ResultadoAnalisisAguaForm(instance=resultado)

    return render(request, 'questions/crear_y_editar_muestra_agua.html', {
        'form': form,
        'resultado_form': resultado_form,
        'muestra_id': muestra_id,
    })



def listar_analisis(request):
    muestras = MuestraAgua.objects.all()
    resultados = ResultadoAnalisisAgua.objects.all()
    # Filtrado
    if request.method == "GET":
        fecha = request.GET.get('fecha')
        planta_id = request.GET.get('planta')
        tipo_analisis_id = request.GET.get('tipo_analisis')
        resultado = request.GET.get('resultado')
        if fecha:
            muestras = muestras.filter(fecha_muestreo=fecha)
        if planta_id:
            muestras = muestras.filter(planta_industrial_id=planta_id)
        if tipo_analisis_id:
            muestras = muestras.filter(tipo_analisis_id=tipo_analisis_id)
        if resultado:
            resultados_ids = ResultadoAnalisisAgua.objects.filter(resultado=resultado).values_list('acta_id', flat=True)
            muestras = muestras.filter(id__in=resultados_ids)
     # Paginación
    paginator = Paginator(muestras, 10)  # 10 muestras por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    plantas = PlantaIndustrial.objects.all()
    tipos_analisis = TipoAnalisisAgua.objects.all()
    context = {
        'muestras': muestras,
        'plantas': plantas,
        'tipos_analisis': tipos_analisis,
        'resultados': resultados,
    }
    return render(request, 'questions/listar_analisis_agua.html', context)

# VISTA PARA MANEJAR INGRESO DE UNIDADES PRODUCTIVAS
def crear_unidad_productiva(request):
    if request.method == 'POST':
        form = UnidadProductivaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_unidades_productivas')
    else:
        form = UnidadProductivaForm()
    return render(request, 'questions/crear_unidad_productiva.html', {'form': form})

def listar_unidades_productivas(request):
    # Obtener los valores únicos para los filtros
    codigos = UnidadProductiva.objects.values_list('codigo', flat=True).distinct()
    razon_social = UnidadProductiva.objects.values_list('razon_social', flat=True).distinct()
    
    # Obtener los parámetros de búsqueda
    codigo_filtro = request.GET.get('codigo')
    razon_social_filtro = request.GET.get('razon_social')
    
    # Filtrar las unidades productivas según los parámetros
    unidades = UnidadProductiva.objects.all()
    
    if codigo_filtro:
        unidades = unidades.filter(codigo=codigo_filtro)
    
    if razon_social_filtro:
        unidades = unidades.filter(razon_social=razon_social_filtro)
    context = {
        'unidades': unidades,
        'codigos': codigos,
        'razon_social': razon_social,
    }
    
    return render(request, 'questions/listar_unidades_productivas.html', context)

def editar_unidad_productiva(request, pk):
    unidad = get_object_or_404(UnidadProductiva, pk=pk)
    
    if request.method == 'POST':
        form = UnidadProductivaForm(request.POST, instance=unidad)
        if form.is_valid():
            form.save()
            messages.success(request, 'Unidad productiva actualizada con éxito.')
            return redirect('listar_unidades_productivas')  # Redirige a la lista después de guardar
    else:
        form = UnidadProductivaForm(instance=unidad)
    return render(request, 'questions/editar_unidad_productiva.html', {'form': form, 'unidad': unidad})

def eliminar_unidad_productiva(request, pk):
    unidad = get_object_or_404(UnidadProductiva, pk=pk)
    if request.method == 'POST':
        unidad.delete()
        messages.success(request, 'Unidad productiva eliminada con éxito.')
        return redirect('listar_unidades_productivas')  # Redirige a la lista después de eliminar
    return render(request, 'questions/confirmar_eliminacion_unidad_productiva.html', {'unidad': unidad})

# VISTAS PARA REGISTRAR MUESTRAS DE LECHE CRUDA Y ANALISIS DE RESIDUOS
def registro_muestra(request, muestra_id=None):
    muestra = MuestraLeche.objects.filter(id=muestra_id).first()
    analitos = muestra.investigaciones.all() if muestra else None

    if not muestra:
        if request.method == 'POST':
            form = MuestraLecheForm(request.POST)
            if form.is_valid():
                nueva = form.save()
                return redirect('registro_muestra', muestra_id=nueva.id)
        else:
            form = MuestraLecheForm()
        return render(request, 'residuos_leche/registro_muestra.html', {
            'muestra_form': form,
            'muestra': None
        })

    else:
        if request.method == 'POST':
            form = InvestigacionAnaliticaForm(request.POST, request.FILES)
            if form.is_valid():
                analito = form.save(commit=False)
                analito.muestra = muestra
                analito.save()
                if 'add_another' in request.POST:
                    return redirect('registro_muestra', muestra_id=muestra.id)
                return redirect('detalle_muestra', pk=muestra.id)
        else:
            form = InvestigacionAnaliticaForm()

        return render(request, 'residuos_leche/registro_muestra.html', {
            'muestra': muestra,
            'muestra_form': None,
            'analito_form': form,
            'analitos': analitos
        })

def detalle_muestra(request, pk):
    muestra = get_object_or_404(MuestraLeche, pk=pk)
    analitos = muestra.investigaciones.all()

    return render(request, 'residuos_leche/detalle_muestra.html', {
        'muestra': muestra,
        'analitos': analitos
    })

def editar_analito(request, pk):
    analito = get_object_or_404(InvestigacionAnalitica, pk=pk)
    if request.method == 'POST':
        form = InvestigacionAnaliticaForm(request.POST, request.FILES, instance=analito)
        if form.is_valid():
            form.save()
            return redirect('detalle_muestra', pk=analito.muestra.pk)
    else:
        form = InvestigacionAnaliticaForm(instance=analito)

    return render(request, 'residuos_leche/editar_analito.html', {
        'form': form,
        'analito': analito,
    })

def listado_analisis(request):
    analitos = Analito.objects.all()
    query = InvestigacionAnalitica.objects.select_related('muestra', 'analito')

    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    codigo_muestra = request.GET.get('codigo_muestra')
    analito_id = request.GET.get('analito')

    filtros = {}

    if fecha_inicio:
        query = query.filter(muestra__fecha__gte=fecha_inicio)
        filtros['fecha_inicio'] = fecha_inicio

    if fecha_fin:
        query = query.filter(muestra__fecha__lte=fecha_fin)
        filtros['fecha_fin'] = fecha_fin

    if codigo_muestra:
        query = query.filter(muestra__codigo_muestra__icontains=codigo_muestra)
        filtros['codigo_muestra'] = codigo_muestra

    if analito_id:
        query = query.filter(analito__id=analito_id)
        filtros['analito'] = analito_id

    return render(request, 'residuos_leche/listado_analisis.html', {
        'analisis': query,
        'analitos': analitos,
        'filtros': filtros
    })


