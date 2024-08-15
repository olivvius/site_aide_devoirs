# Generated by Django 5.1 on 2024-08-13 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_alter_exercise_photo_correction_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exercise',
            name='corrected',
            field=models.CharField(choices=[('oui', 'Oui'), ('non', 'Non'), ('pending', 'En attente de modification')], default='non', max_length=80, verbose_name='Corrigé'),
        ),
    ]
