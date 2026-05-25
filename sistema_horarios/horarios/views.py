from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .forms import (
    AsignaturaForm,
    AsignaturaSesionForm,
    ImportHorarioForm,
    ProfesorForm,
    RegistroForm,
    SesionForm,
    TitulacionForm,
)
from .import_export import excel_response, import_from_excel, pdf_response
from .filters import (
    build_filter_qs,
    count_active_filters,
    filter_asignaturas,
    filter_profesores,
    filter_sesiones,
    filter_titulaciones,
)
from .models import Asignatura, Profesor, Sesion, Titulacion


DIAS_ORDER = ['LUN', 'MAR', 'MIE', 'JUE', 'VIE']


class DuplicateSafeMixin:
    """Re-render form with a friendly message instead of a 500 on IntegrityError."""

    duplicate_message = 'Ya existe un registro con esos datos.'

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, self.duplicate_message)
            return self.form_invalid(form)


class ListFilterMixin:
    """Adds filter context for dropdown filters and pagination."""

    filter_list_keys = []

    def get_filter_context(self):
        user = self.request.user
        return {
            'filter_qs': build_filter_qs(self.request),
            'active_filter_count': count_active_filters(
                self.request, self.filter_list_keys
            ),
            'titulaciones_filtro': Titulacion.objects.filter(creado_por=user),
            'cursos_filtro': Asignatura.CURSOS,
            'dias_filtro': Sesion.DIAS_SEMANA,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_filter_context())
        return context


# ── Helpers ────────────────────────────────────────────────────────────────────

def detectar_conflictos(user):
    conflictos = []

    # Professor conflicts (within the same cuatrimestre)
    for profesor in (
        Profesor.objects.filter(creado_por=user)
        .prefetch_related('asignaturas__sesiones')
    ):
        for cuat_num, cuat_label in Asignatura.CUATRIMESTRES:
            sesion_map = {}
            for asignatura in profesor.asignaturas.filter(
                creado_por=user, cuatrimestre=cuat_num
            ):
                for sesion in asignatura.sesiones.all():
                    if sesion.id in sesion_map:
                        conflictos.append(
                            f"Conflicto de profesor ({cuat_label}): {profesor} imparte "
                            f"'{asignatura.nombre}' y '{sesion_map[sesion.id].nombre}' "
                            f"en la misma sesion ({sesion})."
                        )
                    else:
                        sesion_map[sesion.id] = asignatura

    # Same titulacion + curso + cuatrimestre + session for non-elective subjects
    for titulacion in Titulacion.objects.filter(creado_por=user):
        for curso_num, curso_label in Asignatura.CURSOS:
            for cuat_num, cuat_label in Asignatura.CUATRIMESTRES:
                asignaturas = list(
                    Asignatura.objects.filter(
                        titulacion=titulacion,
                        curso=curso_num,
                        cuatrimestre=cuat_num,
                        es_electiva=False,
                        creado_por=user,
                    ).prefetch_related('sesiones')
                )
                sesion_map = {}
                for asignatura in asignaturas:
                    for sesion in asignatura.sesiones.all():
                        if sesion.id in sesion_map:
                            conflictos.append(
                                f"Conflicto en {titulacion} — {curso_label}, {cuat_label}: "
                                f"'{asignatura.nombre}' y '{sesion_map[sesion.id].nombre}' "
                                f"comparten la sesion '{sesion}'."
                            )
                        else:
                            sesion_map[sesion.id] = asignatura

    return conflictos


def _construir_horario(asignaturas):
    """Build a weekly grid from a list of Asignatura instances."""
    bloques_dict = {}
    for asignatura in asignaturas:
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
        return []

    bloques = sorted(bloques_dict.values(), key=lambda x: x['hora_inicio'])
    horario = []

    for bloque in bloques:
        dias_slots = []
        for dia_code in DIAS_ORDER:
            asigs_in_slot = []
            for asignatura in asignaturas:
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
                                if asignatura.profesor else 'Sin profesor'
                            ),
                            'es_electiva': asignatura.es_electiva,
                        })
            dias_slots.append({'asignaturas': asigs_in_slot})

        horario.append({
            'hora_inicio': bloque['hora_inicio'],
            'hora_fin': bloque['hora_fin'],
            'dias': dias_slots,
        })

    return horario


def generar_horarios_por_titulacion(user):
    all_asignaturas = list(
        Asignatura.objects.filter(creado_por=user)
        .select_related('titulacion', 'profesor')
        .prefetch_related('sesiones')
    )

    result = []

    for titulacion in Titulacion.objects.filter(creado_por=user):
        asignaturas_tit = [a for a in all_asignaturas if a.titulacion_id == titulacion.id]
        if not asignaturas_tit:
            continue

        tit_data = {'codigo': titulacion.codigo, 'nombre': titulacion.nombre, 'cursos': []}

        for curso_num, curso_nombre in Asignatura.CURSOS:
            asignaturas_curso = [a for a in asignaturas_tit if a.curso == curso_num]
            if not asignaturas_curso:
                continue

            cuatrimestres_data = []
            for cuat_num, cuat_nombre in Asignatura.CUATRIMESTRES:
                asignaturas_cuat = [
                    a for a in asignaturas_curso if a.cuatrimestre == cuat_num
                ]
                horario = _construir_horario(asignaturas_cuat)
                if not horario:
                    continue
                cuatrimestres_data.append({
                    'numero': cuat_num,
                    'nombre': cuat_nombre,
                    'horario': horario,
                })

            if not cuatrimestres_data:
                continue

            tit_data['cursos'].append({
                'numero': curso_num,
                'nombre': curso_nombre,
                'cuatrimestres': cuatrimestres_data,
            })

        if tit_data['cursos']:
            result.append(tit_data)

    return result


# ── Auth ───────────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Bienvenido, {user.username}. Tu cuenta ha sido creada.')
            return redirect('index')
    else:
        form = RegistroForm()
    return render(request, 'registration/register.html', {'form': form})


# ── Home ───────────────────────────────────────────────────────────────────────

@login_required
def index(request):
    user = request.user
    num_profesores = Profesor.objects.filter(creado_por=user).count()
    num_asignaturas = Asignatura.objects.filter(creado_por=user).count()
    num_sesiones = Sesion.objects.filter(creado_por=user).count()

    num_visits = request.session.get('num_visits', 0) + 1
    request.session['num_visits'] = num_visits

    conflictos = detectar_conflictos(user)
    horarios_titulaciones = generar_horarios_por_titulacion(user)
    puede_exportar = not conflictos and (
        num_profesores or num_asignaturas or num_sesiones
    )

    import_form = None
    if request.method == 'POST' and request.POST.get('action') == 'import':
        import_form = ImportHorarioForm(request.POST, request.FILES)
        if import_form.is_valid():
            try:
                result = import_from_excel(request.user, import_form.cleaned_data['archivo'])
            except Exception:
                messages.error(
                    request,
                    'No se pudo leer el archivo. Usa un Excel exportado desde este sistema.',
                )
            else:
                c = result['created']
                if any(c.values()):
                    messages.success(
                        request,
                        f'Importacion completada: {c["titulaciones"]} titulacion(es), '
                        f'{c["profesores"]} profesor(es), {c["sesiones"]} sesion(es), '
                        f'{c["asignaturas"]} asignatura(s), {c["enlaces"]} enlace(s) de sesion.',
                    )
                else:
                    messages.info(request, 'No se importo ningun dato nuevo.')
                for aviso in result['skipped'][:20]:
                    messages.warning(request, aviso)
                if len(result['skipped']) > 20:
                    messages.warning(
                        request,
                        f'... y {len(result["skipped"]) - 20} aviso(s) mas.',
                    )
                return redirect('index')
    if import_form is None:
        import_form = ImportHorarioForm()

    return render(request, 'index.html', {
        'num_profesores': num_profesores,
        'num_asignaturas': num_asignaturas,
        'num_sesiones': num_sesiones,
        'num_visits': num_visits,
        'conflictos': conflictos,
        'horarios_titulaciones': horarios_titulaciones,
        'puede_exportar': puede_exportar,
        'import_form': import_form,
    })


@login_required
def export_horario(request, formato):
    conflictos = detectar_conflictos(request.user)
    if conflictos:
        messages.error(
            request,
            'No se puede exportar: resuelve los conflictos de horario antes de exportar.',
        )
        return redirect('index')
    if formato == 'excel':
        return excel_response(request.user)
    if formato == 'pdf':
        return pdf_response(request.user)
    messages.error(request, 'Formato de exportacion no valido.')
    return redirect('index')


# ── Titulacion CRUD ────────────────────────────────────────────────────────────

class TitulacionListView(ListFilterMixin, LoginRequiredMixin, generic.ListView):
    model = Titulacion
    template_name = 'horarios/titulacion_list.html'
    context_object_name = 'titulacion_list'
    paginate_by = 15
    filter_list_keys = []

    def get_queryset(self):
        qs = Titulacion.objects.filter(creado_por=self.request.user)
        return filter_titulaciones(qs, self.request)


class TitulacionCreateView(DuplicateSafeMixin, LoginRequiredMixin, CreateView):
    model = Titulacion
    form_class = TitulacionForm
    template_name = 'horarios/titulacion_form.html'
    success_url = reverse_lazy('titulaciones')
    duplicate_message = 'Ya existe una titulacion con ese codigo.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, f'Titulacion "{form.instance.nombre}" creada.')
        return super().form_valid(form)


class TitulacionUpdateView(DuplicateSafeMixin, LoginRequiredMixin, UpdateView):
    model = Titulacion
    form_class = TitulacionForm
    template_name = 'horarios/titulacion_form.html'
    success_url = reverse_lazy('titulaciones')
    duplicate_message = 'Ya existe una titulacion con ese codigo.'

    def get_queryset(self):
        return Titulacion.objects.filter(creado_por=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Titulacion "{form.instance.nombre}" actualizada.')
        return super().form_valid(form)


class TitulacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Titulacion
    template_name = 'horarios/titulacion_confirm_delete.html'
    success_url = reverse_lazy('titulaciones')

    def get_queryset(self):
        return Titulacion.objects.filter(creado_por=self.request.user)

    def form_valid(self, form):
        try:
            nombre = self.get_object().nombre
            result = super().form_valid(form)
            messages.success(self.request, f'Titulacion "{nombre}" eliminada.')
            return result
        except Exception:
            messages.error(
                self.request,
                'No se puede eliminar: esta titulacion tiene asignaturas asociadas.',
            )
            return redirect('titulaciones')


# ── Asignatura list/detail ─────────────────────────────────────────────────────

class AsignaturaListView(ListFilterMixin, LoginRequiredMixin, generic.ListView):
    model = Asignatura
    paginate_by = 15
    filter_list_keys = ['titulacion', 'curso', 'tipo']

    def get_queryset(self):
        qs = Asignatura.objects.filter(creado_por=self.request.user).select_related(
            'titulacion', 'profesor'
        )
        return filter_asignaturas(qs, self.request)


class AsignaturaDetailView(LoginRequiredMixin, generic.DetailView):
    model = Asignatura

    def get_queryset(self):
        return Asignatura.objects.filter(creado_por=self.request.user)


# ── Profesor list/detail ───────────────────────────────────────────────────────

class ProfesorListView(ListFilterMixin, LoginRequiredMixin, generic.ListView):
    model = Profesor
    paginate_by = 15
    filter_list_keys = ['titulacion']

    def get_queryset(self):
        qs = Profesor.objects.filter(creado_por=self.request.user)
        return filter_profesores(qs, self.request)


class ProfesorDetailView(LoginRequiredMixin, generic.DetailView):
    model = Profesor

    def get_queryset(self):
        return Profesor.objects.filter(creado_por=self.request.user)


# ── Sesion list ────────────────────────────────────────────────────────────────

class SesionListView(ListFilterMixin, LoginRequiredMixin, generic.ListView):
    model = Sesion
    paginate_by = 15
    filter_list_keys = ['dia', 'titulacion']

    def get_queryset(self):
        qs = Sesion.objects.filter(creado_por=self.request.user)
        return filter_sesiones(qs, self.request)


# ── Profesor CRUD ──────────────────────────────────────────────────────────────

class ProfesorCreateView(DuplicateSafeMixin, LoginRequiredMixin, CreateView):
    model = Profesor
    form_class = ProfesorForm
    template_name = 'horarios/profesor_form.html'
    success_url = reverse_lazy('profesores')

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Profesor creado exitosamente.')
        return super().form_valid(form)


class ProfesorUpdateView(DuplicateSafeMixin, LoginRequiredMixin, UpdateView):
    model = Profesor
    form_class = ProfesorForm
    template_name = 'horarios/profesor_form.html'
    success_url = reverse_lazy('profesores')

    def get_queryset(self):
        return Profesor.objects.filter(creado_por=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Profesor actualizado exitosamente.')
        return super().form_valid(form)


class ProfesorDeleteView(LoginRequiredMixin, DeleteView):
    model = Profesor
    template_name = 'horarios/profesor_confirm_delete.html'
    success_url = reverse_lazy('profesores')

    def get_queryset(self):
        return Profesor.objects.filter(creado_por=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Profesor eliminado exitosamente.')
        return super().form_valid(form)


# ── Sesion CRUD ────────────────────────────────────────────────────────────────

class SesionCreateView(DuplicateSafeMixin, LoginRequiredMixin, CreateView):
    model = Sesion
    form_class = SesionForm
    template_name = 'horarios/sesion_form.html'
    success_url = reverse_lazy('sesiones')

    def form_valid(self, form):
        form.instance.creado_por = self.request.user
        messages.success(self.request, 'Sesion creada exitosamente.')
        return super().form_valid(form)


class SesionUpdateView(DuplicateSafeMixin, LoginRequiredMixin, UpdateView):
    model = Sesion
    form_class = SesionForm
    template_name = 'horarios/sesion_form.html'
    success_url = reverse_lazy('sesiones')

    def get_queryset(self):
        return Sesion.objects.filter(creado_por=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Sesion actualizada exitosamente.')
        return super().form_valid(form)


class SesionDeleteView(LoginRequiredMixin, DeleteView):
    model = Sesion
    template_name = 'horarios/sesion_confirm_delete.html'
    success_url = reverse_lazy('sesiones')

    def get_queryset(self):
        return Sesion.objects.filter(creado_por=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Sesion eliminada exitosamente.')
        return super().form_valid(form)


# ── Asignatura CRUD (function views) ──────────────────────────────────────────

@login_required
def asignatura_create(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        post_data.pop('sesiones', None)
        form = AsignaturaForm(post_data, user=request.user)
        if form.is_valid():
            try:
                asignatura = form.save(commit=False)
                asignatura.creado_por = request.user
                asignatura.save()
            except IntegrityError:
                messages.error(
                    request,
                    f'Ya existe una asignatura con el codigo "{form.cleaned_data["codigo"]}".',
                )
            else:
                messages.success(request, f'Asignatura "{asignatura.codigo}" creada exitosamente.')
                return redirect('asignaturas')
    else:
        form = AsignaturaForm(user=request.user)
    return render(request, 'horarios/asignatura_form.html', {'form': form})


@login_required
def asignatura_update(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk, creado_por=request.user)
    if request.method == 'POST':
        form = AsignaturaForm(request.POST, instance=asignatura, user=request.user)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                messages.error(
                    request,
                    f'Ya existe una asignatura con el codigo "{form.cleaned_data["codigo"]}".',
                )
            else:
                messages.success(request, f'Asignatura "{asignatura.codigo}" actualizada.')
                return redirect('asignaturas')
    else:
        form = AsignaturaForm(instance=asignatura, user=request.user)
    return render(request, 'horarios/asignatura_form.html', {'form': form, 'asignatura': asignatura})


@login_required
def asignatura_delete(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk, creado_por=request.user)
    if request.method == 'POST':
        codigo = asignatura.codigo
        asignatura.delete()
        messages.success(request, f'Asignatura "{codigo}" eliminada.')
        return redirect('asignaturas')
    return render(request, 'horarios/asignatura_confirm_delete.html', {'asignatura': asignatura})


@login_required
def asignatura_sesiones(request, pk):
    asignatura = get_object_or_404(Asignatura, pk=pk, creado_por=request.user)
    if request.method == 'POST':
        form = AsignaturaSesionForm(request.POST, instance=asignatura, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sesiones actualizadas para "{asignatura.codigo}".')
            return redirect('asignatura-detail', pk=asignatura.pk)
    else:
        form = AsignaturaSesionForm(instance=asignatura, user=request.user)
    return render(request, 'horarios/asignatura_sesion_form.html', {
        'form': form,
        'asignatura': asignatura,
    })
