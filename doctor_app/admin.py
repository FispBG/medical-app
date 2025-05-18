from django import forms
from django.contrib import admin
from .models import Doctor, Symptom, Appointment, Contact, CustomUser, DoctorSymptomGroup

@admin.register(DoctorSymptomGroup)
class DoctorSymptomGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('doctors', 'symptoms')

class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = '__all__'

    def clean_specialization(self):
        specialization = self.cleaned_data.get('specialization') # Получаем специализацию доктора (например, 'Терапевт')
        if specialization:
            # ИСПРАВЛЕННАЯ СТРОКА:
            # Ищем DoctorSymptomGroup, у которой поле 'name' совпадает со специализацией доктора.
            category = DoctorSymptomGroup.objects.filter(name=specialization).first()
            
            if category:
                # Если найдена соответствующая группа симптомов,
                # устанавливаем связанные симптомы для данного экземпляра доктора.
                # ВАЖНО: Это действие перезапишет любые симптомы,
                # которые пользователь мог выбрать вручную в поле 'related_symptoms' в админке,
                # если категория найдена.
                self.instance.related_symptoms.set(category.symptoms.all())
        return specialization

class DoctorAdmin(admin.ModelAdmin):
    form = DoctorForm
    list_display = ('name', 'specialization')
    filter_horizontal = ('related_symptoms',) # Позволяет редактировать related_symptoms в админке

admin.site.register(Doctor, DoctorAdmin)
admin.site.register(Symptom)
admin.site.register(Appointment)
admin.site.register(Contact)
admin.site.register(CustomUser)