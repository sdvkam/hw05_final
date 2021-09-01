from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_author = User.objects.create(username='author')
        cls.other_author = User.objects.create(username='other_author')
        cls.test_group = Group.objects.create(
            title='Test group',
            slug='test_group',
            description='This empty test group'
        )
        cls.first_post = Post.objects.create(
            text='Simple text',
            author=cls.authorized_author,
            group=cls.test_group
        )
        cls.post_other_author = Post.objects.create(
            text='Post of other author',
            author=cls.other_author,
            group=cls.test_group
        )
        cls.test_comment = Comment.objects.create(
            post=cls.first_post,
            author=cls.authorized_author,
            text='Test comment'
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.authorized_author)

    def test_urls_exists_anonymous_user(self):
        check_urls = {
            reverse('post:index'): HTTPStatus.OK,
            reverse('post:group_list',
                    kwargs={'slug': self.test_group.slug}):
                        HTTPStatus.OK,
            reverse('post:profile',
                    kwargs={'username': self.authorized_author.username}):
                        HTTPStatus.OK,
            reverse('post:post_detail',
                    kwargs={'post_id': self.first_post.pk}):
                        HTTPStatus.OK,
            reverse('post:post_edit',
                    kwargs={'post_id': self.first_post.pk}):
                        HTTPStatus.FOUND,
            reverse('post:post_create'): HTTPStatus.FOUND,
            reverse('post:add_comment',
                    kwargs={'post_id': self.first_post.pk}):
                        HTTPStatus.FOUND,
            '/unexisting.page/': HTTPStatus.NOT_FOUND,
        }
        for adress, status in check_urls.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_urls_exists_authorized_author(self):
        check_urls = {
            reverse('post:index'): HTTPStatus.OK,
            reverse('post:group_list',
                    kwargs={'slug': self.test_group.slug}):
                        HTTPStatus.OK,
            reverse('post:profile',
                    kwargs={'username': self.authorized_author.username}):
                        HTTPStatus.OK,
            reverse('post:post_detail',
                    kwargs={'post_id': self.first_post.pk}):
                        HTTPStatus.OK,
            reverse('post:post_edit',
                    kwargs={'post_id': self.first_post.pk}):
                        HTTPStatus.OK,
            # edit not own post -> redirect
            reverse('post:post_edit',
                    kwargs={'post_id': self.post_other_author.pk}):
                        HTTPStatus.FOUND,
            reverse('post:post_create'): HTTPStatus.OK,
            reverse('post:add_comment',
                    kwargs={'post_id': self.first_post.pk}):
                        HTTPStatus.FOUND,
            '/unexisting.page/': HTTPStatus.NOT_FOUND,
        }
        for adress, status in check_urls.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, status)

    def test_uses_correct_templates(self):
        check_templates = {
            reverse('post:index'): 'posts/index.html',
            reverse('post:group_list',
                    kwargs={'slug': self.test_group.slug}):
                        'posts/group_list.html',
            reverse('post:profile',
                    kwargs={'username': self.authorized_author.username}):
                        'posts/profile.html',
            reverse('post:post_detail',
                    kwargs={'post_id': self.first_post.pk}):
                        'posts/post_detail.html',
            reverse('post:post_edit',
                    kwargs={'post_id': self.first_post.pk}):
                        'posts/create_post.html',
            reverse('post:post_create'): 'posts/create_post.html',
        }
        for adress, template in check_templates.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_redirect_anonymous(self):
        """editing a post, creating a post, create comment -> page of login."""
        pk = self.first_post.pk
        check_urls = {
            reverse('post:post_edit', kwargs={'post_id': pk}):
                reverse('users:login') + '?next='
                + reverse('post:post_edit', kwargs={'post_id': pk}),
            reverse('post:post_create'):
                reverse('users:login') + '?next='
                + reverse('post:post_create'),
            reverse('post:add_comment', kwargs={'post_id': pk}):
                reverse('users:login') + '?next='
                + reverse('post:add_comment', kwargs={'post_id': pk}),
        }
        for adress, redirect in check_urls.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress, follow=True)
                self.assertRedirects(response, redirect)

    def test_redirect_authorized(self):
        """edit not himself post, add comment -> page of this post."""
        pk = self.post_other_author.pk
        check_urls = {
            reverse('post:post_edit', kwargs={'post_id': pk}):
                reverse('post:post_detail', kwargs={'post_id': pk}),
            reverse('post:add_comment', kwargs={'post_id': pk}):
                reverse('post:post_detail', kwargs={'post_id': pk}),
        }
        for adress, redirect in check_urls.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress, follow=True)
                self.assertRedirects(response, redirect)
