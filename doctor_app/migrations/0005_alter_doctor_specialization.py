# Generated by Django 5.1.6 on 2025-03-09 13:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctor_app', '0004_remove_symptom_doctors_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctor',
            name='specialization',
            field=models.CharField(choices=[('Терапевт', 'Терапевт'), ('Кардиолог', 'Кардиолог'), ('Невролог', 'Невролог'), ('Дерматолог', 'Дерматолог')], max_length=100),
        ),
    ]
