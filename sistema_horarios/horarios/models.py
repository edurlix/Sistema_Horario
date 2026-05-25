from django.conf import settings
from django.db import models
from django.urls import reverse


class Titulacion(models.Model):
    codigo = models.CharField(max_length=10, unique=True, verbose_name='Código')
    nombre = models.CharField(max_length=200, verbose_name='Nombre')
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='titulaciones',
        null=True,
    )

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Titulación'
        verbose_name_plural = 'Titulaciones'
        unique_together = [['codigo', 'creado_por']]


class Profesor(models.Model):
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profesores_propios',
        null=True,
    )

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
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sesiones_propias',
        null=True,
    )

    def __str__(self):
        return f"{self.get_dia_display()} {self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')}"

    class Meta:
        ordering = ['dia', 'hora_inicio']


class Asignatura(models.Model):
    CURSOS = [
        (1, '1º Curso'),
        (2, '2º Curso'),
        (3, '3º Curso'),
        (4, '4º Curso'),
        (5, '5º Curso'),
    ]

    CUATRIMESTRES = [
        (1, '1er Cuatrimestre'),
        (2, '2do Cuatrimestre'),
    ]

    nombre = models.CharField(max_length=200)
    codigo = models.CharField(max_length=20)
    titulacion = models.ForeignKey(
        Titulacion,
        on_delete=models.PROTECT,
        related_name='asignaturas',
        verbose_name='Titulación',
    )
    curso = models.IntegerField(choices=CURSOS)
    cuatrimestre = models.IntegerField(
        choices=CUATRIMESTRES, default=1, verbose_name='Cuatrimestre'
    )
    es_electiva = models.BooleanField(
        default=False,
        verbose_name='Es electiva',
        help_text='Las asignaturas electivas pueden compartir franja horaria con otras electivas del mismo curso y cuatrimestre.',
    )
    profesor = models.ForeignKey(
        Profesor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='asignaturas',
    )
    sesiones = models.ManyToManyField(Sesion, blank=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='asignaturas_propias',
        null=True,
    )

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    def get_absolute_url(self):
        return reverse('asignatura-detail', args=[str(self.id)])

    class Meta:
        unique_together = [['codigo', 'creado_por']]
