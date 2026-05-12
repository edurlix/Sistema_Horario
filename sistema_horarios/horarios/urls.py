from django.urls import path
from . import views

urlpatterns = [
    # Vistas principales
    path('', views.index, name='index'),
    path('asignaturas/', views.AsignaturaListView.as_view(), name='asignaturas'),
    path('asignatura/<int:pk>', views.AsignaturaDetailView.as_view(), name='asignatura-detail'),
    path('profesores/', views.ProfesorListView.as_view(), name='profesores'),
    path('profesor/<int:pk>', views.ProfesorDetailView.as_view(), name='profesor-detail'),
    path('sesiones/', views.SesionListView.as_view(), name='sesiones'),
    
    # CRUD para Profesor
    path('profesor/create/', views.ProfesorCreateView.as_view(), name='profesor-create'),
    path('profesor/<int:pk>/update/', views.ProfesorUpdateView.as_view(), name='profesor-update'),
    path('profesor/<int:pk>/delete/', views.ProfesorDeleteView.as_view(), name='profesor-delete'),
    
    # CRUD para Sesion
    path('sesion/create/', views.SesionCreateView.as_view(), name='sesion-create'),
    path('sesion/<int:pk>/update/', views.SesionUpdateView.as_view(), name='sesion-update'),
    path('sesion/<int:pk>/delete/', views.SesionDeleteView.as_view(), name='sesion-delete'),
    
    # CRUD para Asignatura - USANDO VISTAS BASADAS EN FUNCIONES
    path('asignatura/create/', views.asignatura_create, name='asignatura-create'),
    path('asignatura/<int:pk>/update/', views.asignatura_update, name='asignatura-update'),
    path('asignatura/<int:pk>/delete/', views.asignatura_delete, name='asignatura-delete'),
    path('asignatura/<int:pk>/sesiones/', views.asignatura_sesiones, name='asignatura-sesiones'),
]
