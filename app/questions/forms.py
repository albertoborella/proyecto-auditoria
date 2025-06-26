from django import forms
from django.forms import inlineformset_factory, modelformset_factory
from .models import ( Auditoria, Ppr, Referencia, Norma, 
                     Haccp, Ref_haccp, NoConformidades, 
                     Ref_noconformidades, UnidadProductiva, 
                     UnidadProductiva )

class AuditoriaForm(forms.ModelForm):
    class Meta:
        model = Auditoria
        fields = ['fecha', 'cliente', 'auditor', 'auditores_acompanantes', 'lineas_auditadas', 'checklist']  # 👈 Agregado 'checklist'
        widgets = {
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'placeholder': 'Seleccione la fecha',
                'type': 'date'
            }),
            'cliente': forms.Select(attrs={
                'class': 'form-select',
            }),
            'auditor': forms.Select(attrs={
                'class': 'form-select',
            }),
            'auditores_acompanantes': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'lineas_auditadas': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'checklist': forms.Select(attrs={  # 👈 Nuevo widget para el campo checklist
                'class': 'form-select',
            }),
        }

class PprForm(forms.ModelForm):
    class Meta:
        model = Ppr
        fields = ['numero', 'requisito']
        widgets = {
            'numero': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ej: A.1'
            }),
            'requisito': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 4,
                'placeholder': 'Describa el requisito...'
            }),
        }

class ReferenciaForm(forms.ModelForm):
    class Meta:
        model = Referencia
        fields = ['texto']
        widgets = {
            'texto': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ej: Codex Alimentarius - Sección 5'
            })
        }

ReferenciaFormSet = inlineformset_factory(
    Ppr, Referencia, form=ReferenciaForm, extra=1, can_delete=True
)

ReferenciaFormSetEdit = modelformset_factory(
    Referencia,
    fields=('texto',),
    extra=0,  # no crea formularios adicionales por defecto
    can_delete=True  # opcional, si querés permitir eliminar referencias al editar
)

class NormaForm(forms.ModelForm):
    class Meta:
        model = Norma
        fields = [
            'tipo_norma',
            'numero_norma',
            'fecha',
            'seccion',
            'titulo',
            'norma_pdf',
            'activa',
        ]
        widgets = {
            'tipo_norma': forms.Select(attrs={'class': 'form-control'}),
            'numero_norma': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Norma'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'seccion': forms.Select(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la Norma'}),
            'norma_pdf': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'tipo_norma': 'Tipo de Norma',
            'numero_norma': 'Número de Norma',
            'fecha': 'Fecha',
            'seccion': 'Sección',
            'titulo': 'Título',
            'norma_pdf': 'Archivo PDF',
            'activa': '¿Es activa?',
        }
        help_texts = {
            'numero_norma': 'Ingrese el número de la norma, si aplica.',
            'norma_pdf': 'Suba el archivo en formato PDF, si aplica.',
        }
        error_messages = {
            'numero_norma': {
                'max_length': "El número de norma no puede exceder los 20 caracteres.",
            },
        }

class HaccpForm(forms.ModelForm):
    class Meta:
        model = Haccp
        fields = ['numero', 'fase', 'principio']
        widgets = {
            'numero': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ej: A.1'
            }),
            'fase': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Describa fase del proceso'
            }),
            'principio': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Describa el principio'
            }),
        }

class Ref_haccpForm(forms.ModelForm):
    class Meta:
        model = Ref_haccp
        fields = ['texto']
        widgets = {
            'texto': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Ej: Codex Alimentarius - Sección 5'
            })
        }

RefHaccpFormSet = modelformset_factory(Ref_haccp, fields=('texto',), extra=1)

class NcForm(forms.ModelForm):
    class Meta:
        model = NoConformidades
        fields = ['numero', 'seccion', 'nc']
        widgets = {
            'numero': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Coloque número de órden'
            }),
            'seccion': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Sección a la que se refiere'
            }),
            'nc': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Describa la No Conformidad'
            }),
        }

class Ref_noconformidadesForm(forms.ModelForm):
    class Meta:
        model = Ref_noconformidades
        fields = ['texto']
        widgets = {
            'texto': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Colocar normativa interviniente'
            })
        }

RefNcFormSet = modelformset_factory(Ref_noconformidades, fields=('texto',), extra=1)

# FORMULARIO DE INGRESO DE UNIDADES PRODUCTIVAS
class UnidadProductivaForm(forms.ModelForm):
    class Meta:
        model = UnidadProductiva
        fields = ['codigo', 'razon_social', 'renspa', 'telefono', 'email', 'ubicacion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el código'}),
            'razon_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese la razón social'}),
            'renspa': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el RENSPA'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el email'}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese la ubicación'}),
        }