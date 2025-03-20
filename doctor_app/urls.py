from django.urls import path
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from .views import (CustomLoginView, all_doctors, register_view,change_password, profile_view, 
                    index, booking, logout_view,smart_search,book_appointment,manage_doctor_symptoms,contact,delete_appointment,get_available_times)

urlpatterns = [
    path('', index, name="index"),
    path('booking/', booking, name="booking"),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('profile/', profile_view, name='profile'),
    path('doctors/', all_doctors, name='all_doctors'),
    path('contact/', contact, name='contact'),
    path('book-appointment/<int:doctor_id>/', book_appointment, name='book_appointment'),
    path('manage-symptoms/<int:doctor_id>/', manage_doctor_symptoms, name='manage_doctor_symptoms'),
    path('delete-appointment/<int:appointment_id>/', delete_appointment, name='delete_appointment'),
    path('get-available-times/', get_available_times, name='get_available_times'),
    path('change-password/', change_password, name='change_password'),
     path('search/', smart_search, name='smart_search'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)