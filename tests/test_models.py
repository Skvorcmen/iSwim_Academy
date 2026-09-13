from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.news.models import News, Category
from apps.branches.models import Branch
from apps.staff.models import Coach
from apps.education.models import Article, ArticleCategory
from apps.users.models import User

User = get_user_model()

class CoreModelsTest(TestCase):
    def test_timestamped_model_abstract(self):
        from apps.core.models import TimeStampedModel
        self.assertTrue(TimeStampedModel._meta.abstract)
        fields = [f.name for f in TimeStampedModel._meta.fields]
        self.assertIn('created_at', fields)
        self.assertIn('updated_at', fields)

class UserModelTest(TestCase):
    def test_user_creation_with_role(self):
        user = User.objects.create_user(
            username='test_user',
            password='test123',
            role='coach'
        )
        self.assertEqual(user.username, 'test_user')
        self.assertEqual(user.role, 'coach')
    
    def test_user_default_role(self):
        user = User.objects.create_user(
            username='default_user',
            password='default123'
        )
        self.assertEqual(user.role, 'fan')

class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(
            name='Тестовая категория',
            slug='test-category'
        )
        self.assertEqual(category.name, 'Тестовая категория')
        self.assertEqual(category.slug, 'test-category')

class NewsModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.category = Category.objects.create(name='Соревнования', slug='competitions')
    
    def test_news_creation(self):
        news = News.objects.create(
            title='Тестовая новость',
            slug='test-news',
            content='Тестовое содержание',
            category=self.category,
            author=self.user,
            is_published=True
        )
        self.assertEqual(news.title, 'Тестовая новость')
        self.assertTrue(news.is_published)

class BranchModelTest(TestCase):
    def test_branch_creation(self):
        branch = Branch.objects.create(
            name='Бассейн Динамо',
            city='Москва',
            address='ул. Динамо, д. 1',
            phone='+7 (495) 123-45-67',
            is_published=True
        )
        self.assertEqual(branch.name, 'Бассейн Динамо')
        self.assertTrue(branch.is_published)

class CoachModelTest(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name='Бассейн Динамо',
            city='Москва',
            address='ул. Динамо, д. 1',
            phone='+7 (495) 123-45-67'
        )
    
    def test_coach_creation(self):
        coach = Coach.objects.create(
            first_name='Иван',
            last_name='Петров',
            email='ivan@test.com',
            branch=self.branch,
            experience_years=5,
            is_published=True
        )
        self.assertEqual(coach.first_name, 'Иван')
        self.assertTrue(coach.is_published)

class ArticleModelTest(TestCase):
    def setUp(self):
        self.category = ArticleCategory.objects.create(
            name='Обучение',
            slug='education'
        )
    
    def test_article_creation(self):
        article = Article.objects.create(
            title='Тестовая статья',
            slug='test-article',
            content='Тестовое содержание',
            category=self.category,
            is_published=True
        )
        self.assertEqual(article.title, 'Тестовая статья')
        self.assertTrue(article.is_published)
