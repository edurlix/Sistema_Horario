from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('asignaturas/', views.AsignaturaListView.as_view(), name='asignaturas'),
    path('asignatura/<int:pk>', views.AsignaturaDetailView.as_view(), name='asignatura-detail'),
    path('profesores/', views.ProfesorListView.as_view(), name='profesores'),
    path('profesor/<int:pk>', views.ProfesorDetailView.as_view(), name='profesor-detail'),
    path('sesiones/', views.SesionListView.as_view(), name='sesiones'),
]
