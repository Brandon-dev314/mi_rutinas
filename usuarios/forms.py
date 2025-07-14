from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Cliente

User = get_user_model()

class ClienteForm(UserCreationForm):
    peso   = forms.FloatField(label="Peso (kg)")
    altura = forms.FloatField(label="Altura (cm)")
    edad   = forms.IntegerField(label="Edad")
    correo = forms.EmailField(label="Correo")
    genero = forms.ChoiceField(
        label="Género",
        choices=Cliente.GENERO_CHOICES
    )

    class Meta(UserCreationForm.Meta):
        model  = User
        fields = ["username", "password1", "password2"]
