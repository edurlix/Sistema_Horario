from django import forms
from .models import Profesor, Sesion, Asignatura, Titulacion

FC = {'class': 'form-control'}


class TitulacionForm(forms.ModelForm):
    class Meta:
        model = Titulacion
        fields = ['codigo', 'nombre']
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre',
        }
        widgets = {
            'codigo': forms.TextInput(attrs={**FC, 'placeholder': 'Ej: II, IR, DG...'}),
            'nombre': forms.TextInput(attrs={**FC, 'placeholder': 'Ej: Ingeniería Informática'}),
        }


class ProfesorForm(forms.ModelForm):
    class Meta:
        model = Profesor
        fields = ['nombre', 'apellidos', 'email']
        labels = {
            'nombre': 'Nombre',
            'apellidos': 'Apellidos',
            'email': 'Correo electrónico',
        }
        widgets = {
            'nombre':    forms.TextInput(attrs=FC),
            'apellidos': forms.TextInput(attrs=FC),
            'email':     forms.EmailInput(attrs=FC),
        }


class SesionForm(forms.ModelForm):
    class Meta:
        model = Sesion
        fields = ['dia', 'hora_inicio', 'hora_fin']
        labels = {
            'dia': 'Día',
            'hora_inicio': 'Hora de inicio',
            'hora_fin': 'Hora de fin',
        }
        widgets = {
            'dia':         forms.Select(attrs=FC),
            'hora_inicio': forms.TimeInput(attrs={**FC, 'type': 'time'}),
            'hora_fin':    forms.TimeInput(attrs={**FC, 'type': 'time'}),
        }


class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['codigo', 'nombre', 'titulacion', 'curso', 'es_electiva', 'profesor']
        labels = {
            'codigo':      'Código',
            'nombre':      'Nombre',
            'titulacion':  'Titulación',
            'curso':       'Curso',
            'es_electiva': 'Es electiva',
            'profesor':    'Profesor',
        }
        widgets = {
            'codigo':     forms.TextInput(attrs=FC),
            'nombre':     forms.TextInput(attrs=FC),
            'titulacion': forms.Select(attrs=FC),
            'curso':      forms.Select(attrs=FC),
            'profesor':   forms.Select(attrs=FC),
        }


class AsignaturaSesionForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['sesiones']
        labels = {'sesiones': 'Sesiones disponibles'}
        widgets = {'sesiones': forms.CheckboxSelectMultiple()}

    def clean_sesiones(self):
        sesiones = self.cleaned_data.get('sesiones')
        if not sesiones or not self.instance or not self.instance.pk:
            return sesiones

        asignatura = self.instance
        errores = []

        for sesion in sesiones:
            # Professor conflict: same professor already has another subject at this session
            if asignatura.profesor:
                conflicto = (
                    Asignatura.objects.filter(profesor=asignatura.profesor, sesiones=sesion)
                    .exclude(pk=asignatura.pk)
                    .first()
                )
                if conflicto:
                    errores.append(
                        f"Conflicto de profesor: {asignatura.profesor} ya imparte "
                        f"'{conflicto.nombre}' en la sesión '{sesion}'."
                    )

            # Course slot conflict: a non-elective subject of the same degree+year
            # already occupies this session slot (electives are exempt).
            if not asignatura.es_electiva:
                conflicto = (
                    Asignatura.objects.filter(
                        titulacion=asignatura.titulacion,
                        curso=asignatura.curso,
                        sesiones=sesion,
                        es_electiva=False,
                    )
                    .exclude(pk=asignatura.pk)
                    .first()
                )
                if conflicto:
                    errores.append(
                        f"La sesión '{sesion}' ya está ocupada por '{conflicto.nombre}' "
                        f"(obligatoria de {asignatura.get_curso_display()} — "
                        f"{asignatura.titulacion}). "
                        f"Solo las asignaturas electivas pueden compartir franja horaria."
                    )

        if errores:
            raise forms.ValidationError(errores)

        return sesiones
