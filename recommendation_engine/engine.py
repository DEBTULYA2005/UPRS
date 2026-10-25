"""
Lesson 6 recommendation algorithm - integrated from your recommendation_engine.py

WHAT WAS CHANGED vs. your original file (and nothing else):

  * Your file built `content_df` / `interaction_df` from hard-coded demo data
    at import time and used them as module-level globals. Here the SAME two
    DataFrames (same columns) are passed in, loaded from PostgreSQL by
    `recommendation_engine/data_loader.py`.
  * Steps 3-9 (popularity, normalisation, text, TF-IDF, cosine similarity,
    id->index map) live in `build_model()` so they run on the passed-in data.
  * Steps 10-17 live in `recomender()`, same name and same first two
    arguments `(user_id, top_n=5)` as your original.
  * `print()` calls were removed (a web server should not print), and the
    demo `r = recomender(...)` line at the bottom was removed.

UNCHANGED: popularity = interaction count / max count; TF-IDF over
"title category description"; cosine similarity; weighted sum of similarity
rows; division by total weight; final = 0.8 * personalisation + 0.2 *
popularity; seen content set to -1; argsort descending; top_n.
Interaction weights (view=1, search=2, like=3, save=4) are in weights.py.

`similar_content()` at the bottom is an ADDITION (it is not part of your
Lesson 6 function). It reuses the same TF-IDF + cosine matrix to power
GET /api/recommendations/similar/. It does not touch `recomender()`.

Your untouched original is kept in reference/lesson6_original.py.
"""

import numpy as np
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_model(content_df, interaction_df):
    """Steps 3-9 of the original file. Returns (content_df, similarity_matrix, id_to_index)."""
    content_df = content_df.copy()

    # 3. CALCULATE POPULARITY
    content_popularity = (
        interaction_df
        .groupby("content_id").size().reset_index(name="interaction_count")
    )

    # 4. NORMALIZE POPULARITY
    content_popularity["popularity_score"] = (
        content_popularity["interaction_count"] / content_popularity["interaction_count"].max()
    )

    # 5. ADD POPULARITY TO CONTENT
    content_df = content_df.merge(
        content_popularity[
            ["content_id", "popularity_score"]
        ],
        on="content_id",
        how="left"
    )
    # Fill any missing popularity scores with 0
    content_df["popularity_score"] = (content_df["popularity_score"].fillna(0))

    # 6. COMBINE TEXT FOR VECTORIZING
    content_df["text"] = (content_df["title"] + " " + content_df["category"] + " " + content_df["description"])

    # 7. TF-IDF
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(content_df["text"])

    # 8. COSINE SIMILARITY
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # 9. MAP CONTENT ID TO INDEX
    id_to_index = {
        content_id: index
        for index, content_id
        in enumerate(content_df["content_id"])
    }

    return content_df, similarity_matrix, id_to_index


def recomender(user_id, top_n=5, *, content_df, interaction_df):
    """Steps 10-17 of the original file.

    Returns a list of (content_id, title, score) tuples, exactly like the
    original. NOTE (original behaviour, kept): if top_n is larger than the
    number of unseen items, already-seen items come back with score -1.
    The API layer filters those out; this function is left as-is.
    """
    content_df, similarity_matrix, id_to_index = build_model(content_df, interaction_df)

    # 10. SELECT USER
    user_interactions = interaction_df[
        interaction_df["user_id"] == user_id
    ]

    if user_interactions.empty:
        return []

    # 11. SET USER SCORES
    user_scores = np.zeros(len(content_df))

    # 12. USE USER INTERACTIONS
    for _, row in user_interactions.iterrows():

        content_id = row["content_id"]
        weight = row["weight"]
        index = id_to_index[content_id]

        user_scores = user_scores + similarity_matrix[index] * weight

    # 13. NORMALIZE USER SCORES
    total_weight = user_interactions["weight"].sum()
    user_scores = user_scores / total_weight

    # 14. COMBINE PERSONALIZATION AND POPULARITY (80% personalization, 20% popularity)
    final_scores = (
        user_scores * 0.8
        + content_df["popularity_score"].to_numpy() * 0.2
    )

    # 15. REMOVE ALREADY-SEEN CONTENT
    for content_id in user_interactions["content_id"]:
        index = id_to_index[content_id]
        final_scores[index] = -1

    # 16. SORT RECOMMENDATIONS
    recommendation_indexes = np.argsort(final_scores)[::-1]

    # 17. COLLECT RECOMMENDATIONS
    recomendations = []
    for index in recommendation_indexes[:top_n]:
        content = content_df.iloc[index]
        recomendations.append((content['content_id'], content['title'], final_scores[index]))

    return recomendations


# ---------------------------------------------------------------------------
# ADDITION (not part of the Lesson 6 function): content-to-content similarity
# ---------------------------------------------------------------------------
def similar_content(content_id, top_n, *, content_df, interaction_df):
    """Items most similar to `content_id` using the same TF-IDF + cosine matrix.

    Returns a list of (content_id, title, cosine_similarity) tuples, most
    similar first, excluding the item itself. Raises KeyError if content_id
    is not in content_df.
    """
    content_df, similarity_matrix, id_to_index = build_model(content_df, interaction_df)
    source_index = id_to_index[content_id]
    scores = similarity_matrix[source_index].copy()
    scores[source_index] = -1  # never recommend the item to itself

    results = []
    for index in np.argsort(scores)[::-1][:top_n]:
        if scores[index] < 0:
            continue
        content = content_df.iloc[index]
        results.append((content["content_id"], content["title"], scores[index]))
    return results
