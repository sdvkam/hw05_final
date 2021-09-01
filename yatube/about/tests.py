from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()

    def test_urls_exists_at_desired_location(self):
        dic_check = {
            reverse('about:author'): HTTPStatus.OK,
            reverse('about:tech'): HTTPStatus.OK,
        }
        for url_page, expected_http_staus in dic_check.items():
            response = self.guest_client.get(url_page)
            with self.subTest(url_page=url_page):
                self.assertEqual(response.status_code, expected_http_staus)

    def test_uses_correct_templates(self):
        dic_check = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for url_page, expected_template in dic_check.items():
            response = self.guest_client.get(url_page)
            with self.subTest(url_page=url_page):
                self.assertTemplateUsed(response, expected_template)
