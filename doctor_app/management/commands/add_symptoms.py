from django.core.management.base import BaseCommand
from doctor_app.models import Doctor, Symptom, DoctorSymptomGroup

class Command(BaseCommand):
    help = "Заполняет группы врачей симптомами на основе их специализации"

    def handle(self, *args, **kwargs):
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

        for specialization, symptom_names in specialization_symptoms.items():
            # Получаем или создаем группу
            group, _ = DoctorSymptomGroup.objects.get_or_create(name=specialization)

            # Добавляем врачей этой специализации
            doctors = Doctor.objects.filter(specialization=specialization)
            group.doctors.set(doctors)

            # Добавляем симптомы
            symptoms = [Symptom.objects.get_or_create(name=name)[0] for name in symptom_names]
            group.symptoms.set(symptoms)

            group.save()
            self.stdout.write(self.style.SUCCESS(f"Группа '{specialization}' заполнена!"))
