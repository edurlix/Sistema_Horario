from django.db import models
from django.urls import reverse

class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.apellidos}, {self.nombre}"
    
    def get_absolute_url(self):
        return reverse('profesor-detail', args=[str(self.id)])


class Sesion(models.Model):
    DIAS_SEMANA = [
        ('LUN', 'Lunes'),
        ('MAR', 'Martes'),
        ('MIE', 'Miércoles'),
        ('JUE', 'Jueves'),
        ('VIE', 'Viernes'),
    ]
    
    dia = models.CharField(max_length=3, choices=DIAS_SEMANA)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    
    def __str__(self):
        return f"{self.get_dia_display()} {self.hora_inicio} - {self.hora_fin}"
    
    class Meta:
        ordering = ['dia', 'hora_inicio']


class Asignatura(models.Model):
    TITULACIONES = [
        ('II', 'Ingeniería Informática'),
        ('IR', 'Ingeniería Robótica'),
        ('IT', 'Ingeniería Telemática'),
        ('DG', 'Doble Grado Informática + Robótica'),
    ]
    
    CURSOS = [
        (1, '1º Curso'),
        (2, '2º Curso'),
        (3, '3º Curso'),
        (4, '4º Curso'),
    ]
    
    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20, unique=True)
    titulacion = models.CharField(max_length=2, choices=TITULACIONES)
    curso = models.IntegerField(choices=CURSOS)
    profesor = models.ForeignKey(Profesor, on_delete=models.SET_NULL, null=True, blank=True)
    sesiones = models.ManyToManyField(Sesion, blank=True)
    
    def __str__(self):
        return f"{self.codigo} - {self.nombre}"
    
    def get_absolute_url(self):
        return reverse('asignatura-detail', args=[str(self.id)])
