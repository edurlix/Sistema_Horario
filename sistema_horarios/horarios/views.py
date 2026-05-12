from django.shortcuts import render, redirect, get_object_or_404
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import Profesor, Sesion, Asignatura, Titulacion
from .forms import ProfesorForm, SesionForm, AsignaturaForm, AsignaturaSesionForm, TitulacionForm


DIAS_ORDER = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE']


# ── Schedule generation ────────────────────────────────────────────────────────

def detectar_conflictos():
    """Return a list of human-readable conflict strings to display on the home page."""
    conflictos = []

    # Professor conflicts
    for profesor in Profesor.objects.prefetch_related('asignaturas__sesiones'):
        sesion_map = {}
        for asignatura in profesor.asignaturas.all():
            for sesion in asignatura.sesiones.all():
                if sesion.id in sesion_map:
                    conflictos.append(
                        f"Conflicto de profesor: {profesor} imparte "
                        f"'{asignatura.nombre}' y '{sesion_map[sesion.id].nombre}' "
                        f"en la misma sesión ({sesion})."
                    )
                else:
                    sesion_map[sesion.id] = asignatura

    # Same titulación + curso + session conflicts (non-elective only)
    for titulacion in Titulacion.objects.all():
        for curso_num, curso_label in Asignatura.CURSOS:
            asignaturas = list(
                Asignatura.objects.filter(
                    titulacion=titulacion, curso=curso_num, es_electiva=False
                ).prefetch_related('sesiones')
            )
            sesion_map = {}
            for asignatura in asignaturas:
                for sesion in asignatura.sesiones.all():
                    if sesion.id in sesion_map:
                        conflictos.append(
                            f"Conflicto en {titulacion} — {curso_label}: "
                            f"'{asignatura.nombre}' y '{sesion_map[sesion.id].nombre}' "
                            f"comparten la sesión '{sesion}'."
                        )
                    else:
                        sesion_map[sesion.id] = asignatura

    return conflictos


def generar_horarios_por_titulacion():
    """
    Returns a list of dicts, one per titulación that has sessions configured:
      { codigo, nombre, cursos: [ { numero, nombre, horario: [ { hora_inicio, hora_fin,
        dias: [ { asignaturas: [{codigo, nombre, profesor, es_electiva}] } x5 ] } ] } ] }
    """
    all_asignaturas = list(
        Asignatura.objects.select_related('titulacion', 'profesor')
        .prefetch_related('sesiones')
    )

    result = []

    for titulacion in Titulacion.objects.all():
        asignaturas_tit = [a for a in all_asignaturas if a.titulacion_id == titulacion.id]
        if not asignaturas_tit:
            continue

        tit_data = {
            'codigo': titulacion.codigo,
            'nombre': titulacion.nombre,
            'cursos': [],
        }

        for curso_num, curso_nombre in Asignatura.CURSOS:
            asignaturas_curso = [a for a in asignaturas_tit if a.curso == curso_num]
            if not asignaturas_curso:
                continue

            # Collect unique time blocks used by this titulación + curso
            bloques_dict = {}
            for asignatura in asignaturas_curso:
                for sesion in asignatura.sesiones.all():
                    hora_key = (
                        f"{sesion.hora_inicio.strftime('%H:%M')}"
                        f"-{sesion.hora_fin.strftime('%H:%M')}"
                    )
                    if hora_key not in bloques_dict:
                        bloques_dict[hora_key] = {
                            'hora_inicio': sesion.hora_inicio,
                            'hora_fin': sesion.hora_fin,
                        }

            if not bloques_dict:
                continue

            bloques = sorted(bloques_dict.values(), key=lambda x: x['hora_inicio'])

            # Build the weekly grid
            horario = []
            for bloque in bloques:
                dias_slots = []
                for dia_code in DIAS_ORDER:
                    asigs_in_slot = []
                    for asignatura in asignaturas_curso:
                        for sesion in asignatura.sesiones.all():
                            if (
                                sesion.dia == dia_code
                                and sesion.hora_inicio == bloque['hora_inicio']
                                and sesion.hora_fin == bloque['hora_fin']
                            ):
                                asigs_in_slot.append({
                                    'codigo': asignatura.codigo,
                                    'nombre': asignatura.nombre,
                                    'profesor': (
                                        str(asignatura.profesor)
                                        if asignatura.profesor
                                        else 'Sin profesor'
                                    ),
                                    'es_electiva': asignatura.es_electiva,
                                })
                    dias_slots.append({'asignaturas': asigs_in_slot})

                horario.append({
                    'hora_inicio': bloque['hora_inicio'],
                    'hora_fin': bloque['hora_fin'],
                    'dias': dias_slots,
                })

            tit_data['cursos'].append({
                'numero': curso_num,
                'nombre': curso_nombre,
                'horario': horario,
            })

        if tit_data['cursos']:
            result.append(tit_data)

    return result


# ── Home ───────────────────────────────────────────────────────────────────────

def index(request):
    num_profesores = Profesor.objects.count()
    num_asignaturas = Asignatura.objects.count()
    num_sesiones = Sesion.objects.count()

    num_visits = request.session.get('num_visits', 0) + 1
    request.session['num_visits'] = num_visits

    conflictos = detectar_conflictos()
    horarios_titulaciones = generar_horarios_por_titulacion()

    return render(request, 'index.html', {
        'num_profesores': num_profesores,
        'num_asignaturas': num_asignaturas,
        'num_sesiones': num_sesiones,
        'num_visits': num_visits,
        'conflictos': conflictos,
        'horarios_titulaciones': horarios_titulaciones,
    })


# ── Titulacion CRUD ────────────────────────────────────────────────────────────

class TitulacionListView(generic.ListView):
    model = Titulacion
    template_name = 'horarios/titulacion_list.html'
    context_object_name = 'titulacion_list'


class TitulacionCreateView(LoginRequiredMixin, CreateView):
    model = Titulacion
    form_class = TitulacionForm
    template_name = 'horarios/titulacion_form.html'
    success_url = reverse_lazy('titulaciones')

    def form_valid(self, form):
        messages.success(self.request, f'Titulación "{form.instance.nombre}" creada exitosamente.')
        return super().form_valid(form)


class TitulacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Titulacion
    form_class = TitulacionForm
    template_name = 'horarios/titulacion_form.html'
    success_url = reverse_lazy('titulaciones')

    def form_valid(self, form):
        messages.success(self.request, f'Titulación "{form.instance.nombre}" actualizada.')
        return super().form_valid(form)


class TitulacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Titulacion
    template_name = 'horarios/titulacion_confirm_delete.html'
    success_url = reverse_lazy('titulaciones')

    def form_valid(self, form):
        try:
            nombre = self.get_object().nombre
            result = super().form_valid(form)
            messages.success(self.request, f'Titulación "{nombre}" eliminada.')
            return result
        except Exception:
            messages.error(
                self.request,
                'No se puede eliminar esta titulación porque tiene asignaturas asociadas.',
            )
            return redirect('titulaciones')


# ── List / Detail Views ────────────────────────────────────────────────────────

class AsignaturaListView(generic.ListView):
    model = Asignatura
    paginate_by = 15


class AsignaturaDetailView(generic.DetailView):
    model = Asignatura


class ProfesorListView(generic.ListView):
    model = Profesor
    paginate_by = 15


class ProfesorDetailView(generic.DetailView):
    model = Profesor


class SesionListView(generic.ListView):
    model = Sesion
    paginate_by = 15


# ── Profesor CRUD ──────────────────────────────────────────────────────────────

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

    def form_valid(self, form):
        messages.success(self.request, 'Profesor eliminado exitosamente.')
        return super().form_valid(form)


# ── Sesion CRUD ────────────────────────────────────────────────────────────────

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

    def form_valid(self, form):
        messages.success(self.request, 'Sesión eliminada exitosamente.')
        return super().form_valid(form)


# ── Asignatura CRUD (function views to avoid M2M issues) ──────────────────────

@login_required
def asignatura_create(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data.pop('sesiones', None)
        form = AsignaturaForm(post_data)
        if form.is_valid():
            asignatura = form.save()
            messages.success(request, f'Asignatura "{asignatura.codigo}" creada exitosamente.')
            return redirect('asignaturas')
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
    return render(request, 'horarios/asignatura_form.html', {'form': form, 'asignatura': asignatura})


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
    return render(request, 'horarios/asignatura_sesion_form.html', {
        'form': form,
        'asignatura': asignatura,
    })
