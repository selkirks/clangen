# pylint: disable=line-too-long
"""

TODO: Docs


"""  # pylint: enable=line-too-long

import logging
import re
from itertools import combinations
from random import choice, choices, randint, random, sample, randrange, gauss
from sys import exit as sys_exit
from typing import List

import pygame
import ujson

logger = logging.getLogger(__name__)
from scripts.game_structure import image_cache
from scripts.cat.history import History
from scripts.cat.names import names
from scripts.cat.pelts import Pelt
from scripts.cat.sprites import sprites
from scripts.game_structure.game_essentials import game, screen_x, screen_y


# ---------------------------------------------------------------------------- #
#                               Getting Cats                                   #
# ---------------------------------------------------------------------------- #


def get_alive_clan_queens(living_cats):
    living_kits = [
        cat
        for cat in living_cats
        if not (cat.dead or cat.outside) and cat.status in ["kitten", "newborn"]
    ]

    queen_dict = {}
    for cat in living_kits.copy():
        parents = cat.get_parents()
        # Fetch parent object, only alive and not outside.
        parents = [
            cat.fetch_cat(i)
            for i in parents
            if cat.fetch_cat(i)
               and not (cat.fetch_cat(i).dead or cat.fetch_cat(i).outside)
        ]
        if not parents:
            continue

        if (
                len(parents) == 1
                or len(parents) > 2
                or all(i.gender == "male" for i in parents)
                or parents[0].gender == "female"
        ):
            if parents[0].ID in queen_dict:
                queen_dict[parents[0].ID].append(cat)
                living_kits.remove(cat)
            else:
                queen_dict[parents[0].ID] = [cat]
                living_kits.remove(cat)
        elif len(parents) == 2:
            if parents[1].ID in queen_dict:
                queen_dict[parents[1].ID].append(cat)
                living_kits.remove(cat)
            else:
                queen_dict[parents[1].ID] = [cat]
                living_kits.remove(cat)
    return queen_dict, living_kits

def get_alive_status_cats(Cat, get_status: list, working: bool = False, sort: bool = False, includePlayer = True) -> list:
    """
    returns a list of cat objects for all living cats of get_status in Clan
    :param Cat Cat: Cat class
    :param list get_status: list of statuses searching for
    :param bool working: default False, set to True if you would like the list to only include working cats
    :param bool sort: default False, set to True if you would like list sorted by descending moon age
    :param bool includePlayer: default True, set to False if you want to exclude the player
    """

    alive_cats = [i for i in Cat.all_cats.values() if i.status in get_status and not i.dead and not i.outside]

    if working:
        alive_cats = [i for i in alive_cats if not i.not_working()]

    if sort:
        alive_cats = sorted(alive_cats, key=lambda cat: cat.moons, reverse=True)

    if not includePlayer and game.clan.your_cat in alive_cats:
        alive_cats.remove(game.clan.your_cat)

    return alive_cats

def get_alive_cats(Cat):
    """
    returns a list of IDs for all living apps in the clan
    """
    alive_apps = [i for i in Cat.all_cats.values() if
                  not i.dead and not i.outside]
    return alive_apps

def get_living_cat_count(Cat):
    """
    Returns the int of all living cats, both in and out of the Clan
    :param Cat: Cat class
    """
    count = 0
    for the_cat in Cat.all_cats.values():
        if the_cat.dead:
            continue
        count += 1
    return count


def get_living_clan_cat_count(Cat):
    """
    Returns the int of all living cats within the Clan
    :param Cat: Cat class
    """
    count = 0
    for the_cat in Cat.all_cats.values():
        if the_cat.dead or the_cat.exiled or the_cat.outside:
            continue
        count += 1
    return count


def get_cats_same_age(Cat, cat, age_range=10):
    """
    Look for all cats in the Clan and returns a list of cats which are in the same age range as the given cat.
    :param Cat: Cat class
    :param cat: the given cat
    :param int age_range: The allowed age difference between the two cats, default 10
    """
    cats = []
    for inter_cat in Cat.all_cats.values():
        if inter_cat.dead or inter_cat.outside or inter_cat.exiled:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        if (
                inter_cat.moons <= cat.moons + age_range
                and inter_cat.moons <= cat.moons - age_range
        ):
            cats.append(inter_cat)

    return cats


def get_free_possible_mates(cat):
    """Returns a list of available cats, which are possible mates for the given cat."""
    cats = []
    for inter_cat in cat.all_cats.values():
        if inter_cat.dead or inter_cat.outside or inter_cat.exiled:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        if inter_cat.is_potential_mate(cat, for_love_interest=True):
            cats.append(inter_cat)
    return cats


def get_random_moon_cat(Cat, main_cat, parent_child_modifier=True, mentor_app_modifier=True):
    """
    returns a random cat for use in moon events
    :param Cat: Cat class
    :param main_cat: cat object of main cat in event
    :param parent_child_modifier: increase the chance of the random cat being a
    parent of the main cat. Default True
    :param mentor_app_modifier: increase the chance of the random cat being a mentor or
    app of the main cat. Default True
    """
    random_cat = None

    # grab list of possible random cats
    possible_r_c = list(filter(lambda c: not c.dead and not c.exiled and not c.outside and
                                         (c.ID != main_cat.ID), Cat.all_cats.values()))

    if possible_r_c:
        random_cat = choice(possible_r_c)
        if parent_child_modifier and not int(random() * 3):
            possible_parents = []
            if main_cat.parent1:
                if Cat.fetch_cat(main_cat.parent1) in possible_r_c:
                    possible_parents.append(main_cat.parent1)
            if main_cat.parent2:
                if Cat.fetch_cat(main_cat.parent2) in possible_r_c:
                    possible_parents.append(main_cat.parent2)
            if main_cat.adoptive_parents:
                for parent in main_cat.adoptive_parents:
                    if Cat.fetch_cat(parent) in possible_r_c:
                        possible_parents.append(parent)
            if possible_parents:
                random_cat = Cat.fetch_cat(choice(possible_parents))
        if mentor_app_modifier:
            if main_cat.status in ["apprentice", "mediator apprentice", "medicine cat apprentice"] \
                    and main_cat.mentor \
                    and not int(random() * 3):
                random_cat = Cat.fetch_cat(main_cat.mentor)
            elif main_cat.apprentice and not int(random() * 3):
                random_cat = Cat.fetch_cat(choice(main_cat.apprentice))

    if isinstance(random_cat, str):
        print(f"WARNING: random cat was {random_cat} instead of cat object")
        random_cat = Cat.fetch_cat(random_cat)
    return random_cat


def get_warring_clan():
    """
    returns enemy clan if a war is currently ongoing
    """
    enemy_clan = None
    if game.clan.war.get("at_war", False):
        for other_clan in game.clan.all_clans:
            if other_clan.name == game.clan.war["enemy"]:
                enemy_clan = other_clan

    return enemy_clan


# ---------------------------------------------------------------------------- #
#                          Handling Outside Factors                            #
# ---------------------------------------------------------------------------- #


def get_current_season():
    """
    function to handle the math for finding the Clan's current season
    :return: the Clan's current season
    """

    if game.config["lock_season"]:
        game.clan.current_season = game.clan.starting_season
        return game.clan.starting_season

    modifiers = {"Newleaf": 0, "Greenleaf": 3, "Leaf-fall": 6, "Leaf-bare": 9}
    index = game.clan.age % 12 + modifiers[game.clan.starting_season]

    if index > 11:
        index = index - 12

    game.clan.current_season = game.clan.seasons[index]

    return game.clan.current_season


def change_clan_reputation(difference):
    """
    will change the Clan's reputation with outsider cats according to the difference parameter.
    """
    game.clan.reputation += difference


def change_clan_relations(other_clan, difference):
    """
    will change the Clan's relation with other clans according to the difference parameter.
    """
    # grab the clan that has been indicated
    other_clan = other_clan
    # grab the relation value for that clan
    y = game.clan.all_clans.index(other_clan)
    clan_relations = int(game.clan.all_clans[y].relations)
    # change the value
    clan_relations += difference
    # making sure it doesn't exceed the bounds
    if clan_relations > 30:
        clan_relations = 30
    elif clan_relations < 0:
        clan_relations = 0
    # setting it in the Clan save
    game.clan.all_clans[y].relations = clan_relations


def create_new_cat_block(
        Cat,
        Relationship,
        event,
        in_event_cats: dict,
        i: int,
        attribute_list: List[str]
) -> list:
    """
    Creates a single new_cat block and then generates and returns the cats within the block
    :param Cat Cat: always pass Cat class
    :param Relationship Relationship: always pass Relationship class
    :param event: always pass the event class
    :param dict in_event_cats: dict containing involved cats' abbreviations as keys and cat objects as values
    :param int i: index of the cat block
    :param list[str] attribute_list: attribute list contained within the block
    """

    thought = "Is looking around the camp with wonder"
    new_cats = None

    # gather bio parents
    parent1 = None
    parent2 = None
    for tag in attribute_list:
        match = re.match(r"parent:([,0-9]+)", tag)
        if not match:
            continue

        parent_indexes = match.group(1).split(",")
        if not parent_indexes:
            continue

        parent_indexes = [int(index) for index in parent_indexes]
        for index in parent_indexes:
            if index >= i:
                continue

            if parent1 is None:
                parent1 = event.new_cats[index][0]
            else:
                parent2 = event.new_cats[index][0]
        break

    # gather mates
    give_mates = []
    for tag in attribute_list:
        match = re.match(r"mate:([_,0-9a-zA-Z]+)", tag)
        if not match:
            continue

        mate_indexes = match.group(1).split(",")

        # TODO: make this less ugly
        for index in mate_indexes:
            if index in in_event_cats:
                if in_event_cats[index] in ["apprentice", "medicine cat apprentice", "mediator apprentice"]:
                    print("Can't give apprentices mates")
                    continue

                give_mates.append(in_event_cats[index])

            try:
                index = int(index)
            except ValueError:
                print(f"mate-index not correct: {index}")
                continue

            if index >= i:
                continue

            give_mates.extend(event.new_cats[index])

    # determine gender
    if "male" in attribute_list:
        gender = "male"
    elif "female" in attribute_list:
        gender = "female"
    elif "intersex" in attribute_list:
        gender = "intersex"
    elif "can_birth" in attribute_list and not game.clan.clan_settings["same sex birth"]:
        if "female" in attribute_list:
            gender = "female"
        elif "intersex" in attribute_list:
            gender = "intersex"
    else:
        gender = None

    # will the cat get a new name?
    if "new_name" in attribute_list:
        new_name = True
    elif "old_name" in attribute_list:
        new_name = False
    else:
        new_name = choice([True, False])

    # STATUS - must be handled before backstories
    status = None
    for _tag in attribute_list:
        match = re.match(r"status:(.+)", _tag)
        if not match:
            continue

        if match.group(1) in ["newborn", "kitten", "elder", "apprentice", "warrior",
                              "mediator apprentice", "mediator", "medicine cat apprentice",
                              "medicine cat"]:
            status = match.group(1)
            break

    # SET AGE
    age = None
    for _tag in attribute_list:
        match = re.match(r"age:(.+)", _tag)
        if not match:
            continue

        if match.group(1) in Cat.age_moons:
            age = randint(Cat.age_moons[match.group(1)][0], Cat.age_moons[match.group(1)][1])
            break

        # Set same as first mate
        if match.group(1) in ["mate", "mate_with_kits"] and give_mates:
            age = randint(Cat.age_moons[give_mates[0].age][0],
                          Cat.age_moons[give_mates[0].age][1])
            break

        if match.group(1) == "has_kits":
            age = randint(19, 120)
            break

    if status and not age:
        if status in ["apprentice", "mediator apprentice", "medicine cat apprentice"]:
            age = randint(Cat.age_moons["adolescent"][0], Cat.age_moons["adolescent"][1])
        elif status in ["warrior", "mediator", "medicine cat"]:
            age = randint(Cat.age_moons["young adult"][0], Cat.age_moons["senior adult"][1])
        elif status == "elder":
            age = randint(Cat.age_moons["senior"][0], Cat.age_moons["senior"][1])

    if "kittypet" in attribute_list:
        cat_type = "kittypet"
    elif "rogue" in attribute_list:
        cat_type = "rogue"
    elif "loner" in attribute_list:
        cat_type = "loner"
    elif "clancat" in attribute_list:
        cat_type = "former Clancat"
    elif "rivalnew" in attribute_list:
        cat_type = "rival newborn"
    elif "rivalkit" in attribute_list:
        cat_type = "rival kitten"
    elif "rivalapp" in attribute_list:
        cat_type = "rival apprentice"
    elif "rivalmedapp" in attribute_list:
        cat_type = "rival medicine cat apprentice"
    elif "rivalqueenapp" in attribute_list:
        cat_type = "rival queen's apprentice"
    elif "rivalmediaapp" in attribute_list:
        cat_type = "rival mediator apprentice"
    elif "rival" in attribute_list:
        cat_type = "rival Clancat"
    elif "rivalmed" in attribute_list:
        cat_type = "rival medicine cat"
    elif "rivalmedia" in attribute_list:
        cat_type = "rival mediator"
    elif "rivalqueen" in attribute_list:
        cat_type = "rival queen"
    elif "rivaldep" in attribute_list:
        cat_type = "rival deputy"
    elif "rivallead" in attribute_list:
        cat_type = "rival leader"

    # LIFEGEN: for encountered dead cats --
    elif "clan_status" in attribute_list:
        if status:
            cat_type = status
        else:
            if age:
                if age < 6:
                    cat_type = "kitten"
                elif age < 12:
                    cat_type = choice(
                        [
                            "apprentice", "medicine cat apprentice",
                            "mediator apprentice", "queen's apprentice"
                        ]
                    )
                elif age < 120:
                    cat_type = choice(
                        [
                            "warrior", "medicine cat", "mediator", "queen"
                        ]
                    )
                else:
                    cat_type = "elder"
            else:
                age = randint(12,100)
                cat_type = choice(["warrior", "medicine cat", "mediator", "queen"])
    # -------------------------------------

    else:
        cat_type = choice(['kittypet', 'loner', 'former Clancat', 'rival Clancat'])

    # LITTER
    litter = False
    if "litter" in attribute_list:
        litter = True
        if status not in ["kitten", "newborn"]:
            status = "kitten"

    # CHOOSE DEFAULT BACKSTORY BASED ON CAT TYPE, STATUS
   
    if status in ("kitten", "newborn"):
        chosen_backstory = choice(BACKSTORIES["backstory_categories"]["abandoned_backstories"])
    if status == "medicine cat":
        if cat_type == "former Clancat":
            chosen_backstory = choice(["medicine_cat", "disgraced1"])
        else:
            chosen_backstory = choice(["wandering_healer1", "wandering_healer2"])
    if cat_type == "former Clancat":
        x = "former_clancat"
    else:
        x = cat_type
    chosen_backstory = choice(BACKSTORIES["backstory_categories"].get(f"{x}_backstories", ["outsider1"]))

    # OPTION TO OVERRIDE DEFAULT BACKSTORY
    bs_override = False
    stor = []
    for _tag in attribute_list:
        match = re.match(r"backstory:(.+)", _tag)
        if match:
            stor = [x for x in match.group(1).split(",") if x in BACKSTORIES["backstories"]]
            if not stor:
                bs_override = True
                continue
            chosen_backstory = choice(stor)
            break

    # KITTEN THOUGHT
    if status in ["kitten", "newborn"]:
        thought = "Is snuggled safe in the nursery"

    # MEETING - DETERMINE IF THIS IS AN OUTSIDE CAT
    outside = False
    if "meeting" in attribute_list:
        outside = True
        status = cat_type
        new_name = False
        thought = "Is wondering about those new cats"


    # IS THE CAT DEAD?
    alive = True
    if "dead" in attribute_list:
        alive = False
        thought = "Explores a new, starry world"

    outClan = None
    if "rival" in attribute_list and alive == True:
        outClan = 1
        new_name = True
        outside = True
        thought = "Talks to clanmates about their rivals"

    # LIFEGEN: encountered dead cat residences -----------------------
    df = False
    encountered_dead_df = False
    encountered_dead_sc = False
    encountered_dead_ur = False

    for _tag in attribute_list:
        match = re.match(r"residence:(.+)", _tag)
        if not match:
            continue
        if match.group(1) == "ur":
            outside = True
            alive = False
            thought = "Is intrigued by the living cat they just met"
            chosen_backstory = choice(BACKSTORIES["backstory_categories"]["starclan_backstories"])
            encountered_dead_ur = True
            break
        elif match.group(1) == "df":
            df = True
            outside = False
            alive = False
            thought = "Is annoyed with the living cat they just met"
            chosen_backstory = choice(BACKSTORIES["backstory_categories"]["df_backstories"])
            encountered_dead_df = True

            new_name = True
            # ^^ so they get a clan cat name
            break
        elif match.group(1) == "sc":
            alive = False
            outside = False
            df = False
            thought = "Is curious about the living cat they just met"
            chosen_backstory = choice(BACKSTORIES["backstory_categories"]["starclan_backstories"])
            # its annoying i have to do this here but oh welp
            encountered_dead_sc = True

            new_name = True
            # ^^ so they get a clan cat name
            break
    # ---------------------------------------------------------------------

    # check if we can use an existing cat here
    chosen_cat = None
    if "exists" in attribute_list:
        existing_outsiders = [i for i in Cat.all_cats.values() if i.outside and not i.dead]
        possible_outsiders = []
        for cat in existing_outsiders:
            if stor and cat.backstory not in stor:
                continue
            if cat_type != cat.status:
                continue
            if gender and gender != cat.gender:
                continue
            if age and age not in Cat.age_moons[cat.age]:
                continue
            possible_outsiders.append(cat)

        if possible_outsiders:
            chosen_cat = choice(possible_outsiders)
            game.clan.add_to_clan(chosen_cat)
            chosen_cat.status = status
            chosen_cat.outside = outside
            if not alive:
                chosen_cat.die()

            if new_name:
                name = f"{chosen_cat.name.prefix}"
                spaces = name.count(" ")
                if choice([1, 2]) == 1 and spaces > 0:  # adding suffix to OG name
                    # make a list of the words within the name, then add the OG name back in the list
                    words = name.split(" ")
                    words.append(name)
                    new_prefix = choice(words)  # pick new prefix from that list
                    name = new_prefix
                    chosen_cat.name.prefix = name
                    chosen_cat.name.give_suffix(
                        pelt=chosen_cat.pelt,
                        biome=game.clan.biome,
                        tortiepattern=chosen_cat.pelt.tortiepattern
                    )
                else:  # completely new name
                    chosen_cat.name.give_prefix(
                        eyes=chosen_cat.pelt.eye_colour,
                        colour=chosen_cat.pelt.colour,
                        biome=game.clan.biome
                    )
                    chosen_cat.name.give_suffix(
                        pelt=chosen_cat.pelt.colour,
                        biome=game.clan.biome,
                        tortiepattern=chosen_cat.pelt.tortiepattern
                    )

            new_cats = [chosen_cat]

    # Now we generate the new cat
    if not chosen_cat:
        new_cats = create_new_cat(Cat,
                                  new_name=new_name,
                                  loner=cat_type in ["loner", "rogue"],
                                  kittypet=cat_type == "kittypet",
                                  other_clan=cat_type == 'former Clancat',
                                  kit=False if litter else status in ["kitten", "newborn"],
                                  # this is for singular kits, litters need this to be false
                                  litter=litter,
                                  backstory=chosen_backstory,
                                  status=status,
                                  age=age,
                                  gender=gender,
                                  thought=thought,
                                  alive=alive,
                                  df=df,
                                  outside=outside,
                                  parent1=parent1.ID if parent1 else None,
                                  parent2=parent2.ID if parent2 else None,
                                  outClan=outClan if outClan else None
                                  )

        # NEXT
        # add relations to bio parents, if needed
        # add relations to cats generated within the same block, as they are littermates
        # add mates
        # THIS DOES NOT ADD RELATIONS TO CATS IN THE EVENT, those are added within the relationships block of the event

        for n_c in new_cats:

            # LIFEGEN: encountered dead cat stuff -----------------------------
            beginning = History.get_beginning(n_c)
            if encountered_dead_df or encountered_dead_sc or encountered_dead_ur:
                beginning['encountered'] = True
            else:
                beginning['encountered'] = False

            if "encountered" in beginning:
                if beginning["encountered"] is True:
                    if n_c.parent2 != game.clan.your_cat.ID:
                        n_c.dead_for = randint(50,140)
                    n_c.dead = True
                    n_c.status = status

                    if n_c.parent2 == game.clan.your_cat.ID:
                        n_c.thought = "Just met their parent!"
                        n_c.dead_for = n_c.moons
            # ------------------------------------------------------------------

            # SET MATES
            for inter_cat in give_mates:
                if n_c == inter_cat or n_c.ID in inter_cat.mate:
                    continue

                # this is some duplicate work, since this triggers inheritance re-calcs
                # TODO: optimize
                n_c.set_mate(inter_cat)

            # LITTERMATES
            for inter_cat in new_cats:
                if n_c == inter_cat:
                    continue

                y = randrange(0, 20)
                start_relation = Relationship(n_c, inter_cat, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[inter_cat.ID] = start_relation

            # BIO PARENTS
            for par in (parent1, parent2):
                if not par:
                    continue

                y = randrange(0, 20)
                start_relation = Relationship(par, n_c, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                par.relationships[n_c.ID] = start_relation

                y = randrange(0, 20)
                start_relation = Relationship(n_c, par, False, True)
                start_relation.platonic_like += 30 + y
                start_relation.comfortable = 10 + y
                start_relation.admiration = 15 + y
                start_relation.trust = 10 + y
                n_c.relationships[par.ID] = start_relation

            # UPDATE INHERITANCE
            n_c.create_inheritance_new_cat()

    return new_cats


def get_other_clan(clan_name):
    """
    returns the clan object of given clan name
    """
    for clan in game.clan.all_clans:
        if clan.name == clan_name:
            return clan


def create_new_cat(
        Cat,
        new_name: bool = False,
        loner: bool = False,
        kittypet: bool = False,
        kit: bool = False,
        litter: bool = False,
        other_clan: bool = None,
        backstory: bool = None,
        status: str = None,
        age: int = None,
        gender: str = None,
        thought: str = 'Is looking around the camp with wonder',
        alive: bool = True,
        df:bool=False,
        outside: bool = False,
        parent1: str = None,
        parent2: str = None,
        outClan: int = None
) -> list:
    """
    This function creates new cats and then returns a list of those cats
    :param Cat Cat: pass the Cat class
    :params Relationship Relationship: pass the Relationship class
    :param bool new_name: set True if cat(s) is a loner/rogue receiving a new Clan name - default: False
    :param bool loner: set True if cat(s) is a loner or rogue - default: False
    :param bool kittypet: set True if cat(s) is a kittypet - default: False
    :param bool kit: set True if the cat is a lone kitten - default: False
    :param bool litter: set True if a litter of kittens needs to be generated - default: False
    :param bool other_clan: if new cat(s) are from a neighboring clan, set true
    :param bool backstory: a list of possible backstories.json for the new cat(s) - default: None
    :param str status: set as the rank you want the new cat to have - default: None (will cause a random status to be picked)
    :param int age: set the age of the new cat(s) - default: None (will be random or if kit/litter is true, will be kitten.
    :param str gender: set the gender (BIRTH SEX) of the cat - default: None (will be random)
    :param str thought: if you need to give a custom "welcome" thought, set it here
    :param bool alive: set this as False to generate the cat as already dead - default: True (alive)
    :param bool outside: set this as True to generate the cat as an outsider instead of as part of the Clan - default: False (Clan cat)
    :param str parent1: Cat ID to set as the biological parent1
    :param str parent2: Cat ID object to set as the biological parert2
    """
    # TODO: it would be nice to rewrite this to be less bool-centric
    accessory = None
    if isinstance(backstory, list):
        backstory = choice(backstory)

    if backstory in (
            BACKSTORIES["backstory_categories"]["former_clancat_backstories"]
            or BACKSTORIES["backstory_categories"]["otherclan_categories"]
    ):
        other_clan = True

    created_cats = []

    if not litter:
        number_of_cats = 1
    else:
        number_of_cats = choices([2, 3, 4, 5], [5, 4, 1, 1], k=1)[0]

    if not isinstance(age, int):
        if status == "newborn":
            age = 0
        elif litter or kit:
            age = randint(1, 5)
        elif status in ("apprentice", "medicine cat apprentice", "mediator apprentice"):
            age = randint(6, 11)
        elif status == "warrior":
            age = randint(23, 120)
        elif status == "medicine cat":
            age = randint(23, 140)
        elif status == "elder":
            age = randint(120, 130)
        else:
            age = randint(6, 120)

    # setting status
    if not status:
        if outClan is None:
            if age == 0:
                status = "newborn"
            elif age < 6:
                status = "kitten"
            elif 6 <= age <= 11:
                status = "apprentice"
            elif age >= 12:
                status = "warrior"
            elif age >= 120:
                status = "elder"
        else:
            status = "rival Clancat"
    
    # cat creation and naming time
    for index in range(number_of_cats):
        # setting gender
        if not gender:
            _gender = choice(["female", "male", "intersex"])
        else:
            _gender = gender
    
        # other Clan cats, apps, and kittens (kittens and apps get indoctrinated lmao no old names for them)
        if other_clan or kit or litter or age < 12 and not (loner or kittypet):
            new_cat = Cat(
                moons=age,
                status=status,
                gender=_gender,
                backstory=backstory,
                parent1=parent1,
                parent2=parent2,
            )
        else:
            # grab starting names and accs for loners/kittypets
            if kittypet:
                name = choice(names.names_dict["kittypet_names"])
                if choice([1, 2]) == 1:
                    accessory = choice(Pelt.collars)
            elif (
                    loner and choice([1, 2]) == 1
            ):  # try to give name from full loner name list
                name = choice(names.names_dict["loner_names"])
            else:
                name = choice(
                    names.names_dict["normal_prefixes"]
                )  # otherwise give name from prefix list (more nature-y names)

            # now we make the cats
            if new_name:  # these cats get new names
                    
                if choice([1, 2]) == 1:  # adding suffix to OG name
                    spaces = name.count(" ")
                    if spaces > 0:
                        # make a list of the words within the name, then add the OG name back in the list
                        words = name.split(" ")
                        words.append(name)
                        new_prefix = choice(words)  # pick new prefix from that list
                        name = new_prefix
                    new_cat = Cat(
                        moons=age,
                        prefix=name,
                        status=status,
                        gender=_gender,
                        backstory=backstory,
                        parent1=parent1,
                        parent2=parent2,
                    )
                else:  # completely new name
                    new_cat = Cat(
                        moons=age,
                        status=status,
                        gender=_gender,
                        backstory=backstory,
                        parent1=parent1,
                        parent2=parent2,
                    )
            # these cats keep their old names
            else:
                new_cat = Cat(
                    moons=age,
                    prefix=name,
                    suffix="",
                    status=status,
                    gender=_gender,
                    backstory=backstory,
                    parent1=parent1,
                    parent2=parent2,
                )

            # give em a collar if they got one
            if accessory:
                new_cat.pelt.accessories.append(accessory)
        # give apprentice aged cat a mentor
        if new_cat.age == "adolescent":
            new_cat.update_mentor()

        if df is True:
            if status != "kitten":
                scarchance = randint(1,5)
                if scarchance == 1 or 2 or 3:
                    scar = choice(Pelt.scars1)
                    new_cat.pelt.scars.append(scar)
                    if new_cat.status in ["warrior", "deputy", "leader"]:
                        scarchance = randint(1,2)
                        if scarchance == 1:
                            scar = choice(Pelt.scars3)
                            new_cat.pelt.scars.append(scar)
                    elif new_cat.status in ["medicine cat", "apprentice", 
                    "elder", "medicine cat apprentice", "queen", "mediator", 
                    "queen's apprentice", "mediator apprentice"]:
                        scarchance = randint(1,8)
                        if scarchance == 1:
                            scar = choice(Pelt.scars3)
                            new_cat.pelt.scars.append(scar)
                    scar2chance = randint(1,50)
                    if scar2chance == 1:
                        scar = choice(Pelt.scars2)
                        new_cat.pelt.scars.append(scar)
            else:
                scarchance = randint(1,2)
                if scarchance == 1:
                    scar = choice(Pelt.scars1)
                    new_cat.pelt.scars.append(scar)
            
        # Remove disabling scars on living cats, if they generated.
        if not df: 
            not_allowed = ['NOPAW', 'NOTAIL', 'HALFTAIL', 'NOEAR', 'BOTHBLIND', 'RIGHTBLIND', 
                        'LEFTBLIND', 'BRIGHTHEART', 'NOLEFTEAR', 'NORIGHTEAR', 'MANLEG']
            for scar in new_cat.pelt.scars:
                if scar in not_allowed:
                    new_cat.pelt.scars.remove(scar)

        # chance to give the new cat a permanent condition, higher chance for found kits and litters
        if kit or litter:
            chance = int(
                game.config["cat_generation"]["base_permanent_condition"] / 11.25
            )
        else:
            chance = game.config["cat_generation"]["base_permanent_condition"] + 10
        if not int(random() * chance):
            possible_conditions = []
            for condition in PERMANENT:
                if (kit or litter) and PERMANENT[condition]["congenital"] not in [
                    "always",
                    "sometimes",
                ]:
                    continue
                # next part ensures that a kit won't get a condition that takes too long to reveal
                age = new_cat.moons
                leeway = 5 - (PERMANENT[condition]["moons_until"] + 1)
                if age > leeway:
                    continue
                possible_conditions.append(condition)

            if possible_conditions:
                chosen_condition = choice(possible_conditions)
                born_with = False
                if PERMANENT[chosen_condition]["congenital"] in [
                    "always",
                    "sometimes",
                ]:
                    born_with = True

                new_cat.get_permanent_condition(chosen_condition, born_with)
                if (
                        new_cat.permanent_condition[chosen_condition]["moons_until"]
                        == 0
                ):
                    new_cat.permanent_condition[chosen_condition][
                        "moons_until"
                    ] = -2

                # assign scars
                if chosen_condition in ["lost a leg", "born without a leg"]:
                    new_cat.pelt.scars.append("NOPAW")
                elif chosen_condition in ["lost their tail", "born without a tail"]:
                    new_cat.pelt.scars.append("NOTAIL")
                elif chosen_condition == "born without an eye":
                    if random.randint(1, 2) == 1:
                        new_cat.pelt.eye_colour= None
                    else:
                        new_cat.pelt.eye_colour2 = None
                elif chosen_condition == "born without eyes":
                    new_cat.pelt.eye_colour = None
                    new_cat.pelt.eye_colour2 = None

        if outside:
            new_cat.outside = True
        if not alive:
            new_cat.die()

        if df:
            new_cat.df = True
        # give apprentice aged cat a mentor
        # this is in a weird spot but DF cats were getting clancat mentors otherwise
            if new_cat.age == 'adolescent' and not new_cat.dead:
                new_cat.update_mentor()

        # newbie thought
        new_cat.thought = thought

        # and they exist now
        created_cats.append(new_cat)
        game.clan.add_cat(new_cat)
        history = History()
        history.add_beginning(new_cat)

        # create relationships
        new_cat.create_relationships_new_cat()
        # Note - we always update inheritance after the cats are generated, to
        # allow us to add parents.
        # new_cat.create_inheritance_new_cat()

        if outClan is not None:
            new_cat.outClan=outClan
        else:
            new_cat.outClan=None

    return created_cats


# ---------------------------------------------------------------------------- #
#                             Cat Relationships                                #
# ---------------------------------------------------------------------------- #


def get_highest_romantic_relation(
        relationships, exclude_mate=False, potential_mate=False
):
    """Returns the relationship with the highest romantic value."""
    max_love_value = 0
    current_max_relationship = None
    for rel in relationships:
        if rel.romantic_love < 0:
            continue
        if exclude_mate and rel.cat_from.ID in rel.cat_to.mate:
            continue
        if potential_mate and not rel.cat_to.is_potential_mate(
                rel.cat_from, for_love_interest=True
        ):
            continue
        if rel.romantic_love > max_love_value:
            current_max_relationship = rel
            max_love_value = rel.romantic_love

    return current_max_relationship


def check_relationship_value(cat_from, cat_to, rel_value=None):
    """
    returns the value of the rel_value param given
    :param cat_from: the cat who is having the feelings
    :param cat_to: the cat that the feelings are directed towards
    :param rel_value: the relationship value that you're looking for,
    options are: romantic, platonic, dislike, admiration, comfortable, jealousy, trust, toxicity
    """
    if cat_to.ID in cat_from.relationships:
        relationship = cat_from.relationships[cat_to.ID]
    else:
        relationship = cat_from.create_one_relationship(cat_to)

    if rel_value == "romantic":
        return relationship.romantic_love
    elif rel_value == "platonic":
        return relationship.platonic_like
    elif rel_value == "dislike":
        return relationship.dislike
    elif rel_value == "admiration":
        return relationship.admiration
    elif rel_value == "comfortable":
        return relationship.comfortable
    elif rel_value == "jealousy":
        return relationship.jealousy
    elif rel_value == "trust":
        return relationship.trust
    elif rel_value == "toxicity":
        return relationship.toxicity


def get_personality_compatibility(cat1, cat2):
    """Returns:
    True - if personalities have a positive compatibility
    False - if personalities have a negative compatibility
    None - if personalities have a neutral compatibility
    """
    personality1 = cat1.personality.trait
    personality2 = cat2.personality.trait

    if personality1 == personality2:
        if personality1 is None:
            return None
        return True

    lawfulness_diff = abs(cat1.personality.lawfulness - cat2.personality.lawfulness)
    sociability_diff = abs(cat1.personality.sociability - cat2.personality.sociability)
    aggression_diff = abs(cat1.personality.aggression - cat2.personality.aggression)
    stability_diff = abs(cat1.personality.stability - cat2.personality.stability)
    list_of_differences = [
        lawfulness_diff,
        sociability_diff,
        aggression_diff,
        stability_diff,
    ]

    running_total = 0
    for x in list_of_differences:
        if x <= 4:
            running_total += 1
        elif x >= 6:
            running_total -= 1

    if running_total >= 2:
        return True
    if running_total <= -2:
        return False

    return None


def get_cats_of_romantic_interest(cat):
    """Returns a list of cats, those cats are love interest of the given cat"""
    cats = []
    for inter_cat in cat.all_cats.values():
        if inter_cat.dead or inter_cat.outside or inter_cat.exiled:
            continue
        if inter_cat.ID == cat.ID:
            continue

        if inter_cat.ID not in cat.relationships:
            cat.create_one_relationship(inter_cat)
            if cat.ID not in inter_cat.relationships:
                inter_cat.create_one_relationship(cat)
            continue

        # Extra check to ensure they are potential mates
        if (
                inter_cat.is_potential_mate(cat, for_love_interest=True)
                and cat.relationships[inter_cat.ID].romantic_love > 0
        ):
            cats.append(inter_cat)
    return cats


def get_amount_of_cats_with_relation_value_towards(cat, value, all_cats):
    """
    Looks how many cats have the certain value
    :param cat: cat in question
    :param value: value which has to be reached
    :param all_cats: list of cats which has to be checked
    """

    # collect all true or false if the value is reached for the cat or not
    # later count or sum can be used to get the amount of cats
    # this will be handled like this, because it is easier / shorter to check
    relation_dict = {
        "romantic_love": [],
        "platonic_like": [],
        "dislike": [],
        "admiration": [],
        "comfortable": [],
        "jealousy": [],
        "trust": [],
        "toxicity": [],
    }

    for inter_cat in all_cats:
        if cat.ID in inter_cat.relationships:
            relation = inter_cat.relationships[cat.ID]
        else:
            continue

        relation_dict["romantic_love"].append(relation.romantic_love >= value)
        relation_dict["platonic_like"].append(relation.platonic_like >= value)
        relation_dict["dislike"].append(relation.dislike >= value)
        relation_dict["admiration"].append(relation.admiration >= value)
        relation_dict["comfortable"].append(relation.comfortable >= value)
        relation_dict["jealousy"].append(relation.jealousy >= value)
        relation_dict["trust"].append(relation.trust >= value)
        relation_dict["toxicity"].append(relation.toxicity >= value)

    return_dict = {
        "romantic_love": sum(relation_dict["romantic_love"]),
        "platonic_like": sum(relation_dict["platonic_like"]),
        "dislike": sum(relation_dict["dislike"]),
        "admiration": sum(relation_dict["admiration"]),
        "comfortable": sum(relation_dict["comfortable"]),
        "jealousy": sum(relation_dict["jealousy"]),
        "trust": sum(relation_dict["trust"]),
        "toxicity": sum(relation_dict["toxicity"]),
    }

    return return_dict


def filter_relationship_type(
        group: list,
        filter_types: List[str],
        event_id: str = None,
        patrol_leader=None
):
    """
    filters for specific types of relationships between groups of cat objects, returns bool
    :param list[Cat] group: the group of cats to be tested (make sure they're in the correct order (i.e. if testing for
    parent/child, the cat being tested as parent must be index 0)
    :param list[str] filter_types: the relationship types to check for. possible types: "siblings", "mates",
    "mates_with_pl" (PATROL ONLY), "not_mates", "parent/child", "child/parent", "mentor/app", "app/mentor",
    (following tags check if value is over given int) "romantic_int", "platonic_int", "dislike_int", "comfortable_int",
    "jealousy_int", "trust_int", "toxicity_int"
    :param str event_id: if the event has an ID, include it here
    :param Cat patrol_leader: if you are testing a patrol, ensure you include the self.patrol_leader here
    """
    # keeping this list here just for quick reference of what tags are handled here
    possible_rel_types = ["siblings", "mates", "mates_with_pl", "not_mates", "parent/child", "child/parent",
                          "mentor/app", "app/mentor"]

    possible_value_types = ["romantic", "platonic", "dislike", "comfortable", "jealousy", "trust", "admiration", "toxicity", "abusive"]

    if "siblings" in filter_types:
        test_cat = group[0]
        testing_cats = [cat for cat in group if cat.ID != test_cat.ID]

        siblings = [test_cat.is_sibling(inter_cat) for inter_cat in testing_cats]
        if not all(siblings):
            return False

    if "mates" in filter_types:
        # first test if more than one cat
        if len(group) == 1:
            return False

        # then if cats don't have the needed number of mates
        if not all(len(i.mate) >= (len(group) - 1) for i in group):
            return False

        # Now the expensive test.  We have to see if everone is mates with each other
        # Hopefully the cheaper tests mean this is only needed on events with a small number of cats
        for x in combinations(group, 2):
            if x[0].ID not in x[1].mate:
                return False

    # check if all cats are mates with p_l (they do not have to be mates with each other)
    if "mates_with_pl" in filter_types:
        # First test if there is more than one cat
        if len(group) == 1:
            return False

        # Check each cat to see if it is mates with the patrol leader
        for cat in group:
            if cat.ID == patrol_leader.ID:
                continue
            if cat.ID not in patrol_leader.mate:
                return False

    # Check if all cats are not mates
    if "not_mates" in filter_types:
        # opposite of mate check
        for x in combinations(group, 2):
            if x[0].ID in x[1].mate:
                return False

    # Check if the cats are in a parent/child relationship
    if "parent/child" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[0].is_parent(group[1]):
            return False

    if "child/parent" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[1].is_parent(group[0]):
            return False

    if "mentor/app" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[1].ID in group[0].apprentice:
            return False

    if "app/mentor" in filter_types:
        if patrol_leader:
            if patrol_leader in group:
                group.remove(patrol_leader)
            group.insert(0, patrol_leader)
        # It should be exactly two cats for a "parent/child" event
        if len(group) != 2:
            return False
        # test for parentage
        if not group[0].ID in group[1].apprentice:
            return False

    # Filtering relationship values
    break_loop = False
    for v_type in possible_value_types:
        # first get all tags for current value types
        tags = [constraint for constraint in filter_types if v_type in constraint]

        # If there is not a tag for the current value type, check next one
        if len(tags) == 0:
            continue

            # there should be only one value constraint for each value type
        elif len(tags) > 1:
            print(f"ERROR: event {event_id} has multiple relationship constraints for the value {v_type}.")
            break_loop = True
            break

        # try to extract the value/threshold from the text
        try:
            threshold = int(tags[0].split('_')[1])
        except:
            print(
                f"ERROR: event {event_id} with the relationship constraint for the value does not {v_type} follow the formatting guidelines.")
            break_loop = True
            break

        if threshold > 100:
            print(
                f"ERROR: event {event_id} has a relationship constraint for the value {v_type}, which is higher than the max value of a relationship.")
            break_loop = True
            break

        if threshold <= 0:
            print(
                f"ERROR: event {event_id} has a relationship constraint for the value {v_type}, which is lower than the min value of a relationship or 0.")
            break_loop = True
            break

        # each cat has to have relationships with this relationship value above the threshold
        fulfilled = True
        for inter_cat in group:
            rel_above_threshold = []
            group_ids = [cat.ID for cat in group]
            relevant_relationships = list(
                filter(lambda rel: rel.cat_to.ID in group_ids and rel.cat_to.ID != inter_cat.ID,
                       list(inter_cat.relationships.values())
                       )
            )

            # get the relationships depending on the current value type + threshold
            if v_type == "romantic":
                rel_above_threshold = [i for i in relevant_relationships if i.romantic_love >= threshold]
            elif v_type == "platonic":
                rel_above_threshold = [i for i in relevant_relationships if i.platonic_like >= threshold]
            elif v_type == "dislike":
                rel_above_threshold = [i for i in relevant_relationships if i.dislike >= threshold]
            elif v_type == "comfortable":
                rel_above_threshold = [i for i in relevant_relationships if i.comfortable >= threshold]
            elif v_type == "jealousy":
                rel_above_threshold = [i for i in relevant_relationships if i.jealousy >= threshold]
            elif v_type == "trust":
                rel_above_threshold = [i for i in relevant_relationships if i.trust >= threshold]
            elif v_type == "admiration":
                rel_above_threshold = [i for i in relevant_relationships if i.admiration >= threshold]
            elif v_type == "abusive":
                rel_above_threshold = [i for i in relevant_relationships if i.toxicity >= threshold]
            elif v_type == "toxicity":
                rel_above_threshold = [i for i in relevant_relationships if i.toxicity < threshold]

            # if the lengths are not equal, one cat has not the relationship value which is needed to another cat of
            # the event
            if len(rel_above_threshold) + 1 != len(group):
                fulfilled = False
                break

        if not fulfilled:
            break_loop = True
            break

    # if break is used in the loop, the condition are not fulfilled
    # and this event should not be added to the filtered list
    if break_loop:
        return False

    return True


def gather_cat_objects(
        Cat,
        abbr_list: List[str],
        event,
        stat_cat=None,
        extra_cat=None
) -> list:
    """
    gathers cat objects from list of abbreviations used within an event format block
    :param Cat Cat: Cat class
    :param list[str] abbr_list: The list of abbreviations, supports "m_c", "r_c", "p_l", "s_c", "app1", "app2", "clan",
    "some_clan", "patrol", "multi", "n_c{index}"
    :param event: the controlling class of the event (e.g. Patrol, HandleShortEvents), default None
    :param Cat stat_cat: if passing the Patrol class, must include stat_cat separately
    :param Cat extra_cat: if not passing an event class, include the single affected cat object here. If you are not
    passing a full event class, then be aware that you can only include "m_c" as a cat abbreviation in your rel block.
    The other cat abbreviations will not work.
    :return: list of cat objects
    """
    out_set = set()

    for abbr in abbr_list:
        if abbr == "m_c":
            if extra_cat:
                out_set.add(extra_cat)
            else:
                out_set.add(event.main_cat)
        if abbr == "r_c":
            out_set.add(event.random_cat)
        elif abbr == "p_l":
            out_set.add(event.patrol_leader)
        elif abbr == "s_c":
            out_set.add(stat_cat)
        # LG
        elif abbr == "y_c":
            out_set.add(game.clan.your_cat)
        # ---
        elif abbr == "app1" and len(event.patrol_apprentices) >= 1:
            out_set.add(event.patrol_apprentices[0])
        elif abbr == "app2" and len(event.patrol_apprentices) >= 2:
            out_set.add(event.patrol_apprentices[1])
        elif abbr == "clan":
            out_set.update([x for x in Cat.all_cats_list if not (x.dead or x.outside or x.exiled)])
        elif abbr == "some_clan":  # 1 / 8 of clan cats are affected
            clan_cats = [x for x in Cat.all_cats_list if not (x.dead or x.outside or x.exiled)]
            out_set.update(sample(clan_cats, randint(1, round(len(clan_cats) / 8))))
        elif abbr == "patrol":
            out_set.update(event.patrol_cats)
        elif abbr == "multi":
            cat_num = randint(1, max(1, len(event.patrol_cats) - 1))
            out_set.update(sample(event.patrol_cats, cat_num))
        elif re.match(r"n_c:[0-9]+", abbr):
            index = re.match(r"n_c:([0-9]+)", abbr).group(1)
            index = int(index)
            if index < len(event.new_cats):
                out_set.update(event.new_cats[index])

    # LIFEGEN ABBREVS ------------------------
    try:
        for kitty in event.patrol_cat_dict.items():
            print(abbr_list)
            if kitty[0] in abbr_list:
                out_set.add(kitty[1])
    except AttributeError:
        pass
    # im so lazy but this works lmfao
    # ----------------------------------------

    return list(out_set)


def unpack_rel_block(
        Cat,
        relationship_effects: List[dict],
        event=None,
        stat_cat=None,
        extra_cat=None
):
    """
    Unpacks the info from the relationship effect block used in patrol and moon events, then adjusts rel values
    accordingly.

    :param Cat Cat: Cat class
    :param list[dict] relationship_effects: the relationship effect block
    :param event: the controlling class of the event (e.g. Patrol, HandleShortEvents), default None
    :param Cat stat_cat: if passing the Patrol class, must include stat_cat separately
    :param Cat extra_cat: if not passing an event class, include the single affected cat object here. If you are not passing a full event class, then be aware that you can only include "m_c" as a cat abbreviation in your rel block.  The other cat abbreviations will not work.
    """
    possible_values = ("romantic", "platonic", "dislike", "comfort", "jealous", "trust", "respect", "toxicity")

    for block in relationship_effects:
        cats_from = block.get("cats_from", [])
        cats_to = block.get("cats_to", [])
        amount = block.get("amount")
        values = [x for x in block.get("values", ()) if x in possible_values]

        # Gather actual cat objects:
        cats_from_ob = gather_cat_objects(Cat, cats_from, event, stat_cat, extra_cat)
        cats_to_ob = gather_cat_objects(Cat, cats_to, event, stat_cat, extra_cat)

        # Remove any "None" that might have snuck in
        if None in cats_from_ob:
            cats_from_ob.remove(None)
        if None in cats_to_ob:
            cats_to_ob.remove(None)

        # Check to see if value block
        if not (cats_to_ob and cats_from_ob and values and isinstance(amount, int)):
            print(f"Relationship block incorrectly formatted: {block}")
            continue

        positive = False

        # grabbing values
        romantic_love = 0
        platonic_like = 0
        dislike = 0
        comfortable = 0
        jealousy = 0
        admiration = 0
        trust = 0
        toxicity = 0
        if "romantic" in values:
            romantic_love = amount
            if amount > 0:
                positive = True
        if "platonic" in values:
            platonic_like = amount
            if amount > 0:
                positive = True
        if "dislike" in values:
            dislike = amount
            if amount < 0:
                positive = True
        if "comfort" in values:
            comfortable = amount
            if amount > 0:
                positive = True
        if "jealous" in values:
            jealousy = amount
            if amount < 0:
                positive = True
        if "trust" in values:
            trust = amount
            if amount > 0:
                positive = True
        if "respect" in values:
            admiration = amount
            if amount > 0:
                positive = True
        if "toxicity" in values:
            toxicity = amount
            if amount < 0:
                positive = True

        if positive:
            effect = f" (positive effect)"
        else:
            effect = f" (negative effect)"

        # Get log
        log1 = None
        log2 = None
        if block.get("log"):
            log = block.get("log")
            if isinstance(log, str):
                log1 = log
            elif isinstance(log, list):
                if len(log) >= 2:
                    log1 = log[0]
                    log2 = log[1]
                elif len(log) == 1:
                    log1 = log[0]
            else:
                print(f"something is wrong with relationship log: {log}")

        if not log1:
            if hasattr(event, "text"):
                try:
                    log1 = event.text
                except AttributeError:
                    print(f"WARNING: event changed relationships but did not create a relationship log")
            else:
                log1 = "These cats recently interacted." + effect
        if not log2:
            if hasattr(event, "text"):
                try:
                    log2 = event.text
                except AttributeError:
                    print(f"WARNING: event changed relationships but did not create a relationship log")
            else:
                log2 = f"These cats recently interacted." + effect

        change_relationship_values(
            cats_to_ob,
            cats_from_ob,
            romantic_love,
            platonic_like,
            dislike,
            admiration,
            comfortable,
            jealousy,
            trust,
            toxicity,
            log=log1
        )

        if block.get("mutual"):
            change_relationship_values(
                cats_from_ob,
                cats_to_ob,
                romantic_love,
                platonic_like,
                dislike,
                admiration,
                comfortable,
                jealousy,
                trust,
                toxicity,
                log=log2
            )


def change_relationship_values(
        cats_to: list,
        cats_from: list,
        romantic_love: int = 0,
        platonic_like: int = 0,
        dislike: int = 0,
        admiration: int = 0,
        comfortable: int = 0,
        jealousy: int = 0,
        trust: int = 0,
        toxicity: int = 0,
        auto_romance: bool = False,
        log: str = None
):
    """
    changes relationship values according to the parameters.

    :param list[Cat] cats_from: list of cat objects whose rel values will be affected
    (e.g. cat_from loses trust in cat_to)
    :param list[Cat] cats_to: list of cats objects who are the target of that rel value
    (e.g. cat_from loses trust in cat_to)
    :param int romantic_love: amount to change romantic, default 0
    :param int platonic_like: amount to change platonic, default 0
    :param int dislike: amount to change dislike, default 0
    :param int admiration: amount to change admiration (respect), default 0
    :param int comfortable: amount to change comfort, default 0
    :param int jealousy: amount to change jealousy, default 0
    :param int trust: amount to change trust, default 0
    :param bool auto_romance: if the cat_from already has romantic value with cat_to, then the platonic_like param value
    will also be applied to romantic, default False
    :param str log: the string to append to the relationship log of cats involved
        """

    # This is just for test prints - DON'T DELETE - you can use this to test if relationships are changing
    """changed = False
    if romantic_love == 0 and platonic_like == 0 and dislike == 0 and admiration == 0 and \
            comfortable == 0 and jealousy == 0 and trust == 0:
        changed = False
    else:
        changed = True"""

    # pick out the correct cats
    if not cats_from:
        return
    for single_cat_from in cats_from:
        for single_cat_to in cats_to:

            # make sure we aren't trying to change a cat's relationship with themself
            if single_cat_from == single_cat_to:
                continue

            # if the cats don't know each other, start a new relationship
            if single_cat_to.ID not in single_cat_from.relationships:
                single_cat_from.create_one_relationship(single_cat_to)

            rel = single_cat_from.relationships[single_cat_to.ID]

            # here we just double-check that the cats are allowed to be romantic with each other
            if (
                    single_cat_from.is_potential_mate(single_cat_to, for_love_interest=True)
                    or single_cat_to.ID in single_cat_from.mate
            ):
                # if cat already has romantic feelings then automatically increase romantic feelings
                # when platonic feelings would increase
                if rel.romantic_love > 0 and auto_romance:
                    romantic_love = platonic_like

                # now gain the romance
                rel.romantic_love += romantic_love

            # gain other rel values
            rel.platonic_like += platonic_like
            rel.dislike += dislike
            rel.admiration += admiration
            rel.comfortable += comfortable
            rel.jealousy += jealousy
            rel.trust += trust
            rel.toxicity += toxicity

            # for testing purposes - DON'T DELETE - you can use this to test if relationships are changing
            """
            print(str(single_cat_from.name) + " gained relationship with " + str(rel.cat_to.name) + ": " +
                  "Romantic: " + str(romantic_love) +
                  " /Platonic: " + str(platonic_like) +
                  " /Dislike: " + str(dislike) +
                  " /Respect: " + str(admiration) +
                  " /Comfort: " + str(comfortable) +
                  " /Jealousy: " + str(jealousy) +
                  " /Trust: " + str(trust)) if changed else print("No relationship change")"""

            if log and isinstance(log, str):
                if single_cat_to.moons <= 1:
                    log_text = log + f"- {single_cat_to.name} was {single_cat_to.moons} moon old"
                    if log_text not in rel.log:
                        rel.log.append(log_text)
                else:
                    log_text = log + f"- {single_cat_to.name} was {single_cat_to.moons} moons old"
                    if log_text not in rel.log:
                        rel.log.append(log_text)

def get_cluster(trait):
        # Mapping traits to their respective clusters
        trait_to_clusters = {
            "assertive": ["bloodthirsty", "fierce", "bold", "daring", "confident", "arrogant", "competitive", "smug", "impulsive", "noisy"],
            "brooding": ["bloodthirsty", "cold", "gloomy", "strict", "vengeful", "grumpy", "bullying", "secretive", "aloof", "stoic", "reserved"],
            "cool": ["charismatic", "cunning", "arrogant", "charming", "manipulative", "leader-like", "passionate", "witty", "flexible", "mellow", "flamboyant"],
            "upstanding": ["righteous", "ambitious", "strict", "competitive", "responsible", "bossy", "know-it-all", "leader-like", "smug", "loyal", "justified", "methodical"],
            "introspective": ["lonesome", "righteous", "calm", "wise", "thoughtful", "quiet", "daydreamer", "flexible", "mellow"],
            "neurotic": ["nervous", "insecure", "lonesome", "quiet", "secretive", "careful", "meek", "cowardly", "emotional"],
            "silly": ["troublesome", "childish", "playful", "strange", "noisy", "attention-seeker", "rebellious", "bouncy", "energetic", "spontaneous"],
            "stable": ["loyal", "responsible", "wise", "faithful", "polite", "disciplined", "patient", "passionate", "witty", "trusting"],
            "sweet": ["compassionate", "faithful", "loving", "oblivious", "sincere", "sweet", "polite", "daydreamer", "trusting", "humble", "emotional"],
            "unabashed": ["childish", "confident", "bold", "shameless", "strange", "oblivious", "flamboyant", "impulsive", "noisy", "honest", "spontaneous"],
            "unlawful": ["adventurous", "sneaky", "rebellious", "manipulative", "obsessive", "aloof", "stoic", "cunning", "troublesome"]
        }
        clusters = [key for key, values in trait_to_clusters.items() if trait in values]

        # Assign cluster and second_cluster based on the length of clusters list
        cluster = clusters[0] if clusters else ""
        second_cluster = clusters[1] if len(clusters) > 1 else ""

        return cluster, second_cluster


# ---------------------------------------------------------------------------- #
#                               Text Adjust                                    #
# ---------------------------------------------------------------------------- #

def get_leader_life_notice() -> str:
    """
    Returns a string specifying how many lives the leader has left or notifying of the leader's full death
    """
    text = ""

    lives = game.clan.leader_lives

    if lives > 0:
        text = f"The leader has {int(lives)} lives left."
    elif lives <= 0:
        if game.clan.followingsc:
            text = 'The leader has no lives left and has travelled to StarClan.'
        else:
            text = 'The leader has no lives left and has travelled to the Dark Forest.'

    return text


def get_other_clan_relation(relation):
    """
    converts int value into string relation and returns string: "hostile", "neutral", or "ally"
    :param relation: the other_clan.relations value
    """

    if int(relation) >= 17:
        return "ally"
    elif 7 < int(relation) < 17:
        return "neutral"
    elif int(relation) <= 7:
        return "hostile"


def pronoun_repl(m, cat_pronouns_dict, raise_exception=False):
    """Helper function for add_pronouns. If raise_exception is
    False, any error in pronoun formatting will not raise an
    exception, and will use a simple replacement "error" """

    # Add protection about the "insert" sometimes used
    if m.group(0) == "{insert}":
        return m.group(0)

    inner_details = m.group(1).split("/")

    try:
        d = cat_pronouns_dict[inner_details[1]][1]
        if inner_details[0].upper() == "PRONOUN":
            pro = d[inner_details[2]]
            if inner_details[-1] == "CAP":
                pro = pro.capitalize()
            return pro
        elif inner_details[0].upper() == "VERB":
            return inner_details[d["conju"] + 1]

        if raise_exception:
            raise KeyError(
                f"Pronoun tag: {m.group(1)} is not properly"
                "indicated as a PRONOUN or VERB tag."
            )

        print("Failed to find pronoun:", m.group(1))
        return "error1"
    except (KeyError, IndexError) as e:
        if raise_exception:
            raise

        logger.exception("Failed to find pronoun: " + m.group(1))
        print("Failed to find pronoun:", m.group(1))
        return "error2"


def name_repl(m, cat_dict):
    """Name replacement"""
    return cat_dict[m.group(0)][0]


def process_text(text, cat_dict, raise_exception=False):
    """Add the correct name and pronouns into a string."""
    adjust_text = re.sub(
        r"\{(.*?)\}", lambda x: pronoun_repl(x, cat_dict, raise_exception), text
    )

    name_patterns = [r"(?<!\{)" + re.escape(l) + r"(?!\})" for l in cat_dict]
    adjust_text = re.sub(
        "|".join(name_patterns), lambda x: name_repl(x, cat_dict), adjust_text
    )
    return adjust_text


def adjust_list_text(list_of_items) -> str:
    """
    returns the list in correct grammar format (i.e. item1, item2, item3 and item4)
    this works with any number of items
    :param list_of_items: the list of items you want converted
    :return: the new string
    """
    if len(list_of_items) == 0:
        return ""
    if len(list_of_items) == 1:
        insert = f"{list_of_items[0]}"
    elif len(list_of_items) == 2:
        insert = f"{list_of_items[0]} and {list_of_items[1]}"
    else:
        item_line = ", ".join(list_of_items[:-1])
        insert = f"{item_line}, and {list_of_items[-1]}"

    return insert


def adjust_prey_abbr(patrol_text):
    """
    checks for prey abbreviations and returns adjusted text
    """
    for abbr in PREY_LISTS["abbreviations"]:
        if abbr in patrol_text:
            chosen_list = PREY_LISTS["abbreviations"].get(abbr)
            chosen_list = PREY_LISTS[chosen_list]
            prey = choice(chosen_list)
            patrol_text = patrol_text.replace(abbr, prey)

    return patrol_text


def get_special_snippet_list(
        chosen_list, amount, sense_groups=None, return_string=True
):
    """
    function to grab items from various lists in snippet_collections.json
    list options are:
    -prophecy_list - sense_groups = sight, sound, smell, emotional, touch
    -omen_list - sense_groups = sight, sound, smell, emotional, touch
    -clair_list  - sense_groups = sound, smell, emotional, touch, taste
    -dream_list (this list doesn't have sense_groups)
    -story_list (this list doesn't have sense_groups)
    :param chosen_list: pick which list you want to grab from
    :param amount: the amount of items you want the returned list to contain
    :param sense_groups: list which senses you want the snippets to correspond with:
     "touch", "sight", "emotional", "sound", "smell" are the options. Default is None, if left as this then all senses
     will be included (if the list doesn't have sense categories, then leave as None)
    :param return_string: if True then the function will format the snippet list with appropriate commas and 'ands'.
    This will work with any number of items. If set to True, then the function will return a string instead of a list.
    (i.e. ["hate", "fear", "dread"] becomes "hate, fear, and dread") - Default is True
    :return: a list of the chosen items from chosen_list or a formatted string if format is True
    """
    biome = game.clan.biome.casefold()

    # these lists don't get sense specific snippets, so is handled first
    if chosen_list in ["dream_list", "story_list"]:

        if (
                chosen_list == "story_list"
        ):  # story list has some biome specific things to collect
            snippets = SNIPPETS[chosen_list]["general"]
            snippets.extend(SNIPPETS[chosen_list][biome])
        elif (
                chosen_list == "clair_list"
        ):  # the clair list also pulls from the dream list
            snippets = SNIPPETS[chosen_list]
            snippets.extend(SNIPPETS["dream_list"])
        else:  # the dream list just gets the one
            snippets = SNIPPETS[chosen_list]

    else:
        # if no sense groups were specified, use all of them
        if not sense_groups:
            if chosen_list == "clair_list":
                sense_groups = ["taste", "sound", "smell", "emotional", "touch"]
            else:
                sense_groups = ["sight", "sound", "smell", "emotional", "touch"]

        # find the correct lists and compile them
        snippets = []
        for sense in sense_groups:
            snippet_group = SNIPPETS[chosen_list][sense]
            snippets.extend(snippet_group["general"])
            snippets.extend(snippet_group[biome])

    # now choose a unique snippet from each snip list
    unique_snippets = []
    for snip_list in snippets:
        unique_snippets.append(choice(snip_list))

    # pick out our final snippets
    final_snippets = sample(unique_snippets, k=amount)

    if return_string:
        text = adjust_list_text(final_snippets)
        return text
    else:
        return final_snippets


def find_special_list_types(text):
    """
    purely to identify which senses are being called for by a snippet abbreviation
    returns adjusted text, sense list, and list type
    """
    senses = []
    if "omen_list" in text:
        list_type = "omen_list"
    elif "prophecy_list" in text:
        list_type = "prophecy_list"
    elif "dream_list" in text:
        list_type = "dream_list"
    elif "clair_list" in text:
        list_type = "clair_list"
    elif "story_list" in text:
        list_type = "story_list"
    else:
        return text, None, None

    if "_sight" in text:
        senses.append("sight")
        text = text.replace("_sight", "")
    if "_sound" in text:
        senses.append("sound")
        text = text.replace("_sight", "")
    if "_smell" in text:
        text = text.replace("_smell", "")
        senses.append("smell")
    if "_emotional" in text:
        text = text.replace("_emotional", "")
        senses.append("emotional")
    if "_touch" in text:
        text = text.replace("_touch", "")
        senses.append("touch")
    if "_taste" in text:
        text = text.replace("_taste", "")
        senses.append("taste")

    return text, senses, list_type


def history_text_adjust(text,
                        other_clan_name,
                        clan,
                        other_cat_rc=None):
    """
    we want to handle history text on its own because it needs to preserve the pronoun tags and cat abbreviations.
    this is so that future pronoun changes or name changes will continue to be reflected in history
    """
    vowels = ['A', 'E', 'I', 'O', 'U']

    if "o_c_n" in text:
        pos = 0
        for x in range(text.count('o_c_n')):
            if 'o_c_n' in text:
                for y in vowels:
                    if str(other_clan_name).startswith(y):
                        modify = text.split()
                        if 'o_c_n' in modify:
                            pos = modify.index('o_c_n')
                        if "o_c_n's" in modify:
                            pos = modify.index("o_c_n's")
                        if 'o_c_n.' in modify:
                            pos = modify.index('o_c_n.')
                        if modify[pos - 1] == 'a':
                            modify.remove('a')
                            modify.insert(pos - 1, 'an')
                        text = " ".join(modify)
                        break

        text = text.replace('o_c_n', str(other_clan_name) + 'Clan')

    if "c_n" in text:
        text = text.replace("c_n", clan.name)
    if "r_c" in text and other_cat_rc:
        text = selective_replace(text, "r_c", str(other_cat_rc.name))
    return text


def selective_replace(text, pattern, replacement):
    i = 0
    while i < len(text):
        index = text.find(pattern, i)
        if index == -1:
            break
        start_brace = text.rfind("{", 0, index)
        end_brace = text.find("}", index)
        if start_brace != -1 and end_brace != -1 and start_brace < index < end_brace:
            i = index + len(pattern)
        else:
            text = text[:index] + replacement + text[index + len(pattern):]
            i = index + len(replacement)

    return text


def ongoing_event_text_adjust(Cat, text, clan=None, other_clan_name=None):
    """
    This function is for adjusting the text of ongoing events
    :param Cat: the cat class
    :param text: the text to be adjusted
    :param clan: the name of the clan
    :param other_clan_name: the other Clan's name if another Clan is involved
    """
    cat_dict = {}
    if "lead_name" in text:
        kitty = Cat.fetch_cat(game.clan.leader)
        if kitty:
            cat_dict["lead_name"] = (str(kitty.name), choice(kitty.pronouns))
    if "dep_name" in text:
        kitty = Cat.fetch_cat(game.clan.deputy)
        if kitty:
            cat_dict["dep_name"] = (str(kitty.name), choice(kitty.pronouns))
    if "med_name" in text:
        kitty = choice(get_alive_status_cats(Cat, ["medicine cat"], working=True))
        cat_dict["med_name"] = (str(kitty.name), choice(kitty.pronouns))

    if cat_dict:
        text = process_text(text, cat_dict)

    if other_clan_name:
        text = text.replace("o_c_n", other_clan_name)
    if clan:
        clan_name = str(clan.name)
    else:
        if game.clan is None:
            clan_name = game.switches["clan_list"][0]
        else:
            clan_name = str(game.clan.name)

    text = text.replace("c_n", clan_name + "Clan")

    return text


def event_text_adjust(
        Cat,
        text,
        patrol_cat_dict={},
        # LIFEGEN ^^ this dict is for the random abbrevs in our patrols.
        patrol_leader=None,
        main_cat=None,
        random_cat=None,
        stat_cat=None,
        victim_cat=None,
        patrol_cats: list = None,
        patrol_apprentices: list = None,
        new_cats: list = None,
        multi_cats: list = None,
        clan=None,
        other_clan=None,
        chosen_herb: str = None):
    """
    handles finding abbreviations in the text and replacing them appropriately, returns the adjusted text
    :param Cat Cat: always pass the Cat class
    :param str text: the text being adjusted
    "param dict patrol_cat_dict: LIFEGEN: dict to hold random cat abbrevs in LG patrols
    :param Cat patrol_leader: Cat object for patrol_leader (p_l), if present
    :param Cat main_cat: Cat object for main_cat (m_c), if present
    :param Cat random_cat: Cat object for random_cat (r_c), if present
    :param Cat stat_cat: Cat object for stat_cat (s_c), if present
    :param Cat victim_cat: Cat object for victim_cat (mur_c), if present
    :param list[Cat] patrol_cats: List of Cat objects for cats in patrol, if present
    :param list[Cat] patrol_apprentices: List of Cat objects for patrol_apprentices (app#), if present
    :param list[Cat] new_cats: List of Cat objects for new_cats (n_c:index), if present
    :param list[Cat] multi_cats: List of Cat objects for multi_cat (multi_cat), if present
    :param Clan clan: pass game.clan
    :param OtherClan other_clan: OtherClan object for other_clan (o_c_n), if present
    :param str chosen_herb: string of chosen_herb (chosen_herb), if present
    """
    vowels = ["A", "E", "I", "O", "U"]

    if not text:
        text = 'This should not appear, report as a bug please! Tried to adjust the text, but no text was provided.'
        print("WARNING: Tried to adjust text, but no text was provided.")

    replace_dict = {}

    # main_cat
    if "m_c" in text:
        if main_cat:
            replace_dict["m_c"] = (str(main_cat.name), choice(main_cat.pronouns))

    # patrol_lead
    if "p_l" in text:
        if patrol_leader:
            replace_dict["p_l"] = (str(patrol_leader.name), choice(patrol_leader.pronouns))

    # random_cat
    if "r_c" in text:
        if random_cat:
            replace_dict["r_c"] = (str(random_cat.name), get_pronouns(random_cat))

    # stat cat
    if "s_c" in text:
        if stat_cat:
            replace_dict["s_c"] = (str(stat_cat.name), get_pronouns(stat_cat))

    # LIFEGEN ABBREVS
    if game.current_screen == 'patrol screen':
        for cat in patrol_cat_dict.items():
            replace_dict[cat[0]] = (str(cat[1].name), choice(cat[1].pronouns))

    # other_cats
    if patrol_cats:
        other_cats = [i for i in patrol_cats if i not in [patrol_leader, random_cat, patrol_apprentices]]
        other_cat_abbr = ["o_c1", "o_c2", "o_c3", "o_c4"]
        for i, abbr in enumerate(other_cat_abbr):
            if abbr not in text:
                continue
            if len(other_cats) > i:
                replace_dict[abbr] = (str(other_cats[i].name), choice(other_cats[i].pronouns))

    # patrol_apprentices
    app_abbr = ["app1", "app2", "app3", "app4", "app5", "app6"]
    for i, abbr in enumerate(app_abbr):
        if abbr not in text:
            continue
        if len(patrol_apprentices) > i:
            replace_dict[abbr] = (
                str(patrol_apprentices[i].name), choice(patrol_apprentices[i].pronouns)
            )

    # new_cats (include pre version)
    if "n_c" in text:
        for i, cat_list in enumerate(new_cats):
            if len(new_cats) > 1:
                pronoun = Cat.default_pronouns[0]  # They/them for multiple cats
            else:
                pronoun = choice(cat_list[0].pronouns)

            replace_dict[f"n_c:{i}"] = (str(cat_list[0].name), pronoun)
            replace_dict[f"n_c_pre:{i}"] = (str(cat_list[0].name.prefix), pronoun)

    # mur_c (murdered cat for reveals)
    if "mur_c" in text:
        replace_dict["mur_c"] = (str(victim_cat.name), get_pronouns(victim_cat))

    # lead_name
    if "lead_name" in text:
        leader = Cat.fetch_cat(game.clan.leader)
        replace_dict["lead_name"] = (str(leader.name), choice(leader.pronouns))

    # dep_name
    if "dep_name" in text:
        deputy = Cat.fetch_cat(game.clan.deputy)
        replace_dict["dep_name"] = (str(deputy.name), choice(deputy.pronouns))

    # med_name
    if "med_name" in text:
        med = choice(get_alive_status_cats(Cat, ["medicine cat"], working=True))
        replace_dict["med_name"] = (str(med.name), choice(med.pronouns))

    # assign all names and pronouns
    if replace_dict:
        text = process_text(text, replace_dict)

    # multi_cat
    if "multi_cat" in text:
        name_list = []
        for _cat in multi_cats:
            name_list.append(str(_cat.name))
        list_text = adjust_list_text(name_list)
        text = text.replace("multi_cat", list_text)

    # other_clan_name
    if "o_c_n" in text:
        other_clan_name = other_clan.name
        pos = 0
        for x in range(text.count('o_c_n')):
            if 'o_c_n' in text:
                for y in vowels:
                    if str(other_clan_name).startswith(y):
                        modify = text.split()
                        if 'o_c_n' in modify:
                            pos = modify.index('o_c_n')
                        if "o_c_n's" in modify:
                            pos = modify.index("o_c_n's")
                        if 'o_c_n.' in modify:
                            pos = modify.index('o_c_n.')
                        if modify[pos - 1] == 'a':
                            modify.remove('a')
                            modify.insert(pos - 1, 'an')
                        text = " ".join(modify)
                        break

        text = text.replace('o_c_n', str(other_clan_name) + 'Clan')

    # clan_name
    if "c_n" in text:
        try:
            clan_name = clan.name
        except AttributeError:
            clan_name = game.switches['clan_list'][0]

        pos = 0
        for x in range(text.count('c_n')):
            if 'c_n' in text:
                for y in vowels:
                    if str(clan_name).startswith(y):
                        modify = text.split()
                        if 'c_n' in modify:
                            pos = modify.index('c_n')
                        if "c_n's" in modify:
                            pos = modify.index("c_n's")
                        if 'c_n.' in modify:
                            pos = modify.index('c_n.')
                        if modify[pos - 1] == 'a':
                            modify.remove('a')
                            modify.insert(pos - 1, 'an')
                        text = " ".join(modify)
                        break

        text = text.replace('c_n', str(clan_name) + 'Clan')

    # prey lists
    text = adjust_prey_abbr(text)

    # special lists
    text, senses, list_type = find_special_list_types(text)
    if list_type:
        sign_list = get_special_snippet_list(list_type, amount=randint(1, 3), sense_groups=senses)
        text = text.replace(list_type, str(sign_list))

    # acc_plural (only works for main_cat's acc)
    if "acc_plural" in text:
        # text = text.replace("acc_plural", str(ACC_DISPLAY[main_cat.pelt.accessory]["plural"]))
        text = text.replace("acc_plural", str(ACC_DISPLAY[main_cat.pelt.accessories[-1]]["plural"]))

    # acc_singular (only works for main_cat's acc)
    if "acc_singular" in text:
        # text = text.replace("acc_singular", str(ACC_DISPLAY[main_cat.pelt.accessory]["singular"]))
        text = text.replace("acc_singular", str(ACC_DISPLAY[main_cat.pelt.accessories[-1]]["singular"]))

    if "given_herb" in text:
        if "_" in chosen_herb:
            chosen_herb = chosen_herb.replace("_", " ")
        text = text.replace("given_herb", str(chosen_herb))

    return text


def leader_ceremony_text_adjust(
        Cat,
        text,
        leader,
        life_giver=None,
        virtue=None,
        extra_lives=None,
):
    """
    used to adjust the text for leader ceremonies
    """
    replace_dict = {
        "m_c_star": (str(leader.name.prefix + "star"), choice(leader.pronouns)),
        "m_c": (str(leader.name.prefix + leader.name.suffix), choice(leader.pronouns)),
    }

    if life_giver:
        replace_dict["r_c"] = (
            str(Cat.fetch_cat(life_giver).name),
            choice(Cat.fetch_cat(life_giver).pronouns),
        )

    text = process_text(text, replace_dict)

    if virtue:
        virtue = process_text(virtue, replace_dict)
        text = text.replace("[virtue]", virtue)

    if extra_lives:
        text = text.replace("[life_num]", str(extra_lives))

    text = text.replace("c_n", str(game.clan.name) + "Clan")

    return text


def ceremony_text_adjust(
        Cat,
        text,
        cat,
        old_name=None,
        dead_mentor=None,
        mentor=None,
        previous_alive_mentor=None,
        random_honor=None,
        living_parents=(),
        dead_parents=(),
):
    clanname = str(game.clan.name + "Clan")

    random_honor = random_honor
    random_living_parent = None
    random_dead_parent = None

    adjust_text = text

    cat_dict = {
        "m_c": (
            (str(cat.name), choice(cat.pronouns)) if cat else ("cat_placeholder", None)
        ),
        "(mentor)": (
            (str(mentor.name), choice(mentor.pronouns))
            if mentor
            else ("mentor_placeholder", None)
        ),
        "(deadmentor)": (
            (str(dead_mentor.name), get_pronouns(dead_mentor))
            if dead_mentor
            else ("dead_mentor_name", None)
        ),
        "(previous_mentor)": (
            (str(previous_alive_mentor.name), choice(previous_alive_mentor.pronouns))
            if previous_alive_mentor
            else ("previous_mentor_name", None)
        ),
        "l_n": (
            (str(game.clan.leader.name), choice(game.clan.leader.pronouns))
            if game.clan.leader
            else ("leader_name", None)
        ),
        "c_n": (clanname, None),
    }

    if old_name:
        cat_dict["(old_name)"] = (old_name, None)

    if random_honor:
        cat_dict["r_h"] = (random_honor, None)

    if "p1" in adjust_text and "p2" in adjust_text and len(living_parents) >= 2:
        cat_dict["p1"] = (
            str(living_parents[0].name),
            choice(living_parents[0].pronouns),
        )
        cat_dict["p2"] = (
            str(living_parents[1].name),
            choice(living_parents[1].pronouns),
        )
    elif living_parents:
        random_living_parent = choice(living_parents)
        cat_dict["p1"] = (
            str(random_living_parent.name),
            choice(random_living_parent.pronouns),
        )
        cat_dict["p2"] = (
            str(random_living_parent.name),
            choice(random_living_parent.pronouns),
        )

    if (
            "dead_par1" in adjust_text
            and "dead_par2" in adjust_text
            and len(dead_parents) >= 2
    ):
        cat_dict["dead_par1"] = (
            str(dead_parents[0].name),
            get_pronouns(dead_parents[0]),
        )
        cat_dict["dead_par2"] = (
            str(dead_parents[1].name),
            get_pronouns(dead_parents[1]),
        )
    elif dead_parents:
        random_dead_parent = choice(dead_parents)
        cat_dict["dead_par1"] = (
            str(random_dead_parent.name),
            get_pronouns(random_dead_parent),
        )
        cat_dict["dead_par2"] = (
            str(random_dead_parent.name),
            get_pronouns(random_dead_parent),
        )

    adjust_text = process_text(adjust_text, cat_dict)

    return adjust_text, random_living_parent, random_dead_parent

def get_pronouns(Cat):
    """ Get a cat's pronoun even if the cat has faded to prevent crashes (use gender-neutral pronouns when the cat has faded) """
    if Cat.pronouns == []:
        return{
            "subject": "they",
            "object": "them",
            "poss": "their",
            "inposs": "theirs",
            "self": "themself",
            "conju": 1,
        }
    else:
        return choice(Cat.pronouns)


def shorten_text_to_fit(
        name, length_limit, font_size=None, font_type="resources/fonts/NotoSans-Medium.ttf"
):
    length_limit = (
        length_limit // 2 if not game.settings["fullscreen"] else length_limit
    )
    # Set the font size based on fullscreen settings if not provided
    # Text box objects are named by their fullscreen text size so it's easier to do it this way
    if font_size is None:
        font_size = 30
    font_size = font_size // 2 if not game.settings["fullscreen"] else font_size
    # Create the font object
    font = pygame.font.Font(font_type, font_size)

    # Add dynamic name lengths by checking the actual width of the text
    total_width = 0
    short_name = ""
    for index, character in enumerate(name):
        char_width = font.size(character)[0]
        ellipsis_width = font.size("...")[0]

        # Check if the current character is the last one and its width is less than or equal to ellipsis_width
        if index == len(name) - 1 and char_width <= ellipsis_width:
            short_name += character
        else:
            total_width += char_width
            if total_width + ellipsis_width > length_limit:
                break
            short_name += character

    # If the name was truncated, add '...'
    if len(short_name) < len(name):
        short_name += "..."

    return short_name


# ---------------------------------------------------------------------------- #
#                                    Sprites                                   #
# ---------------------------------------------------------------------------- #


def scale(rect):
    rect[0] = round(rect[0] / 1600 * screen_x) if rect[0] > 0 else rect[0]
    rect[1] = round(rect[1] / 1400 * screen_y) if rect[1] > 0 else rect[1]
    rect[2] = round(rect[2] / 1600 * screen_x) if rect[2] > 0 else rect[2]
    rect[3] = round(rect[3] / 1400 * screen_y) if rect[3] > 0 else rect[3]

    return rect


def scale_dimentions(dim):
    dim = list(dim)
    dim[0] = round(dim[0] / 1600 * screen_x) if dim[0] > 0 else dim[0]
    dim[1] = round(dim[1] / 1400 * screen_y) if dim[1] > 0 else dim[1]
    dim = tuple(dim)

    return dim


def update_sprite(cat):
    # First, check if the cat is faded.
    if cat.faded:
        # Don't update the sprite if the cat is faded.
        return

    # apply
    cat.sprite = generate_sprite(cat)
    # update class dictionary
    cat.all_cats[cat.ID] = cat


def clan_symbol_sprite(clan, return_string=False, force_light=False):
    """
    returns the clan symbol for the given clan_name, if no symbol exists then random symbol is chosen
    :param clan: the clan object
    :param return_string: default False, set True if the sprite name string is required rather than the sprite image
    :param force_light: Set true if you want this sprite to override the dark/light mode changes with the light sprite
    """
    clan_name = clan.name
    if clan.chosen_symbol:
        if return_string:
            return clan.chosen_symbol
        else:
            if game.settings["dark mode"] and not force_light:
                return sprites.dark_mode_symbol(sprites.sprites[f"{clan.chosen_symbol}"])
            else:
                return sprites.sprites[f"{clan.chosen_symbol}"]
    else:
        possible_sprites = []
        for sprite in sprites.clan_symbols:
            name = sprite.strip("1234567890")
            if f"symbol{clan_name.upper()}" == name:
                possible_sprites.append(sprite)
        if return_string:  # returns the str of the symbol
            if possible_sprites:
                return choice(possible_sprites)
            else:
                # give random symbol if no matching symbol exists
                print(
                    f"WARNING: attempted to return symbol string, but there's no clan symbol for {clan_name.upper()}.  Random symbol string returned."
                )
                return f"{choice(sprites.clan_symbols)}"

        # returns the actual sprite of the symbol
        if possible_sprites:
            if game.settings["dark mode"] and not force_light:
                return sprites.dark_mode_symbol(sprites.sprites[choice(possible_sprites)])
            else:
                return sprites.sprites[choice(possible_sprites)]
        else:
            # give random symbol if no matching symbol exists
            print(
                f"WARNING: attempted to return symbol sprite, but there's no clan symbol for {clan_name.upper()}.  Random symbol sprite returned."
            )
            return sprites.dark_mode_symbol(sprites.sprites[f"{choice(sprites.clan_symbols)}"])


def generate_sprite(
        cat,
        life_state=None,
        scars_hidden=False,
        acc_hidden=False,
        always_living=False,
        no_not_working=False,
) -> pygame.Surface:
    """
    Generates the sprite for a cat, with optional arguments that will override certain things.

    :param life_state: sets the age life_stage of the cat, overriding the one set by its age. Set to string.
    :param scars_hidden: If True, doesn't display the cat's scars. If False, display cat scars.
    :param acc_hidden: If True, hide the accessory. If false, show the accessory.
    :param always_living: If True, always show the cat with living lineart
    :param no_not_working: If true, never use the not_working lineart.
                    If false, use the cat.not_working() to determine the no_working art.
    """

    if life_state is not None:
        age = life_state
    else:
        age = cat.age

    if always_living:
        dead = False
    else:
        dead = cat.dead

    # setting the cat_sprite (bc this makes things much easier)
    if (
            not no_not_working
            and cat.not_working()
            and age != "newborn"
            and game.config["cat_sprites"]["sick_sprites"]
    ):
        if age in ["kitten", "adolescent"]:
            cat_sprite = str(19)
        else:
            cat_sprite = str(18)
    elif cat.pelt.paralyzed and age != "newborn":
        if age in ["kitten", "adolescent"]:
            cat_sprite = str(17)
        else:
            if cat.pelt.length == "long":
                cat_sprite = str(16)
            else:
                cat_sprite = str(15)
    else:
        if age == "elder" and not game.config["fun"]["all_cats_are_newborn"]:
            age = "senior"

        if game.config["fun"]["all_cats_are_newborn"]:
            cat_sprite = str(cat.pelt.cat_sprites["newborn"])
        else:
            cat_sprite = str(cat.pelt.cat_sprites[age])

    new_sprite = pygame.Surface(
        (sprites.size, sprites.size), pygame.HWSURFACE | pygame.SRCALPHA
    )

    # generating the sprite
    try:
        if cat.pelt.name not in ["Tortie", "Calico"]:
            new_sprite.blit(
                sprites.sprites[
                    cat.pelt.get_sprites_name() + cat.pelt.colour + cat_sprite
                    ],
                (0, 0),
            )
        else:
            # Base Coat
            new_sprite.blit(
                sprites.sprites[cat.pelt.tortiebase + cat.pelt.colour + cat_sprite],
                (0, 0),
            )

            # Create the patch image
            if cat.pelt.tortiepattern == "Single":
                tortie_pattern = "SingleColour"
            else:
                tortie_pattern = cat.pelt.tortiepattern

            patches = sprites.sprites[
                tortie_pattern + cat.pelt.tortiecolour + cat_sprite
                ].copy()
            patches.blit(
                sprites.sprites["tortiemask" + cat.pelt.pattern + cat_sprite],
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )

            # Add patches onto cat.
            new_sprite.blit(patches, (0, 0))

        # TINTS
        if (
                cat.pelt.tint != "none"
                and cat.pelt.tint in sprites.cat_tints["tint_colours"]
        ):
            # Multiply with alpha does not work as you would expect - it just lowers the alpha of the
            # entire surface. To get around this, we first blit the tint onto a white background to dull it,
            # then blit the surface onto the sprite with pygame.BLEND_RGB_MULT
            tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            tint.fill(tuple(sprites.cat_tints["tint_colours"][cat.pelt.tint]))
            new_sprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        if cat.pelt.tint != "none" and cat.pelt.tint in sprites.cat_tints["dilute_tint_colours"]:
            tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
            tint.fill(tuple(sprites.cat_tints["dilute_tint_colours"][cat.pelt.tint]))
            new_sprite.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        # draw white patches
        if cat.pelt.white_patches is not None:
            white_patches = sprites.sprites[
                "white" + cat.pelt.white_patches + cat_sprite
                ].copy()

            # Apply tint to white patches.
            if (
                    cat.pelt.white_patches_tint != "none"
                    and cat.pelt.white_patches_tint
                    in sprites.white_patches_tints["tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(
                    tuple(
                        sprites.white_patches_tints["tint_colours"][
                            cat.pelt.white_patches_tint
                        ]
                    )
                )
                white_patches.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

            new_sprite.blit(white_patches, (0, 0))

        # draw vit & points

        if cat.pelt.points:
            points = sprites.sprites["white" + cat.pelt.points + cat_sprite].copy()
            if (
                    cat.pelt.white_patches_tint != "none"
                    and cat.pelt.white_patches_tint
                    in sprites.white_patches_tints["tint_colours"]
            ):
                tint = pygame.Surface((sprites.size, sprites.size)).convert_alpha()
                tint.fill(
                    tuple(
                        sprites.white_patches_tints["tint_colours"][
                            cat.pelt.white_patches_tint
                        ]
                    )
                )
                points.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
            new_sprite.blit(points, (0, 0))

        if cat.pelt.vitiligo:
            new_sprite.blit(
                sprites.sprites["white" + cat.pelt.vitiligo + cat_sprite], (0, 0)
            )

        # draw eyes & scars1
        if cat.pelt.eye_colour != None:
            eyes = sprites.sprites["eyes" + cat.pelt.eye_colour + cat_sprite].copy()
        if cat.pelt.eye_colour2 != None:
            eyes.blit(
                sprites.sprites["eyes2" + cat.pelt.eye_colour2 + cat_sprite], (0, 0)
            )
        new_sprite.blit(eyes, (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.scars1:
                    new_sprite.blit(
                        sprites.sprites["scars" + scar + cat_sprite], (0, 0)
                    )
                if scar in cat.pelt.scars3:
                    new_sprite.blit(
                        sprites.sprites["scars" + scar + cat_sprite], (0, 0)
                    )

        # draw line art
        if game.settings["shaders"] and not dead:
            if game.settings["shaderartisttoggle"]:
                # neon shader
                new_sprite.blit(
                    sprites.sprites["neonshaders" + cat_sprite],
                    (0, 0),
                    special_flags=pygame.BLEND_RGB_MULT
                    )
            elif game.settings["vanillalineart"]:
                # vanilla lineart, do not enable shader with lineart
                new_sprite.blit(
                    sprites.sprites["shadernolineart" + cat_sprite],
                    (0, 0),
                    special_flags=pygame.BLEND_RGB_MULT
                    )
            else:
                # pink shader, no lineart
                new_sprite.blit(
                    sprites.sprites["shaders" + cat_sprite],
                    (0, 0),
                    special_flags=pygame.BLEND_RGB_MULT
                    )
        
        if game.settings["lightinglayer"] and not dead:
            new_sprite.blit(sprites.sprites["lighting" + cat_sprite], (0, 0),
                            special_flags=pygame.BLEND_RGB_ADD)
        if game.settings["vanillalineart"]:
            if not dead:
                new_sprite.blit(sprites.sprites["lines" + cat_sprite], (0, 0))
            elif cat.df:
                new_sprite.blit(sprites.sprites["lineartdf" + cat_sprite], (0, 0))
            elif cat.dead and cat.outside:
                new_sprite.blit(sprites.sprites["lineartur" + cat_sprite], (0, 0))
            elif dead:
                new_sprite.blit(sprites.sprites["lineartdead" + cat_sprite], (0, 0))
        else :
            if not dead:
                new_sprite.blit(sprites.sprites["neonlines" + cat_sprite], (0, 0))
            elif cat.df:
                new_sprite.blit(sprites.sprites["lineartdf" + cat_sprite], (0, 0))
            elif cat.dead and cat.outside:
                new_sprite.blit(sprites.sprites["lineartur" + cat_sprite], (0, 0))
            elif dead:
                new_sprite.blit(sprites.sprites["lineartdead" + cat_sprite], (0, 0))
        # draw skin and scars2
        blendmode = pygame.BLEND_RGBA_MIN
        new_sprite.blit(sprites.sprites["skin" + cat.pelt.skin + cat_sprite], (0, 0))

        if not scars_hidden:
            for scar in cat.pelt.scars:
                if scar in cat.pelt.scars2:
                    new_sprite.blit(
                        sprites.sprites["scars" + scar + cat_sprite],
                        (0, 0),
                        special_flags=blendmode,
                    )

        # draw accessories
        clangen_accessories = ['MAPLE LEAF',
                            'HOLLY',
                            'BLUE BERRIES',
                            'FORGET ME NOTS',
                            'RYE STALK',
                            'LAUREL',
                            'BLUEBELLS',
                            'NETTLE',
                            'POPPY',
                            'LAVENDER',
                            'HERBS',
                            'PETALS',
                            'OAK LEAVES',
                            'CATMINT',
                            'MAPLE SEED',
                            'JUNIPER',
                            'DRY HERBS',
                            'DAISY',
                            'CLOVER',
                            'GORSE',
                            'HEATHER',
                            'SNAPDRAGON',
                            'LILY OF THE VALLEY',
                            'CATTAIL',
                            'WHITE POPPY',
                            'ORANGE POPPY',
                            'PING POPPY',
                            'CYAN POPPY',
                            'BLUB WHITE',
                            'BLUB YELLOW',
                            'BLUB ORANGE',
                            'BLUB PINK',
                            'BLUB BLUE',
                            'RASPBERRY',
                            'RED FEATHERS',
                            'BLUE FEATHERS',
                            'JAY FEATHERS',
                            'MOTH WINGS',
                            'CICADA WINGS',
                            'SPARROW FEATHERS',
                            'GULL FEATHERS',
                            'MONARCH BUTTERFLY',
                            'MORPHO BUTTERFLY',
                            'ROSY MOTH WINGS',
                            'BLACK CICADA'
                            'CRIMSON',
                            'BLUE',
                            'YELLOW',
                            'CYAN',
                            'RED',
                            'LIME',
                            'GREEN',
                            'RAINBOW',
                            'BLACK',
                            'SPIKES',
                            'WHITE',
                            'PINK',
                            'PURPLE',
                            'MULTI',
                            'INDIGO',
                            'CRIMSONBELL',
                            'BLUEBELL',
                            'YELLOWBELL',
                            'CYANBELL',
                            'REDBELL',
                            'LIMEBELL',
                            'GREENBELL',
                            'RAINBOWBELL',
                            'BLACKBELL',
                            'SPIKESBELL',
                            'WHITEBELL',
                            'PINKBELL',
                            'PURPLEBELL',
                            'MULTIBELL',
                            'INDIGOBELL',
                            'CRIMSONBOW',
                            'BLUEBOW',
                            'YELLOWBOW',
                            'CYANBOW',
                            'REDBOW',
                            'LIMEBOW',
                            'GREENBOW',
                            'RAINBOWBOW',
                            'BLACKBOW',
                            'SPIKESBOW',
                            'WHITEBOW',
                            'PINKBOW',
                            'PURPLEBOW',
                            'MULTIBOW',
                            'INDIGOBOW',
                            'CRIMSONNYLON',
                            'BLUENYLON',
                            'YELLOWNYLON',
                            'CYANNYLON',
                            'REDNYLON',
                            'LIMENYLON',
                            'GREENNYLON',
                            'RAINBOWNYLON',
                            'BLACKNYLON',
                            'SPIKESNYLON',
                            'WHITENYLON',
                            'PINKNYLON',
                            'PURPLENYLON',
                            'MULTINYLON',
                            'INDIGONYLON']

        for i in cat.pelt.accessories:
            if i not in clangen_accessories and game.settings['new accessories'] is False \
             and game.settings['neonpink accessories'] is False:
                continue
            if not acc_hidden:
                try:
                    if i in cat.pelt.plant_accessories:
                        new_sprite.blit(sprites.sprites['acc_herbs' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.wild_accessories:
                        new_sprite.blit(sprites.sprites['acc_wild' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.collars:
                        new_sprite.blit(sprites.sprites['collars' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.flower_accessories:
                        new_sprite.blit(sprites.sprites['acc_flower' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.plant2_accessories:
                        new_sprite.blit(sprites.sprites['acc_plant2' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.snake_accessories:
                        new_sprite.blit(sprites.sprites['acc_snake' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.smallAnimal_accessories:
                        new_sprite.blit(sprites.sprites['acc_smallAnimal' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.deadInsect_accessories:
                        new_sprite.blit(sprites.sprites['acc_deadInsect' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.aliveInsect_accessories:
                        new_sprite.blit(sprites.sprites['acc_aliveInsect' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.fruit_accessories:
                        new_sprite.blit(sprites.sprites['acc_fruit' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.crafted_accessories:
                        new_sprite.blit(sprites.sprites['acc_crafted' + i + cat_sprite], (0, 0))
                    elif i in cat.pelt.tail2_accessories:
                        new_sprite.blit(sprites.sprites['acc_tail2' + i + cat_sprite], (0, 0))
                except:
                    continue
            if game.settings['neonpink accessories'] is True:
                try:
                    if i in cat.pelt.np_autism:
                        new_sprite.blit(sprites.sprites['np_autism' + i + cat_sprite], (0, 0))
                except:
                    continue

        # Apply fading fog
        if (
                cat.pelt.opacity <= 97
                and not cat.prevent_fading
                and game.clan.clan_settings["fading"]
                and dead
        ):

            stage = "0"
            if 80 >= cat.pelt.opacity > 45:
                # Stage 1
                stage = "1"
            elif cat.pelt.opacity <= 45:
                # Stage 2
                stage = "2"

            new_sprite.blit(
                sprites.sprites["fademask" + stage + cat_sprite],
                (0, 0),
                special_flags=pygame.BLEND_RGBA_MULT,
            )

            if cat.df:
                temp = sprites.sprites["fadedf" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp
            else:
                temp = sprites.sprites["fadestarclan" + stage + cat_sprite].copy()
                temp.blit(new_sprite, (0, 0))
                new_sprite = temp

        # reverse, if assigned so
        if cat.pelt.reverse:
            new_sprite = pygame.transform.flip(new_sprite, True, False)

    except (TypeError, KeyError):
        logger.exception("Failed to load sprite")

        # Placeholder image
        new_sprite = image_cache.load_image(
            f"sprites/error_placeholder.png"
        ).convert_alpha()

    return new_sprite


def apply_opacity(surface, opacity):
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            pixel = list(surface.get_at((x, y)))
            pixel[3] = int(pixel[3] * opacity / 100)
            surface.set_at((x, y), tuple(pixel))
    return surface


# ---------------------------------------------------------------------------- #
#                                     OTHER                                    #
# ---------------------------------------------------------------------------- #


def chunks(L, n):
    return [L[x: x + n] for x in range(0, len(L), n)]


def is_iterable(y):
    try:
        0 in y
    except TypeError:
        return False


def get_text_box_theme(theme_name=""):
    """Updates the name of the theme based on dark or light mode"""
    if game.settings["dark mode"]:
        if theme_name == "":
            return "#default_dark"
        else:
            return theme_name + "_dark"
    else:
        if theme_name == "":
            return "#text_box"
        else:
            return theme_name

# ---------------------------------------------------------------------------- #
#                            LIFEGEN TEXT ABBREVS                              #
# ---------------------------------------------------------------------------- #


def add_to_cat_dict(abbrev, cluster, x, rel, r, abbrev_cat, text, cat_dict):
    """ Adds a cat to the dict, assigning them to their abbrev to be reused in later text. """

    if cluster and rel:
        cat_dict[f"{r}_{abbrev}_{x}"] = abbrev_cat
        text = re.sub(fr'(?<!\/){r}_{abbrev}_{x}(?!\/)', str(abbrev_cat.name), text)
    elif cluster and not rel:
        cat_dict[f"{abbrev}_{x}"] = abbrev_cat
        text = re.sub(fr'(?<!\/){abbrev}_{x}(?!\/)', str(abbrev_cat.name), text)
    elif rel and not cluster:
        cat_dict[f"{r}_{abbrev}"] = abbrev_cat
        text = re.sub(fr'(?<!\/){r}_{abbrev}(?!\/)', str(abbrev_cat.name), text)
    else:
        cat_dict[f"{abbrev}"] = abbrev_cat
        text = re.sub(fr'(?<!\/){abbrev}(?!\/)', str(abbrev_cat.name), text)
    
    return text


def abbrev_addons(t_c, r_c, cluster, x, rel, r):
    """ Checks if cluster and relationship adodns are fulfilled.
        x = cluster
        r = relationship value
        cluster and rel are booleans for if the addons are present.
    """

    rc_skillpath1 = str(r_c.skills.primary.path) if r_c.skills.primary else None
    rc_skillpath2 = str(r_c.skills.secondary.path) if r_c.skills.secondary else None

    if rc_skillpath1:
        rc_skill1 = rc_skillpath1.split(".")[1].lower()
    else:
        rc_skill1 = "none"
    if rc_skillpath2:
        rc_skill2 = rc_skillpath2.split(".")[1].lower()
    else:
        rc_skill2 = "any"

    if (
        cluster and (
            x not in get_cluster(r_c.personality.trait) and
            x != r_c.personality.trait and
            x not in [rc_skill1, rc_skill2])
        ):
        return False
    
    if (
            (
            rel and (
                r_c.ID not in t_c.relationships) or
                (r == "plike" and t_c.relationships[r_c.ID].platonic_like < 20) or
                (r == "plove" and t_c.relationships[r_c.ID].platonic_like < 50) or
                (r == "rlike" and t_c.relationships[r_c.ID].romantic_love < 10) or
                (r == "rlove" and t_c.relationships[r_c.ID].romantic_love < 50) or
                (r == "dislike" and t_c.relationships[r_c.ID].dislike < 15) or
                (r == "hate" and t_c.relationships[r_c.ID].dislike < 50) or
                (r == "jealous" and t_c.relationships[r_c.ID].jealousy < 20) or
                (r == "trust" and t_c.relationships[r_c.ID].trust < 20) or
                (r == "comfort" and t_c.relationships[r_c.ID].comfortable < 20) or 
                (r == "respect" and t_c.relationships[r_c.ID].admiration < 20) or 
                (r == "toxicity" and t_c.relationships[r_c.ID].toxicity < 20) or
                (r == "abusive" and t_c.relationships[r_c.ID].toxicity < 60) or
                (r == "neutral" and
                (
                    (t_c.relationships[r_c.ID].platonic_like > 20) or
                    (t_c.relationships[r_c.ID].romantic_love > 20) or
                    (t_c.relationships[r_c.ID].dislike > 20) or
                    (t_c.relationships[r_c.ID].jealousy > 20) or
                    (t_c.relationships[r_c.ID].trust > 20) or
                    (t_c.relationships[r_c.ID].comfortable > 20) or
                    (t_c.relationships[r_c.ID].admiration > 20) or
                    (t_c.relationships[r_c.ID].toxicity > 20)
                    )
                )
            )
        ):
        print("abbrev addon failed")
        return False
    return True

def cat_dict_check(abbrev, cluster, x, rel, r, text, cat_dict):
    """ Checks if a cat is in the dict already.
    If so, it will reuse the name in later text.
    If not, it will find a cat for the abbrev."""
    in_dict = False
    try:
        if f"{abbrev}_{x}" in cat_dict or f"{abbrev}" in cat_dict or f"{r}_{abbrev}" in cat_dict or f"{r}_{abbrev}_{x}" in cat_dict:
            in_dict = True
            if cluster and rel:
                text = re.sub(fr'(?<!\/){r}_{abbrev}_{x}(?!\/)', str(cat_dict[f"{r}_{abbrev}_{x}"].name), text)
            elif cluster and not rel:
                text = re.sub(fr'(?<!\/){abbrev}_{x}(?!\/)', str(cat_dict[f"{abbrev}_{x}"].name), text)
            elif rel and not cluster:
                text = re.sub(fr'(?<!\/){r}_{abbrev}(?!\/)', str(cat_dict[f"{r}_{abbrev}"].name), text)
            else:
                text = re.sub(fr'(?<!\/){abbrev}(?!\/)', str(cat_dict[f"{abbrev}"].name), text)
    except KeyError:
        print("WARNING: Keyerror with", abbrev, ".")
        text = ""
        # returning an empty string to reroll for dialogue
    return text, in_dict

def in_dict_check_2(chosen_cat, cat_dict):
    """ Checks if a cat is already in the cat dict as another abbrev.
    So r_c and r_w, for example, don't end up being the same cat. """

    already_there = False
    for item in cat_dict.items():
        if item[1] == chosen_cat:
            already_there = True
            break

    return already_there

other_dict = {}   
def adjust_txt(Cat, text, cat, cat_dict, r_c_allowed, o_c_allowed):
    """ Adjusts dialogue text by replacing abbreviations with cat names
    :param Cat Cat: Cat class
    :param list text: The text being processed 
    :param Cat cat: The object of the cat to whom relationship addons will apply
    :param Dict cat_dict: the dict of cat objects
    :param bool r_c_allowed: Whether or not r_c will be tried for. True for dialogue, False for patrols
    :param bool o_c_allowed: Whether or not o_c will be tried for. True for dialogue, False for patrols
    """

    COUNTER_LIM = 30
    you = game.clan.your_cat
    # try:
    if "your_crush" in text:
        cluster = False
        rel = False
        match = re.search(r'your_crush(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)your_crush', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        text, in_dict = cat_dict_check("your_crush", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if len(you.mate) > 0 or you.no_mates:
                return ""
            crush = None
            for c in get_alive_cats(Cat):
                addon_check = abbrev_addons(cat, c, cluster, x, rel, r)

                skip = False
                in_dict_2 = in_dict_check_2(c, cat_dict)
                if in_dict_2 is True:
                    skip = True

                if c.ID == you.ID or c.ID == cat.ID or c.ID in cat.mate or c.ID in you.mate or c.age != you.age or\
                addon_check is False or skip is True:
                    continue
                relations = you.relationships.get(c.ID)
                if not relations:
                    continue
                if relations.romantic_love > 10:
                    crush = c
                    break
            if crush:
                text = add_to_cat_dict("your_crush", cluster, x, rel, r, crush, text, cat_dict)
            else:
                return ""

    if "their_crush" in text:
        cluster = False
        rel = False
        match = re.search(r'their_crush(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)their_crush', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("their_crush", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if len(cat.mate) > 0 or cat.no_mates:
                return ""
            crush = None
            for c in get_alive_cats(Cat):
                addon_check = abbrev_addons(cat, c, cluster, x, rel, r)

                skip = False
                in_dict_2 = in_dict_check_2(c, cat_dict)
                if in_dict_2 is True:
                    skip = True

                if c.ID == you.ID or c.ID == cat.ID or c.ID in cat.mate or c.ID in you.mate or c.age != cat.age or\
                addon_check is False or skip is True:
                    continue
                relations = cat.relationships.get(c.ID)
                if not relations:
                    continue
                if relations.romantic_love > 10:
                    crush = c
                    break
            if crush:
                text = add_to_cat_dict("their_crush", cluster, x, rel, r, crush, text, cat_dict)
            else:
                return ""

    # Multiple random cats
    for i in range(0,4):
        # Random cats
        r_c_str = f"r_c{i}"
        if r_c_str in text:
            cluster = False
            rel = False
            match = re.search(fr'r_c{i}(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""

            match2 = re.search(fr'(\w+)r_c{i}', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""

            text, in_dict = cat_dict_check(r_c_str, cluster, x, rel, r, text, cat_dict)

            if in_dict is False:
                alive_cats = get_alive_cats(Cat)
                if len(alive_cats) < 3:
                    return ""
                alive_cat = choice(alive_cats)
                addon_check = abbrev_addons(cat, alive_cat, cluster, x, rel, r)
                
                skip = False
                in_dict_2 = in_dict_check_2(alive_cat, cat_dict)
                if in_dict_2 is True:
                    skip = True

                counter = 0

                while (alive_cat.ID == you.ID or alive_cat.ID == cat.ID or addon_check is False\
                or alive_cat in list(cat_dict.values())) or skip is True:
                    alive_cat = choice(alive_cats)
                    addon_check = abbrev_addons(cat, alive_cat, cluster, x, rel, r)
                    skip = False
                    in_dict_2 = in_dict_check_2(alive_cat, cat_dict)
                    if in_dict_2 is True:
                        skip = True
                    counter += 1
                    if counter >= 30:
                        return ""
                text = add_to_cat_dict(f"r_c{i}", cluster, x, rel, r, alive_cat, text, cat_dict)

        # Random warriors
        r_w_str = f"r_w{i}"
        if r_w_str in text:
            cluster = False
            rel = False
            match = re.search(fr'r_w{i}(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""

            match2 = re.search(fr'(\w+)r_w{i}', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""

            text, in_dict = cat_dict_check(f"r_w{i}", cluster, x, rel, r, text, cat_dict)
                
            alive_cats = get_alive_status_cats(Cat, ["warrior"])
            if len(alive_cats) < 3:
                return ""
            alive_cat = choice(alive_cats)
            addon_check = abbrev_addons(cat, alive_cat, cluster, x, rel, r)
            
            skip = False
            in_dict_2 = in_dict_check_2(alive_cat, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0
            while (alive_cat.ID == you.ID or alive_cat.ID == cat.ID or addon_check is False\
            or alive_cat in list(cat_dict.values())) or skip is True:
                alive_cat = choice(alive_cats)
                addon_check = abbrev_addons(cat, alive_cat, cluster, x, rel, r)
                skip = False
                in_dict_2 = in_dict_check_2(alive_cat, cat_dict)
                if in_dict_2 is True:
                    skip = True
                counter += 1
                if counter > COUNTER_LIM:
                    return ""
            text = add_to_cat_dict(f"r_w{i}", cluster, x, rel, r, alive_cat, text, cat_dict)
    
    # Random cats who are potential mates
    if "n_r1" in text:
        if "n_r2" not in text:
            return ""
        cluster1 = False
        rel1 = False
        cluster2 = False
        rel2 = False
        match = re.search(fr'n_r1{i}(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster1 = True
        else:
            x = ""
        match2 = re.search(fr'(\w+)n_r1{i}', text)
        if match2:
            r = match2.group(1).strip("_")
            rel1 = True
        else:
            r = ""
        match3 = re.search(fr'n_r2{i}(\w+)', text)
        if match:
            x = match3.group(1).strip("_")
            cluster2 = True
        else:
            x = ""
        match4 = re.search(fr'(\w+)n_r2{i}', text)
        if match2:
            r = match4.group(1).strip("_")
            rel2 = True
        else:
            r = ""

        random_cat1 = choice(get_alive_cats(Cat))
        random_cat2 = choice(get_alive_cats(Cat))

        addon_check1 = abbrev_addons(cat, random_cat1, cluster1, x, rel1, r)
        addon_check2 = abbrev_addons(cat, random_cat2, cluster2, x, rel2, r)
        
        skip1 = False
        in_dict_2 = in_dict_check_2(random_cat1, cat_dict)
        if in_dict_2 is True:
            skip1 = True
        
        skip2 = False
        in_dict_2 = in_dict_check_2(random_cat2, cat_dict)
        if in_dict_2 is True:
            skip2 = True


        counter = 0

        while (random_cat1.ID == you.ID or random_cat1.ID == cat.ID or addon_check1 is False or\
        not random_cat1.is_potential_mate(random_cat2) or random_cat2.age != random_cat1.age) or \
        (random_cat2.ID == you.ID or random_cat2.ID == cat.ID or addon_check2 is False or\
        not random_cat2.is_potential_mate(random_cat1)) or skip1 is True or skip2 is True:
            
            random_cat1 = choice(get_alive_cats(Cat))
            random_cat2 = choice(get_alive_cats(Cat))
            addon_check1 = abbrev_addons(cat, random_cat1, cluster1, x, rel1, r)
            addon_check2 = abbrev_addons(cat, random_cat2, cluster2, x, rel2, r)

            skip1 = False
            in_dict_2 = in_dict_check_2(random_cat1, cat_dict)
            if in_dict_2 is True:
                skip1 = True
            
            skip2 = False
            in_dict_2 = in_dict_check_2(random_cat2, cat_dict)
            if in_dict_2 is True:
                skip2 = True

            counter +=1
            if counter > 40:
                return ""
        if random_cat1.ID == you.ID or random_cat1.ID == cat.ID or random_cat2.ID == you.ID or random_cat2.ID == cat.ID:
            return ""
        
        text = add_to_cat_dict("n_r1", cluster1, x, rel1, r, random_cat1, text, cat_dict)
        text = add_to_cat_dict("n_r2", cluster2, x, rel2, r, random_cat2, text, cat_dict)

    # Random kit
    if "r_k" in text:
        cluster = False
        rel = False
        match = re.search(r'r_k(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""

        match2 = re.search(r'(\w+)r_k', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("r_k", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_kits = get_alive_status_cats(Cat, ["kitten", "newborn"])
            if len(alive_kits) <= 0:
                return ""

            alive_kit = choice(alive_kits)
            addon_check = abbrev_addons(cat, alive_kit, cluster, x, rel, r)

            skip = False
            in_dict_2 = in_dict_check_2(alive_kit, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0

            while (alive_kit.ID == you.ID or alive_kit.ID == cat.ID or addon_check is False) or skip is True:
                counter += 1
                alive_kit = choice(alive_kits)
                addon_check = abbrev_addons(cat, alive_kit, cluster, x, rel, r)
                
                skip = False
                in_dict_2 = in_dict_check_2(alive_kit, cat_dict)
                if in_dict_2 is True:
                    skip = True

                if counter >= 30:
                    return ""
                
            text = add_to_cat_dict("r_k", cluster, x, rel, r, alive_kit, text, cat_dict)
    
    # Random warrior apprentice
    if "r_a" in text:
        cluster = False
        rel = False
        match = re.search(r'r_a(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""

        match2 = re.search(r'(\w+)r_a', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("r_a", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_apps = get_alive_status_cats(Cat, ["apprentice"])
            if len(alive_apps) <= 0:
                return ""

            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)

            skip = False
            in_dict_2 = in_dict_check_2(alive_app, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0
            
            while alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or skip is True:
                counter += 1
                if counter >= 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                    
                skip = False
                in_dict_2 = in_dict_check_2(alive_app, cat_dict)
                if in_dict_2 is True:
                    skip = True

            
            text = add_to_cat_dict("r_a", cluster, x, rel, r, alive_app, text, cat_dict)
    
    # Random warriors
    if "r_w" in text and "r_w1" not in text and "r_w2" not in text and "r_w3" not in text:
        cluster = False
        rel = False
        match = re.search(r'r_w(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""

        match2 = re.search(r'(\w+)r_w', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("r_w", cluster, x, rel, r, text, cat_dict)
        
        
        if in_dict is False:
            alive_apps = get_alive_status_cats(Cat, ["warrior"])
            if len(alive_apps) <= 0:
                return ""

            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            
            skip = False
            in_dict_2 = in_dict_check_2(alive_app, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0
            
            while alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or skip is True:
                counter += 1
                if counter >= 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                    
                skip = False
                in_dict_2 = in_dict_check_2(alive_app, cat_dict)
                if in_dict_2 is True:
                    skip = True


            text = add_to_cat_dict("r_w", cluster, x, rel, r, alive_app, text, cat_dict)

    # Random medicine cat or medicine cat apprentice
    if "r_m" in text:
        cluster = False
        rel = False
        match = re.search(r'r_m(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)r_m', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("r_m", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_apps = get_alive_status_cats(Cat, ["medicine cat", "medicine cat apprentice"])
            if len(alive_apps) <= 0:
                return ""
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            
            skip = False
            in_dict_2 = in_dict_check_2(alive_app, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0

            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False) or skip is True:
                counter += 1
                if counter == 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                
                skip = False
                in_dict_2 = in_dict_check_2(alive_app, cat_dict)
                if in_dict_2 is True:
                    skip = True


            text = add_to_cat_dict("r_m", cluster, x, rel, r, alive_app, text, cat_dict)

    # Random mediator or mediator apprentice
    if "r_d" in text:
        cluster = False
        rel = False
        match = re.search(r'r_d(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)r_d', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        
        text, in_dict = cat_dict_check("r_d", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_apps = get_alive_status_cats(Cat, ["mediator", "mediator apprentice"])
            if len(alive_apps) <= 0:
                return ""
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            
            skip = False
            in_dict_2 = in_dict_check_2(alive_app, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0

            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False) or skip is True:
                counter += 1
                if counter == 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                
                skip = False
                in_dict_2 = in_dict_check_2(alive_app, cat_dict)
                if in_dict_2 is True:
                    skip = True

            
            text = add_to_cat_dict("r_d", cluster, x, rel, r, alive_app, text, cat_dict)

    # Random queen or queen's apprentice
    if "r_q" in text:
        cluster = False
        rel = False
        match = re.search(r'r_q(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)r_q', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("r_q", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_apps = get_alive_status_cats(Cat, ["queen", "queen's apprentice"])
            if len(alive_apps) <= 0:
                return ""
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            
            skip = False
            in_dict_2 = in_dict_check_2(alive_app, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0

            while alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or skip is True:
                counter += 1
                if counter == 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                
                skip = False
                in_dict_2 = in_dict_check_2(alive_app, cat_dict)
                if in_dict_2 is True:
                    skip = True


            text = add_to_cat_dict("r_q", cluster, x, rel, r, alive_app, text, cat_dict)

    # Random elder
    if "r_e" in text:
        cluster = False
        rel = False
        match = re.search(r'r_e(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)r_e', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        
        text, in_dict = cat_dict_check("r_e", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_apps = get_alive_status_cats(Cat, ["elder"])
            if len(alive_apps) <= 0:
                return ""
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            
            skip = False
            in_dict_2 = in_dict_check_2(alive_app, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0
            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False) or skip is True:
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                    
                skip = False
                in_dict_2 = in_dict_check_2(alive_app, cat_dict)
                if in_dict_2 is True:
                    skip = True

                counter += 1
                if counter == 30:
                    return ""
                
            text = add_to_cat_dict("r_e", cluster, x, rel, r, alive_app, text, cat_dict)
    
    # Random sick cat
    if "r_s" in text:
        cluster = False
        rel = False
        match = re.search(r'r_s(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)r_s', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        
        text, in_dict = cat_dict_check("r_s", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_apps = get_alive_cats(Cat)
            if len(alive_apps) <= 0:
                return ""
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            
            skip = False
            in_dict_2 = in_dict_check_2(alive_app, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0
            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or not alive_app.is_ill()) or skip is True:
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                    
                skip = False
                in_dict_2 = in_dict_check_2(alive_app, cat_dict)
                if in_dict_2 is True:
                    skip = True

                counter += 1
                if counter == 30:
                    return ""
            text = add_to_cat_dict("r_s", cluster, x, rel, r, alive_app, text, cat_dict)

    # Random injured cat
    if "r_i" in text:
        cluster = False
        rel = False
        match = re.search(r'r_i(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)r_i', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        
        text, in_dict = cat_dict_check("r_i", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_apps = get_alive_cats(Cat)
            if len(alive_apps) <= 0:
                return ""
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            
            skip = False
            in_dict_2 = in_dict_check_2(alive_app, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0
            while alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or not alive_app.is_injured() or skip is True:
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                
                skip = False
                in_dict_2 = in_dict_check_2(alive_app, cat_dict)
                if in_dict_2 is True:
                    skip = True

                counter += 1
                if counter == 30:
                    return ""
            text = add_to_cat_dict("r_i", cluster, x, rel, r, alive_app, text, cat_dict)
    # random grieving cat
    if "r_g" in text:
        cluster = False
        rel = False
        match = re.search(r'r_g(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)r_g', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        
        text, in_dict = cat_dict_check("r_g", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_apps = get_alive_cats(Cat)
            if len(alive_apps) <= 0:
                return ""
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            
            skip = False
            in_dict_2 = in_dict_check_2(alive_app, cat_dict)
            if in_dict_2 is True:
                skip = True

            counter = 0
            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or "grief stricken" not in alive_app.illnesses) or skip is True:
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                    
                skip = False
                in_dict_2 = in_dict_check_2(alive_app, cat_dict)
                if in_dict_2 is True:
                    skip = True

                counter += 1
                if counter == 40:
                    return ""
            text = add_to_cat_dict("r_g", cluster, x, rel, r, alive_app, text, cat_dict)

    # Your sibling-- any age
    if "y_s" in text:
        cluster = False
        rel = False
        match = re.search(r'y_s(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)y_s', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        
        text, in_dict = cat_dict_check("y_s", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if len(you.inheritance.get_siblings()) == 0:
                return ""
            counter = 0
            sibling = Cat.fetch_cat(choice(you.inheritance.get_siblings()))
            addon_check = abbrev_addons(cat, sibling, cluster, x, rel, r)

            while sibling.outside or sibling.dead or sibling.ID == game.clan.your_cat.ID or sibling.ID == cat.ID or\
            addon_check is False:
                counter += 1
                if counter > COUNTER_LIM:
                    return ""
                sibling = Cat.fetch_cat(choice(you.inheritance.get_siblings()))
                addon_check = abbrev_addons(cat, sibling, cluster, x, rel, r)

            text = add_to_cat_dict("y_s", cluster, x, rel, r, sibling, text, cat_dict)

    # your littermate
    if "y_l" in text:
        cluster = False
        rel = False
        match = re.search(r'y_l(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)y_l', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        
        text, in_dict = cat_dict_check("y_l", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if len(you.inheritance.get_siblings()) == 0:
                return ""
            counter = 0
            sibling = Cat.fetch_cat(choice(you.inheritance.get_siblings()))
            addon_check = abbrev_addons(cat, sibling, cluster, x, rel, r)
            while sibling.outside or sibling.dead or sibling.ID == you.ID or sibling.ID == cat.ID or sibling.moons != cat.moons or addon_check is False:
                counter += 1
                if counter > COUNTER_LIM:
                    return ""
                sibling = Cat.fetch_cat(choice(you.inheritance.get_siblings()))
                addon_check = abbrev_addons(cat, sibling, cluster, x, rel, r)

            text = add_to_cat_dict("y_l", cluster, x, rel, r, sibling, text, cat_dict)

    # Their sibling-- any age
    if "t_s" in text:
        cluster = False
        rel = False
        match = re.search(r't_s(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)t_s', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        
        text, in_dict = cat_dict_check("t_s", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if len(cat.inheritance.get_siblings()) == 0:
                return ""
            sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
            addon_check = abbrev_addons(cat, sibling, cluster, x, rel, r)
            counter = 0
            while sibling.outside or sibling.dead or sibling.ID == game.clan.your_cat.ID or sibling.ID == cat.ID or\
            addon_check is False:
                counter += 1
                if counter > COUNTER_LIM:
                    return ""
                sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                addon_check = abbrev_addons(cat, sibling, cluster, x, rel, r)
            
            text = add_to_cat_dict("t_s", cluster, x, rel, r, sibling, text, cat_dict)

    # their littermate
    if "t_l" in text:
        cluster = False
        rel = False
        match = re.search(r't_l(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)t_l', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        
        text, in_dict = cat_dict_check("t_l", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if len(cat.inheritance.get_siblings()) == 0:
                return ""
            sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
            addon_check = abbrev_addons(cat, sibling, cluster, x, rel, r)
            counter = 0

            while sibling.outside or sibling.dead or sibling.ID == game.clan.your_cat.ID or sibling.ID == cat.ID or sibling.moons != cat.moons or addon_check is False:
                counter += 1
                if counter > COUNTER_LIM:
                    return ""
                sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                addon_check = abbrev_addons(cat, sibling, cluster, x, rel, r)

            text = add_to_cat_dict("t_l", cluster, x, rel, r, sibling, text, cat_dict)

    # Your apprentice
    if "y_a" in text:
        cluster = False
        rel = False
        match = re.search(r'y_a(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)y_a', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        if cat.mentor is None or cat.mentor == you.ID:
            return ""
        text, in_dict = cat_dict_check("y_a", cluster, x, rel, r, text, cat_dict)
        

        your_app = Cat.fetch_cat(choice(you.apprentice))
        cat_dict["y_a"] = your_app
        addon_check = abbrev_addons(cat, your_app, cluster, x, rel, r)
        if addon_check is False:
            return ""

        text = add_to_cat_dict("y_a", cluster, x, rel, r, your_app, text, cat_dict)

    # Their apprentice
    if "t_a" in text:
        cluster = False
        rel = False
        match = re.search(r't_a(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)t_a', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        if cat.mentor is None or cat.mentor == you.ID:
            return ""
        text, in_dict = cat_dict_check("t_a", cluster, x, rel, r, text, cat_dict)
        

        their_app = Cat.fetch_cat(choice(cat.apprentice))
        cat_dict["t_a"] = their_app
        addon_check = abbrev_addons(cat, their_app, cluster, x, rel, r)
        if addon_check is False:
            return ""

        text = add_to_cat_dict("t_a", cluster, x, rel, r, their_app, text, cat_dict)

    # Your parent
    if "y_p" in text:
        cluster = False
        rel = False
        match = re.search(r'y_p(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)y_p', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("y_p", cluster, x, rel, r, text, cat_dict)

        if in_dict is False:
            try:
                parent = Cat.fetch_cat(choice(you.inheritance.get_parents()))
            except:
                return ""
            addon_check = abbrev_addons(cat, parent, cluster, x, rel, r)

            if len(you.inheritance.get_parents()) == 0 or parent.outside or parent.dead or parent.ID == cat.ID or\
            addon_check is False:
                return ""
            
            in_dict_2 = in_dict_check_2(parent, cat_dict)
            if in_dict_2 is True:
                return ""
            
            text = add_to_cat_dict("y_p", cluster, x, rel, r, parent, text, cat_dict)

    # Their parent
    if "t_p_positive" in text or "t_p_negative" in text or "t_p" in text:
        if "t_p_positive" in cat_dict:
            text = re.sub(r'(?<!\/)t_p_positive(?!\/)', str(cat_dict["t_p_positive"].name), text)
        if "t_p_negative" in cat_dict:
            text = re.sub(r'(?<!\/)t_p_negative(?!\/)', str(cat_dict["t_p_negative"].name), text)
        if "t_p" in cat_dict:
            text = re.sub(r'(?<!\/)t_p(?!\/)', str(cat_dict["t_p"].name), text)
        if "t_p_positive" not in cat_dict or "t_p_negative" not in cat_dict or "t_p" not in cat_dict:
            if len(cat.inheritance.get_parents()) == 0:
                return ""
            parent = Cat.fetch_cat(choice(cat.inheritance.get_parents()))
            counter = 0
            while parent.outside or parent.dead or parent.ID == you.ID:
                counter += 1
                if counter > COUNTER_LIM:
                    return ""
                parent = Cat.fetch_cat(choice(cat.inheritance.get_parents()))
            if parent.relationships and cat.ID in parent.relationships and parent.relationships[cat.ID].dislike > 10 and "t_p_negative" in text:
                cat_dict["t_p_negative"] = parent
                text = re.sub(r'(?<!\/)t_p_negative(?!\/)', str(parent.name), text)
            else:
                return ""
            if parent.relationships and cat.ID in parent.relationships and parent.relationships[cat.ID].platonic_like > 10 and "t_p_positive" in text:
                cat_dict["t_p_positive"] = parent
                text = re.sub(r'(?<!\/)t_p_positive(?!\/)', str(parent.name), text)
            else:
                return ""
            if parent.relationships and cat.ID in parent.relationships and parent.relationships[cat.ID].platonic_like > 10 and "t_o" in text:
                cat_dict["t_p"] = parent
                text = re.sub(r'(?<!\/)t_p(?!\/)', str(parent.name), text)
            else:
                return ""
    
    # Your mate
    if "y_m" in text:
        cluster = False
        rel = False
        match = re.search(r'y_m(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)y_m', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        text, in_dict = cat_dict_check("y_m", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if you.mate:
                mate0 = Cat.fetch_cat(choice(you.mate))
            else:
                return ""
            addon_check = abbrev_addons(cat, mate0, cluster, x, rel, r)

            if you.mate is None or len(you.mate) == 0 or you.ID in cat.mate or addon_check is False:
                return ""
            if mate0.outside or mate0.dead:
                return ""
            
            text = add_to_cat_dict("y_m", cluster, x, rel, r, mate0, text, cat_dict)

    # Their mate
    if "t_m" in text:
        cluster = False
        rel = False
        match = re.search(r't_m(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)t_m', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        text, in_dict = cat_dict_check("t_m", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if cat.mate:
                mate1 = Cat.fetch_cat(choice(cat.mate))
            else:
                return ""
            addon_check = abbrev_addons(cat, mate1, cluster, x, rel, r)

            if cat.mate is None or len(cat.mate) == 0 or cat.ID in you.mate or addon_check is False:
                return ""
            if mate1.outside or mate1.dead:
                return ""
            
            text = add_to_cat_dict("t_m", cluster, x, rel, r, mate1, text, cat_dict)

    # Their adult kit
    if "t_ka" in text:
        cluster = False
        rel = False
        match = re.search(r't_ka(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)t_ka', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        text, in_dict = cat_dict_check("t_ka", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if cat.inheritance.get_children() is None or len(cat.inheritance.get_children()) == 0:
                return ""
            
            kit = Cat.fetch_cat(choice(cat.inheritance.get_children()))
            addon_check = abbrev_addons(cat, kit, cluster, x, rel, r)

            if kit.moons < 12 or kit.outside or kit.dead or kit.ID == cat.ID or kit.ID == you.ID or\
            addon_check is False:
                return ""
            
            text = add_to_cat_dict("t_ka", cluster, x, rel, r, kit, text, cat_dict)

    # Their kitten kit
    if "t_kk" in text:
        cluster = False
        rel = False
        match = re.search(r't_kk(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)t_kk', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        text, in_dict = cat_dict_check("t_kk", cluster, x, rel, r, text, cat_dict)

        if in_dict is False:
            if cat.inheritance.get_children() is None or len(cat.inheritance.get_children()) == 0:
                return ""
            
            kit = Cat.fetch_cat(choice(cat.inheritance.get_children()))
            addon_check = abbrev_addons(cat, kit, cluster, x, rel, r)

            if kit.moons >= 6 or kit.outside or kit.dead or kit.ID == cat.ID or kit.ID == you.ID or\
            addon_check is False:
                return ""
            
            text = add_to_cat_dict("t_kk", cluster, x, rel, r, kit, text, cat_dict)

    # Their kit
    if "t_k" in text and "t_kk" not in text and "t_ka" not in text:
        cluster = False
        rel = False
        match = re.search(r't_k(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)t_k', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        text, in_dict = cat_dict_check("t_k", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if cat.inheritance.get_children() is None or len(cat.inheritance.get_children()) == 0:
                return ""
            
            kit = Cat.fetch_cat(choice(cat.inheritance.get_children()))
            addon_check = abbrev_addons(cat, kit, cluster, x, rel, r)

            if kit.outside or kit.dead or kit.ID == cat.ID or kit.ID == you.ID or addon_check is False:
                return ""
            
            text = add_to_cat_dict("t_k", cluster, x, rel, r, kit, text, cat_dict)

    # Your kit
    if "y_k" in text and "y_kk" not in text:
        cluster = False
        rel = False
        match = re.search(r'y_k(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)y_k', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        text, in_dict = cat_dict_check("y_k", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if you.inheritance.get_children() is None or len(you.inheritance.get_children()) == 0:
                return ""
            
            kit = Cat.fetch_cat(choice(you.inheritance.get_children()))
            addon_check = abbrev_addons(cat, kit, cluster, x, rel, r)

            if kit.outside or kit.dead or kit.ID == cat.ID or addon_check is False:
                return ""
            
            text = add_to_cat_dict("r_w", cluster, x, rel, r, kit, text, cat_dict)

    # Your kit-- kitten age
    if "y_kk" in text:
        cluster = False
        rel = False
        match = re.search(r'y_kk(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)y_kk', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        text, in_dict = cat_dict_check("y_kk", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if you.inheritance.get_children() is None or len(you.inheritance.get_children()) == 0:
                return ""
            
            kit = Cat.fetch_cat(choice(you.inheritance.get_children()))
            addon_check = abbrev_addons(cat, kit, cluster, x, rel, r)

            if kit.moons >= 6 or kit.outside or kit.dead or kit.ID == cat.ID or addon_check is False:
                return ""
            
            text = add_to_cat_dict("y_kk", cluster, x, rel, r, kit, text, cat_dict)
    
    # Random cat
    if r_c_allowed is True:
        if "r_c" in text and "r_c1" not in text and "r_c2" not in text and "r_c3" not in text and "r_c4" not in text:
            cluster = False
            rel = False
            match = re.search(r'r_c(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)r_c', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
        
            text, in_dict = cat_dict_check("r_c", cluster, x, rel, r, text, cat_dict)

            if in_dict is False:
                random_cat = choice(get_alive_cats(Cat))
                addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)

                counter = 0
                while random_cat.ID == you.ID or random_cat.ID == cat.ID or addon_check is False:
                    if counter == 30:
                        return ""
                    random_cat = choice(get_alive_cats(Cat))
                    addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)
                    counter += 1

                text = add_to_cat_dict("r_c", cluster, x, rel, r, random_cat, text, cat_dict)
    # Other Clan
    if o_c_allowed is True:
        if "o_c" in text:
            if "o_c" in other_dict:
                text = re.sub(r'(?<!\/)o_c(?!\/)', str(other_dict["o_c"].name), text)
            else:
                other_clan = choice(game.clan.all_clans)
                if not other_clan:
                    return ""
                other_dict["o_c"] = other_clan
                text = re.sub(r'(?<!\/)o_c(?!\/)', str(other_clan.name), text)

    # Your DF Mentor
    if "df_m_n" in text:
        cluster = False
        rel = False
        match = re.search(r'df_m_n(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)df_m_n', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        if you.joined_df and not you.dead and you.df_mentor and cat.ID != you.df_mentor and not Cat.all_cats.get(you.df_mentor) is None:
            text, in_dict = cat_dict_check("df_m_n", cluster, x, rel, r, text, cat_dict)
            cat_dict["df_m_n"] = Cat.all_cats.get(you.df_mentor)
            text = add_to_cat_dict("df_m_n", cluster, x, rel, r, Cat.fetch_cat(you.df_mentor), text, cat_dict)
        else:
            return ""
        
    # Their mentor
    if "tm_n" in text:
        cluster = False
        rel = False
        match = re.search(r'tm_n(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)tm_n', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        if cat.mentor is None or cat.mentor == you.ID:
            return ""
        text, in_dict = cat_dict_check("tm_n", cluster, x, rel, r, text, cat_dict)
        

        cat_dict["tm_n"] = Cat.fetch_cat(cat.mentor)
        addon_check = abbrev_addons(cat, Cat.fetch_cat(cat.mentor), cluster, x, rel, r)
        if addon_check is False:
            return ""

        text = add_to_cat_dict("tm_n", cluster, x, rel, r, Cat.fetch_cat(cat.mentor), text, cat_dict)

    # Your mentor
    elif "m_n" in text:
        cluster = False
        rel = False
        match = re.search(r'm_n(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)m_n', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        if you.mentor is None or you.mentor == cat.ID:
            return ""
        text, in_dict = cat_dict_check("m_n", cluster, x, rel, r, text, cat_dict)
        

        cat_dict["m_n"] = Cat.fetch_cat(you.mentor)
        addon_check = abbrev_addons(cat, Cat.fetch_cat(you.mentor), cluster, x, rel, r)
        if addon_check is False:
            return ""
        text = add_to_cat_dict("m_n", cluster, x, rel, r, Cat.fetch_cat(you.mentor), text, cat_dict)

    # Their DF metnor
    if "t_df_mn" in text:
        cluster = False
        rel = False
        match = re.search(r't_df_mn(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)t_df_mn', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        if cat.joined_df and not cat.dead and cat.df_mentor:
            text, in_dict = cat_dict_check("t_df_mn", cluster, x, rel, r, text, cat_dict)
            cat_dict["t_df_mn"] = Cat.all_cats.get(cat.df_mentor)
            addon_check = abbrev_addons(cat, Cat.fetch_cat(cat.df_mentor), cluster, x, rel, r)
        if addon_check is False:
            return ""
        text = add_to_cat_dict("t_df_mn", cluster, x, rel, r, Cat.fetch_cat(cat.df_mentor), text, cat_dict)
    
    # Clan leader's name
    if "l_n" in text:
        cluster = False
        rel = False
        match = re.search(r'l_n(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)l_n', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        if game.clan.leader is None:
            return ""
        addon_check = abbrev_addons(cat, game.clan.leader, cluster, x, rel, r)
        if game.clan.leader.dead or game.clan.leader.outside or game.clan.leader.ID == you.ID or game.clan.leader.ID == cat.ID or addon_check is False:
            return ""
        
        text = add_to_cat_dict("l_n", cluster, x, rel, r, game.clan.leader, text, cat_dict)

    # Deputy's name
    if "d_n" in text:
        cluster = False
        rel = False
        match = re.search(r'd_n(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)d_n', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        if game.clan.deputy is None:
            return ""
        addon_check = abbrev_addons(cat, game.clan.deputy, cluster, x, rel, r)
        if game.clan.deputy.dead or game.clan.deputy.outside or game.clan.deputy.ID == you.ID or game.clan.deputy.ID == cat.ID or addon_check is False:
            return ""
        
        text = add_to_cat_dict("d_n", cluster, x, rel, r, game.clan.deputy, text, cat_dict)

    # Dead cat
    # if cat is grieving, will their grief cat. otherwise will be arandom starclan cat
    if "d_c" in text:
        cluster = False
        rel = False
        match = re.search(r'd_c(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)d_c', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("d_c", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            if "grief stricken" in cat.illnesses:
                try:
                    dead_cat = Cat.all_cats.get(cat.illnesses['grief stricken'].get("grief_cat"))
                    if dead_cat is None:
                        if "lasting grief" not in cat.permanent_condition:
                            print("Warning:", cat.name, "is grieving + has no grief cat?")
                        dead_cat = Cat.all_cats.get(choice(game.clan.starclan_cats))
                except:
                    dead_cat = Cat.all_cats.get(choice(game.clan.starclan_cats))
            else:
                dead_cat = Cat.all_cats.get(choice(game.clan.starclan_cats))

            addon_check = abbrev_addons(cat, dead_cat, cluster, x, rel, r)

            counter = 0
            while (dead_cat.ID == you.ID or dead_cat.ID == cat.ID or dead_cat.ID in [game.clan.instructor.ID, game.clan.demon.ID] or addon_check is False):
                if counter == 30:
                    return ""
                dead_cat = Cat.all_cats.get(choice(game.clan.starclan_cats))
                addon_check = abbrev_addons(cat, dead_cat, cluster, x, rel, r)
                counter += 1
            cat_dict["d_c"] = dead_cat
            # words = text.split()
            # for i, word in enumerate(words):
            #     if word == "d_c" and (i == 0 or words[i-1][-1] != "{"):
            #         words[i] = str(dead_cat.name)
            # text = " ".join(words)

            text = add_to_cat_dict("d_c", cluster, x, rel, r, dead_cat, text, cat_dict)

    # Random dark forest cat
    if "rdf_c" in text:
        cluster = False
        rel = False
        match = re.search(r'rdf_c(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)rdf_c', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("rdf_c", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            random_cat = Cat.all_cats.get(choice(game.clan.darkforest_cats))
            addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)

            counter = 0
            while random_cat.ID == you.ID or random_cat.ID == cat.ID or addon_check is False:
                if counter == 30:
                    return ""
                random_cat = Cat.all_cats.get(choice(game.clan.darkforest_cats))
                addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)
                counter +=1

            text = add_to_cat_dict("rdf_c", cluster, x, rel, r, random_cat, text, cat_dict)
    
    # Random shunned cat
    if "rsh_c" in text:
        cluster = False
        rel = False
        match = re.search(r'rsh_c(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)rsh_c', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("rsh_c", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            random_cat = choice(get_alive_cats(Cat))
            addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)
            counter = 0

            while (random_cat.ID == you.ID or random_cat.ID == cat.ID or addon_check is False or random_cat.shunned == 0):
                if counter == 30:
                    return ""
                random_cat = choice(get_alive_cats(Cat))
                addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)
                counter +=1

            text = add_to_cat_dict("rsdh_c", cluster, x, rel, r, random_cat, text, cat_dict)

    # Shunned kit
    if "rsh_k" in text:
        cluster = False
        rel = False
        match = re.search(r'rsh_k(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)rsh_k', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        alive_kits = get_alive_status_cats(Cat, ["kitten", "newborn"])
        if len(alive_kits) < 1:
            return ""
        
        text, in_dict = cat_dict_check("rsh_k", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_kit = choice(alive_kits)
            addon_check = abbrev_addons(cat, alive_kit, cluster, x, rel, r)
            counter = 0

            while (alive_kit.ID == you.ID or alive_kit.ID == cat.ID or addon_check is False or alive_kit.shunned == 0):
                alive_kit = choice(alive_kits)
                addon_check = abbrev_addons(cat, alive_kit, cluster, x, rel, r)
                counter+=1
                if counter == 30:
                    return ""
                
            text = add_to_cat_dict("rsh_k", cluster, x, rel, r, alive_kit, text, cat_dict)

    # Shunned apprentice
    if "rsh_a" in text:
        cluster = False
        rel = False
        match = re.search(r'rsh_a(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)rsh_a', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        alive_apps = get_alive_status_cats(Cat, ["apprentice"])
        if len(alive_apps) < 1:
            return ""
        
        text, in_dict = cat_dict_check("rsh_a", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            counter = 0

            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or alive_app.shunned == 0):
                counter+=1
                if counter == 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)

            text = add_to_cat_dict("rsh_a", cluster, x, rel, r, alive_app, text, cat_dict)

    # Shunned warrior
    if "rsh_w" in text:
        cluster = False
        rel = False
        match = re.search(r'rsh_w(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)rsh_w', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        alive_apps = get_alive_status_cats(Cat, ["warrior"])
        if len(alive_apps) < 1:
            return ""
        
        text, in_dict = cat_dict_check("rsh_w", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            counter = 0

            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or alive_app.shunned == 0):
                counter+=1
                if counter == 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)

            text = add_to_cat_dict("rsh_w", cluster, x, rel, r, alive_app, text, cat_dict)

    # Shunned medicine cat or medicine cat apprentice
    if "rsh_m" in text:
        cluster = False
        rel = False
        match = re.search(r'rsh_m(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)rsh_m', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        alive_apps = get_alive_status_cats(Cat, ["medicine cat", "medicine cat apprentice"])
        if len(alive_apps) < 1:
            return ""
        
        text, in_dict = cat_dict_check("rsh_a", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            counter = 0

            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or alive_app.shunned == 0):
                counter+=1
                if counter == 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)

            text = add_to_cat_dict("rsh_m", cluster, x, rel, r, alive_app, text, cat_dict)

    # Shunned mediator or mediator apprentice
    if "rsh_d" in text:
        cluster = False
        rel = False
        match = re.search(r'rsh_d(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)rsh_d', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        alive_apps = get_alive_status_cats(Cat, ["mediator", "mediator apprentice"])
        if len(alive_apps) < 1:
            return ""
        
        text, in_dict = cat_dict_check("rsh_d", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            counter = 0

            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or alive_app.shunned == 0):
                counter+=1
                if counter == 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)

            text = add_to_cat_dict("rsh_d", cluster, x, rel, r, alive_app, text, cat_dict)

    # Shunned queen or queen's apprentice
    if "rsh_q" in text:
        cluster = False
        rel = False
        match = re.search(r'rsh_q(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)rsh_q', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        alive_apps = get_alive_status_cats(Cat, ["queen", "queen's apprentice"])
        if len(alive_apps) < 1:
            return ""
        
        text, in_dict = cat_dict_check("rsh_q", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            counter = 0

            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or alive_app.shunned == 0):
                counter+=1
                if counter == 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)

            text = add_to_cat_dict("rsh_q", cluster, x, rel, r, alive_app, text, cat_dict)

    # Shunned elder
    if "rsh_e" in text:
        cluster = False
        rel = False
        match = re.search(r'rsh_e(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)rsh_e', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        alive_apps = get_alive_status_cats(Cat, ["elder"])
        if len(alive_apps) < 1:
            return ""
        
        text, in_dict = cat_dict_check("rsh_e", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_app = choice(alive_apps)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            counter = 0

            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False or alive_app.shunned == 0):
                counter+=1
                if counter == 30:
                    return ""
                alive_app = choice(alive_apps)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)

            text = add_to_cat_dict("rsh_e", cluster, x, rel, r, alive_app, text, cat_dict)

    # Shunned deputy
    if "sh_d" in text:
        cluster = False
        rel = False
        match = re.search(r'sh_d(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)sh_d', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        random_cat = choice(get_alive_cats(Cat))
        addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)
        counter = 0

        while (random_cat.ID == you.ID or random_cat.ID == cat.ID or addon_check is False or random_cat.shunned == 0 or random_cat.status != "deputy"):
            if counter == 30:
                return ""
            random_cat = choice(get_alive_cats(Cat))
            addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)
            counter +=1
        
        text = add_to_cat_dict("sh_d", cluster, x, rel, r, random_cat, text, cat_dict)

    # Shunned leader
    if "sh_l" in text:
        cluster = False
        rel = False
        match = re.search(r'sh_l(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)sh_l', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        random_cat = choice(get_alive_cats(Cat))
        addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)
        counter = 0

        while (random_cat.ID == you.ID or random_cat.ID == cat.ID or addon_check is False or random_cat.shunned == 0 or random_cat.status != "leader"):
            if counter == 30:
                return ""
            random_cat = choice(get_alive_cats(Cat))
            addon_check = abbrev_addons(cat, random_cat, cluster, x, rel, r)
            counter +=1
        
        text = add_to_cat_dict("sh_l", cluster, x, rel, r, random_cat, text, cat_dict)

    # Warring Clan
    if "w_cClan" in text:
        if game.clan.war.get("at_war", False):
            return ""
        text = text.replace("w_c", str(game.clan.war["enemy"]))

    # Random lost cat
    if "l_c" in text:
        cluster = False
        rel = False
        match = re.search(r'l_c(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)l_c', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""
        text, in_dict = cat_dict_check("l_c", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_outside_cats = [i for i in Cat.all_cats.values() if not i.dead and i.outside and not i.exiled]
            if len(alive_outside_cats) <= 0:
                return ""
            alive_app = choice(alive_outside_cats)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            counter = 0

            while alive_app.ID == you.ID or alive_app.ID == cat.ID or cat.status in [
                "rogue", "loner", "former Clancat", "kittypet", "rival Clancat"
                ] or addon_check is False:
                alive_app = choice(alive_outside_cats)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                counter += 1
                if counter == 30:
                    return ""
                
            text = add_to_cat_dict("l_c", cluster, x, rel, r, alive_app, text, cat_dict)

    # Random exiled cat
    if "e_c" in text:
        cluster = False
        rel = False
        match = re.search(r'e_c(\w+)', text)
        if match:
            x = match.group(1).strip("_")
            cluster = True
        else:
            x = ""
        match2 = re.search(r'(\w+)e_c', text)
        if match2:
            r = match2.group(1).strip("_")
            rel = True
        else:
            r = ""

        text, in_dict = cat_dict_check("e_c", cluster, x, rel, r, text, cat_dict)
        

        if in_dict is False:
            alive_outside_cats = [i for i in Cat.all_cats.values() if not i.dead and i.outside and i.exiled]
            if len(alive_outside_cats) <= 0:
                return ""
            alive_app = choice(alive_outside_cats)
            addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
            counter = 0

            while (alive_app.ID == you.ID or alive_app.ID == cat.ID or addon_check is False):
                alive_app = choice(alive_outside_cats)
                addon_check = abbrev_addons(cat, alive_app, cluster, x, rel, r)
                counter += 1
                if counter == 30:
                    return ""

            text = add_to_cat_dict("e_c", cluster, x, rel, r, alive_app, text, cat_dict)

    # Dialogue focus cat
    if game.clan.focus_cat is not None:
        if "fc_c" in text:
            cluster = False
            rel = False
            match = re.search(r'fc_c(\w+)', text)
            if match:
                x = match.group(1).strip("_")
                cluster = True
            else:
                x = ""
            match2 = re.search(r'(\w+)fc_c', text)
            if match2:
                r = match2.group(1).strip("_")
                rel = True
            else:
                r = ""
            addon_check = abbrev_addons(cat, game.clan.focus_cat, cluster, x, rel, r)

            if game.clan.focus_cat.ID == cat.ID or game.clan.focus_cat.ID == game.clan.your_cat.ID or \
            addon_check is False:
                return ""

            text = add_to_cat_dict("fc_c", cluster, x, rel, r, game.clan.focus_cat, text, cat_dict)
    else:
        if "fc_c" in text:
            print(game.clan.focus_cat)
            return ""
    # except:
    #     print("the fuck", cat_dict)
    #     return ""

    return text


def quit(savesettings=False, clearevents=False):
    """
    Quits the game, avoids a bunch of repeated lines
    """
    if savesettings:
        game.save_settings()
    if clearevents:
        game.cur_events_list.clear()
    game.rpc.close_rpc.set()
    game.rpc.update_rpc.set()
    pygame.display.quit()
    pygame.quit()
    if game.rpc.is_alive():
        game.rpc.join(1)
    sys_exit()


with open(f"resources/dicts/conditions/permanent_conditions.json", "r") as read_file:
    PERMANENT = ujson.loads(read_file.read())

with open(f"resources/dicts/acc_display.json", "r") as read_file:
    ACC_DISPLAY = ujson.loads(read_file.read())

with open(f"resources/dicts/snippet_collections.json", "r") as read_file:
    SNIPPETS = ujson.loads(read_file.read())

with open(f"resources/dicts/prey_text_replacements.json", "r") as read_file:
    PREY_LISTS = ujson.loads(read_file.read())

with open(f"resources/dicts/backstories.json", "r") as read_file:
    BACKSTORIES = ujson.loads(read_file.read())
