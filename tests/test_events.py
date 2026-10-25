from interactions.models import Interaction, UserProfile

from .helpers import ApiTestCase


class EventTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.make_content(self.client_a, "1", "One")
        self.make_content(self.client_b, "1", "B One")
        self.make_content(self.client_b, "77", "B only")

    def test_server_side_weights(self):
        for event_type, weight in (("view", 1), ("search", 2), ("like", 3), ("save", 4)):
            r = self.event(self.key_a, "u1", "1", event_type)
            self.assertEqual(r.status_code, 201, r.content)
            self.assertEqual(r.json()["weight"], weight)

    def test_weight_sent_by_frontend_is_ignored(self):
        r = self.post("/api/events/", {"user_id": "u1", "content_id": "1", "event_type": "view", "weight": 100},
                      self.key_a)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json()["weight"], 1)
        self.assertEqual(Interaction.objects.get().weight, 1)

    def test_user_profile_created_for_authenticated_client_only(self):
        self.event(self.key_a, "u1", "1", "view")
        self.assertTrue(UserProfile.objects.filter(client=self.client_a, external_user_id="u1").exists())
        self.assertFalse(UserProfile.objects.filter(client=self.client_b).exists())

    def test_same_user_id_is_isolated_between_clients(self):
        self.event(self.key_a, "u1", "1", "view")
        self.event(self.key_b, "u1", "1", "like")
        self.assertEqual(UserProfile.objects.filter(external_user_id="u1").count(), 2)

    def test_content_from_other_client_rejected(self):
        r = self.event(self.key_a, "u1", "77", "view")  # "77" belongs to client B
        self.assertEqual(r.status_code, 400)
        self.assertIn("content_id", r.json())
        self.assertEqual(Interaction.objects.count(), 0)

    def test_unknown_content_rejected(self):
        self.assertEqual(self.event(self.key_a, "u1", "does-not-exist", "view").status_code, 400)

    def test_invalid_event_type_and_user_id(self):
        self.assertEqual(self.event(self.key_a, "u1", "1", "purchase").status_code, 400)
        self.assertEqual(self.event(self.key_a, "bad user!", "1", "view").status_code, 400)
        self.assertEqual(self.post("/api/events/", {"content_id": "1", "event_type": "view"}, self.key_a).status_code, 400)

    def test_inactive_content_rejected(self):
        self.make_content(self.client_a, "off", "Off").__class__.objects.filter(content_id="off").update(is_active=False)
        self.assertEqual(self.event(self.key_a, "u1", "off", "view").status_code, 400)

    def test_model_level_client_validation(self):
        from django.core.exceptions import ValidationError
        user_a = UserProfile.objects.create(client=self.client_a, external_user_id="x")
        content_b = self.client_b.contents.get(content_id="77")
        with self.assertRaises(ValidationError):
            Interaction.objects.create(client=self.client_a, user=user_a, content=content_b, event_type="view")

    def test_events_require_auth(self):
        self.assertEqual(self.event(None, "u1", "1", "view").status_code, 401)
