from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.index, name='index'),

    # Titulación
    path('titulaciones/', views.TitulacionListView.as_view(), name='titulaciones'),
    path('titulacion/create/', views.TitulacionCreateView.as_view(), name='titulacion-create'),
    path('titulacion/<int:pk>/update/', views.TitulacionUpdateView.as_view(), name='titulacion-update'),
    path('titulacion/<int:pk>/delete/', views.TitulacionDeleteView.as_view(), name='titulacion-delete'),

    # Asignatura
    path('asignaturas/', views.AsignaturaListView.as_view(), name='asignaturas'),
    path('asignatura/<int:pk>', views.AsignaturaDetailView.as_view(), name='asignatura-detail'),
    path('asignatura/create/', views.asignatura_create, name='asignatura-create'),
    path('asignatura/<int:pk>/update/', views.asignatura_update, name='asignatura-update'),
    path('asignatura/<int:pk>/delete/', views.asignatura_delete, name='asignatura-delete'),
    path('asignatura/<int:pk>/sesiones/', views.asignatura_sesiones, name='asignatura-sesiones'),

    # Profesor
    path('profesores/', views.ProfesorListView.as_view(), name='profesores'),
    path('profesor/<int:pk>', views.ProfesorDetailView.as_view(), name='profesor-detail'),
    path('profesor/create/', views.ProfesorCreateView.as_view(), name='profesor-create'),
    path('profesor/<int:pk>/update/', views.ProfesorUpdateView.as_view(), name='profesor-update'),
    path('profesor/<int:pk>/delete/', views.ProfesorDeleteView.as_view(), name='profesor-delete'),

    # Sesión
    path('sesiones/', views.SesionListView.as_view(), name='sesiones'),
    path('sesion/create/', views.SesionCreateView.as_view(), name='sesion-create'),
    path('sesion/<int:pk>/update/', views.SesionUpdateView.as_view(), name='sesion-update'),
    path('sesion/<int:pk>/delete/', views.SesionDeleteView.as_view(), name='sesion-delete'),
]
