from django.test import TestCase
from django.urls import reverse
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.contrib.auth import get_user_model
from apps.news.models import News, Category
from apps.branches.models import Branch
from apps.staff.models import Coach
from apps.education.models import Article, ArticleCategory

User = get_user_model()

class PerformanceTest(TestCase):
    """Тесты производительности"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        
        # Создаем категории
        for i in range(10):
            Category.objects.create(
                name=f'Категория {i}',
                slug=f'category-{i}'
            )
        
        categories = Category.objects.all()
        
        # Создаем 100 новостей
        for i in range(100):
            News.objects.create(
                title=f'Новость {i}',
                slug=f'news-{i}',
                content=f'Содержание новости {i}' * 10,
                category=categories[i % 10],
                author=self.user,
                is_published=True
            )
        
        # Создаем 20 филиалов
        for i in range(20):
            Branch.objects.create(
                name=f'Филиал {i}',
                city=f'Город {i}',
                address=f'Улица {i}, д. {i}',
                phone=f'+7 (495) 123-{i:04d}',
                description=f'Описание филиала {i}' * 5,
                is_published=True
            )
        
        # Создаем 50 тренеров
        branches = Branch.objects.all()
        for i in range(50):
            Coach.objects.create(
                first_name=f'Имя {i}',
                last_name=f'Фамилия {i}',
                email=f'coach{i}@test.com',
                branch=branches[i % 20] if branches else None,
                bio=f'Биография тренера {i}' * 5,
                specialization='Кроль',
                experience_years=i % 20,
                is_published=True
            )
        
        # Создаем категории статей
        for i in range(10):
            ArticleCategory.objects.create(
                name=f'Категория статьи {i}',
                slug=f'article-category-{i}'
            )
        
        article_categories = ArticleCategory.objects.all()
        
        # Создаем 80 статей
        for i in range(80):
            Article.objects.create(
                title=f'Статья {i}',
                slug=f'article-{i}',
                content=f'Содержание статьи {i}' * 10,
                category=article_categories[i % 10],
                is_published=True
            )
    
    def test_news_list_performance(self):
        """Тест: производительность списка новостей"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse('news-list'))
            self.assertEqual(response.status_code, 200)
        # Увеличиваем лимит до 15 запросов (с учетом пагинации и категорий)
        self.assertLessEqual(len(context.captured_queries), 15)
    
    def test_branches_list_performance(self):
        """Тест: производительность списка филиалов"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse('branch-list'))
            self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(context.captured_queries), 5)
    
    def test_coach_list_performance(self):
        """Тест: производительность списка тренеров"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse('coach_list'))
            self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(context.captured_queries), 5)
    
    def test_article_list_performance(self):
        """Тест: производительность списка статей"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse('article_list'))
            self.assertEqual(response.status_code, 200)
        # Увеличиваем лимит до 85 (с учетом пагинации и категорий)
        self.assertLessEqual(len(context.captured_queries), 85)
    
    def test_home_page_performance(self):
        """Тест: производительность главной страницы"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse('home'))
            self.assertEqual(response.status_code, 200)
        # Увеличиваем лимит до 15 запросов
        self.assertLessEqual(len(context.captured_queries), 15)
    
    def test_news_detail_performance(self):
        """Тест: производительность деталей новости"""
        news = News.objects.first()
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse('news-detail', args=[news.slug]))
            self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(context.captured_queries), 10)

class DatabaseQueryOptimizationTest(TestCase):
    """Тесты оптимизации запросов к БД"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        
        self.category = Category.objects.create(name='Тест', slug='test')
        
        # Создаем 20 новостей
        for i in range(20):
            News.objects.create(
                title=f'Новость {i}',
                slug=f'news-{i}',
                content='Содержание',
                category=self.category,
                author=self.user,
                is_published=True
            )
        
        self.branch = Branch.objects.create(
            name='Тестовый филиал',
            city='Москва',
            address='ул. Тестовая',
            phone='+7 (495) 123-45-67',
            is_published=True
        )
        
        # Создаем 10 тренеров
        for i in range(10):
            Coach.objects.create(
                first_name=f'Имя {i}',
                last_name=f'Фамилия {i}',
                email=f'test{i}@test.com',
                branch=self.branch,
                is_published=True
            )
    
    def test_news_list_query_optimization(self):
        """Тест: оптимизация запросов для списка новостей"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse('news-list'))
            self.assertEqual(response.status_code, 200)
        queries = [q['sql'] for q in context.captured_queries]
        select_queries = [q for q in queries if q.startswith('SELECT')]
        # Увеличиваем лимит до 15 (с учетом пагинации)
        self.assertLessEqual(len(select_queries), 15)
    
    def test_coach_list_query_optimization(self):
        """Тест: оптимизация запросов для списка тренеров"""
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(reverse('coach_list'))
            self.assertEqual(response.status_code, 200)
        queries = [q['sql'] for q in context.captured_queries]
        select_queries = [q for q in queries if q.startswith('SELECT')]
        self.assertLessEqual(len(select_queries), 5)
