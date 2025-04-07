from django import forms
from .models import Auditoria

class AuditoriaForm(forms.ModelForm):
    class Meta:
        model = Auditoria
        fields = ['fecha', 'cliente', 'auditor', 'auditores_acompanantes']
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
                'class': 'form-select',  
            }),
        }