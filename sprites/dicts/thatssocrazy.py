from itertools import combinations

import ujson

with open(
        "white_patches_mostly_sprite_data.json", "r", encoding="utf-8"
) as read_file:
    WHITE_MOSTLY_DATA = ujson.loads(read_file.read())
with open(
        "white_patches_high_sprite_data.json", "r", encoding="utf-8"
) as read_file:
    WHITE_HIGH_DATA = ujson.loads(read_file.read())
with open(
        "white_patches_mid_sprite_data.json", "r", encoding="utf-8"
) as read_file:
    WHITE_MID_DATA = ujson.loads(read_file.read())
with open(
        "white_patches_little_sprite_data.json", "r", encoding="utf-8"
) as read_file:
    WHITE_LITTLE_DATA = ujson.loads(read_file.read())

try:
    with open(
            "white_patches_combos.json", "r", encoding="utf-8"
    ) as read_file:
        WHITE_PATCH_COMBOS = ujson.loads(read_file.read())
except FileNotFoundError:
    # this is probably a mod that ain't adding patch combos
    WHITE_PATCH_COMBOS = {}

list_of_white_patches = []
for sprites in WHITE_HIGH_DATA["sprite_list"]:
    list_of_white_patches.extend([f"high{s}" for s in sprites])
for sprites in WHITE_MID_DATA["sprite_list"]:
    list_of_white_patches.extend([f"mid{s}" for s in sprites])
for sprites in WHITE_LITTLE_DATA["sprite_list"]:
    list_of_white_patches.extend([f"little{s}" for s in sprites])
sprite_combos = combinations(list_of_white_patches, 3)

combo_dict = {}
for i, combo in enumerate(sprite_combos):
    combo_dict[f"COMBO{i}"] = list(combo)

final_dict = {
    "high": {},
    "mid": {},
    "little": {}
}
for name, patches in combo_dict.items():
    size = patches[0].rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    final_dict[size].update({name: patches})

final_dict = ujson.dumps(final_dict, indent=4)
final_dict = final_dict.replace(
                "\/", "/"
            )  # ujson tries to escape "/", but doesn't end up doing a good job.

with open(
        f"thebigjson.json", "x"
) as write_file:
    write_file.write(final_dict)




