from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.news.models import News, Category
from apps.branches.models import Branch
from apps.staff.models import Coach
from apps.education.models import Article, ArticleCategory

User = get_user_model()

class NewsViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='test123')
        self.category = Category.objects.create(name='Соревнования', slug='competitions')
        self.news = News.objects.create(
            title='Тестовая новость',
            slug='test-news',
            content='Тестовое содержание',
            category=self.category,
            author=self.user,
            is_published=True
        )
    
    def test_news_list_view(self):
        response = self.client.get(reverse('news-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовая новость')
    
    def test_news_detail_view(self):
        response = self.client.get(reverse('news-detail', args=[self.news.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовая новость')

class BranchViewsTest(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name='Бассейн Динамо',
            city='Москва',
            address='ул. Динамо, д. 1',
            phone='+7 (495) 123-45-67',
            is_published=True
        )
    
    def test_branch_list_view(self):
        response = self.client.get(reverse('branch-list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Бассейн Динамо')
    
    def test_branch_detail_view(self):
        response = self.client.get(reverse('branch-detail', args=[self.branch.id]))
        self.assertEqual(response.status_code, 200)

class CoachViewsTest(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name='Бассейн Динамо',
            city='Москва',
            address='ул. Динамо, д. 1',
            phone='+7 (495) 123-45-67'
        )
        self.coach = Coach.objects.create(
            first_name='Иван',
            last_name='Петров',
            email='ivan@test.com',
            branch=self.branch,
            is_published=True
        )
    
    def test_coach_list_view(self):
        response = self.client.get(reverse('coach_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Иван Петров')
    
    def test_coach_detail_view(self):
        response = self.client.get(reverse('coach_detail', args=[self.coach.id]))
        self.assertEqual(response.status_code, 200)

class ArticleViewsTest(TestCase):
    def setUp(self):
        self.category = ArticleCategory.objects.create(
            name='Обучение',
            slug='education'
        )
        self.article = Article.objects.create(
            title='Тестовая статья',
            slug='test-article',
            content='Тестовое содержание',
            category=self.category,
            is_published=True
        )
    
    def test_article_list_view(self):
        response = self.client.get(reverse('article_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Тестовая статья')
    
    def test_article_detail_view(self):
        response = self.client.get(reverse('article_detail', args=[self.article.slug]))
        self.assertEqual(response.status_code, 200)

class PagesViewsTest(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            name='Бассейн Динамо',
            city='Москва',
            address='ул. Динамо, д. 1',
            phone='+7 (495) 123-45-67',
            is_published=True
        )
        self.coach = Coach.objects.create(
            first_name='Иван',
            last_name='Петров',
            email='ivan@test.com',
            branch=self.branch,
            is_published=True
        )
    
    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
    
    def test_contacts_view(self):
        response = self.client.get(reverse('contacts'))
        self.assertEqual(response.status_code, 200)
