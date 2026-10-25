"""Loads one client's PostgreSQL data into the exact DataFrame structures
the Lesson 6 algorithm expects.

content_df     : content_id, title, category, description
interaction_df : user_id, content_id, action, weight

Only ACTIVE content is loaded, and interactions are restricted to that
content (the algorithm looks every interacted content_id up in content_df).
Everything is filtered by the given client, so no cross-client data can leak.
"""

import pandas as pd

CONTENT_COLUMNS = ["content_id", "title", "category", "description"]
INTERACTION_COLUMNS = ["user_id", "content_id", "action", "weight"]


def load_dataframes(client):
    from content.models import Content
    from interactions.models import Interaction

    content_rows = list(
        Content.objects.filter(client=client, is_active=True)
        .order_by("id")
        .values_list("content_id", "title", "category", "description")
    )
    interaction_rows = list(
        Interaction.objects.filter(client=client, content__is_active=True)
        .order_by("id")
        .values_list("user__external_user_id", "content__content_id", "event_type", "weight")
    )

    content_df = pd.DataFrame(content_rows, columns=CONTENT_COLUMNS, dtype=object)
    interaction_df = pd.DataFrame(interaction_rows, columns=INTERACTION_COLUMNS)
    # keep id columns as plain Python strings so merges/lookups behave identically
    interaction_df["user_id"] = interaction_df["user_id"].astype(object)
    interaction_df["content_id"] = interaction_df["content_id"].astype(object)
    interaction_df["action"] = interaction_df["action"].astype(object)
    interaction_df["weight"] = interaction_df["weight"].astype("int64")
    return content_df, interaction_df
