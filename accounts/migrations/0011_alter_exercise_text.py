# Generated by Django 5.1 on 2024-08-13 15:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0010_exercise_audio_correction_alter_exercise_corrected'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='text',
            field=models.TextField(blank=True, null=True),
        ),
    ]
