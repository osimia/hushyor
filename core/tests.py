from django.test import TestCase

from django.urls import reverse
from rest_framework.test import APITestCase

class GminiApiTest(APITestCase):
    def test_gmini_echo(self):
        url = reverse('gmini-api')
        response = self.client.post(url, {'message': 'hello'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('reply', response.data)
