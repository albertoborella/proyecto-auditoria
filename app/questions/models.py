from django.db import models
from django.db.models import Sum, Count

class Checklist(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class PreguntaPredefinida(models.Model):
    texto = models.TextField()
    texto_critico = models.BooleanField(default=False)
    numero_pregunta = models.IntegerField(blank=True, null=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, related_name='preguntas')
    
    class Meta():
        ordering = ['numero_pregunta']

    def __str__(self):
        return self.texto


class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    def __str__(self):
        return self.nombre
    

class Auditor(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre
    

class Auditoria(models.Model):
    fecha = models.DateField()
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)  
    auditor = models.ForeignKey(Auditor, on_delete=models.CASCADE)
    auditores_acompanantes = models.CharField(verbose_name='Auditores acompañantes',max_length=255, blank=True, null=True)
    lineas_auditadas = models.CharField(verbose_name='Lineas de producción auditadas',max_length=255, blank=True, null=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Auditoría de {self.cliente} realizada por {self.auditor} el {self.fecha}"
     

class Respuesta(models.Model):
    OPCIONES_RESPUESTA = [
        ('correcto', 'Correcto'),
        ('parcialmente_correcto', 'Parcialmente Correcto'),
        ('no_correcto', 'No Correcto'),
        ('critica', 'Critica'),
    ]
    pregunta_predefinida = models.ForeignKey(PreguntaPredefinida, on_delete=models.CASCADE)
    auditoria = models.ForeignKey(Auditoria, on_delete=models.CASCADE)
    tipo_respuesta = models.CharField(max_length=21, choices=OPCIONES_RESPUESTA)
    puntaje = models.IntegerField()
    observaciones = models.TextField(blank=True, null=True)
    

    def save(self, *args, **kwargs):
        if self.tipo_respuesta == 'correcto':
            self.puntaje = 1
        elif self.tipo_respuesta == 'parcialmente_correcto':
            self.puntaje = -2
        elif self.tipo_respuesta == 'no_correcto':
            self.puntaje = -3
        elif self.tipo_respuesta == 'critica':
            self.puntaje = -21
        else:
            print("Tipo de respuesta no válido")
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.pregunta_predefinida} - {self.get_tipo_respuesta_display()}"
    
    @classmethod
    def calcular_resultados(cls, auditoria):
        # Filtrar respuestas por auditoría
        respuestas = cls.objects.filter(auditoria=auditoria)
        # Contar respuestas correctas, parcialmente correctas y no correctas
        correctas = respuestas.filter(tipo_respuesta='correcto')
        parciales = respuestas.filter(tipo_respuesta='parcialmente_correcto')
        no_correctas = respuestas.filter(tipo_respuesta='no_correcto')
        criticas = respuestas.filter(tipo_respuesta='critica')
        # Sumar puntajes
        puntaje_correcto = correctas.aggregate(Sum('puntaje'))['puntaje__sum'] or 0
        puntaje_parcial = parciales.aggregate(Sum('puntaje'))['puntaje__sum'] or 0
        puntaje_no_correcto = no_correctas.aggregate(Sum('puntaje'))['puntaje__sum'] or 0
        puntaje_critico = criticas.aggregate(Sum('puntaje'))['puntaje__sum'] or 0
        # Calcular cantidad de respuestas
        cantidad_correctas = correctas.count()
        cantidad_parciales = parciales.count()
        cantidad_no_correctas = no_correctas.count()
        cantidad_criticas = criticas.count()
        print(cantidad_criticas)
        # Calcular puntaje máximo
        puntaje_maximo = respuestas.count()  # Total de preguntas
        # Calcular puntaje obtenido
        puntaje_obtenido = puntaje_maximo + puntaje_parcial + puntaje_no_correcto + puntaje_critico
        # Determinar si el resultado es aceptable
        resultado_aceptable = puntaje_obtenido >= (0.75 * puntaje_maximo)
        # Porcentaje obtenido
        porcentaje_obtenido = (puntaje_obtenido / puntaje_maximo * 100) if puntaje_maximo > 0 else 0
        porcentaje_obtenido = round(porcentaje_obtenido, 2)  # Redondear a 2 decimales
        # Devolver resultados
        return {
            'cantidad_correctas': cantidad_correctas,
            'puntaje_correcto': puntaje_correcto,
            'cantidad_parciales': cantidad_parciales,
            'cantidad_criticas': cantidad_criticas,
            'puntaje_parcial': puntaje_parcial,
            'puntaje_critico': puntaje_critico,
            'cantidad_no_correctas': cantidad_no_correctas,
            'puntaje_no_correcto': puntaje_no_correcto,
            'puntaje_maximo': puntaje_maximo,
            'puntaje_obtenido': puntaje_obtenido,
            'resultado_aceptable': resultado_aceptable,
            'porcentaje_obtenido': porcentaje_obtenido
        }

