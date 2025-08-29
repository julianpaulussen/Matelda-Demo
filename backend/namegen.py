import random
from typing import Set


ADJECTIVES = [
    "brisk",
    "swift",
    "bright",
    "calm",
    "clever",
    "daring",
    "eager",
    "fuzzy",
    "gentle",
    "happy",
    "icy",
    "jolly",
    "kind",
    "lively",
    "mighty",
    "nimble",
    "odd",
    "proud",
    "quick",
    "rapid",
    "sunny",
    "tidy",
    "upbeat",
    "vivid",
    "witty",
    "young",
    "zesty",
]

ANIMALS = [
    "otter",
    "panda",
    "tiger",
    "lion",
    "eagle",
    "falcon",
    "dolphin",
    "whale",
    "fox",
    "wolf",
    "bear",
    "moose",
    "yak",
    "goat",
    "koala",
    "lemur",
    "mole",
    "mouse",
    "owl",
    "quail",
    "rabbit",
    "seal",
    "snake",
    "swallow",
    "zebra",
]


def generate_unique_name(used_in_session: Set[str]) -> str:
    """Generate an adjective-animal-number name unique within a session."""
    while True:
        name = f"{random.choice(ADJECTIVES)}-{random.choice(ANIMALS)}-{random.randint(100, 9999)}"
        if name not in used_in_session:
            return name

