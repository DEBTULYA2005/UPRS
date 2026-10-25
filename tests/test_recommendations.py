import contextlib
import io

import numpy as np

from recommendation_engine import recomender
from recommendation_engine.data_loader import load_dataframes

from .helpers import ApiTestCase


class EngineFidelityTests(ApiTestCase):
    """The integrated engine must give the same answer as your ORIGINAL file."""

    def test_matches_original_lesson6_file_on_demo_data(self):
        with contextlib.redirect_stdout(io.StringIO()):  # the original prints at import
            from recommendation_engine.reference import lesson6_original as original

        demo_content = original.content_df[["content_id", "title", "category", "description"]].copy()
        demo_interactions = original.interaction_df.copy()

        for user_id in (101, 102, 103):
            with contextlib.redirect_stdout(io.StringIO()):
                expected = original.recomender(user_id=user_id, top_n=3)
            actual = recomender(user_id, top_n=3, content_df=demo_content, interaction_df=demo_interactions)
            self.assertEqual([e[0] for e in expected], [a[0] for a in actual])
            self.assertEqual([e[1] for e in expected], [a[1] for a in actual])
            np.testing.assert_allclose([e[2] for e in expected], [a[2] for a in actual])

    def test_database_loader_reproduces_original_user_101_result(self):
        """Load the demo data through PostgreSQL/ORM and compare with the original result."""
        self.seed_catalogue(self.client_a, self.key_a)
        demo = [("101", "1", "view"), ("101", "2", "like"), ("101", "4", "save"),
                ("102", "5", "view"), ("102", "6", "like"), ("103", "3", "view"), ("103", "4", "save")]
        for user, content, event in demo:
            self.assertEqual(self.event(self.key_a, user, content, event).status_code, 201)

        with contextlib.redirect_stdout(io.StringIO()):
            from recommendation_engine.reference import lesson6_original as original
            expected = original.recomender(user_id=101, top_n=3)

        content_df, interaction_df = load_dataframes(self.client_a)
        self.assertEqual(list(content_df.columns), ["content_id", "title", "category", "description"])
        self.assertEqual(list(interaction_df.columns), ["user_id", "content_id", "action", "weight"])
        actual = recomender("101", top_n=3, content_df=content_df, interaction_df=interaction_df)
        self.assertEqual([str(e[0]) for e in expected], [a[0] for a in actual])
        np.testing.assert_allclose([e[2] for e in expected], [a[2] for a in actual])


class RecommendationApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.seed_catalogue(self.client_a, self.key_a)
        for user, content, event in [("101", "1", "view"), ("101", "2", "like"), ("101", "4", "save"),
                                     ("102", "5", "view"), ("102", "6", "like"),
                                     ("103", "3", "view"), ("103", "4", "save")]:
            self.event(self.key_a, user, content, event)

    def test_response_format(self):
        r = self.get("/api/recommendations/?user_id=101&top_k=3", self.key_a)
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertEqual(body["strategy"], "personalized")
        self.assertEqual(body["user_id"], "101")
        self.assertEqual(body["count"], len(body["results"]))
        self.assertEqual(set(body["results"][0]), {"content_id", "title", "category", "image_url", "score"})
        self.assertIsInstance(body["results"][0]["score"], float)

    def test_matches_original_ranking_for_user_101(self):
        body = self.get("/api/recommendations/?user_id=101&top_k=3", self.key_a).json()
        self.assertEqual([x["content_id"] for x in body["results"]], ["3", "6", "5"])  # 5 and 6 tie; order matches the original file

    def test_previously_interacted_content_never_returned(self):
        body = self.get("/api/recommendations/?user_id=101&top_k=50", self.key_a).json()
        returned = {x["content_id"] for x in body["results"]}
        self.assertTrue(returned.isdisjoint({"1", "2", "4"}))
        self.assertEqual(returned, {"3", "5", "6"})  # no -1 sentinel rows leak through
        self.assertTrue(all(x["score"] >= 0 for x in body["results"]))

    def test_user_who_has_seen_everything_gets_empty_list(self):
        for cid in ("3", "5", "6"):
            self.event(self.key_a, "101", cid, "view")
        body = self.get("/api/recommendations/?user_id=101", self.key_a).json()
        self.assertEqual((body["strategy"], body["results"]), ("personalized", []))

    def test_new_user_gets_clearly_labelled_fallback(self):
        body = self.get("/api/recommendations/?user_id=brand-new&top_k=2", self.key_a).json()
        self.assertEqual(body["strategy"], "popular_fallback")
        self.assertEqual(body["results"][0]["content_id"], "4")  # most interacted-with item
        self.assertEqual(body["results"][0]["score"], 1.0)
        self.assertEqual(body["count"], 2)

    def test_empty_dataset(self):
        r = self.get("/api/recommendations/?user_id=1", self.key_b)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"user_id": "1", "strategy": "empty", "count": 0, "results": []})

    def test_catalogue_without_any_interactions(self):
        self.make_content(self.client_b, "1", "One", "Cat", "alpha beta")
        self.make_content(self.client_b, "2", "Two", "Cat", "alpha gamma")
        body = self.get("/api/recommendations/?user_id=1", self.key_b).json()
        self.assertEqual(body["strategy"], "popular_fallback")
        self.assertEqual(body["count"], 2)
        self.assertTrue(all(x["score"] == 0.0 for x in body["results"]))

    def test_top_k_validation(self):
        for q in ("top_k=0", "top_k=abc", "top_k=1000"):
            self.assertEqual(self.get(f"/api/recommendations/?user_id=1&{q}", self.key_a).status_code, 400, q)
        self.assertEqual(self.get("/api/recommendations/", self.key_a).status_code, 400)  # user_id missing

    def test_requires_authentication(self):
        self.assertEqual(self.get("/api/recommendations/?user_id=101").status_code, 401)
        self.assertEqual(self.get("/api/recommendations/similar/?content_id=1").status_code, 401)

    # ---- cross-client isolation ----
    def test_other_client_cannot_see_my_users_or_content(self):
        self.make_content(self.client_b, "900", "B Only Item", "Misc", "unrelated words")
        body = self.get("/api/recommendations/?user_id=101", self.key_b).json()
        # user 101 does not exist for client B -> fallback over B's own content only
        self.assertEqual(body["strategy"], "popular_fallback")
        self.assertEqual([x["content_id"] for x in body["results"]], ["900"])

    def test_same_user_id_has_independent_history_per_client(self):
        self.make_content(self.client_b, "x1", "Alpha", "Cat", "alpha")
        self.make_content(self.client_b, "x2", "Beta", "Cat", "beta")
        self.event(self.key_b, "101", "x1", "like")
        body_b = self.get("/api/recommendations/?user_id=101", self.key_b).json()
        self.assertEqual([x["content_id"] for x in body_b["results"]], ["x2"])
        body_a = self.get("/api/recommendations/?user_id=101&top_k=50", self.key_a).json()
        self.assertEqual({x["content_id"] for x in body_a["results"]}, {"3", "5", "6"})

    # ---- similar ----
    def test_similar_content(self):
        r = self.get("/api/recommendations/similar/?content_id=5&top_k=2", self.key_a)
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["strategy"], "content_similarity")
        self.assertEqual(body["results"][0]["content_id"], "6")  # football -> cricket (same category)
        self.assertNotIn("5", [x["content_id"] for x in body["results"]])

    def test_similar_for_other_clients_content_is_404(self):
        self.assertEqual(self.get("/api/recommendations/similar/?content_id=1", self.key_b).status_code, 404)

    def test_similar_with_single_item_catalogue(self):
        self.make_content(self.client_b, "only", "Lonely item")
        body = self.get("/api/recommendations/similar/?content_id=only", self.key_b).json()
        self.assertEqual(body["results"], [])
