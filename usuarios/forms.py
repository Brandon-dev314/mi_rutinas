from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import Cliente

User = get_user_model()

class ClienteForm(UserCreationForm):
    # nuevos campos de nombre y apellidos
    first_name = forms.CharField(label="Nombre")
    last_name  = forms.CharField(label="Apellidos")

    # campos extra para el perfil Cliente
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
        fields = [
            "username",
            "first_name",    # aquí va Nombre
            "last_name",     # aquí van Apellidos
            "password1",
            "password2",
        ]
