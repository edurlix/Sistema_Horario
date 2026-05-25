from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horarios', '0004_asignatura_semestre'),
    ]

    operations = [
        migrations.RenameField(
            model_name='asignatura',
            old_name='semestre',
            new_name='cuatrimestre',
        ),
        migrations.AlterField(
            model_name='asignatura',
            name='cuatrimestre',
            field=models.IntegerField(
                choices=[(1, '1er Cuatrimestre'), (2, '2do Cuatrimestre')],
                default=1,
                verbose_name='Cuatrimestre',
            ),
        ),
    ]
