import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, Comment
from posts.forms import PostForm, CommentForm
from http import HTTPStatus
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.form = PostForm()
        cls.form_comment = CommentForm()
        cls.user = User.objects.create_user(username='Japrojah')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post(self):
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_1 = Post.objects.get(id=self.group.id)
        author_1 = User.objects.get(username='Japrojah')
        group_1 = Group.objects.get(title='Заголовок для тестовой группы')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertEqual(post_1.text, 'Данные из формы')
        self.assertEqual(author_1.username, 'Japrojah')
        self.assertEqual(group_1.title, 'Заголовок для тестовой группы')

    def test_authorized_edit_post(self):
        """Тест изменение поста."""
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.group.id)
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:edit',
                    args=(f'{post_2.id}',)),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.group.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post_2.text, 'Измененный текст')

    def test_create_post_image(self):
        """Валидная форма создает запись в Task."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_comment_added(self):
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            author=self.user,
            text='Это тестовый пост'
        )
        form_data = {
            'text': 'комент'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(f'{post.id}',)),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
