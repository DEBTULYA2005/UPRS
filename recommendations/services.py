"""Glue between the API and the Lesson 6 engine. Views stay thin; this module
loads PostgreSQL data into DataFrames, calls the engine, and shapes results."""

import logging

from content.models import Content
from recommendation_engine import recomender, similar_content
from recommendation_engine.data_loader import load_dataframes

from .fallback import popular_content

logger = logging.getLogger(__name__)

STRATEGY_PERSONALIZED = "personalized"
STRATEGY_FALLBACK = "popular_fallback"
STRATEGY_SIMILAR = "content_similarity"
STRATEGY_EMPTY = "empty"


def _enrich(client, tuples):
    """Attach category / image_url (not returned by the algorithm) from the DB."""
    ids = [t[0] for t in tuples]
    meta = {
        c.content_id: c
        for c in Content.objects.filter(client=client, content_id__in=ids)
    }
    return [
        {
            "content_id": str(cid),
            "title": str(title),
            "category": meta[cid].category,
            "image_url": meta[cid].image_url,
            "score": round(float(score), 6),
        }
        for cid, title, score in tuples
    ]


def personalized_recommendations(client, user_id, top_k):
    content_df, interaction_df = load_dataframes(client)

    if content_df.empty:
        return STRATEGY_EMPTY, []

    has_history = not interaction_df[interaction_df["user_id"] == user_id].empty
    if not has_history:
        # New / unknown user: the Lesson 6 function would return [] here.
        return STRATEGY_FALLBACK, popular_content(client, top_k)

    try:
        raw = recomender(user_id, top_n=top_k, content_df=content_df, interaction_df=interaction_df)
    except ValueError:
        # e.g. TF-IDF "empty vocabulary" when every title/description is only
        # single characters. Degrade gracefully instead of returning a 500.
        logger.exception("Recommendation engine failed for client %s", client.pk)
        return STRATEGY_FALLBACK, popular_content(client, top_k)

    # Engine quirk: when top_k > number of unseen items, seen items come back
    # with the sentinel score -1. Real scores are always >= 0, so drop them.
    raw = [t for t in raw if t[2] >= 0]
    return STRATEGY_PERSONALIZED, _enrich(client, raw)


def similar_recommendations(client, content_id, top_k):
    """Returns (strategy, results) or None if the content doesn't exist for this client."""
    content_df, interaction_df = load_dataframes(client)
    if content_df.empty or content_id not in set(content_df["content_id"]):
        return None
    try:
        raw = similar_content(content_id, top_k, content_df=content_df, interaction_df=interaction_df)
    except ValueError:
        logger.exception("Similarity computation failed for client %s", client.pk)
        return STRATEGY_EMPTY, []
    return STRATEGY_SIMILAR, _enrich(client, raw)
