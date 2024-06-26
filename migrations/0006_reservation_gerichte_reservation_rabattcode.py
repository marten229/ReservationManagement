# Generated by Django 5.0.6 on 2024-06-14 09:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('MarketingFunctions', '0002_specialoffer_code'),
        ('ReservationManagement', '0005_reservation_anmerkungen'),
        ('RestaurantManagement', '0009_delete_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='gerichte',
            field=models.ManyToManyField(blank=True, to='RestaurantManagement.menuitem'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='rabattcode',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='MarketingFunctions.specialoffer'),
        ),
    ]
