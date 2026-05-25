from django.contrib import admin
from .models import Profesor, Sesion, Asignatura, Titulacion


@admin.register(Titulacion)
class TitulacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre')
    search_fields = ('codigo', 'nombre')


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('apellidos', 'nombre', 'email')
    search_fields = ('apellidos', 'nombre', 'email')


@admin.register(Sesion)
class SesionAdmin(admin.ModelAdmin):
    list_display = ('dia', 'hora_inicio', 'hora_fin')
    list_filter = ('dia',)


@admin.register(Asignatura)
class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'titulacion', 'curso', 'cuatrimestre', 'es_electiva', 'profesor')
    list_filter = ('titulacion', 'curso', 'cuatrimestre', 'es_electiva')
    search_fields = ('codigo', 'nombre')
