from rest_framework.test import APITestCase

from clients.models import Client
from content.models import Content


class ApiTestCase(APITestCase):
    """Creates two independent clients, A and B, each with its own API key."""

    def setUp(self):
        self.client_a, self.key_a = Client.create_with_key("Client A")
        self.client_b, self.key_b = Client.create_with_key("Client B")

    def call(self, method, url, key=None, **kwargs):
        headers = {"HTTP_X_API_KEY": key} if key else {}
        return getattr(self.client, method)(url, format="json", **headers, **kwargs)

    def get(self, url, key=None):
        return self.call("get", url, key)

    def post(self, url, data, key=None):
        return self.call("post", url, key, data=data)

    def make_content(self, client, content_id, title, category="General", description=""):
        return Content.objects.create(
            client=client, content_id=content_id, title=title,
            category=category, description=description,
        )

    def seed_catalogue(self, client, key):
        """Same six items as the Lesson 6 demo data."""
        items = [
            ("1", "Python Programming", "Programming", "Learn Python programming and coding"),
            ("2", "Django Web Development", "Programming", "Build web applications using Django and Python"),
            ("3", "Java Programming", "Programming", "Learn Java programming and object oriented programming"),
            ("4", "React Development", "Programming", "Build modern web applications using React JavaScript"),
            ("5", "Football Highlights", "Sports", "Latest football match highlights and goals"),
            ("6", "Cricket Analysis", "Sports", "Cricket match analysis and player performance"),
        ]
        for cid, title, cat, desc in items:
            self.make_content(client, cid, title, cat, desc)

    def event(self, key, user_id, content_id, event_type):
        return self.post("/api/events/", {"user_id": user_id, "content_id": content_id, "event_type": event_type}, key)
