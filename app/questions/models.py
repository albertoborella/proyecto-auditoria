from django.db import models
from django.db.models import Sum, Count

class Checklist(models.Model):
    nombre = models.CharField(max_length=100)
    usa_puntaje = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

class PreguntaPredefinida(models.Model):
    texto = models.TextField()
    texto_critico = models.BooleanField(default=False)
    numero_pregunta = models.CharField(max_length=5, blank=True, null=True)
    checklist = models.ForeignKey(Checklist, on_delete=models.CASCADE, null=True, blank=True)

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
    checklist = models.ForeignKey(Checklist, on_delete=models.SET_NULL, null=True, blank=True)
    resultado_pdf = models.FileField(upload_to='auditorias/', null=True, blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Auditoría de {self.cliente} realizada por {self.auditor} el {self.fecha}"


class Respuesta(models.Model):
    OPCIONES_RESPUESTA = [
        ('correcto', 'Correcto'),
        ('parcialmente_correcto', 'Parcialmente Correcto'),
        ('no_correcto', 'No Correcto'),
        ('critica', 'Critica'),
    ]
    pregunta_predefinida = models.ForeignKey(PreguntaPredefinida, on_delete=models.CASCADE, default='correcto')
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

    @staticmethod
    def calcular_resultados(auditoria):
        checklist = auditoria.checklist
        respuestas = Respuesta.objects.filter(auditoria=auditoria)

        if not respuestas.exists():
            return {
                'modo_sin_puntaje': not checklist.usa_puntaje,
                'cantidad_correctas': 0,
                'cantidad_parciales': 0,
                'cantidad_no_correctas': 0,
                'cantidad_criticas': 0,
                'puntaje_correcto': 0,
                'puntaje_parcial': 0,
                'puntaje_no_correcto': 0,
                'puntaje_critico': 0,
                'puntaje_maximo': 0,
                'puntaje_obtenido': 0,
                'resultado_aceptable': False,
                'porcentaje_obtenido': 0,
            }

        correctas = respuestas.filter(tipo_respuesta='correcto')
        parciales = respuestas.filter(tipo_respuesta='parcialmente_correcto')
        no_correctas = respuestas.filter(tipo_respuesta='no_correcto')
        criticas = respuestas.filter(tipo_respuesta='critica')

        puntaje_correcto = correctas.aggregate(total=Sum('puntaje'))['total'] or 0
        puntaje_parcial = parciales.aggregate(total=Sum('puntaje'))['total'] or 0
        puntaje_no_correcto = no_correctas.aggregate(total=Sum('puntaje'))['total'] or 0
        puntaje_critico = criticas.aggregate(total=Sum('puntaje'))['total'] or 0

        puntaje_maximo = respuestas.count()  # Cada respuesta correcta suma 1
        puntaje_obtenido = puntaje_correcto + puntaje_parcial + puntaje_no_correcto + puntaje_critico
        porcentaje_obtenido = (puntaje_obtenido / puntaje_maximo) * 100 if puntaje_maximo > 0 else 0

        return {
            'modo_sin_puntaje': not checklist.usa_puntaje,
            'cantidad_correctas': correctas.count(),
            'cantidad_parciales': parciales.count(),
            'cantidad_no_correctas': no_correctas.count(),
            'cantidad_criticas': criticas.count(),
            'puntaje_correcto': puntaje_correcto,
            'puntaje_parcial': puntaje_parcial,
            'puntaje_no_correcto': puntaje_no_correcto,
            'puntaje_critico': puntaje_critico,
            'puntaje_maximo': puntaje_maximo,
            'puntaje_obtenido': puntaje_obtenido,
            'resultado_aceptable': porcentaje_obtenido >= 75,
            'porcentaje_obtenido': round(porcentaje_obtenido, 2),
        }


# models para referencias normativas y prerrequisitos
class Ppr(models.Model):
    numero = models.CharField(max_length=5)
    requisito = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.numero} - {self.requisito}"


class Referencia(models.Model):
    prr = models.ForeignKey(Ppr, related_name='referencias', on_delete=models.CASCADE)
    texto = models.CharField(max_length=255)

    def __str__(self):
        return self.texto


class TipoNorma(models.Model):
    nombre = models.CharField(max_length=100)
    class Meta:
        ordering = ['nombre']
    def __str__(self):
        return self.nombre


class TipoSeccion(models.Model):
    nombre = models.CharField(max_length=100)
    class Meta:
        ordering = ['nombre']
    def __str__(self):
        return self.nombre


class Norma(models.Model):
    tipo_norma = models.ForeignKey(TipoNorma, on_delete=models.CASCADE)
    numero_norma = models.CharField(max_length=20, null=True, blank=True)
    fecha = models.DateField()
    seccion = models.ForeignKey(TipoSeccion, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    norma_pdf = models.FileField(upload_to='normativas/', null=True, blank=True)
    activa = models.BooleanField(default=True)
    class Meta:
        ordering = ['seccion']
    def __str__(self):
        return f"{self.tipo_norma} - {self.numero_norma}"


# Modelos HACCP
class Haccp(models.Model):
    numero = models.CharField(max_length=5)
    fase = models.CharField(max_length=30)
    principio = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.fase} - {self.principio}"

class Ref_haccp(models.Model):
    haccp_list = models.ForeignKey(Haccp, related_name='ref_haccp', on_delete=models.CASCADE)
    texto = models.CharField(max_length=255)

    def __str__(self):
        return self.texto

class NoConformidades(models.Model):
    numero = models.CharField(max_length=10)
    seccion = models.TextField(max_length=100, blank=True, null=True)
    nc = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.seccion} - {self.nc}"


class Ref_noconformidades(models.Model):
    nc_lista = models.ForeignKey(NoConformidades, related_name='ref_noconformidades', on_delete=models.CASCADE)
    texto = models.CharField(max_length=255)

    def __str__(self):
        return self.texto

# MODELOS SOBRE CONTROLES
# AGUA
class TipoAnalisisAgua(models.Model):
    nombre = models.CharField(max_length=100)
    class Meta:
        ordering = ['nombre']
    def __str__(self):
        return self.nombre


class PlantaIndustrial(models.Model):
    nombre = models.CharField(max_length=100)
    localidadd = models.CharField(max_length=100)
    direccion = models.CharField(max_length=100)
        
    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class MuestraAgua(models.Model):
    planta_industrial = models.ForeignKey(PlantaIndustrial, on_delete=models.CASCADE)
    fecha_muestreo = models.DateField()
    lugar_muestreo = models.CharField(max_length=100)
    responsable = models.CharField(max_length=100)
    acta_numero = models.CharField(max_length=10)
    tipo_analisis = models.ForeignKey(TipoAnalisisAgua, on_delete=models.CASCADE)
    laboratorio = models.CharField(max_length=100)
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.acta_numero} - {self.lugar_muestreo}"


class ResultadoAnalisisAgua(models.Model):
    choice_resultados = [
        ('A', 'Aceptable'),
        ('NA', 'No Aceptable'),
    ]
    acta_id = models.ForeignKey(MuestraAgua, on_delete=models.CASCADE)
    resultado = models.CharField(max_length=2, choices=choice_resultados)
    observaciones = models.TextField(blank=True, null=True)
    protocolo_pdf = models.FileField(upload_to='analisis_agua/', null=True, blank=True)

    def __str__(self):
       return f"{self.acta_id.acta_numero} - {self.resultado}" 


# MODELOS UNIDAD PRODUCTIVA
class UnidadProductiva(models.Model):
    codigo = models.CharField(max_length=10)
    razon_social = models.CharField(max_length=100)
    renspa = models.CharField(max_length=100, blank=True, null=True)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    ubicacion = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.codigo} - Renspa: {self.renspa}"


# MODELOS RESIDUOS EN LECHE CRUDA
class Analito(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre
    
    
class MuestraLeche(models.Model):
    codigo_muestra = models.CharField(max_length=20, verbose_name='Código de muestreo', blank=True, null=True)
    fecha = models.DateField()
    unidad_productiva = models.ForeignKey(UnidadProductiva, on_delete=models.CASCADE)
    volumen_litros = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"Muestra {self.id} - {self.fecha} - {self.unidad_productiva}"


class InvestigacionAnalitica(models.Model):
    ESTADO_RESULTADO_CHOICES = [
        ('aceptable', 'Aceptable'),
        ('no_aceptable', 'No aceptable'),
        ('falta', 'Falta resultado'),
    ]

    muestra = models.ForeignKey(MuestraLeche, on_delete=models.CASCADE, related_name='investigaciones')
    analito = models.ForeignKey(Analito, on_delete=models.CASCADE)
    numero_acta = models.CharField(max_length=50)
    protocolo = models.FileField(upload_to='protocolos/', blank=True, null=True)
    estado_resultado = models.CharField(
        max_length=20,
        choices=ESTADO_RESULTADO_CHOICES,
        default='falta'
    )
    fecha_resultado = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.muestra} - {self.analito} - Acta {self.numero_acta}"
    
# MODELOS REFERENTES CALIDAD DE LECHE CRUDA
class IngresoLeche(models.Model):
    unidad_productiva = models.ForeignKey(UnidadProductiva, on_delete=models.CASCADE)
    fecha = models.DateField()
    volumen = models.DecimalField(max_digits=6, decimal_places=2)
    temperatura = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    prueba_alcohol = models.BooleanField(null=True, blank=True)
    ph = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    acidez = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    antibiotico = models.BooleanField(null=True, blank=True)
    tipo_antibiotico = models.CharField(max_length=100, null=True, blank=True)

    class meta:
        ordering = ['fecha']

    def __str__(self):
        return f"{self.fecha} - {self.unidad_productiva} - {self.volumen} Lts."
