import io
import json
import requests
from PIL import Image as PILImage
from datetime import date, timedelta
from django.utils import timezone
from reportlab.lib.utils import ImageReader
from django.db.models import Count, Q
from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate,login,logout, get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Ejercicio, Cliente, Rutina, RutinaAsignada, Notification
from .forms import ClienteForm

User = get_user_model()

def bienvenida(request):
    return render(request,'usuarios/bienvenida.html')

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,'¡Usuario registrado exitosamente!')
            return redirect('login')
    else:
        form=UserCreationForm()
    return render(request,'usuarios/registro.html', {'form': form})


def iniciar_sesion(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Redirige según rol
            if hasattr(user, 'perfil_cliente'):
                return redirect('cliente_resumen')
            return redirect('panel_resumen')
        messages.error(request, 'Usuario o contraseña inválidos')
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})

def cerrar_sesion(request):
    logout(request)
    return redirect('login')

@login_required
def panel_resumen(request):
    
    total_clientes = Cliente.objects.filter(coach=request.user).count()
    total_rutinas  = Rutina.objects.filter(owner=request.user).count()
    ultimos_clientes = Cliente.objects.filter(coach=request.user).order_by('-id')[:5]
    ultimas_rutinas  = Rutina.objects.filter(owner=request.user).order_by('-creado')[:5]
    
    progreso = (RutinaAsignada.objects.filter(rutina__owner=request.user, completada=True).values('cliente__user__username').annotate(completadas=Count('id')))
    labels = [ item['cliente__user__username'] for item in progreso ]
    data   = [ item['completadas'] for item in progreso ]

    
    notifs_qs    = Notification.objects.filter(user=request.user, is_read=False)
    notifications = list(notifs_qs) # marcar todas como leídas para que no repitan siguiente vez
    notifs_qs.update(is_read=True)
    
    return render(request, 'usuarios/panel_resumen.html', {
        'total_clientes':   total_clientes,
        'total_rutinas':    total_rutinas,
        'ultimos_clientes': ultimos_clientes,
        'ultimas_rutinas':  ultimas_rutinas,
        'notifications':    notifications,
        'chart_labels':     json.dumps(labels),  # LOS LABELS van aquí
        'chart_values':     json.dumps(data),    # LOS VALUES van aquí
    })

@login_required
def panel_rutinas(request):
    if request.method == 'POST':
        # 1. Leer formulario
        nombre        = request.POST.get('nombre', '').strip()
        ejercicio_ids = request.POST.getlist('ejercicios')
        cliente_id    = request.POST.get('cliente')

        if nombre and ejercicio_ids and cliente_id:
            # 2. Crear Rutina con owner y asignar ejercicios
            rutina = Rutina.objects.create(
                nombre=nombre,
                owner=request.user
            )
            rutina.ejercicios.set(
                Ejercicio.objects.filter(pk__in=ejercicio_ids)
            )

            # 3. Construir JSON de detalles
               # 3. Construir JSON de detalles (solo parsear cuando venga un número)
            detalles = {}
            for ej_id in ejercicio_ids:
                s = request.POST.get(f'series-{ej_id}', '').strip()
                r = request.POST.get(f'reps-{ej_id}',   '').strip()
                d = request.POST.get(f'duracion-{ej_id}', '').strip()
                comentarios = request.POST.get('comentarios', '').strip()

                detalles[int(ej_id)] = {
                    'series':   int(s) if s.isdigit() else None,
                    'reps':     int(r) if r.isdigit() else None,
                    'duracion': int(d) if d.isdigit() else None,
                }

            # 4. Crear asignación
            cliente = get_object_or_404(Cliente, pk=cliente_id, coach=request.user)
            RutinaAsignada.objects.create(
                rutina=rutina,
                cliente=cliente,
                detalles=detalles,
                comentarios=comentarios,  
            )

            # 5. Generar PDF con imágenes
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=(595, 842))  # A4

            p.setFont("Helvetica-Bold", 16)
            p.drawString(40, 800, f"Rutina: {rutina.nombre}")
            
            
            if comentarios:
                p.setFont("Helvetica", 12)
                
                p.drawString(40, 780, f"Comentarios: {comentarios}")
                y = 750
            else:
                y = 770
                
            for ej_id, det in detalles.items():
                # Descargar y preparar imagen
                url   = Ejercicio.objects.values_list('gif_url', flat=True).get(pk=ej_id)
                resp  = requests.get(url, timeout=5)
                img_pil = PILImage.open(io.BytesIO(resp.content)).convert("RGB")
                img_pil.thumbnail((100, 100), PILImage.LANCZOS)

                img_buf = io.BytesIO()
                img_pil.save(img_buf, format='PNG')
                img_buf.seek(0)
                img = ImageReader(img_buf)

                # Dibujar imagen y texto
                p.drawImage(img, 40, y-100, width=100, height=100, mask='auto')
                p.setFont("Helvetica", 12)
                nombre_ej = Ejercicio.objects.values_list('nombre', flat=True).get(pk=ej_id)
                partes = []
                if det.get('series') is not None and det.get('reps') is not None:
                    partes.append(f"{det['series']}×{det['reps']}")
                if det.get('duracion') is not None:
                    partes.append(f"{det['duracion']} seg")

                texto = f"{nombre_ej}: " + ", ".join(partes) if partes else nombre_ej

                p.drawString(150, y-20, texto)

                y -= 130
                if y < 100:
                    p.showPage()
                    y = 800

            p.showPage()
            p.save()
            buffer.seek(0)

            # 6. Enviar correo con PDF
            email = EmailMessage(
                subject=f"Tu rutina {rutina.nombre}",
                body="¡Hola! Te envío tu rutina de ejercicios en PDF, con imágenes incluidas.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[cliente.correo],
            )
            filename = f"Rutina_{rutina.nombre.replace(' ','_')}.pdf"
            email.attach(filename, buffer.read(), 'application/pdf')
            email.send()

        return redirect('panel_rutinas')

    # GET: búsqueda y modal
    q = request.GET.get('q', '').strip()
    m = request.GET.get('m', '').strip()
    

    ejercicios = Ejercicio.objects.all()
    if q:
        ejercicios = ejercicios.filter(nombre__icontains=q)
    if m:
        ejercicios = ejercicios.filter(musculo=m)
        
    musculos = Ejercicio.objects.values_list('musculo', flat=True).distinct()

    clientes = Cliente.objects.filter(coach=request.user)

    return render(request, 'usuarios/panel_rutinas.html', {
        'ejercicios': ejercicios,
        'q':           q,
        'musculos': musculos,
        'm': m,
        'clientes':    clientes,
    })

@login_required
def panel_clientes(request):
    clientes = Cliente.objects.filter(coach=request.user)
    return render(request,'usuarios/panel_clientes.html', {'clientes':clientes})


@login_required
def cliente_rutinas(request, cliente_pk):
    cliente = get_object_or_404(Cliente, pk=cliente_pk)
    # Trae las asignaciones de ese cliente
    raw = (
        RutinaAsignada.objects
        .filter(cliente=cliente)
        .select_related('rutina')
        .order_by('-asignada_el')
    )

    # Prepara una lista plana para el template
    rutinas = []
    for a in raw:
        detalles = []
        for ej_id, det in a.detalles.items():
            nombre_ej = Ejercicio.objects.values_list('nombre', flat=True).get(pk=ej_id)
            detalles.append({
                'nombre':   nombre_ej,
                'series':   det['series'],
                'reps':     det['reps'],
                'duracion': det['duracion'],
            })
        rutinas.append({
            'pk':          a.pk,     
            'nombre':     a.rutina.nombre,
            'asignada_el': a.asignada_el,
            'detalles':   detalles,
        })

    return render(request, 'usuarios/cliente_rutinas.html', {
        'cliente': cliente,
        'rutinas': rutinas,
    })
    
@login_required
def cliente_asignacion_eliminar(request, asign_id):
    # Solo el coach que creó la rutina puede borrarla
    asign = get_object_or_404(
        RutinaAsignada,
        pk=asign_id,
        rutina__owner=request.user
    )
    cliente_pk = asign.cliente.pk
    asign.delete()
    return redirect('cliente_rutinas', cliente_pk=cliente_pk)


@login_required
def cliente_crear(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # 1) crea el usuario cliente
            user = User.objects.create_user(
                username=data['Nombre'],
                password=data['Contraseña']
            )
            # 2) crea el perfil Cliente vinculando coach=request.user
            Cliente.objects.create(
                coach=request.user,
                user=user,
                peso=data['Peso'],
                altura=data['Altura'],
                edad=data['Edad'],
                correo=data['Correo'],
                genero=data['Genero']
            )
            return redirect('panel_clientes')
    else:
        form = ClienteForm()

    return render(request, 'usuarios/cliente_form.html', {
        'form':   form,
        'titulo': 'Agregar cliente'
    })


@login_required
def cliente_editar(request, pk):
    # obtenemos el Cliente existente (incluye user y coach)
    cliente = get_object_or_404(Cliente, pk=pk, coach=request.user)

    if request.method == 'POST':
        # usamos un formulario solo de los campos de Cliente
        # (sin username/password)
        form = ClienteForm(
            request.POST,
            instance=cliente
        )
        if form.is_valid():
            # guardamos solo los campos de Cliente, coach y user no cambian
            perfil = form.save(commit=False)
            perfil.save()
            return redirect('panel_clientes')
    else:
        # pre-llenamos el formulario con los datos del perfil
        # y con username si tu form lo incluye
        initial = {
            'username': cliente.user.username
        }
        form = ClienteForm(instance=cliente, initial=initial)

    return render(request, 'usuarios/cliente_form.html', {
        'form':   form,
        'titulo': 'Editar cliente'
    })

@login_required
def cliente_eliminar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('panel_clientes')
    return render(request, 'usuarios/cliente_confirm_delete.html', {
        'cliente': cliente
    })


@login_required
def cliente_dashboard(request):
    # busca el perfil
    cliente = get_object_or_404(Cliente, user=request.user)
    asigns  = RutinaAsignada.objects.filter(cliente=cliente).select_related('rutina')
    return render(request, 'usuarios/cliente_dashboard.html', {
        'asignaciones': asigns
    })

@login_required
def cliente_completar(request, asig_id):
    asig = get_object_or_404(
        RutinaAsignada,
        pk=asig_id,
        cliente__user=request.user
    )
    asig.completada= True
    asig.completada_el = timezone.now()   # ← ahora sí existe
    asig.save()

    # Notificación al coach
    coach = asig.rutina.owner
    Notification.objects.create(
        user=coach,
        message=(
            f"Tu cliente {asig.cliente.user.username} "
            f"completó la rutina “{asig.rutina.nombre}”."
        )
    )

    return redirect('cliente_mis_rutinas')

def cliente_resumen(request):
    cliente = get_object_or_404(Cliente, user=request.user)

    # 1. Fecha de hoy y primer día de la semana (lunes)
    today      = date.today()
    start_week = today - timedelta(days=today.weekday())

    # 2. Conteos
    completadas_semana = RutinaAsignada.objects.filter(
        cliente=cliente,
        completada=True,
        asignada_el__date__gte=start_week
    ).count()

    total_asignadas = RutinaAsignada.objects.filter(
        cliente=cliente
    ).count()

    progress = {
        'completadas_semana': completadas_semana,
        'total_asignadas':    total_asignadas,
    }
    
    asigns = RutinaAsignada.objects.filter(
        cliente=cliente,
        completada=True,
        completada_el__isnull=False
    ).order_by('completada_el')
    
    
    labels = []
    data   = []
    acumulado = 0
    for a in asigns:
        acumulado += 1
        fecha = a.completada_el.strftime('%d %b')
        labels.append(f"{a.rutina.nombre} ({fecha})")
        data.append(acumulado)
    

    return render(request, 'usuarios/cliente_resumen.html', {
        'progress':      progress,
        'chart_labels':  json.dumps(labels),  # igualamos nombres
        'chart_values':  json.dumps(data),
    })

@login_required
def cliente_mis_rutinas(request):
    cliente = get_object_or_404(Cliente, user=request.user)
    asignaciones = (
        RutinaAsignada.objects
        .filter(cliente=cliente)
        .select_related('rutina')
        .order_by('-asignada_el')
    )

    for a in asignaciones:
        details_list = []
        # 'a.detalles' es dict de {ej_id: {series,reps,duracion,…}}
        for ej_id, det in a.detalles.items():
            ej = a.rutina.ejercicios.filter(pk=ej_id).first()
            if not ej:
                continue
            details_list.append({
                'ejercicio':  ej,
                'series':      det.get('series', None),
                'reps':        det.get('reps', None),
                'duracion':    det.get('duracion', None),
            })
        a.details_list = details_list
        a.texto_comentario = a.comentarios or ''

    return render(request, 'usuarios/cliente_mis_rutinas.html', {
        'asignaciones': asignaciones
    })
    
    
@login_required
def cliente_contactar(request):
    cliente = get_object_or_404(Cliente, user=request.user)
    coach   = cliente.coach
    return render(request, 'usuarios/cliente_contactar.html', {
        'coach': coach
    })
# Create your views here.
