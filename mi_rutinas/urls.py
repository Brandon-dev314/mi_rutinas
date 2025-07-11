"""
URL configuration for mi_rutinas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from usuarios import views as usuarios_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',usuarios_views.bienvenida, name='bienvenida'),    
    
    path('dashboard/', usuarios_views.cliente_resumen,        name='cliente_resumen'),
    path('dashboard/rutinas/', usuarios_views.cliente_mis_rutinas, name='cliente_mis_rutinas'),
    path('dashboard/contactar/', usuarios_views.cliente_contactar, name='cliente_contactar'),   
    path('dashboard/rutinas/<int:asig_id>/completar/', usuarios_views.cliente_completar, name='cliente_completar'),    
    
    path('register/', usuarios_views.registro, name='registro'),
    path('login/',usuarios_views.iniciar_sesion,name='login'),
    path('logout/',usuarios_views.cerrar_sesion, name='logout'),
    path('panel/', usuarios_views.panel_resumen, name='panel_resumen'),
    path('panel/rutinas/',usuarios_views.panel_rutinas,name='panel_rutinas'),
    
    path('panel/clientes/', usuarios_views.panel_clientes, name='panel_clientes'),
    path('panel/clientes/<int:cliente_pk>/rutinas/', usuarios_views.cliente_rutinas, name='cliente_rutinas'),
    path('panel/clientes/<int:asign_id>/delete_rutina/',usuarios_views.cliente_asignacion_eliminar,name='cliente_asignacion_eliminar'),
    path('panel/clientes/nuevo/', usuarios_views.cliente_crear, name='cliente_crear'),
    path('panel/clientes/<int:pk>/edit/', usuarios_views.cliente_editar,name='cliente_editar'),
    path('panel/clientes/<int:pk>/delete/', usuarios_views.cliente_eliminar, name='cliente_eliminar'),
]
