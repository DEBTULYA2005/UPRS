"""Popular-content fallback for users with no interaction history.

THIS IS NOT PART OF THE LESSON 6 ALGORITHM. It is a deliberately separate,
simple rule used only when the Lesson 6 function has nothing to personalise
from. Responses produced here are labelled strategy="popular_fallback".

Score = interaction_count / max_interaction_count (same definition of
"popularity" as Lesson 6), or 0.0 if nothing has been interacted with yet.
"""

from django.db.models import Count

from content.models import Content


def popular_content(client, top_k):
    rows = list(
        Content.objects.filter(client=client, is_active=True)
        .annotate(n=Count("interactions"))
        .order_by("-n", "-created_at", "content_id")[:top_k]
    )
    max_n = max((c.n for c in rows), default=0)
    return [
        {
            "content_id": c.content_id,
            "title": c.title,
            "category": c.category,
            "image_url": c.image_url,
            "score": round(c.n / max_n, 6) if max_n else 0.0,
        }
        for c in rows
    ]
