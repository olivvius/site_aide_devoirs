# Generated by Django 5.1 on 2024-08-10 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_exercise_submission_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='credits',
            field=models.IntegerField(default=0),
        ),
    ]
