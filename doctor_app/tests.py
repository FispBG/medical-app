from django.test import TestCase

# tests.py (или doctor_app/tests.py)

from django.test import TestCase, Client
from django.urls import reverse
from .models import Doctor, Symptom # CustomUser и DoctorSymptomGroup могут понадобиться для более сложных тестов

class SmartSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаем симптомы, которые будут автоматически связаны с врачами через сигнал
        # при создании объектов Doctor с соответствующими специализациями.
        cls.symptom_cough = Symptom.objects.create(name="Кашель")
        cls.symptom_fever = Symptom.objects.create(name="Температура")
        cls.symptom_headache = Symptom.objects.create(name="Головная боль") # Для терапевта и невролога
        # Дополнительные симптомы для других специализаций, если необходимо для полноты данных
        Symptom.objects.create(name="Боль в груди") # Для кардиолога
        Symptom.objects.create(name="Одышка") # Для кардиолога
        Symptom.objects.create(name="Сыпь") # Для дерматолога

        # Создаем врачей. Сигнал assign_symptoms_to_doctor должен сработать здесь.
        cls.therapist = Doctor.objects.create(name="Доктор Айболит", specialization="Терапевт", schedule="Пн-Пт 9-17")
        cls.neurologist = Doctor.objects.create(name="Доктор Хаус", specialization="Невролог", schedule="Вт-Сб 10-18")
        cls.cardiologist = Doctor.objects.create(name="Доктор Стренж", specialization="Кардиолог", schedule="Пн-Пт 9-17")
        cls.dermatologist = Doctor.objects.create(name="Доктор Скиннер", specialization="Дерматолог", schedule="Ср-Вс 11-19")

        # Можно добавить проверку, что сигнал отработал и симптомы связаны (опционально)
        # print(f"Therapist symptoms: {[s.name for s in cls.therapist.related_symptoms.all()]}")
        # Ожидаемый результат для Терапевта: ['Кашель', 'Температура', 'Головная боль', ...] (в зависимости от полного списка в сигнале)

    def setUp(self):
        self.client = Client()

    def test_smart_search_symptoms_match_specialist(self):
        """
        Тестирует сценарий, когда описанные симптомы четко указывают на специалиста.
        """
        # Описание содержит симптомы, характерные для Терапевта
        response = self.client.post(reverse('smart_search'), {'symptoms_description': 'У меня сильный кашель и высокая температура'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['searched']) # Проверяем, что поиск был выполнен
        
        # Проверяем, что Терапевт есть среди найденных специалистов
        found_specialists_data = response.context['found_specialists']
        self.assertTrue(any(spec_data[0] == 'Терапевт' for spec_data in found_specialists_data),
                        "Терапевт не найден среди предложенных специалистов")
        
        # Проверяем, что "Кашель" и "Температура" есть среди найденных симптомов
        found_symptoms_names = response.context['found_symptoms']
        self.assertIn('Кашель', found_symptoms_names, "Симптом 'Кашель' не найден")
        self.assertIn('Температура', found_symptoms_names, "Симптом 'Температура' не найден")

class AllDoctorsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Создаем врачей для тестов фильтрации
        self.doctor_therapist = Doctor.objects.create(name="Доктор Петров", specialization="Терапевт", schedule="Пн-Пт 08:00-16:00")
        self.doctor_cardiologist = Doctor.objects.create(name="Доктор Иванов", specialization="Кардиолог", schedule="Вт,Чт 10:00-18:00")
        self.another_therapist = Doctor.objects.create(name="Доктор Сидорова", specialization="Терапевт", schedule="Ср,Пт 09:00-17:00")

    def test_all_doctors_with_specialization_filter(self):
        """
        Тестирует фильтрацию врачей по указанной специализации ("Терапевт").
        """
        response = self.client.get(reverse('all_doctors'), {'specialization': 'Терапевт'})
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что врачи-терапевты присутствуют в контексте
        self.assertContains(response, self.doctor_therapist.name)
        self.assertContains(response, self.another_therapist.name)
        
        # Проверяем, что врач другой специализации (Кардиолог) отсутствует
        self.assertNotContains(response, self.doctor_cardiologist.name)
        
        # Проверяем количество врачей в контексте и их специализацию
        doctors_in_context = response.context['doctors']
        self.assertEqual(len(doctors_in_context), 2) # Ожидаем двух терапевтов
        for doctor in doctors_in_context:
            self.assertEqual(doctor.specialization, 'Терапевт')
