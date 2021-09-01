import datetime as dt
from time import sleep

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostCacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.period_save_cache = dt.timedelta(seconds=20)
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание',
        )
        for i in range(4):
            cls.post = Post.objects.create(
                author=cls.user,
                text='сообщение-' + str(i + 1),
                group=cls.group,
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_main_page(self):
        response = self.authorized_client.get(reverse('post:index'))
        first_page = response.content
        now = dt.datetime.utcnow()
        finish = now + self.period_save_cache
        Post.objects.create(
            author=self.user,
            text='Еще одно сообщение',
            group=self.group,
        )
        while now <= finish:
            sleep(2)
            now = dt.datetime.utcnow()
            response = self.authorized_client.get(reverse('post:index'))
            if response.content != first_page:
                break
        self.assertNotEqual(response.content, first_page)
