from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Company, UserProfile, ClientData
from unittest.mock import patch, MagicMock
import json

class CompanyModelTests(TestCase):
    def test_create_company(self):
        company = Company.objects.create(name="TestCo")
        self.assertEqual(str(company), "TestCo")

    def test_create_multiple_companies(self):
        Company.objects.create(name="AlphaCo")
        Company.objects.create(name="BetaCo")
        self.assertEqual(Company.objects.count(), 2)


class UserProfileModelTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="TestCorp")
        self.user = User.objects.create_user(username="tester", password="pass123")
        self.profile = UserProfile.objects.create(user=self.user, company=self.company)

    def test_user_profile_creation(self):
        self.assertEqual(self.profile.company.name, "TestCorp")
        self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

    def test_user_profile_defaults(self):
        self.assertEqual(self.profile.email_host, "smtp.gmail.com")
        self.assertEqual(self.profile.email_port, 587)
        self.assertTrue(self.profile.use_tls)


class ClientDataModelTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name="DemoCo")

    def test_client_data_creation(self):
        client = ClientData.objects.create(
            name="Alice",
            phone_number="1234567890",
            email="alice@example.com",
            revenue=10000,
            interest_level=5,
            tenant=self.company
        )
        self.assertEqual(str(client), "Alice (alice@example.com)")

    def test_client_data_without_tenant(self):
        client = ClientData.objects.create(
            name="Bob",
            phone_number="9999999999",
            email="bob@example.com",
            revenue=5000,
            interest_level=3,
            tenant=None
        )
        self.assertIsNone(client.tenant)

    def test_interest_level_range(self):
        client = ClientData.objects.create(
            name="Charlie",
            phone_number="8888888888",
            email="charlie@example.com",
            revenue=7500,
            interest_level=9,
            tenant=self.company
        )
        self.assertGreaterEqual(client.interest_level, 0)
        self.assertLessEqual(client.interest_level, 10)


class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_store_email_credentials_post(self):
        url = reverse("store_email_credentials")
        data = {
            "email": "test@example.com",
            "app_password": "apppass123"
        }
        response = self.client.post(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    def test_store_email_credentials_missing_field(self):
        url = reverse("store_email_credentials")
        data = {"email": "test@example.com"}  # missing app_password
        response = self.client.post(url, data=json.dumps(data), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    @patch("imaplib.IMAP4_SSL")
    def test_get_messages_with_mocked_email(self, mock_imap):
        mock_mail = MagicMock()
        mock_imap.return_value = mock_mail
        mock_mail.login.return_value = ("OK", [b'Logged in'])
        mock_mail.select.return_value = ("OK", [b'INBOX'])
        mock_mail.search.return_value = ("OK", [b'1'])
        mock_mail.fetch.return_value = ("OK", [(b'1 (RFC822)', b"From: test@example.com\nSubject: Hello\nDate: Today")])

        session = self.client.session
        session['email'] = 'dummy@example.com'
        session['app_password'] = 'fakepass'
        session.save()

        response = self.client.get(reverse("get_messages"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(msg["channel"] == "Email" for msg in data))

    def test_get_messages_with_no_session(self):
        response = self.client.get(reverse("get_messages"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(len(data) >= 3)
        self.assertTrue(all("channel" in msg for msg in data))
