from django.test import TestCase
from django.urls import reverse, resolve
from apps.news.views import NewsListView, NewsDetailView
from apps.branches.views import BranchListView, BranchDetailView
from apps.staff.views import CoachListView, CoachDetailView
from apps.education.views import ArticleListView, ArticleDetailView
from apps.pages.views import HomeView, ContactsView, AboutView
from apps.users.views import RegisterView, ProfileView

class NewsURLsTest(TestCase):
    def test_news_list_url(self):
        url = reverse('news-list')
        self.assertEqual(url, '/news/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, NewsListView)
    
    def test_news_detail_url(self):
        url = reverse('news-detail', args=['test-slug'])
        self.assertEqual(url, '/news/slug/test-slug')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, NewsDetailView)

class BranchesURLsTest(TestCase):
    def test_branch_list_url(self):
        url = reverse('branch-list')
        self.assertEqual(url, '/branches/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, BranchListView)
    
    def test_branch_detail_url(self):
        url = reverse('branch-detail', args=[1])
        self.assertEqual(url, '/branches/1/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, BranchDetailView)

class StaffURLsTest(TestCase):
    def test_coach_list_url(self):
        url = reverse('coach_list')
        self.assertEqual(url, '/coaches/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, CoachListView)
    
    def test_coach_detail_url(self):
        url = reverse('coach_detail', args=[1])
        self.assertEqual(url, '/coaches/1/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, CoachDetailView)

class EducationURLsTest(TestCase):
    def test_article_list_url(self):
        url = reverse('article_list')
        self.assertEqual(url, '/educations/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, ArticleListView)
    
    def test_article_detail_url(self):
        url = reverse('article_detail', args=['test-slug'])
        self.assertEqual(url, '/educations/test-slug/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, ArticleDetailView)

class PagesURLsTest(TestCase):
    def test_home_url(self):
        url = reverse('home')
        self.assertEqual(url, '/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, HomeView)
    
    def test_about_url(self):
        url = reverse('about')
        self.assertEqual(url, '/about/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, AboutView)
    
    def test_contacts_url(self):
        url = reverse('contacts')
        self.assertEqual(url, '/contacts/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, ContactsView)

class UsersURLsTest(TestCase):
    def test_register_url(self):
        url = reverse('register')
        self.assertEqual(url, '/accounts/register/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, RegisterView)
    
    def test_profile_url(self):
        url = reverse('profile')
        self.assertEqual(url, '/accounts/profile/')
        resolver = resolve(url)
        self.assertEqual(resolver.func.view_class, ProfileView)
