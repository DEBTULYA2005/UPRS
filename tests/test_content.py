from content.models import Content

from .helpers import ApiTestCase


class ContentTests(ApiTestCase):
    def test_create_and_retrieve(self):
        r = self.post("/api/content/", {"content_id": "12", "title": "Blue Shirt", "category": "Clothing",
                                        "description": "Cotton", "image_url": "https://img.example/1.jpg"}, self.key_a)
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(Content.objects.get(content_id="12").client, self.client_a)
        r = self.get("/api/content/12/", self.key_a)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["title"], "Blue Shirt")

    def test_list_is_paginated(self):
        self.make_content(self.client_a, "1", "One")
        r = self.get("/api/content/", self.key_a)
        self.assertEqual(r.json()["count"], 1)
        self.assertEqual(r.json()["results"][0]["content_id"], "1")

    def test_duplicate_content_id_same_client_rejected(self):
        self.make_content(self.client_a, "1", "One")
        r = self.post("/api/content/", {"content_id": "1", "title": "Again"}, self.key_a)
        self.assertEqual(r.status_code, 400)
        self.assertIn("content_id", r.json())

    def test_same_content_id_allowed_for_different_clients(self):
        self.make_content(self.client_a, "1", "One")
        r = self.post("/api/content/", {"content_id": "1", "title": "B's item"}, self.key_b)
        self.assertEqual(r.status_code, 201)

    def test_validation_errors(self):
        for payload in (
            {"title": "no id"},
            {"content_id": "1"},
            {"content_id": "bad id/with slash", "title": "x"},
            {"content_id": "1", "title": "   "},
            {"content_id": "1", "title": "x", "image_url": "not-a-url"},
        ):
            r = self.post("/api/content/", payload, self.key_a)
            self.assertEqual(r.status_code, 400, payload)

    def test_client_in_body_is_ignored(self):
        r = self.post("/api/content/", {"content_id": "9", "title": "x", "client": self.client_b.pk}, self.key_a)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Content.objects.get(content_id="9").client, self.client_a)

    def test_cannot_read_other_clients_content(self):
        self.make_content(self.client_a, "1", "A's secret item")
        self.assertEqual(self.get("/api/content/1/", self.key_b).status_code, 404)
        self.assertEqual(self.get("/api/content/", self.key_b).json()["count"], 0)

    def test_unknown_content_is_404(self):
        self.assertEqual(self.get("/api/content/nope/", self.key_a).status_code, 404)
