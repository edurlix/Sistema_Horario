from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horarios', '0003_user_isolation'),
    ]

    operations = [
        migrations.AddField(
            model_name='asignatura',
            name='semestre',
            field=models.IntegerField(
                choices=[(1, '1er Semestre'), (2, '2do Semestre')],
                default=1,
                verbose_name='Semestre',
            ),
        ),
    ]
