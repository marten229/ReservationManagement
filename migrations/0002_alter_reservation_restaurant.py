# Generated by Django 5.0.6 on 2024-06-07 14:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ReservationManagement', '0001_initial'),
        ('RestaurantManagement', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='restaurant',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='RestaurantManagement.restaurant'),
        ),
    ]
