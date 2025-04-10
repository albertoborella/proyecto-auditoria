from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum
from django.contrib import messages
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from weasyprint import HTML
from .forms import AuditoriaForm
from .models import Auditoria, PreguntaPredefinida, Respuesta

@login_required
def home(request):
    return render(request, 'questions/home.html')

@login_required
def crear_auditoria(request):
    if request.method == 'POST':
        form = AuditoriaForm(request.POST)  
        if form.is_valid():
            auditoria = form.save()  
            print(auditoria)
            # Crear preguntas predefinidas para la auditoria
            preguntas = PreguntaPredefinida.objects.all()
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
    preguntas = PreguntaPredefinida.objects.all()
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
    preguntas = PreguntaPredefinida.objects.all()
    respuestas = Respuesta.objects.filter(auditoria=auditoria)
    resultados = Respuesta.calcular_resultados(auditoria)
    puntaje_total = sum(respuesta.puntaje for respuesta in respuestas)
    
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
        
        # Redirigir a la función que genera el PDF
        return redirect('resultado_auditoria_pdf', auditoria_id=auditoria.id)
    
    # Si no es un POST, solo renderiza la plantilla
    return render(request, 'questions/resultado_auditoria.html', {
        'auditoria': auditoria,
        'preguntas': preguntas,
        'respuestas': respuestas,
        'resultados': resultados,
        'puntaje_total': puntaje_total,
        'comentario_general': '',  # Asegúrate de pasar un valor por defecto si no hay comentario
    })

@login_required
def lista_auditorias(request):
    auditorias = Auditoria.objects.all()
    auditorias_con_puntaje = []
    for auditoria in auditorias:
        puntaje_total = Respuesta.objects.filter(auditoria=auditoria).aggregate(Sum('puntaje'))['puntaje__sum'] or 0
        # Calcular el resultado basado en el puntaje total
        if puntaje_total >= puntaje_total * 0.75:  # Suponiendo que 75 es el puntaje mínimo para aprobar
            resultado = "ACEPTADO"
        else:
            resultado = "NO ACEPTADO"
        auditorias_con_puntaje.append({
            'auditoria': auditoria,
            'puntaje_total': puntaje_total,
            'resultado': resultado
        })
    return render(request, 'questions/lista_auditorias.html', {'auditorias': auditorias_con_puntaje})   

@login_required
def eliminar_auditoria(request, auditoria_id):
    auditoria = get_object_or_404(Auditoria, id=auditoria_id)
    
    if request.method == 'POST':
        auditoria.delete()
        messages.success(request, 'La auditoría ha sido eliminada exitosamente.')
        return redirect('lista_auditorias') 
    return render(request, 'questions/confirmar_eliminacion.html', {'auditoria': auditoria})

@login_required
def resultado_auditoria_pdf(request, auditoria_id):
    auditoria = get_object_or_404(Auditoria, id=auditoria_id)
    preguntas = PreguntaPredefinida.objects.all()
    respuestas = Respuesta.objects.filter(auditoria=auditoria)
    resultados = Respuesta.calcular_resultados(auditoria)
    puntaje_total = sum(respuesta.puntaje for respuesta in respuestas)
    
    # Recuperar el comentario de la sesión
    comentario_general = request.session.get('comentario_general', '')
    
    # Renderiza el template a un HTML
    html_string = render_to_string('questions/resultado_auditoria.html', {
        'auditoria': auditoria,
        'preguntas': preguntas,
        'respuestas': respuestas,
        'resultados': resultados,
        'puntaje_total': puntaje_total,
        'comentario_general': comentario_general,
    })
    # Genera el PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="resultado_auditoria_{auditoria_id}.pdf"'
    
    # Genera el PDF
    pdf = HTML(string=html_string).write_pdf()
    # Aquí puedes agregar el número de página si es necesario
    # Sin embargo, WeasyPrint no permite directamente la inserción de números de página en el PDF de esta manera.
    # Necesitarás usar un enfoque diferente para incluir números de página.
    response.write(pdf)
    return response