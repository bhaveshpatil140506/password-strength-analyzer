import json
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from .models import (AnalyzedPassword, ApiSession, Report, User, hash_password,
                     verify_app_password)


class ApiFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            fullname='Test User', username='test_user', email='test@example.test',
            password_hash=hash_password('Test1234'),
        )
        self.other = User.objects.create(
            fullname='Other User', username='other_user', email='other@example.test',
            password_hash=hash_password('Other123'),
        )
        self.admin = User.objects.create(
            fullname='Admin User', username='admin_user', email='admin@example.test',
            password_hash=hash_password('Admin123'), is_admin=True,
        )
        self.user_token = self.login('test_user', 'Test1234')
        self.admin_token = self.login('admin_user', 'Admin123')

    def post(self, path, payload, token=None):
        headers = {'HTTP_AUTHORIZATION': f'Bearer {token}'} if token else {}
        return self.client.post(
            path, data=json.dumps(payload), content_type='application/json', **headers,
        )

    def login(self, username, password):
        response = self.client.post(
            '/api/login', data=json.dumps({'username': username, 'password': password}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        return response.json()['session']['token']

    def test_login_issues_bcrypt_compatible_expiring_session(self):
        session = ApiSession.objects.get(user=self.user)
        self.assertEqual(len(session.token_hash), 64)
        self.assertGreater(session.expires_at, timezone.now())

    def test_login_rejects_passwords_longer_than_eight_characters(self):
        response = self.client.post(
            '/api/login',
            data=json.dumps({'username': 'test_user', 'password': 'TestPassword7!'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_password_hashes_are_compatible_with_php_bcrypt(self):
        encoded = hash_password('CrossBackendPassword1!')
        self.assertTrue(encoded.startswith('$2b$'))
        self.assertTrue(verify_app_password('CrossBackendPassword1!', encoded))
        php_style = '$2y$' + encoded[4:]
        self.assertTrue(verify_app_password('CrossBackendPassword1!', php_style))
        self.assertFalse(verify_app_password('wrong password', encoded))

    def test_analysis_accepts_short_and_long_passwords(self):
        for password in ('x', 'abc123456'):
            with self.subTest(password_length=len(password)):
                response = self.client.post(
                    '/api/analyze', data=json.dumps({'password': password}),
                    content_type='application/json',
                )
                self.assertEqual(response.status_code, 200)

        empty = self.client.post(
            '/api/analyze', data=json.dumps({'password': ''}),
            content_type='application/json',
        )
        self.assertEqual(empty.status_code, 400)

    def test_history_crud_is_authenticated_and_user_scoped(self):
        payload = {
            'action': 'save', 'user_id': self.user.pk,
            'result': {
                'password_placeholder': 'Ab********7', 'score': 6, 'label': 'STRONG',
                'length': 10, 'has_uppercase': True, 'has_lowercase': True,
                'has_numbers': True, 'has_special': True, 'entropy': 52.4,
                'linkLabel': 'Safe for decades', 'crackTime': '3 years',
                'isCommon': False, 'breached': 0,
            },
        }
        saved = self.post('/api/history', payload, self.user_token)
        self.assertEqual(saved.status_code, 200)
        record_id = saved.json()['id']
        self.assertEqual(AnalyzedPassword.objects.get(pk=record_id).strength_score, 6)

        foreign = self.post('/api/history', {'action': 'list', 'user_id': self.other.pk}, self.user_token)
        self.assertEqual(foreign.status_code, 403)
        listed = self.post('/api/history', {'user_id': self.user.pk}, self.user_token)
        self.assertEqual(len(listed.json()['data']), 1)
        detail = self.post('/api/history', {'action': 'detail', 'user_id': self.user.pk, 'id': record_id}, self.user_token)
        self.assertEqual(detail.json()['data']['password_placeholder'], 'Ab********7')
        deleted = self.post('/api/history', {'action': 'delete', 'user_id': self.user.pk, 'id': record_id}, self.user_token)
        self.assertTrue(deleted.json()['success'])
        self.assertFalse(AnalyzedPassword.objects.filter(pk=record_id).exists())

    def test_report_generation_saves_analysis_and_rejects_other_user(self):
        result = {
            'placeholder': 'Ax********9', 'score': 7, 'label': 'EXCELLENT',
            'length': 14, 'has_uppercase': True, 'has_lowercase': True,
            'has_numbers': True, 'has_special': True, 'entropy': 72.8,
            'linkLabel': 'Safe for decades', 'crackTime': 'centuries',
            'isCommon': False, 'breached': 0, 'recommendations': [],
        }
        response = self.post(
            '/api/report', {'user_id': self.user.pk, 'result_data': result}, self.user_token,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AnalyzedPassword.objects.filter(user=self.user).count(), 1)
        self.assertEqual(Report.objects.filter(user=self.user).count(), 1)
        forbidden = self.post('/api/report', {'action': 'full', 'user_id': self.other.pk}, self.user_token)
        self.assertEqual(forbidden.status_code, 403)

    def test_admin_requires_admin_session_and_logout_revokes_token(self):
        denied = self.post('/api/admin', {'action': 'users', 'admin_id': self.admin.pk}, self.user_token)
        self.assertEqual(denied.status_code, 403)
        allowed = self.post('/api/admin', {'action': 'users'}, self.admin_token)
        self.assertEqual(allowed.status_code, 200)

        signed_out = self.post('/api/session', {}, self.user_token)
        self.assertTrue(signed_out.json()['success'])
        after_logout = self.post('/api/history', {'user_id': self.user.pk}, self.user_token)
        self.assertEqual(after_logout.status_code, 401)

    def test_expired_session_is_rejected(self):
        session = ApiSession.objects.get(user=self.user)
        session.expires_at = timezone.now() - timedelta(seconds=1)
        session.save(update_fields=['expires_at'])
        response = self.post('/api/history', {'user_id': self.user.pk}, self.user_token)
        self.assertEqual(response.status_code, 401)

    def test_login_and_registration_reject_malformed_payload_shapes(self):
        for payload in ('[]', 'null', '{broken'):
            login = self.client.post('/api/login', data=payload, content_type='application/json')
            self.assertIn(login.status_code, (400, 422))
            registration = self.client.post('/api/register', data=payload, content_type='application/json')
            self.assertIn(registration.status_code, (400, 422))

        invalid_password = self.client.post(
            '/api/login', data=json.dumps({'username': ['test_user'], 'password': {'value': 'x'}}),
            content_type='application/json',
        )
        self.assertEqual(invalid_password.status_code, 400)

    def test_registration_accepts_short_passwords_and_rejects_over_eight_characters(self):
        payload = {
            'fullname': 'Passphrase User', 'username': 'passphrase_user',
            'email': 'passphrase@example.test', 'password': 'abcd5678',
        }
        response = self.client.post('/api/register', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        created = User.objects.get(username='passphrase_user')
        self.assertTrue(verify_app_password(payload['password'], created.password_hash))

        payload.update(username='long_password', email='long@example.test', password='abcd56789')
        rejected = self.client.post('/api/register', data=json.dumps(payload), content_type='application/json')
        self.assertEqual(rejected.status_code, 422)
