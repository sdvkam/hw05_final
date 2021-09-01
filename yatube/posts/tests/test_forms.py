import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='author')
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
        cls.first_post = Post.objects.create(
            text='Simple text-1',
            author=cls.author,
            group=cls.test_group
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_pic_1 = SimpleUploadedFile(
            name='small_1.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.uploaded_pic_2 = SimpleUploadedFile(
            name='small_2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # folder where save pictures by defuault
        cls.folder_for_pics = Post._meta.get_field('image').upload_to
        cls.authorized_author = Client()
        cls.authorized_author.force_login(cls.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_form_create_post(self):
        expected_count_posts = Post.objects.count() + 1
        form_data = {
            'text': 'New post',
            'group': self.test_group.pk,
        }
        response = self.authorized_author.post(
            reverse('post:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('post:profile', args=[self.author]))
        # Checking that the number of posts has increased
        self.assertEqual(Post.objects.count(), expected_count_posts)
        # Checking that a record  with the transmitted data was created
        self.assertTrue(
            Post.objects.filter(
                pk=expected_count_posts,
                text=form_data['text'],
                author=self.author,
                group=form_data['group']
            ).exists()
        )

    def test_form_edit_post(self):
        expected_count_post = Post.objects.count()
        form_data = {
            'text': 'Other text',
            'group': self.other_group.pk,
        }
        response = self.authorized_author.post(
            reverse('post:post_edit', kwargs={'post_id': self.first_post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('post:post_detail', args=[self.first_post.pk]))
        # Checking that the number of posts has not change
        self.assertEqual(Post.objects.count(), expected_count_post)
        # Checking that record did not change
        self.assertTrue(
            Post.objects.filter(
                pk=self.first_post.pk,
                text=form_data['text'],
                author=self.author,
                group=form_data['group']
            ).exists()
        )

    def test_form_create_post_with_picture(self):
        expected_count_posts = Post.objects.count() + 1
        form_data = {
            'text': 'Create post with picture',
            'image': self.uploaded_pic_1,
        }
        self.authorized_author.post(
            reverse('post:post_create'),
            data=form_data,
            follow=True
        )
        # Checking that the number of posts has increased
        self.assertEqual(Post.objects.count(), expected_count_posts)
        # Checking that a record with the picture was created
        self.assertTrue(
            Post.objects.filter(
                pk=expected_count_posts,
                text=form_data['text'],
                author=self.author,
                image=self.folder_for_pics + str(form_data['image'])
            ).exists()
        )

    def test_form_edit_post_add_picture(self):
        expected_count_post = Post.objects.count()
        form_data = {
            'text': 'Add picture to the post',
            'image': self.uploaded_pic_2,
        }
        self.authorized_author.post(
            reverse('post:post_edit', kwargs={'post_id': self.first_post.pk}),
            data=form_data,
            follow=True
        )
        # Checking that the number of posts has not change
        self.assertEqual(Post.objects.count(), expected_count_post)
        # Checking that record did not change
        self.assertTrue(
            Post.objects.filter(
                pk=self.first_post.pk,
                text=form_data['text'],
                author=self.author,
                image=self.folder_for_pics + str(form_data['image'])
            ).exists()
        )

    def test_form_add_comment(self):
        pk = self.first_post.pk
        expected_count_com = self.first_post.comments.count() + 1
        form_data = {'text': 'New comment', }
        response = self.authorized_author.post(
            reverse('post:add_comment', kwargs={'post_id': pk}),
            data=form_data,
            follow=True
        )
        # Checking that the number of comments of this post has increased
        self.assertEqual(self.first_post.comments.count(), expected_count_com)
        # Checking that  this comment was created
        self.assertTrue(
            self.first_post.comments.filter(
                pk=pk,
                text=form_data['text'],
                author=self.author,
            ).exists()
        )
        # Checking that comment appear on page of this post
        comment = self.first_post.comments.filter(
            pk=pk,
            text=form_data['text'],
            author=self.author,
        )
        self.assertTrue(list(comment)[0] in list(response.context['comments']))
