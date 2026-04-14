from django.shortcuts import render
from django.views import generic
from .models import Profesor, Sesion, Asignatura

def index(request):
    num_profesores = Profesor.objects.count()
    num_asignaturas = Asignatura.objects.count()
    num_sesiones = Sesion.objects.count()
    
    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits
    
    return render(
        request,
        'index.html',
        context={
            'num_profesores': num_profesores,
            'num_asignaturas': num_asignaturas,
            'num_sesiones': num_sesiones,
            'num_visits': num_visits,
        }
    )


class AsignaturaListView(generic.ListView):
    model = Asignatura
    paginate_by = 5


class AsignaturaDetailView(generic.DetailView):
    model = Asignatura


class ProfesorListView(generic.ListView):
    model = Profesor
    paginate_by = 5


class ProfesorDetailView(generic.DetailView):
    model = Profesor


class SesionListView(generic.ListView):
    model = Sesion
    paginate_by = 5
