# from django.contrib.auth import get_user_model
# from django.test import Client, TestCase
# from django.urls import reverse

# from ..models import Follow, Post

# User = get_user_model()


# class PostFollowTest(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.user_main = User.objects.create(username='user_main')

#     def setUp(self):
#         self.authorized_client = Client()
#         self.authorized_client.force_login(self.user_main)

#     def test_follow(self):
#         user_temp = User.objects.create(username='user_temp')
#         self.authorized_client.get(
#             reverse('post:profile_follow', kwargs={'username': user_temp}))
#         self.assertTrue(
#             Follow.objects.filter(
#                 user=self.user_main, author=user_temp).exists())

#     def test_unfollow(self):
#         user_temp = User.objects.create(username='user_temp')
#         Follow.objects.create(user=self.user_main, author=user_temp)
#         self.authorized_client.get(reverse(
#             'post:profile_unfollow', kwargs={'username': user_temp}))
#         self.assertFalse(
#             Follow.objects.filter(
#                 user=self.user_main, author=user_temp).exists())

#     def test(self):
#         user_temp = User.objects.create(username='user_temp')
#         Follow.objects.create(user=self.user_main, author=user_temp)
#         test_post = Post.objects.create(
#             text="one post",
#             author=user_temp,
#         )
#         response = self.authorized_client.get(reverse('post:follow_index'))
#         self.assertIn(
#             test_post, list(response.context['page_obj'].object_list))
#         Follow.objects.filter(user=self.user_main, author=user_temp).delete()
#         response = self.authorized_client.get(reverse('post:follow_index'))
#         self.assertNotIn(
#             test_post, list(response.context['page_obj'].object_list))
