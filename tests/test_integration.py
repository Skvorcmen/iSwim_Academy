from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.news.models import News, Category
from apps.branches.models import Branch
from apps.staff.models import Coach
from apps.education.models import Article, ArticleCategory

User = get_user_model()

class FullUserJourneyTest(TestCase):
    """Интеграционный тест: полный путь пользователя по сайту"""
    
    def setUp(self):
        # Создаем тестовые данные
        self.user = User.objects.create_user(
            username='testuser',
            password='test123',
            email='test@test.com'
        )
        
        self.category = Category.objects.create(
            name='Соревнования',
            slug='competitions'
        )
        
        self.news = News.objects.create(
            title='Тестовая новость',
            slug='test-news',
            content='Тестовое содержание новости',
            category=self.category,
            author=self.user,
            is_published=True
        )
        
        self.branch = Branch.objects.create(
            name='Бассейн Динамо',
            city='Москва',
            address='ул. Динамо, д. 1',
            phone='+7 (495) 123-45-67',
            description='Описание филиала',
            is_published=True
        )
        
        self.coach = Coach.objects.create(
            first_name='Иван',
            last_name='Петров',
            email='ivan@test.com',
            branch=self.branch,
            bio='Опытный тренер',
            specialization='Кроль',
            experience_years=5,
            is_published=True
        )
        
        self.article_category = ArticleCategory.objects.create(
            name='Обучение',
            slug='education'
        )
        
        self.article = Article.objects.create(
            title='Тестовая статья',
            slug='test-article',
            content='Тестовое содержание статьи',
            category=self.article_category,
            is_published=True
        )
    
    def test_home_page_flow(self):
        """Тест: главная страница отображает все данные"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что все данные на месте
        self.assertContains(response, 'Тестовая новость')
        self.assertContains(response, 'Бассейн Динамо')
        self.assertContains(response, 'Иван Петров')
        self.assertContains(response, 'Тестовая статья')
    
    def test_news_flow(self):
        """Тест: просмотр новостей"""
        # Список новостей
        response = self.client.get(reverse('news-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовая новость')
        
        # Детали новости
        response = self.client.get(reverse('news-detail', args=[self.news.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовое содержание новости')
    
    def test_branches_flow(self):
        """Тест: просмотр филиалов"""
        # Список филиалов
        response = self.client.get(reverse('branch-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Бассейн Динамо')
        
        # Детали филиала
        response = self.client.get(reverse('branch-detail', args=[self.branch.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Описание филиала')
    
    def test_staff_flow(self):
        """Тест: просмотр тренеров"""
        # Список тренеров
        response = self.client.get(reverse('coach_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Иван Петров')
        
        # Детали тренера
        response = self.client.get(reverse('coach_detail', args=[self.coach.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Опытный тренер')
    
    def test_education_flow(self):
        """Тест: просмотр статей"""
        # Список статей
        response = self.client.get(reverse('article_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовая статья')
        
        # Детали статьи
        response = self.client.get(reverse('article_detail', args=[self.article.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовое содержание статьи')
    
    def test_pages_flow(self):
        """Тест: статические страницы"""
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'О нас')
        
        response = self.client.get(reverse('contacts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Контакты')
    
    def test_registration_flow(self):
        """Тест: регистрация пользователя"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        
        # Регистрация нового пользователя
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'role': 'athlete',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        response = self.client.post(reverse('register'), data)
        # Должен быть редирект после успешной регистрации
        self.assertIn(response.status_code, [302, 200])
        
        # Проверяем, что пользователь создан
        self.assertTrue(User.objects.filter(username='newuser').exists())

class SearchAndFilterTest(TestCase):
    """Интеграционные тесты для поиска и фильтрации"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        
        self.category1 = Category.objects.create(name='Соревнования', slug='competitions')
        self.category2 = Category.objects.create(name='Новости клуба', slug='club-news')
        
        self.news1 = News.objects.create(
            title='Новость 1',
            slug='news-1',
            content='Содержание 1',
            category=self.category1,
            author=self.user,
            is_published=True
        )
        self.news2 = News.objects.create(
            title='Новость 2',
            slug='news-2',
            content='Содержание 2',
            category=self.category2,
            author=self.user,
            is_published=True
        )
        
        self.article_category1 = ArticleCategory.objects.create(
            name='Обучение',
            slug='education'
        )
        self.article_category2 = ArticleCategory.objects.create(
            name='Тренировки',
            slug='training'
        )
        
        self.article1 = Article.objects.create(
            title='Статья 1',
            slug='article-1',
            content='Содержание 1',
            category=self.article_category1,
            is_published=True
        )
        self.article2 = Article.objects.create(
            title='Статья 2',
            slug='article-2',
            content='Содержание 2',
            category=self.article_category2,
            is_published=True
        )
    
    def test_news_filter_by_category(self):
        """Тест: фильтрация новостей по категории"""
        response = self.client.get(reverse('news-list') + '?category=competitions')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Новость 1')
        self.assertNotContains(response, 'Новость 2')
    
    def test_articles_filter_by_category(self):
        """Тест: фильтрация статей по категории"""
        response = self.client.get(reverse('article_list') + '?category=education')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Статья 1')
        self.assertNotContains(response, 'Статья 2')
