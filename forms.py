from django import forms
from .models import Reservation

class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['name', 'email', 'telefon_nummer', 'datum', 'uhrzeit', 'anzahl_an_gästen']

class ReservationFormLoggedIn(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['datum', 'uhrzeit', 'anzahl_an_gästen']
