"""Interaction weights from the Lesson 6 algorithm.

This is the single source of truth. The API never accepts a weight from a
client; it looks the weight up here from the event type.
"""

INTERACTION_WEIGHTS = {
    "view": 1,
    "search": 2,
    "like": 3,
    "save": 4,
}

EVENT_TYPE_CHOICES = [(name, name) for name in INTERACTION_WEIGHTS]
