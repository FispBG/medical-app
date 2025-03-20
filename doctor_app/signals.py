from django.db.models.signals import post_save
from django.dispatch import receiver
from doctor_app.models import Doctor, Symptom, DoctorSymptomGroup

@receiver(post_save, sender=Doctor)
def assign_symptoms_to_doctor(sender, instance, created, **kwargs):
    if created:  
        specialization_symptoms = {
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

        symptom_names = specialization_symptoms.get(instance.specialization, [])
        symptoms = [Symptom.objects.get_or_create(name=name)[0] for name in symptom_names]

        instance.related_symptoms.set(symptoms)

        group, _ = DoctorSymptomGroup.objects.get_or_create(name=instance.specialization)
        group.doctors.add(instance)
        group.symptoms.add(*symptoms)
        group.save()
