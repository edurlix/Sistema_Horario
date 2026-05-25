"""
Migration: per-user data isolation.
 - Adds creado_por FK (nullable) to Titulacion, Profesor, Sesion, Asignatura.
 - Assigns all existing objects to the first superuser found.
 - Adds unique_together constraints per user.
"""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def asignar_a_superusuario(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    superuser = User.objects.filter(is_superuser=True).order_by('id').first()
    if not superuser:
        return

    for model_name in ['Titulacion', 'Profesor', 'Sesion', 'Asignatura']:
        Model = apps.get_model('horarios', model_name)
        Model.objects.filter(creado_por__isnull=True).update(creado_por=superuser)


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('horarios', '0002_titulacion_refactor'),
    ]

    operations = [
        # ── Add creado_por to every model ──────────────────────────────────────
        migrations.AddField(
            model_name='titulacion',
            name='creado_por',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='titulaciones',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='profesor',
            name='creado_por',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='profesores_propios',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='sesion',
            name='creado_por',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sesiones_propias',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='asignatura',
            name='creado_por',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='asignaturas_propias',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # ── Populate existing data ─────────────────────────────────────────────
        migrations.RunPython(asignar_a_superusuario, migrations.RunPython.noop),

        # ── Remove old global unique constraint on Asignatura.codigo ──────────
        migrations.AlterField(
            model_name='asignatura',
            name='codigo',
            field=models.CharField(max_length=20),
        ),

        # ── unique_together per user ───────────────────────────────────────────
        migrations.AlterUniqueTogether(
            name='titulacion',
            unique_together={('codigo', 'creado_por')},
        ),
        migrations.AlterUniqueTogether(
            name='asignatura',
            unique_together={('codigo', 'creado_por')},
        ),
    ]
