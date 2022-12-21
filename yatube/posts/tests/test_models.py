from django.test import TestCase
from ..models import Group, Post
from django.contrib.auth import get_user_model

User = get_user_model()


class PostModelTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            author=User.objects.create_user(username='test_name',
                                            email='test@mail.ru',
                                            password='test_password',),
            text='Тестовая запись для создания нового поста'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )

    def test_str_method_post(self):
        post = PostModelTests.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_str_method_group(self):
        group = PostModelTests.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
