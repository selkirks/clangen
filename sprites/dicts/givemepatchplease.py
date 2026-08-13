from itertools import combinations
from random import choice

import ujson

try:
    with open(
            "thebigjson.json", "r", encoding="utf-8"
    ) as read_file:
        THEBIGJASON = ujson.loads(read_file.read())
except FileNotFoundError:
    # this is probably a mod that ain't adding patch combos
    THEBIGJASON = {}

random_patch = []
for v in THEBIGJASON.values():
  random_patch.extend(v.values())

print(choice(random_patch))




