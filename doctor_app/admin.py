from django import forms
from django.contrib import admin
from .models import Doctor, Symptom, Appointment, Contact, CustomUser, DoctorSymptomGroup

SPECIALIZATION_SYMPTOMS_MAP = {
    'Терапевт': [
        'Кашель', 'Насморк', 'Температура', 'Боль в горле',
        'Слабость', 'Головная боль', 'Боль в мышцах'
    ],
    'Кардиолог': [
        'Боль в груди', 'Одышка', 'Учащенное сердцебиение',
        'Отек ног', 'Головокружение', 'Повышенное давление'
    ],
    'Невролог': [
        'Головная боль', 'Головокружение', 'Нарушение сна',
        'Онемение конечностей', 'Слабость в конечностях', 'Тремор',
        'Нарушение координации', 'Боли в спине'
    ],
    'Дерматолог': [
        'Сыпь', 'Зуд', 'Покраснение кожи', 'Сухость кожи',
        'Высыпания', 'Изменение пигментации', 'Шелушение'
    ],
}

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
        return specialization

class DoctorAdmin(admin.ModelAdmin):
    form = DoctorForm
    list_display = ('name', 'specialization')
    filter_horizontal = ('related_symptoms',) 

    def save_model(self, request, obj, form, change):

        original_specialization = None
        if change and obj.pk:
            try:
                original_specialization = Doctor.objects.get(pk=obj.pk).specialization
            except Doctor.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

        new_specialization = obj.specialization

        if change and original_specialization != new_specialization and new_specialization:
            

            symptom_names_for_new_spec = SPECIALIZATION_SYMPTOMS_MAP.get(new_specialization, [])
            symptoms_to_set = []
            if symptom_names_for_new_spec:
                for name in symptom_names_for_new_spec:
                    symptom, _ = Symptom.objects.get_or_create(name=name)
                    symptoms_to_set.append(symptom)
            
            obj.related_symptoms.set(symptoms_to_set)

            if original_specialization:
                old_group = DoctorSymptomGroup.objects.filter(name=original_specialization).first()
                if old_group:
                    old_group.doctors.remove(obj)
            
            new_group, created_new_group = DoctorSymptomGroup.objects.get_or_create(name=new_specialization)
            new_group.doctors.add(obj)
            if symptoms_to_set:
                new_group.symptoms.add(*symptoms_to_set)
            

admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Symptom) 
admin.site.register(Appointment) 
admin.site.register(Contact) 
admin.site.register(CustomUser) 