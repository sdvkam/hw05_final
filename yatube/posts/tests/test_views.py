import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.test_group = Group.objects.create(
            title='Test group',
            slug='test_group',
            description='This is test group'
        )
        for i in range(13):
            Post.objects.create(
                text='Simple text-' + str(i + 1),
                author=cls.author,
                group=cls.test_group
            )
        cls.first_post = Post.objects.get(pk=1)
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('post:index'): 'posts/index.html',
            reverse('post:group_list', kwargs={'slug': self.test_group.slug}):
                'posts/group_list.html',
            reverse('post:profile', kwargs={'username': self.author.username}):
                'posts/profile.html',
            reverse('post:post_detail',
                    kwargs={'post_id': self.first_post.pk}):
                        'posts/post_detail.html',
            reverse('post:post_edit', kwargs={'post_id': self.first_post.pk}):
                'posts/create_post.html',
            reverse('post:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_with_list_posts_context(self):
        """pages: main - all post, posts of one group, posts of one author."""
        reverse_context = {
            reverse('post:index'):
                list(Post.objects.all()[:10]),
            reverse('post:group_list', kwargs={'slug': self.test_group.slug}):
                list(Group.objects.get(slug='test_group').posts.all()[:10]),
            reverse('post:profile', kwargs={'username': self.author.username}):
                list(User.objects.get(username='author').posts.all()[:10])
        }
        for adress, passed_to_context in reverse_context.items():
            with self.subTest(adress=adress):
                response = self.authorized_author.get(adress)
                from_context = list(response.context['page_obj'].object_list)
                self.assertListEqual(passed_to_context, from_context)

    def test_page_post_detail_context(self):
        response = self.authorized_author.get(
            reverse('post:post_detail',
                    kwargs={'post_id': self.first_post.pk}))
        from_context = str(response.context['post'])
        passed_to_context = str(self.first_post)
        self.assertEqual(passed_to_context, from_context)

    def test_page_post_create_context(self):
        response = self.authorized_author.get(reverse('post:post_create'))
        obj_from_context = response.context.get('form').fields.get('text')
        self.assertIsInstance(obj_from_context, forms.fields.CharField)
        obj_from_context = response.context.get('form').fields.get('group')
        self.assertIsInstance(obj_from_context, forms.models.ModelChoiceField)

    def test_page_post_edit_context(self):
        response = self.authorized_author.get(
            reverse('post:post_edit', kwargs={'post_id': self.first_post.pk}))
        obj_from_context = response.context.get('form').fields.get('text')
        self.assertIsInstance(obj_from_context, forms.fields.CharField)
        obj_from_context = response.context.get('form').fields.get('group')
        self.assertIsInstance(obj_from_context, forms.models.ModelChoiceField)
        first_post = self.first_post
        passed_to_context = first_post.text
        from_context = response.context['form']['text'].value()
        self.assertEqual(passed_to_context, from_context)
        # список групп на форме начинается с 0 -> пустого названия
        # поэтому можно брать как номер группы в списке - group.pk
        passed_to_context = first_post.group.pk
        from_context = response.context['form']['group'].value()
        self.assertEqual(passed_to_context, from_context)

    def test_where_one_post_exist(self):
        """yes: main, own group, own author; no: not his own group."""
        other_group = Group.objects.create(
            title='Other group',
            slug='other_group',
            description='This is other group'
        )
        other_author = User.objects.create(username='other_author')
        seek_post = Post.objects.create(
            text='one post of other group',
            author=other_author,
            group=other_group
        )
        slug = seek_post.group.slug
        other_author = seek_post.author.username
        # checking: post exist on this pages
        reverse_pages = [
            reverse('post:index'),
            reverse('post:group_list', kwargs={'slug': slug}),
            reverse('post:profile', kwargs={'username': other_author})
        ]
        for reverse_page in reverse_pages:
            with self.subTest(url=reverse_page):
                response = self.authorized_author.get(reverse_page)
                list_posts_context = (
                    response.context['page_obj'].object_list)
                self.assertEqual(list_posts_context[0], seek_post)
        # checking: post do not exist on page of not own group
        reverse_page = reverse(
            'post:group_list', kwargs={'slug': self.test_group.slug})
        with self.subTest(url=reverse_page):
            response = self.authorized_author.get(reverse_page)
            list_posts_context = response.context['page_obj'].object_list
            self.assertNotEqual(list_posts_context[0], seek_post)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.other_author = User.objects.create(username='other_author')
        cls.test_group = Group.objects.create(
            title='Test group',
            slug='test_group',
            description='This is test group'
        )
        cls.other_group = Group.objects.create(
            title='Other group',
            slug='other_group',
            description='This is other group'
        )
        for i in range(13):
            Post.objects.create(
                text='Simple text-' + str(i + 1),
                author=cls.author,
                group=cls.test_group
            )
        Post.objects.create(
            text='Simple text-14',
            author=cls.author
        )
        Post.objects.create(
            text='Simple text-15',
            author=cls.other_author,
            group=cls.other_group
        )
        # количество постов на полной странице paginator
        cls.nums_paginator = 10
        # считаем количество постов на главной странице
        cls.nums_main = Post.objects.count()
        # считаем количество постов на странице группы
        cls.nums_group = cls.test_group.posts.count()
        # считаем количество постов на странице автора
        cls.nums_author = cls.author.posts.count()
        # авторизованный пользователь с одним созданным постом
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

    def test_paginator(self):
        """main page, posts of one group, posts of one author."""
        reverse_paginator = {
            reverse('post:index'): self.nums_main - self.nums_paginator,
            reverse('post:group_list',
                    kwargs={'slug': self.test_group.slug}):
                        self.nums_group - self.nums_paginator,
            reverse('post:profile',
                    kwargs={'username': self.author.username}):
                        self.nums_author - self.nums_paginator
        }
        for reverse_name, amout_post_on2page in reverse_paginator.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), self.nums_paginator)
                response = self.authorized_author.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), amout_post_on2page)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ShowPicturesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
        cls.test_group = Group.objects.create(
            title='Test group',
            slug='test_group',
            description='This is test group'
        )
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
        cls.post_with_picture = Post.objects.create(
            text='Text and picture',
            author=cls.author,
            group=cls.test_group,
            image=uploaded
        )
        cls.post_without_pic = Post.objects.create(
            text='Text and all',
            author=cls.author,
            group=cls.test_group
        )
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pictures_on_pages_list_posts(self):
        reverse_context = {
            reverse('post:index'):
                Post.objects.all()[:10],
            reverse('post:group_list', kwargs={'slug': self.test_group.slug}):
                Group.objects.get(slug='test_group').posts.all()[:10],
            reverse('post:profile', kwargs={'username': self.author.username}):
                User.objects.get(username='author').posts.all()[:10]
        }
        for adress, passed_posts in reverse_context.items():
            with self.subTest(adress=adress):
                nums_passed_posts = passed_posts.count()
                response = self.authorized_author.get(adress)
                objs_on_page = list(response.context['page_obj'].object_list)
                self.assertEqual(nums_passed_posts, len(objs_on_page))
                for i in range(nums_passed_posts):
                    self.assertEqual(
                        passed_posts[i].image, objs_on_page[i].image)

    def test_picture_on_page_post_detail(self):
        passed_post = self.post_with_picture
        adress = reverse(
            'post:post_detail', kwargs={'post_id': passed_post.id})
        response = self.authorized_author.get(adress)
        self.assertEqual(passed_post.image, response.context['post'].image)
