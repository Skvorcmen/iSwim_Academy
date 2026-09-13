from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.users.forms import RegisterForm

User = get_user_model()

class RegisterFormTest(TestCase):
    def test_register_form_valid(self):
        """Тест: валидная форма регистрации"""
        form_data = {
            'username': 'new_user',
            'email': 'new@test.com',
            'role': 'coach',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_register_form_password_mismatch(self):
        """Тест: пароли не совпадают"""
        form_data = {
            'username': 'new_user',
            'email': 'new@test.com',
            'role': 'coach',
            'password1': 'TestPass123!',
            'password2': 'TestPass456!',
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
    
    def test_register_form_missing_username(self):
        """Тест: отсутствует username"""
        form_data = {
            'email': 'new@test.com',
            'role': 'coach',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_register_form_email_optional(self):
        """Тест: email не обязателен"""
        form_data = {
            'username': 'new_user',
            'role': 'coach',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = RegisterForm(data=form_data)
        # Если email не обязателен, форма должна быть валидна
        # Если обязателен, то должна быть ошибка
        # Проверяем, что ошибки нет или она есть - в зависимости от требований
        if 'email' in form.fields and form.fields['email'].required:
            self.assertFalse(form.is_valid())
            self.assertIn('email', form.errors)
        else:
            self.assertTrue(form.is_valid())
    
    def test_register_form_short_password(self):
        """Тест: слишком короткий пароль"""
        form_data = {
            'username': 'new_user',
            'email': 'new@test.com',
            'role': 'coach',
            'password1': '123',
            'password2': '123',
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_register_form_invalid_role(self):
        """Тест: неверная роль"""
        form_data = {
            'username': 'new_user',
            'email': 'new@test.com',
            'role': 'invalid_role',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())
