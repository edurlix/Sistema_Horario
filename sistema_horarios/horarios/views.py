from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Profesor, Sesion, Asignatura
from .forms import ProfesorForm, SesionForm, AsignaturaForm, AsignaturaSesionForm
from collections import defaultdict

# Función index (la que faltaba)
def index(request):
    num_profesores = Profesor.objects.count()
    num_asignaturas = Asignatura.objects.count()
    num_sesiones = Sesion.objects.count()
    
    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits
    
    # Verificar conflictos para mostrar alerta (RF-02)
    conflictos = []
    for asignatura in Asignatura.objects.all():
        try:
            asignatura.clean()
        except Exception as e:
            conflictos.append(f"{asignatura.codigo}: {str(e)}")
    
    # Generar tabla de horario semanal
    horario_semanal = generar_horario_semanal()
    
    return render(
        request,
        'index.html',
        context={
            'num_profesores': num_profesores,
            'num_asignaturas': num_asignaturas,
            'num_sesiones': num_sesiones,
            'num_visits': num_visits,
            'conflictos': conflictos,
            'horario_semanal': horario_semanal,
        }
    )

def generar_horario_semanal():
    """Versión simplificada del horario semanal"""
    
    # Días de la semana
    dias = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE']
    dias_nombres = {'LUN': 'Lunes', 'MAR': 'Martes', 'MIE': 'Miércoles', 'JUE': 'Jueves', 'VIE': 'Viernes'}
    
    # Obtener todos los bloques horarios únicos ordenados
    todas_sesiones = Sesion.objects.all().order_by('hora_inicio', 'dia')
    
    # Crear lista de bloques únicos
    bloques_dict = {}
    for sesion in todas_sesiones:
        hora_key = f"{sesion.hora_inicio.strftime('%H:%M')}-{sesion.hora_fin.strftime('%H:%M')}"
        if hora_key not in bloques_dict:
            bloques_dict[hora_key] = {
                'hora_inicio': sesion.hora_inicio,
                'hora_fin': sesion.hora_fin,
                'hora_key': hora_key
            }
    
    bloques = list(bloques_dict.values())
    bloques.sort(key=lambda x: x['hora_inicio'])
    
    # Crear estructura de datos para el horario
    horario = []
    for bloque in bloques:
        fila = {
            'hora_inicio': bloque['hora_inicio'],
            'hora_fin': bloque['hora_fin'],
            'lunes': None,
            'martes': None,
            'miercoles': None,
            'jueves': None,
            'viernes': None
        }
        horario.append(fila)
    
    # Llenar con asignaturas
    asignaturas = Asignatura.objects.all().prefetch_related('sesiones', 'profesor')
    
    for asignatura in asignaturas:
        for sesion in asignatura.sesiones.all():
            hora_key = f"{sesion.hora_inicio.strftime('%H:%M')}-{sesion.hora_fin.strftime('%H:%M')}"
            
            # Encontrar la fila correspondiente
            for fila in horario:
                if f"{fila['hora_inicio'].strftime('%H:%M')}-{fila['hora_fin'].strftime('%H:%M')}" == hora_key:
                    # Asignar al día correspondiente
                    if sesion.dia == 'LUN':
                        fila['lunes'] = {
                            'codigo': asignatura.codigo,
                            'nombre': asignatura.nombre,
                            'profesor': str(asignatura.profesor) if asignatura.profesor else 'Sin prof',
                            'titulacion': asignatura.get_titulacion_display(),
                            'curso': asignatura.get_curso_display(),
                            'asignatura': asignatura
                        }
                    elif sesion.dia == 'MAR':
                        fila['martes'] = {
                            'codigo': asignatura.codigo,
                            'nombre': asignatura.nombre,
                            'profesor': str(asignatura.profesor) if asignatura.profesor else 'Sin prof',
                            'titulacion': asignatura.get_titulacion_display(),
                            'curso': asignatura.get_curso_display(),
                            'asignatura': asignatura
                        }
                    elif sesion.dia == 'MIE':
                        fila['miercoles'] = {
                            'codigo': asignatura.codigo,
                            'nombre': asignatura.nombre,
                            'profesor': str(asignatura.profesor) if asignatura.profesor else 'Sin prof',
                            'titulacion': asignatura.get_titulacion_display(),
                            'curso': asignatura.get_curso_display(),
                            'asignatura': asignatura
                        }
                    elif sesion.dia == 'JUE':
                        fila['jueves'] = {
                            'codigo': asignatura.codigo,
                            'nombre': asignatura.nombre,
                            'profesor': str(asignatura.profesor) if asignatura.profesor else 'Sin prof',
                            'titulacion': asignatura.get_titulacion_display(),
                            'curso': asignatura.get_curso_display(),
                            'asignatura': asignatura
                        }
                    elif sesion.dia == 'VIE':
                        fila['viernes'] = {
                            'codigo': asignatura.codigo,
                            'nombre': asignatura.nombre,
                            'profesor': str(asignatura.profesor) if asignatura.profesor else 'Sin prof',
                            'titulacion': asignatura.get_titulacion_display(),
                            'curso': asignatura.get_curso_display(),
                            'asignatura': asignatura
                        }
                    break
    
    return horario

# Vistas basadas en clases (ListView, DetailView)
class AsignaturaListView(generic.ListView):
    model = Asignatura
    paginate_by = 10

class AsignaturaDetailView(generic.DetailView):
    model = Asignatura

class ProfesorListView(generic.ListView):
    model = Profesor
    paginate_by = 10

class ProfesorDetailView(generic.DetailView):
    model = Profesor

class SesionListView(generic.ListView):
    model = Sesion
    paginate_by = 10

# Vistas para Profesor CRUD
class ProfesorCreateView(LoginRequiredMixin, CreateView):
    model = Profesor
    form_class = ProfesorForm
    template_name = 'horarios/profesor_form.html'
    success_url = reverse_lazy('profesores')
    
    def form_valid(self, form):
        messages.success(self.request, 'Profesor creado exitosamente.')
        return super().form_valid(form)

class ProfesorUpdateView(LoginRequiredMixin, UpdateView):
    model = Profesor
    form_class = ProfesorForm
    template_name = 'horarios/profesor_form.html'
    success_url = reverse_lazy('profesores')
    
    def form_valid(self, form):
        messages.success(self.request, 'Profesor actualizado exitosamente.')
        return super().form_valid(form)

class ProfesorDeleteView(LoginRequiredMixin, DeleteView):
    model = Profesor
    template_name = 'horarios/profesor_confirm_delete.html'
    success_url = reverse_lazy('profesores')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Profesor eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)

# Vistas para Sesion CRUD
class SesionCreateView(LoginRequiredMixin, CreateView):
    model = Sesion
    form_class = SesionForm
    template_name = 'horarios/sesion_form.html'
    success_url = reverse_lazy('sesiones')
    
    def form_valid(self, form):
        messages.success(self.request, 'Sesión creada exitosamente.')
        return super().form_valid(form)

class SesionUpdateView(LoginRequiredMixin, UpdateView):
    model = Sesion
    form_class = SesionForm
    template_name = 'horarios/sesion_form.html'
    success_url = reverse_lazy('sesiones')
    
    def form_valid(self, form):
        messages.success(self.request, 'Sesión actualizada exitosamente.')
        return super().form_valid(form)

class SesionDeleteView(LoginRequiredMixin, DeleteView):
    model = Sesion
    template_name = 'horarios/sesion_confirm_delete.html'
    success_url = reverse_lazy('sesiones')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Sesión eliminada exitosamente.')
        return super().delete(request, *args, **kwargs)

# Vistas basadas en funciones para Asignatura (para evitar el error ManyToMany)
@login_required
def asignatura_create(request):
    if request.method == 'POST':
        # Crear una copia mutable del POST
        post_data = request.POST.copy()
        
        # Eliminar 'sesiones' si existe (para evitar el error)
        if 'sesiones' in post_data:
            del post_data['sesiones']
        
        form = AsignaturaForm(post_data)
        if form.is_valid():
            asignatura = form.save()
            messages.success(request, f'Asignatura "{asignatura.codigo}" creada exitosamente.')
            return redirect('asignaturas')
        else:
            messages.error(request, f'Error: {form.errors}')
    else:
        form = AsignaturaForm()
    
    return render(request, 'horarios/asignatura_form.html', {'form': form})
@login_required
def asignatura_update(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    
    if request.method == 'POST':
        form = AsignaturaForm(request.POST, instance=asignatura)
        if form.is_valid():
            form.save()
            messages.success(request, f'Asignatura "{asignatura.codigo}" actualizada exitosamente.')
            return redirect('asignaturas')
    else:
        form = AsignaturaForm(instance=asignatura)
    
    return render(request, 'horarios/asignatura_form.html', {'form': form})

@login_required
def asignatura_delete(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    
    if request.method == 'POST':
        codigo = asignatura.codigo
        asignatura.delete()
        messages.success(request, f'Asignatura "{codigo}" eliminada exitosamente.')
        return redirect('asignaturas')
    
    return render(request, 'horarios/asignatura_confirm_delete.html', {'asignatura': asignatura})

@login_required
def asignatura_sesiones(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk)
    
    if request.method == 'POST':
        form = AsignaturaSesionForm(request.POST, instance=asignatura)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sesiones actualizadas para "{asignatura.codigo}".')
            return redirect('asignatura-detail', pk=asignatura.pk)
    else:
        form = AsignaturaSesionForm(instance=asignatura)
    
    return render(request, 'horarios/asignatura_sesion_form.html', {'form': form, 'asignatura': asignatura})
