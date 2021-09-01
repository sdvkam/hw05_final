from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class CoreURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_author = User.objects.create(username='author')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.authorized_author)

    def test_url_correct_templates(self):
        check_url = {'/unexisting.page/': 'core/404.html', }
        for adress, template in check_url.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)
