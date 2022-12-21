from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post
from django.urls import reverse
from http import HTTPStatus

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='test_name01',
            email='test@mail.ru',
            password='test_password'
        )
        cls.post = Post.objects.create(
            author=PostsURLTests.author,
            text='Тестовая запись для создания нового поста',
            group=Group.objects.create(
                title=('Заголовок для тестовой группы'),
                slug='test_slug')
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = PostsURLTests.author
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_page_404_available(self):
        response = self.guest_client.get('/1234567890/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_404_page_uses_correct_template(self):
        response = self.client.get('/nonexistpage/')
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)

    def test_non_private_urls(self):
        """Страницы доступны всем."""
        post = PostsURLTests.post
        url_name = reverse('posts:post_detail', kwargs={'post_id': post.id})
        url_names = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}),
            reverse('posts:profile', kwargs={
                'username': 'HasNoName'
            }),
        )
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get(url_name)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url(self):
        """Авторизированному пользователю."""
        template = 'posts/create_post.html'
        address = reverse('posts:post_create')
        response = self.authorized_client.get(address)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, template)

        response = self.guest_client.get(address)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_author_url_and_template(self):
        """Только автору."""
        template = 'posts/create_post.html'
        post = PostsURLTests.post
        address = reverse('posts:edit', kwargs={'post_id': post.id})
        response = self.author_client.get(address)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': 'test_slug'}
            ),
            'posts/profile.html': reverse('posts:profile', kwargs={
                'username': 'HasNoName'
            }),
        }
        post = PostsURLTests.post
        url_name = reverse('posts:post_detail', kwargs={'post_id': post.id})
        template_name = 'posts/post_detail.html'
        response = self.authorized_client.get(url_name)
        self.assertTemplateUsed(response, template_name)
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
