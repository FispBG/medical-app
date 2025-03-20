from django import forms
from django.contrib.auth.models import User
from .models import Appointment, Symptom
from .models import CustomUser
import datetime
from datetime import datetime, date, time
from django.contrib.auth.forms import PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm password", widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def clean_password2(self):
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords do not match")
        return password2


class AppointmentForm(forms.ModelForm):
    time = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Время приема"
    )
    symptoms = forms.ModelMultipleChoiceField(
        queryset=Symptom.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Симптомы"
    )
    custom_symptoms = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3, 
            'placeholder': 'Опишите ваши симптомы, если их нет в списке или нужно указать дополнительные детали'
        }),
        required=False,
        label="Опишите свои симптомы"
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'min': datetime.today().isoformat()
        }),
        initial=datetime.today(),
        label="Дата приема"
    )

    class Meta:
        model = Appointment
        fields = ['date', 'time', 'symptoms', 'custom_symptoms']

    def __init__(self, *args, **kwargs):
        doctor = kwargs.pop('doctor', None)
        selected_date = kwargs.pop('selected_date', None)
        super(AppointmentForm, self).__init__(*args, **kwargs)

        if doctor and selected_date:
            all_time_slots = [time(hour, minute) for hour in range(9, 17) for minute in (0, 15, 30, 45)]
            
            booked_slots = set(
                app.time for app in Appointment.objects.filter(doctor=doctor, date=selected_date)
            )
            
            booked_slots_str = {t.strftime("%H:%M") for t in booked_slots}
            
            available_time_slots = [(t.strftime("%H:%M"), t.strftime("%H:%M")) for t in all_time_slots if t.strftime("%H:%M") not in booked_slots_str]
            
            self.fields['time'].choices = available_time_slots
        else:
            self.fields['time'].choices = []

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)

        self.fields['old_password'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите текущий пароль'
        })
        
        self.fields['new_password1'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новый пароль'
        })
        self.fields['new_password1'].help_text = _(
            "Ваш пароль должен содержать не менее 8 символов. "
            "Пароль не должен быть слишком похож на другую личную информацию, "
            "не должен быть часто используемым и не может состоять только из цифр."
        )
        self.fields['new_password1'].help_text = mark_safe(
            "Требования к паролю:<br>"
            "<ul>"
            "<li>Должен содержать не менее 8 символов.</li>"
            "<li>Не должен быть слишком похож на другую личную информацию.</li>"
            "<li>Не должен быть часто используемым.</li>"
            "<li>Не может состоять только из цифр.</li>"
            "</ul>"
        )

        self.fields['new_password2'].widget = forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Подтвердите новый пароль'
        })
        self.fields['new_password2'].error_messages = {
            'password_mismatch': _("Пароли не совпадают."),
        }

