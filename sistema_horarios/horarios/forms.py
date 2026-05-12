from django import forms
from .models import Profesor, Sesion, Asignatura

class ProfesorForm(forms.ModelForm):
    class Meta:
        model = Profesor
        fields = ['nombre', 'apellidos', 'email']
        labels = {
            'nombre': 'Nombre',
            'apellidos': 'Apellidos',
            'email': 'Correo electrónico',
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
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }

class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['codigo', 'nombre', 'titulacion', 'curso', 'profesor']  # Sin sesiones
        labels = {
            'codigo': 'Código',
            'nombre': 'Nombre',
            'titulacion': 'Titulación',
            'curso': 'Curso',
            'profesor': 'Profesor',
        }

class AsignaturaSesionForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['sesiones']
        labels = {
            'sesiones': 'Sesiones',
        }
        widgets = {
            'sesiones': forms.CheckboxSelectMultiple(),
        }
