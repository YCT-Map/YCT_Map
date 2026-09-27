import re
import json

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from routing.models import PathSurvey
from yctmap.settings import ALLOWED_HOSTS, SECURE_PROXY_SSL_HEADER, _development_tunnel_config


class DevelopmentTunnelSettingsTests(SimpleTestCase):
    def test_development_allows_loopback_and_cloudflare_quick_tunnel(self):
        self.assertIn("127.0.0.1", ALLOWED_HOSTS)
        self.assertIn("localhost", ALLOWED_HOSTS)
        hosts, origins = _development_tunnel_config("development", ".trycloudflare.com")
        self.assertEqual(hosts, (".trycloudflare.com",))
        self.assertEqual(origins, ("https://*.trycloudflare.com",))

    def test_production_never_inherits_development_tunnel_wildcards(self):
        self.assertEqual(_development_tunnel_config("production", ".trycloudflare.com"), ((), ()))

    def test_development_recognises_forwarded_https(self):
        self.assertEqual(SECURE_PROXY_SSL_HEADER, ("HTTP_X_FORWARDED_PROTO", "https"))


class HealthCheckTests(SimpleTestCase):
    def test_health_check_is_lightweight_and_available(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


class HttpsCsrfFlowTests(TestCase):
    host = "field-test.trycloudflare.com"
    origin = "https://field-test.trycloudflare.com"

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            "field-owner", "field@example.test", "Strong-test-password-42"
        )

    @staticmethod
    def token(response):
        return re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', response.content.decode()).group(1)

    def request_args(self):
        return {"HTTP_HOST": self.host, "HTTP_ORIGIN": self.origin,
                "HTTP_X_FORWARDED_PROTO": "https", "secure": True}

    def test_fresh_https_login_rotates_token_and_editor_ajax_uses_current_token(self):
        client = Client(enforce_csrf_checks=True)
        login = client.get(reverse("editor:login"), **self.request_args())
        original_cookie = client.cookies["csrftoken"].value
        response = client.post(reverse("editor:login"), {
            "username": "field-owner", "password": "Strong-test-password-42",
            "csrfmiddlewaretoken": self.token(login),
        }, **self.request_args())
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(client.cookies["csrftoken"].value, original_cookie)

        survey = PathSurvey.objects.create(owner=self.user, status=PathSurvey.Status.ACTIVE)
        detail = client.get(reverse("editor:survey-detail", args=(survey.id,)), **self.request_args())
        current_token = self.token(detail)
        timing = client.post(reverse("editor:survey-timing", args=(survey.id,)),
            data=json.dumps({"active_capture_seconds": 4}), content_type="application/json",
            HTTP_X_CSRFTOKEN=current_token, **self.request_args())
        self.assertEqual(timing.status_code, 200)
        self.assertEqual(timing.json()["active_capture_seconds"], 4)
        self.assertEqual(detail.headers["Cache-Control"], "no-store, private")

    def test_stale_pre_login_token_remains_rejected_with_recovery_page(self):
        client = Client(enforce_csrf_checks=True)
        login = client.get(reverse("editor:login"), **self.request_args())
        stale_token = self.token(login)
        client.post(reverse("editor:login"), {
            "username": "field-owner", "password": "Strong-test-password-42",
            "csrfmiddlewaretoken": stale_token,
        }, **self.request_args())
        rejected = client.post(reverse("editor:logout"), {"csrfmiddlewaretoken": stale_token},
                               **self.request_args())
        self.assertEqual(rejected.status_code, 403)
        self.assertContains(rejected, "This form has expired", status_code=403)
