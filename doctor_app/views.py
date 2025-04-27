from django.contrib.auth import login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .forms import RegisterForm
from django.contrib import messages
from .models import Doctor, Symptom, Appointment, Contact, DoctorSymptomGroup
from .models import CustomUser
from django.utils.timezone import now
from django.http import JsonResponse
from datetime import datetime,time,timedelta
from .forms import AppointmentForm,CustomPasswordChangeForm
from django.urls import reverse
from django.core.mail import send_mail,BadHeaderError
from django.conf import settings
import re

def index(request):
    return render(request, "doctor/index.html")

def booking(request):
    return render(request, "doctor/booking.html")

class CustomLoginView(LoginView):
    template_name = "registration/login.html"

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('profile')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'registration/profile.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def all_doctors(request):
    specialization = request.GET.get('specialization', '')
    
    if specialization:
        doctors = Doctor.objects.filter(specialization=specialization)
    else:
        doctors = Doctor.objects.all()
    
    available_hours = ["9", "10", "11", "12", "13", "14", "15", "16"]
    
    return render(request, "doctor/doctors.html", {
        "doctors": doctors,
        "available_hours": available_hours,
        "selected_specialization": specialization
    })

@login_required
def book_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    related_symptoms = Symptom.objects.filter(doctor_groups__doctors=doctor).distinct()
    symptom_groups = DoctorSymptomGroup.objects.filter(doctors=doctor)
    group_symptoms = Symptom.objects.filter(doctor_groups__in=symptom_groups).distinct()
    all_symptoms = related_symptoms | group_symptoms
    
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    current_time = current_datetime.time()
    
    max_date = (current_date + timedelta(days=7)).strftime('%Y-%m-%d')
    min_date = current_date.strftime('%Y-%m-%d')
    
    selected_date = request.POST.get('date') or request.GET.get('date') or current_date.strftime('%Y-%m-%d')
    
    try:
        selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
        if selected_date_obj < current_date:
            messages.error(request, 'Невозможно выбрать прошедшую дату.')
            return redirect(request.path + f"?date={min_date}")
        elif selected_date_obj > current_date + timedelta(days=7):
            messages.error(request, 'Можно записаться только на неделю вперед.')
            return redirect(request.path + f"?date={max_date}")
    except ValueError:
        messages.error(request, 'Неверный формат даты.')
        return redirect(request.path + f"?date={min_date}")
    
    all_time_slots = [time(hour, minute) for hour in range(9, 17) for minute in (0, 15, 30, 45)]
    
    booked_appointments = Appointment.objects.filter(doctor=doctor, date=selected_date_obj)
    booked_slots_strings = {appointment.time.strftime("%H:%M") for appointment in booked_appointments}
    
    available_time_slots = [(t.strftime("%H:%M"), t.strftime("%H:%M")) for t in all_time_slots if t.strftime("%H:%M") not in booked_slots_strings]
    
    if request.method == 'POST' and 'time' in request.POST:
        form = AppointmentForm(request.POST, doctor=doctor, selected_date=selected_date_obj)
        form.fields['symptoms'].queryset = all_symptoms
        form.fields['time'].choices = available_time_slots
        
        if form.is_valid():
            selected_time_str = form.cleaned_data['time']
            
            updated_booked_slots = {appointment.time.strftime("%H:%M") for appointment in Appointment.objects.filter(doctor=doctor, date=selected_date_obj)}
            
            if selected_time_str in updated_booked_slots:
                messages.error(request, 'Выбранное время уже занято. Пожалуйста, выберите другое.')
                return redirect(request.path + f"?date={selected_date}")
            
            selected_time = datetime.strptime(selected_time_str, "%H:%M").time()
            
            if selected_date_obj == current_date and selected_time <= current_time:
                messages.error(request, 'Невозможно записаться на прошедшее время.')
                return redirect(request.path + f"?date={selected_date}")
            
            appointment = form.save(commit=False)
            appointment.doctor = doctor
            appointment.patient_name = request.user.username
            appointment.patient_email = request.user.email
            appointment.custom_symptoms_text = form.cleaned_data.get('custom_symptoms', '')
            appointment.time = selected_time
            appointment.date = selected_date_obj
            appointment.save()
            
            symptom_ids = request.POST.getlist('symptoms')
            if symptom_ids:
                symptoms = Symptom.objects.filter(id__in=symptom_ids)
                appointment.symptoms.set(symptoms)
            
            messages.success(request, f'Вы успешно записались к врачу {doctor.name}')
            
            subject = 'Подтверждение записи к врачу'
            message = (f'Здравствуйте, {request.user.username}!\n\n'
                       f'Вы записались на прием к врачу {doctor.name}.\n'
                       f'Дата: {selected_date}\n'
                       f'Время: {selected_time.strftime("%H:%M")}\n\n'
                       f'Спасибо за использование нашего сервиса!')
            recipient_list = [request.user.email]
            
            try:
                send_mail(
                    subject, 
                    message, 
                    settings.EMAIL_HOST_USER, 
                    recipient_list, 
                    fail_silently=False
                )
            except Exception as e:
                print(f"Error sending email: {str(e)}")
                messages.info(request, 'Запись создана успешно, но письмо с подтверждением может прийти с задержкой.')

            return redirect('profile')
    else:
        form = AppointmentForm(doctor=doctor, selected_date=selected_date_obj)
        form.fields['symptoms'].queryset = all_symptoms
        form.fields['time'].choices = available_time_slots
    
    return render(request, 'doctor/booking.html', {
        'form': form,
        'doctor': doctor,
        'related_symptoms': all_symptoms,
        'min_date': min_date,
        'max_date': max_date,
        'selected_date': selected_date,
    })

@login_required
def delete_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if appointment.patient_email != request.user.email:
        messages.error(request, "У вас нет прав для удаления этой записи")
        return redirect('profile')
    
    doctor_name = appointment.doctor.name
    
    appointment.delete()
    
    messages.success(request, f"Запись к врачу {doctor_name} успешно отменена")
    return redirect('profile')

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    
    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse('profile')
    
@login_required
def profile_view(request):
    user_appointments = Appointment.objects.filter(patient_email=request.user.email).order_by('date', 'time')
    
    return render(request, 'registration/profile.html', {
        'appointments': user_appointments
    })

@login_required
def manage_doctor_symptoms(request, doctor_id):
    if not request.user.is_staff:
        messages.error(request, "У вас нет доступа к этой странице")
        return redirect('index')
        
    doctor = get_object_or_404(Doctor, id=doctor_id)
    all_symptoms = Symptom.objects.all()
    
    if request.method == 'POST':
        selected_symptoms = request.POST.getlist('symptoms')
        doctor.related_symptoms.clear()
        for symptom_id in selected_symptoms:
            symptom = get_object_or_404(Symptom, id=symptom_id)
            doctor.related_symptoms.add(symptom)
        
        messages.success(request, f'Симптомы для врача {doctor.name} обновлены')
        return redirect('all_doctors')
    
    return render(request, 'doctor_app/manage_symptoms.html', {
        'doctor': doctor,
        'all_symptoms': all_symptoms,
        'selected_symptoms': doctor.related_symptoms.all()
    })

def get_available_times(request):
    date_str = request.GET.get('date')
    doctor_id = request.GET.get('doctor')
    
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        all_time_slots = [time(hour, minute) for hour in range(9, 17) for minute in (0, 15, 30, 45)]
        
        booked_appointments = Appointment.objects.filter(doctor=doctor, date=selected_date)
        
        booked_slots = {appointment.time.strftime("%H:%M") for appointment in booked_appointments}
        
        available_slots = [t.strftime("%H:%M") for t in all_time_slots if t.strftime("%H:%M") not in booked_slots]
        
        if selected_date == datetime.now().date():
            current_time = datetime.now().time()
            available_slots = [t for t in available_slots if 
                              datetime.strptime(t, "%H:%M").time() > current_time]
        
        return JsonResponse({'times': available_slots})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
def contact(request):
    return render(request, 'doctor/contact.html')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message', '')
        
        if not name or not email or not message:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля.')
            return render(request, 'doctor/contact.html')
        
        subject = f'Сообщение от {name} через форму обратной связи'
        email_message = f"""
        Имя: {name}
        Email: {email}
        Телефон: {phone}
        
        Сообщение:
        {message}
        """
        
        try:
            send_mail(
                subject,
                email_message,
                settings.EMAIL_HOST_USER,
                [settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Спасибо! Ваше сообщение отправлено.')
            return redirect('contact')
        except (BadHeaderError, Exception) as e:
            messages.error(request, 'Произошла ошибка при отправке сообщения. Пожалуйста, попробуйте позже.')
            print(f"Email error: {str(e)}")
            return render(request, 'doctor/contact.html')
            
    return render(request, 'doctor/contact.html')

@login_required
def profile_view(request):
    appointments = Appointment.objects.filter(patient_email=request.user.email).order_by('date', 'time')
    
    password_form = CustomPasswordChangeForm(request.user)
    
    context = {
        'user': request.user,
        'appointments': appointments,
        'password_form': password_form,
    }
    
    return render(request, 'registration/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            from django.contrib import messages
            messages.success(request, 'Ваш пароль был успешно изменен!')
            return redirect('profile')
        else:
            pass
    else:
        form = CustomPasswordChangeForm(request.user)
    
    context = {
        'password_form': form,
        'appointments': Appointment.objects.filter(patient_email=request.user.email).order_by('date', 'time')
    }
    return render(request, 'registration/profile.html', context)
from django.utils import timezone
@login_required
def profile_view(request):
    current_datetime = timezone.now()
    Appointment.objects.filter(patient_email=request.user.email, date__lt=current_datetime.date()).delete()
    Appointment.objects.filter(patient_email=request.user.email, date=current_datetime.date(), time__lt=current_datetime.time()).delete()

    appointments = Appointment.objects.filter(patient_email=request.user.email).order_by('date', 'time')
    
    password_form = CustomPasswordChangeForm(request.user)
    
    context = {
        'user': request.user,
        'appointments': appointments,
        'password_form': password_form,
    }
    
    return render(request, 'registration/profile.html', context)

def smart_search(request):
    context = {
        'searched': False,
        'description': '',
        'found_specialists': [],
        'found_symptoms': []
    }
    
    if request.method == 'POST':
        description = request.POST.get('symptoms_description', '').strip()
        if description:
            context['searched'] = True
            context['description'] = description
            
            all_symptoms = Symptom.objects.all()
            
            found_symptoms = []
            for symptom in all_symptoms:
                pattern = r'\b' + re.escape(symptom.name.lower()) + r'\b'
                if re.search(pattern, description.lower()):
                    found_symptoms.append(symptom)
                    
                words = symptom.name.lower().split()
                if len(words) > 1:
                    matches = sum(1 for word in words if word in description.lower())
                    if matches >= len(words) * 0.7:
                        if symptom not in found_symptoms:
                            found_symptoms.append(symptom)
            
            specialist_scores = {}
            
            for symptom in found_symptoms:
                for doctor in symptom.related_doctors.all():
                    specialization = doctor.specialization
                    specialist_scores[specialization] = specialist_scores.get(specialization, 0) + 1
            
            for symptom in found_symptoms:
                symptom_groups = symptom.doctor_groups.all()
                for group in symptom_groups:
                    for doctor in group.doctors.all():
                        specialization = doctor.specialization
                        specialist_scores[specialization] = specialist_scores.get(specialization, 0) + 1
            
            if not specialist_scores:
                specializations = dict(Doctor.SPECIALIZATION_CHOICES)
                for spec_key in specializations:
                    if spec_key.lower() in description.lower():
                        specialist_scores[spec_key] = specialist_scores.get(spec_key, 0) + 5
                    
                    keywords = {
                        'Терапевт': ['простуда', 'грипп', 'температура', 'кашель', 'общее самочувствие', 'горло', 'боль в горле'],
                        'Кардиолог': ['сердце', 'давление', 'пульс', 'боль в груди', 'одышка', 'тахикардия', 'аритмия'],
                        'Невролог': ['голова', 'головная боль', 'мигрень', 'нервы', 'онемение', 'головокружение', 'равновесие'],
                        'Дерматолог': ['кожа', 'сыпь', 'зуд', 'высыпание', 'покраснение', 'аллергия', 'родинки']
                    }
                    
                    if spec_key in keywords:
                        for keyword in keywords[spec_key]:
                            if keyword.lower() in description.lower():
                                specialist_scores[spec_key] = specialist_scores.get(spec_key, 0) + 3
            
            if specialist_scores:
                total_symptoms = len(found_symptoms) if found_symptoms else 1
                max_score = max(specialist_scores.values())
                
                found_specialists = []
                for spec, score in specialist_scores.items():
                    percentage = min(100, int((score / max_score) * 100))
                    found_specialists.append((spec, percentage))
                
                found_specialists.sort(key=lambda x: x[1], reverse=True)
                
                context['found_specialists'] = found_specialists[:3]
            
            context['found_symptoms'] = [symptom.name for symptom in found_symptoms]
    
    return render(request, 'doctor/search.html', context)