from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profesor, Sesion, Asignatura, Titulacion

FC = {'class': 'form-control'}


# ── Authentication ─────────────────────────────────────────────────────────────

class RegistroForm(UserCreationForm):
    """Styled registration form."""

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


# ── Titulacion ─────────────────────────────────────────────────────────────────

class TitulacionForm(forms.ModelForm):
    class Meta:
        model = Titulacion
        fields = ['codigo', 'nombre']
        labels = {'codigo': 'Código', 'nombre': 'Nombre'}
        widgets = {
            'codigo': forms.TextInput(attrs={**FC, 'placeholder': 'Ej: II, IR, GIIA...'}),
            'nombre': forms.TextInput(attrs={**FC, 'placeholder': 'Ej: Ingeniería Informática'}),
        }


# ── Profesor ───────────────────────────────────────────────────────────────────

class ProfesorForm(forms.ModelForm):
    class Meta:
        model = Profesor
        fields = ['nombre', 'apellidos', 'email']
        labels = {'nombre': 'Nombre', 'apellidos': 'Apellidos', 'email': 'Correo electrónico'}
        widgets = {
            'nombre':    forms.TextInput(attrs=FC),
            'apellidos': forms.TextInput(attrs=FC),
            'email':     forms.EmailInput(attrs=FC),
        }


# ── Sesion ─────────────────────────────────────────────────────────────────────

class SesionForm(forms.ModelForm):
    class Meta:
        model = Sesion
        fields = ['dia', 'hora_inicio', 'hora_fin']
        labels = {'dia': 'Día', 'hora_inicio': 'Hora de inicio', 'hora_fin': 'Hora de fin'}
        widgets = {
            'dia':         forms.Select(attrs=FC),
            'hora_inicio': forms.TimeInput(attrs={**FC, 'type': 'time'}),
            'hora_fin':    forms.TimeInput(attrs={**FC, 'type': 'time'}),
        }


# ── Asignatura ─────────────────────────────────────────────────────────────────

class AsignaturaForm(forms.ModelForm):
    """
    Accepts `user` kwarg to restrict titulacion/profesor dropdowns to the
    current user's own objects.
    """

    class Meta:
        model = Asignatura
        fields = ['codigo', 'nombre', 'titulacion', 'curso', 'cuatrimestre', 'es_electiva', 'profesor']
        labels = {
            'codigo':       'Código',
            'nombre':       'Nombre',
            'titulacion':   'Titulación',
            'curso':        'Curso',
            'cuatrimestre': 'Cuatrimestre',
            'es_electiva':  'Es electiva',
            'profesor':     'Profesor',
        }
        widgets = {
            'codigo':       forms.TextInput(attrs=FC),
            'nombre':       forms.TextInput(attrs=FC),
            'titulacion':   forms.Select(attrs=FC),
            'curso':        forms.Select(attrs=FC),
            'cuatrimestre': forms.Select(attrs=FC),
            'profesor':     forms.Select(attrs=FC),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['titulacion'].queryset = Titulacion.objects.filter(creado_por=self.user)
            self.fields['profesor'].queryset = Profesor.objects.filter(creado_por=self.user)


class AsignaturaSesionForm(forms.ModelForm):
    """
    Accepts `user` kwarg to restrict sesion choices and validate conflicts only
    within the current user's own data.
    """

    class Meta:
        model = Asignatura
        fields = ['sesiones']
        labels = {'sesiones': 'Sesiones disponibles'}
        widgets = {'sesiones': forms.CheckboxSelectMultiple()}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['sesiones'].queryset = Sesion.objects.filter(creado_por=self.user)

    def clean_sesiones(self):
        sesiones = self.cleaned_data.get('sesiones')
        if not sesiones or not self.instance or not self.instance.pk:
            return sesiones

        asignatura = self.instance
        errores = []

        for sesion in sesiones:
            # Professor conflict within the user's own schedule
            if asignatura.profesor:
                conflicto = (
                    Asignatura.objects.filter(
                        profesor=asignatura.profesor,
                        cuatrimestre=asignatura.cuatrimestre,
                        sesiones=sesion,
                        creado_por=self.user,
                    )
                    .exclude(pk=asignatura.pk)
                    .first()
                )
                if conflicto:
                    errores.append(
                        f"Conflicto de profesor: {asignatura.profesor} ya imparte "
                        f"'{conflicto.nombre}' en la sesion '{sesion}'."
                    )

            # Non-elective course slot conflict (same titulacion, curso and cuatrimestre)
            if not asignatura.es_electiva:
                conflicto = (
                    Asignatura.objects.filter(
                        titulacion=asignatura.titulacion,
                        curso=asignatura.curso,
                        cuatrimestre=asignatura.cuatrimestre,
                        sesiones=sesion,
                        es_electiva=False,
                        creado_por=self.user,
                    )
                    .exclude(pk=asignatura.pk)
                    .first()
                )
                if conflicto:
                    errores.append(
                        f"La sesion '{sesion}' ya esta ocupada por '{conflicto.nombre}' "
                        f"(obligatoria de {asignatura.get_curso_display()}, "
                        f"{asignatura.get_cuatrimestre_display()} — {asignatura.titulacion}). "
                        f"Solo las electivas pueden compartir franja horaria."
                    )

        if errores:
            raise forms.ValidationError(errores)

        return sesiones
