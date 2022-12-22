import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, Comment, Follow
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.cache import cache


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.author = User.objects.create_user(
            username='author_name',
            email='test@mail.ru',
            password='test_pass',
        )
        cls.second_author = User.objects.create_user(
            username='test_name2',
            email='test2@mail.ru',
            password='test_pass',
        )

        cls.group = Group.objects.create(
            title='Заголовок для 1 тестовой группы',
            slug='test_slug1'
        )

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        cls.post1 = Post.objects.create(
            author=cls.author,
            text='Тестовая запись для создания 1 поста',
            group=cls.group)

        cls.post2 = Post.objects.create(
            author=cls.second_author,
            text='Тестовая запись для создания 2 поста',
            group=Group.objects.create(
                title='Заголовок для 2 тестовой группы',
                slug='test_slug2'),
            image=cls.uploaded
        )

        cls.comment = Comment.objects.create(
            post=cls.post2,
            author=cls.second_author,
            text='это тестовый коммент',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Japrojah')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = PostsViewsTests.author
        self.author_client = Client()
        self.author_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post = PostsViewsTests.post2
        templates_page_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': 'test_slug2'})
            ),
            'posts/post_detail.html': reverse('posts:post_detail', kwargs={
                'post_id': f'{post.id}'
            }),
            'posts/profile.html': reverse('posts:profile', kwargs={
                'username': 'Japrojah'
            })
        }
        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
        post = PostsViewsTests.post1
        address = (f'/posts/{post.id}/edit/')
        response = self.author_client.get(address)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(post_text_0,
                         'Тестовая запись для создания 2 поста')
        expected_context = first_object.image
        self.assertEqual(expected_context, self.post2.image)

    def test_group_pages_show_correct_context(self):
        """Шаблон группы c правильным контекстом."""
        response = self.authorized_client.get(reverse
                                              ('posts:group_list',
                                               kwargs={'slug': 'test_slug2'}))
        first_object = response.context['group']
        group_title_0 = first_object.title
        group_slug_0 = first_object.slug
        self.assertEqual(group_title_0, 'Заголовок для 2 тестовой группы')
        self.assertEqual(group_slug_0, 'test_slug2')
        first_object = response.context['page_obj'][0]
        expected_context = first_object.image
        self.assertEqual(expected_context, self.post2.image)

    def test_post_another_group(self):
        """Пост не попал в другую группу."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug1'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertTrue(post_text_0, 'Тестовая запись для создания 2 поста')

    def test_create_post_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'test_name2'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(response.context['author'].username, 'test_name2')
        self.assertEqual(post_text_0, 'Тестовая запись для создания 2 поста')
        expected_context = first_object.image
        self.assertEqual(expected_context, self.post2.image)

    def test_post_detail_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post2.id})
        )
        object = response.context.get('post')
        comment_object = response.context['comments'][0]
        self.assertEqual(object.image, self.post2.image)
        self.assertEqual(comment_object.text, self.comment.text)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='Пост для теста кэша',
            author=self.author,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name',
                                              email='test@mail.ru',
                                              password='test_pass',)
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug2',
            description='Тестовое описание')
        cls.posts = []
        for i in range(12):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Japrojah')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        list_urls = {
            reverse("posts:index"): "index",
            reverse(
                "posts:group_list",
                args=(f'{self.group.slug}',)
            ): "group",
            reverse(
                "posts:profile",
                args=(f'{self.author.username}',)
            ): "profile",
        }
        for tested_url in list_urls.keys():
            response = self.authorized_client.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 10
            )

    def test_second_page_contains_two_posts(self):
        list_urls = {
            reverse('posts:index') + '?page=2': 'index',
            reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug2'}
            ) + '?page=2':
            'group_list',
            reverse(
                'posts:profile',
                kwargs={'username': 'test_name'}
            ) + '?page=2':
            'profile',
        }
        for tested_url in list_urls.keys():
            response = self.authorized_client.get(tested_url)
            self.assertEqual(
                len(response.context.get('page_obj').object_list), 2
            )


class FollowTests(TestCase):
    def setUp(self):
        self.client_auth_follower = Client()
        self.client_auth_following = Client()
        self.user_follower = User.objects.create_user(username='follower',
                                                      email='test_11@mail.ru',
                                                      password='test_pass')
        self.user_following = User.objects.create_user(username='following',
                                                       email='test22@mail.ru',
                                                       password='test_pass')
        self.post = Post.objects.create(
            author=self.user_following,
            text='Тестовая запись для тестирования ленты'
        )
        self.client_auth_follower.force_login(self.user_follower)
        self.client_auth_following.force_login(self.user_following)

    def test_follow(self):
        cache.clear()
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        self.client_auth_follower.get(reverse('posts:profile_follow',
                                              kwargs={'username':
                                                      self.user_following.
                                                      username}))
        self.client_auth_follower.get(reverse('posts:profile_unfollow',
                                      kwargs={'username':
                                              self.user_following.username}))
        cache.clear()
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        cache.clear()
        response = self.client_auth_follower.get(
            reverse('posts:follow_index')
        )
        post_text_0 = response.context["page_obj"][0].text
        self.assertEqual(post_text_0, 'Тестовая запись для тестирования ленты')
        cache.clear()
        response = self.client_auth_following.get('/follow/')
        self.assertNotContains(response,
                               'Тестовая запись для тестирования ленты')
