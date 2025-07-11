from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Cliente

User = get_user_model()

class ClienteForm(forms.ModelForm):
    
    Nombre= forms.CharField()
    Contraseña = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirma la contraseña")
    class Meta:
        model = Cliente
        fields = ['Nombre','Contraseña', 'password2','Peso', 'Altura', 'Edad', 'Correo', 'Genero']
    
    def clean(self):
        cleaned = super().clean()
        if cleaned.get('Contraseña') != cleaned.get('password2'):
            self.add_error('password2', "Las contraseñas no coinciden")
        return cleaned        