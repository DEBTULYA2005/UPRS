from clients.models import Client

from .helpers import ApiTestCase


class HealthTests(ApiTestCase):
    def test_health_is_public_and_ok(self):
        r = self.get("/api/health/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok", "database": "ok"})

    def test_api_docs_available(self):
        self.assertEqual(self.get("/api/schema/").status_code, 200)
        self.assertEqual(self.get("/api/docs/").status_code, 200)


class AuthTests(ApiTestCase):
    def test_missing_key_is_401(self):
        self.assertEqual(self.get("/api/content/").status_code, 401)

    def test_invalid_key_is_401(self):
        self.assertEqual(self.get("/api/content/", key="urs_deadbeef.notarealsecret").status_code, 401)
        self.assertEqual(self.get("/api/content/", key="garbage").status_code, 401)

    def test_right_prefix_wrong_secret_is_401(self):
        prefix = self.key_a.split(".")[0]
        self.assertEqual(self.get("/api/content/", key=f"{prefix}.wrong").status_code, 401)

    def test_valid_key_is_200(self):
        self.assertEqual(self.get("/api/content/", key=self.key_a).status_code, 200)

    def test_inactive_client_is_rejected(self):
        Client.objects.filter(pk=self.client_a.pk).update(is_active=False)
        self.assertEqual(self.get("/api/content/", key=self.key_a).status_code, 401)

    def test_raw_key_is_not_stored(self):
        c = Client.objects.get(pk=self.client_a.pk)
        self.assertNotIn(self.key_a, (c.key_hash, c.key_prefix))
        self.assertEqual(len(c.key_hash), 64)

    def test_client_id_in_body_is_not_authentication(self):
        r = self.post("/api/events/", {"client": self.client_a.pk, "user_id": "u", "content_id": "1",
                                       "event_type": "view"})
        self.assertEqual(r.status_code, 401)

    def test_rotating_key_invalidates_old_key(self):
        client = Client.objects.get(pk=self.client_a.pk)
        new_key = client.set_new_api_key()
        client.save()
        self.assertEqual(self.get("/api/content/", key=self.key_a).status_code, 401)
        self.assertEqual(self.get("/api/content/", key=new_key).status_code, 200)

    def test_error_responses_do_not_echo_the_key(self):
        r = self.get("/api/content/", key="urs_deadbeef.supersecretvalue")
        self.assertNotIn("supersecretvalue", r.content.decode())
