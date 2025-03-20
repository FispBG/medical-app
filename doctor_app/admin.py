
from django import forms
from django.contrib import admin
from .models import Doctor, Symptom, Appointment, Contact, CustomUser,DoctorSymptomGroup

class DoctorAdminForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ['name', 'specialization', 'schedule', 'photo']

@admin.register(DoctorSymptomGroup)
class DoctorSymptomGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('doctors', 'symptoms')

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = '__all__'

    def clean_specialization(self):
        specialization = self.cleaned_data.get('specialization')
        if specialization:
            category = DoctorSymptomGroup.objects.filter(specialization=specialization).first()
            if category:
                self.instance.related_symptoms.set(category.symptoms.all())
        return specialization

class DoctorAdmin(admin.ModelAdmin):
    form = DoctorForm
    list_display = ('name', 'specialization')
    filter_horizontal = ('related_symptoms',)

admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Symptom)
admin.site.register(Appointment)
admin.site.register(Contact)
admin.site.register(CustomUser)