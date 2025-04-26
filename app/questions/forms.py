from django import forms
from .models import Auditoria, Ppr, Referencia
from django.forms import inlineformset_factory, modelformset_factory

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
