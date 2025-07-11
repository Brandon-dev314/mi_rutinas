from django.db import models
from django.conf import settings
from django.utils import timezone

class Ejercicio(models.Model):
    nombre = models.CharField(max_length=100,blank=True, null=False)
    musculo = models.CharField(max_length=100,blank=True, null=False)
    equipamiento = models.CharField(max_length=100, blank=True, null=False)
    gif_url = models.URLField(help_text="URL del GIF animado")
    
    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clientes',    
        null= True, 
        blank= True
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_cliente',
        null= True,
        blank= True
    )
    Peso     = models.FloatField()
    Altura   = models.FloatField(help_text="En centímetros")
    Edad     = models.PositiveIntegerField()
    Correo   = models.EmailField(unique=False)
    GENERO_CHOICES = [('M','Masculino'),('F','Femenino'),('O','Otro')]
    Genero   = models.CharField(max_length=1, choices=GENERO_CHOICES)

    def __str__(self):
        return self.user.username
    
class Rutina(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete= models.CASCADE, related_name= 'rutinas', null=True, blank=True)
    nombre = models.CharField(max_length=100)
    ejercicios = models.ManyToManyField(Ejercicio)
    creado = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre

class RutinaAsignada(models.Model):
    cliente     = models.ForeignKey(
        'Cliente',
        on_delete=models.CASCADE,
        related_name='rutinas'
    )
    rutina      = models.ForeignKey(
        'Rutina',
        on_delete=models.CASCADE,
        related_name='asignaciones'
    )
    asignada_el = models.DateTimeField(auto_now_add=True)
    completada = models.BooleanField(default=False)
    completada_el = models.DateTimeField(null=True, blank=True)
    comentarios = models.TextField(blank=True, null=True)

    # Nuevo campo para guardar por ejercicio: series, reps y duración
    detalles    = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.rutina.nombre} → {self.cliente.nombre}"
    
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications', 
        blank= True,
        null= True
    )
    message     = models.CharField(max_length=255)
    created_at  = models.DateTimeField(auto_now_add=True)
    is_read     = models.BooleanField(default=False)

    def __str__(self):
        status = "✓" if self.is_read else "●"
        return f"{status} {self.message[:30]}…"


    