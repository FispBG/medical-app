from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    doctors = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.username

class Symptom(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
class Doctor(models.Model):
    SPECIALIZATION_CHOICES = [
        ('Терапевт', 'Терапевт'),
        ('Кардиолог', 'Кардиолог'),
        ('Невролог', 'Невролог'),
        ('Дерматолог', 'Дерматолог'),
    ]
    
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES)
    schedule = models.TextField()
    photo = models.ImageField(upload_to='doctors/', null=True, blank=True)
    related_symptoms = models.ManyToManyField(Symptom, related_name='related_doctors', blank=True)
    
    def __str__(self):
        return self.name

class Appointment(models.Model):
    patient_name = models.CharField(max_length=100)
    patient_email = models.EmailField()
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    symptoms = models.ManyToManyField(Symptom, blank=True)
    custom_symptoms_text = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.patient_name} - {self.doctor.name} ({self.date} {self.time})"
    
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    
    def __str__(self):
        return self.name


class DoctorSymptomGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)
    doctors = models.ManyToManyField('Doctor', related_name='symptom_groups')
    symptoms = models.ManyToManyField('Symptom', related_name='doctor_groups')

    def __str__(self):
        return self.name