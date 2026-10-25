import pandas as pd
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 1. CONTENT DATA

content_df = pd.DataFrame({
    "content_id": [1, 2, 3, 4, 5, 6],

    "title": [
        "Python Programming",
        "Django Web Development",
        "Java Programming",
        "React Development",
        "Football Highlights",
        "Cricket Analysis"
    ],

    "category": [
        "Programming",
        "Programming",
        "Programming",
        "Programming",
        "Sports",
        "Sports"
    ],

    "description": [
        "Learn Python programming and coding",
        "Build web applications using Django and Python",
        "Learn Java programming and object oriented programming",
        "Build modern web applications using React JavaScript",
        "Latest football match highlights and goals",
        "Cricket match analysis and player performance"
    ]
})

# 2. USER INTERACTIONS

interaction_df = pd.DataFrame({
    "user_id": [101, 101, 101, 102, 102, 103, 103],

    "content_id": [1, 2, 4, 5, 6, 3, 4],

    "action": [
        "view",
        "like",
        "save",
        "view",
        "like",
        "view",
        "save"
    ],

    "weight": [
        1,
        3,
        4,
        1,
        3,
        1,
        4
    ]
})

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

def recomender(user_id, top_n = 5):

    # 10. SELECT USER
    # user_id = int(input("Enter user ID to get recommendations: "))

    user_interactions = interaction_df[
        interaction_df["user_id"] == user_id
    ]
    
    if user_interactions.empty:
        print(f"No interactions found for user {user_id}.")
        return []
    
    # print(f"User {user_id} Interactions:")
    # print(user_interactions)

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

    # 17. DISPLAY RECOMMENDATIONS
    # top_k = 3
    recomendations = []
    print("\nRecommended Content:")
    for index in recommendation_indexes[:top_n]:
        content = content_df.iloc[index]
        recomendations.append((content['content_id'], content['title'], final_scores[index]))
    
    return recomendations


r = recomender(user_id=101, top_n=3)
print(r)