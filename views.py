from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from .models import Restaurant, User, Reservation
from .forms import ReservationForm, ReservationFormLoggedIn
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from django.utils import timezone
from django.db.models import Avg
from TableManagement.functions import is_a_table_available_with_size
from django.contrib import messages
from MarketingFunctions.models import SpecialOffer, Event, Promotion
from ReviewFeedbackSystem.models import Bewertung
from django.contrib.auth.decorators import login_required
from UserManagement.decorators import role_and_restaurant_required
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.http import HttpResponse
from RestaurantManagement.models import MenuItem

class RestaurantListView(ListView):
    model = Restaurant
    template_name = 'restaurant_list.html'
    context_object_name = 'restaurants'

    def get_queryset(self):
        return Restaurant.objects.all()

class RestaurantDetailView(DetailView):
    model = Restaurant
    template_name = 'restaurant_detail.html'
    context_object_name = 'restaurant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        restaurant = self.get_object()
        context['special_offers'] = SpecialOffer.objects.filter(restaurant=restaurant)
        context['events'] = Event.objects.filter(restaurant=restaurant)
        context['promotions'] = Promotion.objects.filter(restaurant=restaurant, active=True)
        context['menu_items'] = MenuItem.objects.filter(restaurant=restaurant)

        bewertungen = Bewertung.objects.filter(restaurant=restaurant)
        
        durchschnittliche_bewertung_gesamt = bewertungen.aggregate(Avg('bewertung_gesamt'))['bewertung_gesamt__avg'] or 0
        durchschnittliche_bewertung_service = bewertungen.aggregate(Avg('bewertung_service'))['bewertung_service__avg'] or 0
        durchschnittliche_bewertung_essen = bewertungen.aggregate(Avg('bewertung_essen'))['bewertung_essen__avg'] or 0
        durchschnittliche_bewertung_ambiente = bewertungen.aggregate(Avg('bewertung_ambiente'))['bewertung_ambiente__avg'] or 0
        anzahl_bewertungen = bewertungen.count()

        volle_sterne = int(durchschnittliche_bewertung_gesamt)
        halber_stern = durchschnittliche_bewertung_gesamt - volle_sterne >= 0.5
        
        context['durchschnittliche_bewertung_gesamt'] = durchschnittliche_bewertung_gesamt
        context['durchschnittliche_bewertung_service'] = durchschnittliche_bewertung_service
        context['durchschnittliche_bewertung_essen'] = durchschnittliche_bewertung_essen
        context['durchschnittliche_bewertung_ambiente'] = durchschnittliche_bewertung_ambiente
        context['anzahl_bewertungen'] = anzahl_bewertungen
        context['volle_sterne'] = volle_sterne
        context['halber_stern'] = halber_stern
        context['bewertungen'] = bewertungen
        return context



def create_reservation(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        if request.user.is_authenticated:
            form = ReservationFormLoggedIn(request.POST, restaurant=restaurant)
        else:
            form = ReservationForm(request.POST, restaurant=restaurant)
        if form.is_valid():
            date = form.cleaned_data['datum']
            time = form.cleaned_data['uhrzeit']
            duration = form.cleaned_data['dauer']
            party_size = form.cleaned_data['anzahl_an_gästen']

            if restaurant.check_ifopendayandtime(date, time):
                available_tables = is_a_table_available_with_size(restaurant, date, time, duration, party_size)
                if available_tables.exists():
                    reservation = form.save(commit=False)
                    reservation.restaurant = restaurant
                    reservation.table = available_tables.first()
                    if request.user.is_authenticated:
                        reservation.user = request.user
                    reservation.save()
                    
                    confirmation_message = (
                        f"Reservierung bestätigt für den {reservation.datum} um {reservation.uhrzeit} "
                        f"im Restaurant {reservation.restaurant.name}. Ihre Buchungsnummer lautet {reservation.pk}."
                        f"Wir würden uns freuen, wenn sie nach ihrem Besuch eine Bewertung innerhalb 48 Stunden abgeben würden."
                        f"Diese können sie auf der Restaurantseite machen."
                        f"Wir freuen uns auf Ihren Besuch!"
                    )
                    messages.success(request, confirmation_message)

                    send_mail('Reservation', confirmation_message, settings.EMAIL_HOST_USER, [request.user.email])

                    staff_emails = restaurant.staff_members.filter(role='restaurant_staff').values_list('email', flat=True)
                    staff_message = (
                        f"Neue Reservierung im Restaurant {restaurant.name}.\n\n"
                        f"Details:\nDatum: {reservation.datum}\nUhrzeit: {reservation.uhrzeit}\n"
                        f"Anzahl der Gäste: {reservation.anzahl_an_gästen}\nBuchungsnummer: {reservation.pk}."
                    )
                    send_mail('Neue Reservierung', staff_message, settings.EMAIL_HOST_USER, staff_emails)

                    return redirect('restaurant-detail', pk=restaurant.pk)
                else:
                    form.add_error(None, 'Kein verfügbarer Tisch für die angegebene Zeit und Gruppengröße')
            else:
                form.add_error(None, 'Das Restaurant ist zu dieser Zeit geschlossen')
    else:
        if request.user.is_authenticated:
            form = ReservationFormLoggedIn(restaurant=restaurant)
        else:
            form = ReservationForm(restaurant=restaurant)
    return render(request, 'create_reservation.html', {'form': form, 'restaurant': restaurant})

class ReservationListView(ListView):
    model = Reservation
    template_name = 'reservation_list.html'
    context_object_name = 'reservations'

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user)

class ReservationUpdateView(UpdateView):
    model = Reservation
    form_class = ReservationFormLoggedIn
    template_name = 'reservation_form.html'
    context_object_name = 'reservation'

    def get_success_url(self):
        return reverse_lazy('reservation-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        reservation = form.instance
        restaurant = reservation.restaurant

        staff_emails = restaurant.staff_members.filter(role='restaurant_staff').values_list('email', flat=True)
        staff_message = (
            f"Die Reservierung im Restaurant {restaurant.name} wurde aktualisiert.\n\n"
            f"Neue Details:\nDatum: {reservation.datum}\nUhrzeit: {reservation.uhrzeit}\n"
            f"Anzahl der Gäste: {reservation.anzahl_an_gästen}\nBuchungsnummer: {reservation.pk}."
        )
        send_mail('Aktualisierte Reservierung', staff_message, settings.EMAIL_HOST_USER, staff_emails)

        return response

class ReservationDeleteView(DeleteView):
    model = Reservation
    template_name = 'reservation_confirm_delete.html'
    context_object_name = 'reservation'
    success_url = reverse_lazy('reservation-list')

    def delete(self, request, *args, **kwargs):
        reservation = self.get_object()
        restaurant = reservation.restaurant
        response = super().delete(request, *args, **kwargs)

        staff_emails = restaurant.staff_members.filter(role='restaurant_staff').values_list('email', flat=True)
        staff_message = (
            f"Die Reservierung im Restaurant {restaurant.name} wurde storniert.\n\n"
            f"Details der stornierten Reservierung:\nDatum: {reservation.datum}\nUhrzeit: {reservation.uhrzeit}\n"
            f"Anzahl der Gäste: {reservation.anzahl_an_gästen}\nBuchungsnummer: {reservation.pk}."
        )
        send_mail('Stornierte Reservierung', staff_message, settings.EMAIL_HOST_USER, staff_emails)

        return response


@login_required
@role_and_restaurant_required(['administrator', 'restaurant_owner', 'restaurant_staff'])
def reservations_view(request, pk):
    restaurant = get_object_or_404(Restaurant, id=pk)
    now = timezone.localtime()
    current_time = now.time()
    current_date = now.date()

    today_reservations = Reservation.objects.filter(
        restaurant=restaurant,
        datum=current_date,
        uhrzeit__gte=current_time
    )

    context = {
        'restaurant': restaurant,
        'today_reservations': today_reservations
    }
    return render(request, 'reservations.html', context)