"""
Migration that:
 1. Creates the Titulacion model.
 2. Populates it with the four original degrees.
 3. Replaces Asignatura.titulacion (CharField) with a ForeignKey.
 4. Adds Asignatura.es_electiva boolean field.
 5. Adds 5th-year choice (no DB change needed for IntegerField choices).
"""

import django.db.models.deletion
from django.db import migrations, models


TITULACIONES_INICIALES = [
    ('II', 'Ingeniería Informática'),
    ('IR', 'Ingeniería Robótica'),
    ('IT', 'Ingeniería Telemática'),
    ('DG', 'Doble Grado Informática + Robótica'),
]


def crear_titulaciones_y_migrar(apps, schema_editor):
    Titulacion = apps.get_model('horarios', 'Titulacion')
    Asignatura = apps.get_model('horarios', 'Asignatura')

    tit_map = {}
    for codigo, nombre in TITULACIONES_INICIALES:
        tit = Titulacion.objects.create(codigo=codigo, nombre=nombre)
        tit_map[codigo] = tit

    for asignatura in Asignatura.objects.all():
        old_code = asignatura.titulacion_codigo
        if old_code in tit_map:
            asignatura.titulacion = tit_map[old_code]
            asignatura.save()


def revertir_titulaciones(apps, schema_editor):
    Asignatura = apps.get_model('horarios', 'Asignatura')
    for asignatura in Asignatura.objects.select_related('titulacion').all():
        if asignatura.titulacion:
            asignatura.titulacion_codigo = asignatura.titulacion.codigo
            asignatura.save()


class Migration(migrations.Migration):

    dependencies = [
        ('horarios', '0001_initial'),
    ]

    operations = [
        # 1. Create Titulacion model
        migrations.CreateModel(
            name='Titulacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=10, unique=True, verbose_name='Código')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre')),
            ],
            options={
                'verbose_name': 'Titulación',
                'verbose_name_plural': 'Titulaciones',
                'ordering': ['nombre'],
            },
        ),

        # 2. Rename the old CharField so we can reuse the name for the FK
        migrations.RenameField(
            model_name='asignatura',
            old_name='titulacion',
            new_name='titulacion_codigo',
        ),

        # 3. Add new FK (nullable during migration)
        migrations.AddField(
            model_name='asignatura',
            name='titulacion',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='asignaturas',
                to='horarios.titulacion',
                verbose_name='Titulación',
            ),
        ),

        # 4. Populate Titulacion table + migrate FK values
        migrations.RunPython(crear_titulaciones_y_migrar, revertir_titulaciones),

        # 5. Make FK non-null
        migrations.AlterField(
            model_name='asignatura',
            name='titulacion',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='asignaturas',
                to='horarios.titulacion',
                verbose_name='Titulación',
            ),
        ),

        # 6. Drop old CharField
        migrations.RemoveField(
            model_name='asignatura',
            name='titulacion_codigo',
        ),

        # 7. Add es_electiva boolean
        migrations.AddField(
            model_name='asignatura',
            name='es_electiva',
            field=models.BooleanField(
                default=False,
                verbose_name='Es electiva',
                help_text='Las asignaturas electivas pueden compartir franja horaria con otras electivas del mismo curso.',
            ),
        ),
    ]
