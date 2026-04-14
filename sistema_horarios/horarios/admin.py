from django.contrib import admin
from .models import Profesor, Sesion, Asignatura

class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('apellidos', 'nombre', 'email')

class SesionAdmin(admin.ModelAdmin):
    list_display = ('get_dia_display', 'hora_inicio', 'hora_fin')
    list_filter = ('dia',)

class AsignaturaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'titulacion', 'curso', 'profesor')
    list_filter = ('titulacion', 'curso')

admin.site.register(Profesor, ProfesorAdmin)
admin.site.register(Sesion, SesionAdmin)
admin.site.register(Asignatura, AsignaturaAdmin)
