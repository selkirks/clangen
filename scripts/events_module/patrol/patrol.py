#!/usr/bin/env python3
# -*- coding: ascii -*-
import logging
import random
<<<<<<< HEAD
from copy import deepcopy
from os.path import exists as path_exists
from random import choice, randint, choices
from typing import List, Tuple, Optional, Union

import pygame

from scripts.cat import pronouns
from scripts.cat.cats import Cat
from scripts.cat_relations.enums import RelType
from scripts.cat.enums import CatAge, CatRank, CatCompatibility
from scripts.clan import Clan
from scripts.clan_package.settings import get_clan_setting
from scripts.config import get_config
from scripts.events_module.event_filters import (
    event_for_tags,
    get_frequency,
    find_new_frequency,
    filter_relationship_type,
    check_relationship_value,
    get_personality_compatibility,
    event_for_location,
    event_for_season,
    cat_for_event,
    event_for_poi,
)
from scripts.events_module.patrol.patrol_event import PatrolEvent
from scripts.events_module.patrol.patrol_outcome import PatrolOutcome
from scripts.game_structure import localization, constants
from scripts.game_structure.game.settings import game_setting_get
from scripts.game_structure import game
from scripts.game_structure.localization import load_lang_resource
from scripts.events_module.text_adjust import (
    process_text,
    adjust_prey_abbr,
    get_special_snippet_list,
    find_special_list_types,
    adjust_list_text,
=======
from os.path import exists as path_exists
from random import choice, randint, choices
from typing import List, Tuple, Optional, Union, Literal, TypedDict

import pygame

from scripts.cat.cats import Cat
from scripts.cat_relations.enums import RelType
from scripts.cat.enums import CatAge, CatRank, CatCompatibility
from scripts.config import get_config
from scripts.events_module.consequences import gather_cat_objects
from scripts.events_module.event_filters import (
    get_frequency,
    find_new_frequency,
    check_relationship_value,
    get_personality_compatibility,
    event_for_poi,
    check_rel_constraint_groups,
)
from scripts.events_module.patrol.create_new_cat import updated_create_new_cat
from scripts.events_module.patrol.generate_patrol_list import (
    get_patrol_list,
    will_allow_outsider_patrols,
)
from scripts.events_module.patrol.patrol_event import PatrolEvent
from scripts.events_module.text_pool_event import handle_consequences
from scripts.events_module.text_pool_event.check_general_constraints import (
    passes_general_constraints,
)
from scripts.events_module.text_pool_event.find_involved_cats import find_cats
from scripts.events_module.text_pool_event.text_pool_event import TextPoolEvent
from scripts.game_structure import constants
from scripts.game_structure.game.settings import game_setting_get
from scripts.game_structure import game
from scripts.events_module.text_adjust import (
>>>>>>> clangen-megamerge
    event_text_adjust,
)
from scripts.special_dates import SpecialDate, is_today


logger = logging.getLogger(__name__)

<<<<<<< HEAD
# ---------------------------------------------------------------------------- #
#                              PATROL CLASS START                              #
# ---------------------------------------------------------------------------- #
"""
When adding new patrols, use \n to add a paragraph break in the text
"""

=======
>>>>>>> clangen-megamerge

class Patrol:
    used_patrols = []

    def __init__(self):
        self.patrol_event: Optional[PatrolEvent] = None
<<<<<<< HEAD

        self.patrol_leader = None
        self.random_cat = None
        self.patrol_cats = []
        self.patrol_apprentices = []
        self.other_clan = None
        self.intro_text = ""

        self.patrol_statuses = {}
        self.patrol_status_list = []

        # Holds new cats for easy access
        self.new_cats: List[List[Cat]] = []

        # False if no debug patrol set, value if one is set
        self.debug_patrol: Union[bool, str] = False

        # the patrols
        self.HUNTING_SZN = None
        self.HUNTING = None
        self.TRAINING_SZN = None
        self.TRAINING = None
        self.BORDER_SZN = None
        self.BORDER = None
        self.MEDCAT_SZN = None
        self.MEDCAT = None
        self.NEW_CAT = None
        self.NEW_CAT_HOSTILE = None
        self.NEW_CAT_WELCOMING = None
        self.OTHER_CLAN = None
        self.OTHER_CLAN_HOSTILE = None
        self.OTHER_CLAN_ALLIES = None
        self.HUNTING_GEN = None
        self.BORDER_GEN = None
        self.TRAINING_GEN = None
        self.MEDCAT_GEN = None
        self.DISASTER = None

    def setup_patrol(self, patrol_cats: List[Cat], patrol_type: str) -> str:
        # Add cats

        print("PATROL START ---------------------------------------------------")

        self.add_patrol_cats(patrol_cats, game.clan)

        self.debug_patrol = (
            constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]
            if constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]
            else False
        )

        final_patrols, final_romance_patrols = self.get_possible_patrols(
            str(game.clan.current_season).casefold(),
            str(
                game.clan.biome
                if not game.clan.override_biome
                else game.clan.override_biome
            ).casefold(),
            str(game.clan.camp_bg).casefold(),
            patrol_type,
            get_clan_setting("disasters"),
        )

        print(
            f"Total Number of Possible Patrols | normal: {len(final_patrols)}, romantic: {len(final_romance_patrols)} "
        )

        if final_patrols:
            normal_event_choice = choices(
                final_patrols, weights=[x.weight for x in final_patrols]
            )[0]
        else:
            print("ERROR: NO POSSIBLE NORMAL PATROLS FOUND for: ", self.patrol_statuses)
            raise RuntimeError

        romantic_event_choice = None
        if final_romance_patrols:
            romantic_event_choice = choices(
                final_romance_patrols, [x.weight for x in final_romance_patrols]
            )[0]

        if romantic_event_choice and Patrol.decide_if_romantic(
            romantic_event_choice,
            self.patrol_leader,
            self.random_cat,
            self.patrol_apprentices,
        ):
            print("did the romance")
            self.patrol_event = romantic_event_choice
        else:
            self.patrol_event = normal_event_choice

        Patrol.used_patrols.append(self.patrol_event.patrol_id)

        return event_text_adjust(
            Cat,
            self.patrol_event.intro_text,
            patrol_leader=self.patrol_leader,
            random_cat=self.random_cat,
            patrol_cats=self.patrol_cats,
            patrol_apprentices=self.patrol_apprentices,
            new_cats=self.new_cats,
=======
        self.debug_patrol_id: str = ""
        self.other_clan = None

        self.patrol_cats: list[Cat] = []
        """Holds all the cats that are on the patrol"""
        self.involved_cats: dict[str, Union[list[Cat], Cat]] = {}
        """Cats directly involved and referenced in the event. Keys are their text abbreviation, values are the associated cat objects"""
        self.outcome_cats: TypedDict(
            "outcome_cats", {"success": dict[str, Cat], "failure": dict[str, Cat]}
        ) = {"success": {}, "failure": {}}

    def begin_patrol(self, patrol_cats: List[Cat], patrol_type: str) -> str:
        """
        Handles all the initial patrol setup, returns the prepared patrol intro text.
        :param patrol_cats: All cats that have been chosen for this patrol
        :param patrol_type: Type of patrol
        """
        self.debug_patrol_id = get_config("patrol_generation.debug_ensure_patrol_id")

        print("PATROL START ---------------------------------------------------")

        # Add cats
        self._add_patrol_cats(patrol_cats)

        # Choose other clan
        if game.clan.all_other_clans and len(game.clan.all_other_clans) > 0:
            self.other_clan = choice(game.clan.all_other_clans)
        else:
            self.other_clan = None

        # Find valid patrol
        self.patrol_event = self._get_possible_patrol(patrol_type)

        Patrol.used_patrols.append(self.patrol_event.event_id)

        # Return text adjusted patrol intro
        return event_text_adjust(
            Cat,
            self.patrol_event.intro_text,
            involved_cat_dict=self.involved_cats,
>>>>>>> clangen-megamerge
            clan=game.clan,
            other_clan=self.other_clan,
        )

    def proceed_patrol(
<<<<<<< HEAD
        self, path: str = "proceed"
=======
        self, path: Literal["proceed", "antag", "decline"] = "proceed"
>>>>>>> clangen-megamerge
    ) -> Tuple[str, str, list, Optional[str]]:
        """Proceed the patrol to the next step.
        path can be: "proceed", "antag", or "decline" """

        if path == "decline":
            if self.patrol_event:
                print(
<<<<<<< HEAD
                    f"PATROL ID: {self.patrol_event.patrol_id} | SUCCESS: N/A (did not proceed)"
=======
                    f"PATROL ID: {self.patrol_event.event_id} | SUCCESS: N/A (did not proceed)"
>>>>>>> clangen-megamerge
                )
                return (
                    event_text_adjust(
                        Cat,
                        self.patrol_event.decline_text,
<<<<<<< HEAD
                        patrol_leader=self.patrol_leader,
                        random_cat=self.random_cat,
                        patrol_cats=self.patrol_cats,
                        patrol_apprentices=self.patrol_apprentices,
                        new_cats=self.new_cats,
=======
                        involved_cat_dict=self.involved_cats,
>>>>>>> clangen-megamerge
                        clan=game.clan,
                        other_clan=self.other_clan,
                    ),
                    "",
                    [],
                    None,
                )
            else:
<<<<<<< HEAD
                return "Error - no event chosen", "", None

        return self.determine_outcome(antagonize=(path == "antag"))

    def add_patrol_cats(self, patrol_cats: List[Cat], clan: Clan) -> None:
        """Add the list of cats to the patrol class and handles to set all needed values.

        Parameters
        ----------
        patrol_cats : list
            list of cats which are on the patrol

        clan: Clan
            the Clan class of the game, this parameter is needed to make tests possible

        Returns
        ----------
        """
        for cat in patrol_cats:
            self.patrol_cats.append(cat)

            if cat.status.rank.is_any_apprentice_rank():
                self.patrol_apprentices.append(cat)

            self.patrol_status_list.append(cat.status.rank)

            if cat.status.rank in self.patrol_statuses:
                self.patrol_statuses[cat.status.rank] += 1
            else:
                self.patrol_statuses[cat.status.rank] = 1

            # Combined patrol_statuses categories
            if cat.status.rank.is_any_medicine_rank():
                if "healer cats" in self.patrol_statuses:
                    self.patrol_statuses["healer cats"] += 1
                else:
                    self.patrol_statuses["healer cats"] = 1

            if cat.status.rank.is_any_apprentice_rank():
                if "all apprentices" in self.patrol_statuses:
                    self.patrol_statuses["all apprentices"] += 1
                else:
                    self.patrol_statuses["all apprentices"] = 1
=======
                return "Error - no event chosen", "", [], None

        return self.determine_outcome(antagonize=(path == "antag"))

    def _add_patrol_cats(self, patrol_cats: List[Cat]) -> None:
        """
        Sorts and categorizes patrol cats, then determines a patrol leader.
        :param patrol_cats: list of cats which are on the patrol
        """
        # ADD TO PATROL_CATS

        self.patrol_cats = patrol_cats
        for cat in patrol_cats:
            # ADD TO STATUS LIST
            if cat.status.rank in self.involved_cats:
                self.involved_cats[cat.status.rank].append(cat)
            else:
                self.involved_cats[cat.status.rank] = [cat]

            # Combined patrol_statuses categories
            if cat.status.rank.is_any_medicine_rank():
                if "healer cats" in self.involved_cats:
                    self.involved_cats["healer cats"].append(cat)
                else:
                    self.involved_cats["healer cats"] = [cat]

            if cat.status.rank.is_any_apprentice_rank():
                if "all apprentices" in self.involved_cats:
                    self.involved_cats["all apprentices"].append(cat)
                else:
                    self.involved_cats["all apprentices"] = [cat]
>>>>>>> clangen-megamerge

            if (
                cat.status.rank.is_any_adult_warrior_like_rank()
                and cat.age != CatAge.ADOLESCENT
            ):
<<<<<<< HEAD
                if "normal adult" in self.patrol_statuses:
                    self.patrol_statuses["normal adult"] += 1
                else:
                    self.patrol_statuses["normal adult"] = 1

            game.patrolled.append(cat.ID)

        # PATROL LEADER AND RANDOM CAT CAN NOT CHANGE AFTER SET-UP

        # DETERMINE PATROL LEADER
        # sets medcat as leader if they're in the patrol
        if CatRank.MEDICINE_CAT in self.patrol_status_list:
            index = self.patrol_status_list.index(CatRank.MEDICINE_CAT)
            self.patrol_leader = self.patrol_cats[index]
            # If there is no medicine cat, but there is a medicine cat apprentice, set them as the patrol leader.
            # This prevents warrior from being treated as medicine cats in medicine cat patrols.
        elif CatRank.MEDICINE_APPRENTICE in self.patrol_status_list:
            index = self.patrol_status_list.index(CatRank.MEDICINE_APPRENTICE)
            self.patrol_leader = self.patrol_cats[index]
            # then we just make sure that this app will also be app1
            self.patrol_apprentices.remove(self.patrol_leader)
            self.patrol_apprentices = [self.patrol_leader] + self.patrol_apprentices
            # sets leader as patrol leader
        elif CatRank.LEADER in self.patrol_status_list:
            index = self.patrol_status_list.index(CatRank.LEADER)
            self.patrol_leader = self.patrol_cats[index]
        elif CatRank.DEPUTY in self.patrol_status_list:
            index = self.patrol_status_list.index(CatRank.DEPUTY)
            self.patrol_leader = self.patrol_cats[index]
        else:
            # Get the oldest cat
            possible_leader = [
                i
                for i in self.patrol_cats
                if not i.status.rank.is_any_apprentice_rank()
            ]
            if possible_leader:
                # Flip a coin to pick the most experience, or oldest.
                if randint(0, 1):
                    possible_leader.sort(key=lambda x: x.moons)
                else:
                    possible_leader.sort(key=lambda x: x.experience)
                self.patrol_leader = possible_leader[-1]
            else:
                self.patrol_leader = choice(self.patrol_cats)

        if clan.all_other_clans and len(clan.all_other_clans) > 0:
            self.other_clan = choice(clan.all_other_clans)
        else:
            self.other_clan = None

        # DETERMINE RANDOM CAT
        # Find random cat
        if len(patrol_cats) > 1:
            # prioritize grabbing an adult as the random cat
            if self.patrol_statuses.get("normal adult", 0) > 1:
                self.random_cat = choice(
                    [
                        i
                        for i in self.patrol_cats
                        if i != self.patrol_leader and i not in self.patrol_apprentices
                    ]
                )
            # if no adults, grab anyone
            else:
                self.random_cat = choice(
                    [i for i in patrol_cats if i != self.patrol_leader]
                )
        else:
            self.random_cat = choice(patrol_cats)

        print("Patrol Leader:", str(self.patrol_leader.name))
        print("Random Cat:", str(self.random_cat.name))

    def get_possible_patrols(
        self,
        current_season: str,
        biome: str,
        camp: str,
        patrol_type: str,
        game_setting_disaster=None,
    ) -> Tuple[List[PatrolEvent]]:
        # ---------------------------------------------------------------------------- #
        #                                LOAD RESOURCES                                #
        # ---------------------------------------------------------------------------- #
        biome = biome.lower()
        camp = camp.lower()
        game_setting_disaster = (
            game_setting_disaster
            if game_setting_disaster is not None
            else get_clan_setting("disasters")
        )
        season = current_season.lower()
        leaf = f"{season}"
        biome_dir = f"{biome}/"
        self.update_resources(biome_dir, leaf)

        possible_patrols = []
        # This is for debugging purposes, load-in *ALL* the possible patrols when debug_override_patrol_stat_requirements is true. (May require longer loading time)
        if constants.CONFIG["patrol_generation"][
            "debug_override_patrol_stat_requirements"
        ]:
            leaves = ["greenleaf", "leaf-bare", "leaf-fall", "newleaf", "any"]
            for biome in constants.BIOME_TYPES:
                for leaf in leaves:
                    biome_dir = f"{biome.lower()}/"
                    self.update_resources(biome_dir, leaf)
                    possible_patrols.extend(self.generate_patrol_events(self.HUNTING))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.HUNTING_SZN)
                    )
                    possible_patrols.extend(self.generate_patrol_events(self.BORDER))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.BORDER_SZN)
                    )
                    possible_patrols.extend(self.generate_patrol_events(self.TRAINING))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.TRAINING_SZN)
                    )
                    possible_patrols.extend(self.generate_patrol_events(self.MEDCAT))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.MEDCAT_SZN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.HUNTING_GEN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.BORDER_GEN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.TRAINING_GEN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.MEDCAT_GEN)
                    )
                    possible_patrols.extend(self.generate_patrol_events(self.DISASTER))
                    possible_patrols.extend(self.generate_patrol_events(self.NEW_CAT))
                    possible_patrols.extend(
                        self.generate_patrol_events(self.NEW_CAT_WELCOMING)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.NEW_CAT_HOSTILE)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.OTHER_CLAN)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.OTHER_CLAN_ALLIES)
                    )
                    possible_patrols.extend(
                        self.generate_patrol_events(self.OTHER_CLAN_HOSTILE)
                    )

        # this next one is needed for Classic specifically
        patrol_type = (
            "med"
            if [CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE]
            in self.patrol_status_list
            else patrol_type
        )
        patrol_size = len(self.patrol_cats)
        reputation = game.clan.reputation  # reputation with outsiders
        other_clan = self.other_clan
        hostile_rep = False
        neutral_rep = False
        welcoming_rep = False
        clan_neutral = False
        clan_hostile = False
        clan_allies = False
        clan_size = int(len(game.clan.clan_cats))
        chance = 0
        # assigning other_clan relations
        other_clan_standing = other_clan.get_standing()
        if other_clan_standing == "ally":
            clan_allies = True
        elif other_clan_standing == "hostile":
            clan_hostile = True
        elif other_clan_standing == "neutral":
            clan_neutral = True
        # chance for each kind of loner event to occur
        small_clan = False
        if clan_size < 20:
            small_clan = True
        regular_chance = int(random.getrandbits(2))
        hostile_chance = int(random.getrandbits(5))
        welcoming_chance = int(random.getrandbits(1))
        if 1 <= int(reputation) <= 30:
            hostile_rep = True
            if small_clan:
                chance = welcoming_chance
            else:
                chance = hostile_chance
        elif 31 <= int(reputation) <= 70:
            neutral_rep = True
            if small_clan:
                chance = welcoming_chance
            else:
                chance = regular_chance
        elif int(reputation) >= 71:
            welcoming_rep = True
            chance = welcoming_chance

        possible_patrols.extend(self.generate_patrol_events(self.HUNTING))
        possible_patrols.extend(self.generate_patrol_events(self.HUNTING_SZN))
        possible_patrols.extend(self.generate_patrol_events(self.BORDER))
        possible_patrols.extend(self.generate_patrol_events(self.BORDER_SZN))
        possible_patrols.extend(self.generate_patrol_events(self.TRAINING))
        possible_patrols.extend(self.generate_patrol_events(self.TRAINING_SZN))
        possible_patrols.extend(self.generate_patrol_events(self.MEDCAT))
        possible_patrols.extend(self.generate_patrol_events(self.MEDCAT_SZN))
        possible_patrols.extend(self.generate_patrol_events(self.HUNTING_GEN))
        possible_patrols.extend(self.generate_patrol_events(self.BORDER_GEN))
        possible_patrols.extend(self.generate_patrol_events(self.TRAINING_GEN))
        possible_patrols.extend(self.generate_patrol_events(self.MEDCAT_GEN))

        if game_setting_disaster:
            dis_chance = int(random.getrandbits(3))  # disaster patrol chance
            if dis_chance == 1:
                possible_patrols.extend(self.generate_patrol_events(self.DISASTER))

        # new cat patrols
        if chance == 1:
            if welcoming_rep:
                possible_patrols.extend(
                    self.generate_patrol_events(self.NEW_CAT_WELCOMING)
                )
            elif neutral_rep:
                possible_patrols.extend(self.generate_patrol_events(self.NEW_CAT))
            elif hostile_rep:
                possible_patrols.extend(
                    self.generate_patrol_events(self.NEW_CAT_HOSTILE)
                )

        # other Clan patrols
        if other_clan:
            if clan_neutral:
                possible_patrols.extend(self.generate_patrol_events(self.OTHER_CLAN))
            elif clan_allies:
                possible_patrols.extend(
                    self.generate_patrol_events(self.OTHER_CLAN_ALLIES)
                )
            elif clan_hostile:
                possible_patrols.extend(
                    self.generate_patrol_events(self.OTHER_CLAN_HOSTILE)
                )
        patrol_ids = [patrol.patrol_id for patrol in possible_patrols]
        if self.debug_patrol and self.debug_patrol not in patrol_ids:
=======
                if "normal adult" in self.involved_cats:
                    self.involved_cats["normal adult"].append(cat)
                else:
                    self.involved_cats["normal adult"] = [cat]

            game.patrolled.append(cat.ID)

        # DETERMINE PATROL LEADER
        # THIS CANNOT CHANGE AFTER SET-UP
        # sets medcat as patrol leader if they're in the patrol
        if CatRank.MEDICINE_CAT in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.MEDICINE_CAT]

        # If there is no medicine cat, but there is a medicine cat apprentice, set them as the patrol leader.
        # This prevents warriors from being treated as medicine cats in medicine cat patrols.
        elif CatRank.MEDICINE_APPRENTICE in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.MEDICINE_APPRENTICE]

        # if no meddies set leader as patrol leader
        elif CatRank.LEADER in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.LEADER]

        # if no leader set the deputy as patrol leader
        elif CatRank.DEPUTY in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.DEPUTY]

        # if not deputy, try warriors
        elif CatRank.WARRIOR in self.involved_cats.keys():
            possible_leads = self.involved_cats[CatRank.WARRIOR]
        # if no warriors, set oldest or most experienced of any cats as patrol lead
        else:
            possible_leads = self.patrol_cats

        # Flip a coin to pick the most experienced or the oldest.
        if randint(0, 1):
            possible_leads.sort(key=lambda x: x.moons)
        else:
            possible_leads.sort(key=lambda x: x.experience)

        self.involved_cats["p_l"] = possible_leads[-1]
        self.involved_cats["patrol_cats"] = patrol_cats

        print("Patrol Leader:", str(self.involved_cats["p_l"].name))

    def _get_possible_patrol(
        self,
        patrol_type: str,
    ) -> PatrolEvent:
        # ---------------------------------------------------------------------------- #
        #                                LOAD RESOURCES                                #
        # ---------------------------------------------------------------------------- #

        # this is needed for Classic specifically
        # Classic doesn't let you pick patrol type, so instead we specify herb_gathering if meddies are present
        patrol_type = (
            "herb_gathering"
            if {CatRank.MEDICINE_CAT, CatRank.MEDICINE_APPRENTICE}.intersection(
                set(self.involved_cats.keys())
            )
            else patrol_type
        )
        # This make sure general only gets hunting, border, or training patrols
        if patrol_type == "general":
            # choosing a type now means that the type of patrol later chosen isn't influenced
            # by the amount of patrols available of that type
            patrol_type = random.choice(["hunting", "border", "training"])

        # GET PATROL LIST
        patrol_list = get_patrol_list(
            patrol_type,
            outsider_rep=will_allow_outsider_patrols(
                small_clan=int(len(game.clan.clan_cats))
                < get_config("patrol_generation.small_clan_threshold")
            ),
            other_clan_rep=self.other_clan.get_standing(),
        )

        # INFORM -NOT PRESENT-
        patrol_ids = [patrol.event_id for patrol in patrol_list]
        if self.debug_patrol_id and self.debug_patrol_id not in patrol_ids:
>>>>>>> clangen-megamerge
            print(
                "DEBUG: requested patrol not present (check spelling/mismatched season, biome, patrol type, new cat flag, other clan relations, disaster setting)"
            )

<<<<<<< HEAD
        final_patrols, final_romance_patrols = self.get_filtered_patrols(
            possible_patrols, biome, camp, current_season, patrol_type
        )

=======
        # DEBUG - NO FILTER
>>>>>>> clangen-megamerge
        # This is a debug option, this allows you to remove any constraints of a patrol regarding location, session, biomes, etc.
        if constants.CONFIG["patrol_generation"][
            "debug_override_patrol_stat_requirements"
        ]:
<<<<<<< HEAD
            final_patrols = final_romance_patrols = possible_patrols
            # Logging
            print(
                "All patrol filters regarding location, session, etc. have been removed."
            )

        # This is a debug option. If the patrol_id set in "debug_ensure_patrol" is possible,
        # make it the *only* possible patrol
        if self.debug_patrol:
            for _pat in final_patrols + final_romance_patrols:
                if _pat.patrol_id == self.debug_patrol:
                    patrol_type = choice(_pat.types) if _pat.types != [] else "general"
                    rom = "non-romance"
                    if _pat in final_patrols:
                        final_patrols = [_pat]
                    elif _pat in final_romance_patrols:
                        final_romance_patrols = [_pat]
                        rom = "romance"
                    print(
                        f"debug_ensure_patrol_id: "
                        f'"{constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]}" '
                        f"is a possible {patrol_type} patrol, and was set as the only "
                        f"{patrol_type} {rom} patrol option"
                    )
                    break
            else:
                print(
                    f"debug_ensure_patrol_id: "
                    f'"{constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]}" '
                    f"is not found. Check output for reason."
                )
        return final_patrols, final_romance_patrols

    def _check_constraints(self, patrol: PatrolEvent) -> bool:
        if not filter_relationship_type(
            group=self.patrol_cats,
            filter_types=patrol.relationship_constraints,
            patrol_leader=self.patrol_leader,
        ):
            if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                print(
                    "DEBUG: requested patrol does not meet constraints (relationship type)"
                )
            return False

        if (
            patrol.pl_skill_constraints
            and not self.patrol_leader.skills.check_skill_requirement_list(
                patrol.pl_skill_constraints
            )
        ):
            if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                print("DEBUG: requested patrol does not meet constraints (pl_skill)")
            return False

        if (
            patrol.pl_trait_constraints
            and self.patrol_leader.personality.trait not in patrol.pl_trait_constraints
        ):
            if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                print("DEBUG: requested patrol does not meet constraints (pl_trait)")
            return False

        return True

    @staticmethod
    def decide_if_romantic(
        romantic_event, patrol_leader, random_cat, patrol_apprentices: list
    ) -> bool:
        # if no romance was available or the patrol lead and random cat aren't potential mates then use the normal event
=======
            if self.debug_patrol_id:
                chosen_patrol = [
                    p for p in patrol_list if p.event_id == self.debug_patrol_id
                ][0]
            else:
                chosen_patrol = choice(patrol_list)
            print(
                "All patrol filters regarding location, session, etc. have been removed."
            )
        # FILTER PATROLS when no debug set
        else:
            chosen_patrol = self._filter_patrols(patrol_list, patrol_type)

        return chosen_patrol

    def _decide_if_romantic(self, romantic_event: Optional[PatrolEvent]) -> bool:
        """
        Finds the chance of this patrol being romantic based on the cats involved and their current relationship with each other
        :return: True if patrol should be romantic, False otherwise
        """
>>>>>>> clangen-megamerge

        if not romantic_event:
            print("No romantic event")
            return False

<<<<<<< HEAD
        if "rom_two_apps" in romantic_event.tags:
            if len(patrol_apprentices) < 2:
                print("somehow, there are not enough apprentices for romantic patrol")
                return False
            love1 = patrol_apprentices[0]
            love2 = patrol_apprentices[1]
        else:
            love1 = patrol_leader
            love2 = random_cat

        if (
            not love1.is_potential_mate(love2, for_love_interest=True)
            and love1.ID not in love2.mate
        ):
            print("not a potential mate or current mate")
            return False

        print("attempted romance between:", love1.name, love2.name)
        chance_of_romance_patrol = constants.CONFIG["patrol_generation"][
            "chance_of_romance_patrol"
        ]

        if (
            get_personality_compatibility(love1, love2) == CatCompatibility.POSITIVE
            or love1.ID in love2.mate
        ):
            chance_of_romance_patrol -= 10
        else:
            chance_of_romance_patrol += 10

        values = [*RelType]
        for val in values:
            value_check = check_relationship_value(love1, love2, val)
            if value_check < 0:
                chance_of_romance_patrol -= 1
            elif value_check > 0:
                chance_of_romance_patrol += 2

        if (
            romantic_event.patrol_id
            == game.constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]
        ):
            chance_of_romance_patrol = 1
=======
        chance_of_romance_patrol = get_config(
            "patrol_generation.chance_of_romance_patrol"
        )

        for block in romantic_event.relationship_constraint:
            if "can_romance" in block["constraints"]:
                # gather the kitty cats
                cats_from = gather_cat_objects(
                    Cat,
                    block["cats_from"],
                    event=self,
                    involved_cats=self.involved_cats,
                )
                cats_to = gather_cat_objects(
                    Cat, block["cats_to"], event=self, involved_cats=self.involved_cats
                )
                # now affect the chance depending on the compatibility
                for c in cats_from:
                    compatibility = [
                        get_personality_compatibility(c, love_cat)
                        for love_cat in cats_to
                        if love_cat != c
                    ]
                    for compat in compatibility:
                        if compat == CatCompatibility.POSITIVE:
                            chance_of_romance_patrol -= 5
                        elif compat == CatCompatibility.NEGATIVE:
                            chance_of_romance_patrol += 5

                    rel_values = [
                        check_relationship_value(c, love_cat, val)
                        for val in [*RelType]
                        for love_cat in cats_to
                        if love_cat != c
                    ]
                    for v in rel_values:
                        if v > 0:
                            chance_of_romance_patrol -= 1
                        else:
                            chance_of_romance_patrol += 1
>>>>>>> clangen-megamerge

        if chance_of_romance_patrol <= 0:
            chance_of_romance_patrol = 1
        print("final romance chance:", chance_of_romance_patrol)
        return not int(random.random() * chance_of_romance_patrol)

    def _filter_patrols(
        self,
        possible_patrols: List[PatrolEvent],
<<<<<<< HEAD
        biome: str,
        camp: str,
        current_season: str,
        patrol_type: str,
    ):
        chosen_frequency = get_frequency()
        used_frequencies = set()

        filtered_patrols = []
        romantic_patrols = []
        # This make sure general only gets hunting, border, or training patrols
        # chose fix type will make it not depending on the content amount
        if patrol_type == "general":
            patrol_type = random.choice(["hunting", "border", "training"])

        app_number_mentor_checks = {}
        for i in range(1, 7):
            app_number_mentor_checks[f"app{i}_mentored"] = (
                len(self.patrol_apprentices) >= i
                and self.patrol_apprentices[i - 1].mentor is not None
            )
        general_mentor_checks = (
            all(app.mentor for app in self.patrol_apprentices)
            if self.patrol_apprentices
            else False
        )
        has_mentor = {"general": general_mentor_checks, **app_number_mentor_checks}

        # makes sure that it grabs patrols in the correct biomes, season, with the correct number of cats
        while not filtered_patrols:
            for patrol in possible_patrols:
                if (
                    patrol.frequency != chosen_frequency
                    and patrol.patrol_id
                    != constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]
                ):
                    continue
                if not self._check_constraints(patrol):
                    continue

                # Don't check for repeat patrols if ensure_patrol_id is being used.
                if (
                    constants.CONFIG["patrol_generation"]["debug_ensure_patrol_id"]
                    == ""
                    and patrol.patrol_id in self.used_patrols
                ):
                    continue

                if not (patrol.min_cats <= len(self.patrol_cats) <= patrol.max_cats):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (min or max cats range)"
                        )
                    continue

                flag = False
                for sta, num in patrol.min_max_status.items():
                    if len(num) != 2:
                        print(f"Issue with status limits: {patrol.patrol_id}")
                        continue

                    if not (num[0] <= self.patrol_statuses.get(sta, -1) <= num[1]):
                        flag = True
                        break
                if flag:
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (min max status)"
                        )
                    continue

                if not event_for_tags(
                    patrol.tags, Cat, mentor_tags_fulfilled=has_mentor
                ):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (tags)"
                        )
                    continue

                if not event_for_location(patrol.biome):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (biome)"
                        )
                    continue
                if camp not in patrol.camp and "any" not in patrol.camp:
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (camp)"
                        )
                    continue
                if not event_for_season(patrol.season):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (season)"
                        )
                    continue

                if not event_for_poi(patrol.poi):
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print("DEBUG: requested patrol does not meet constraints (PoI)")
                    continue

                if "hunting" not in patrol.types and patrol_type == "hunting":
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (patrol type)"
                        )
                    continue
                elif "border" not in patrol.types and patrol_type == "border":
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (patrol type)"
                        )
                    continue
                elif "training" not in patrol.types and patrol_type == "training":
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (patrol type)"
                        )
                    continue
                elif "herb_gathering" not in patrol.types and patrol_type == "med":
                    if self.debug_patrol and self.debug_patrol == patrol.patrol_id:
                        print(
                            "DEBUG: requested patrol does not meet constraints (patrol type)"
                        )
                    continue

                if "romance" in patrol.tags:
                    romantic_patrols.append(patrol)
                else:
                    filtered_patrols.append(patrol)

            if not filtered_patrols:
                # if we've circled back around to 4 then we need to reset the used patrols
                if 4 in used_frequencies and chosen_frequency == 4:
                    self.used_patrols.clear()
=======
        patrol_type: str,
    ) -> PatrolEvent:
        # GET POSSIBLE PATROLS
        # run the first set of really basic constraint filtering, just to get our base of valid patrols
        possible_patrols = [
            p
            for p in possible_patrols
            if self._patrol_pass_basic_constraints(
                p, patrol_type, is_debug_patrol=p.event_id == self.debug_patrol_id
            )
        ]
        # make sure the hunting patrols are balanced
        if patrol_type == "hunting":
            possible_patrols = self.balance_hunting(possible_patrols)

        # separate into the two lists
        normal_patrols: list[PatrolEvent] = []
        romantic_patrols: list[PatrolEvent] = []
        for p in possible_patrols:
            if "romance" in p.tags:
                romantic_patrols.append(p)
            else:
                normal_patrols.append(p)

        print(
            f"Total Number of Possible Patrols | normal: {len(normal_patrols)}, romantic: {len(romantic_patrols)} "
        )

        # GET FREQUENCY
        chosen_frequency = get_frequency()

        # always try to do the debugged ID first
        if self.debug_patrol_id:
            patrol_override = [
                p for p in possible_patrols if p.event_id == self.debug_patrol_id
            ]
            if patrol_override:
                patrol_override = patrol_override[0]
                chosen_frequency = patrol_override.frequency
            else:
                print(
                    "Debug patrol wasn't in the list of possible patrols, make sure to choose the matching patrol type in-game!"
                )
        else:
            patrol_override = None

        # GET PATROL
        chosen_patrol: Optional[PatrolEvent] = None

        # first we see if we can get a romantic patrol
        if romantic_patrols and not patrol_override:
            chosen_patrol = self._get_valid_patrol(
                romantic_patrols.copy(), chosen_frequency, patrol_override
            )

        if chosen_patrol and not self._decide_if_romantic(chosen_patrol):
            chosen_patrol = None

        # if no romantic patrol possible, we get a normal one!
        if not chosen_patrol:
            chosen_patrol = self._get_valid_patrol(
                normal_patrols.copy(), chosen_frequency, patrol_override
            )

        return chosen_patrol

    def _get_valid_patrol(
        self,
        possible_patrols: List[PatrolEvent],
        chosen_frequency: int,
        patrol_override: Optional[PatrolEvent],
    ) -> Optional[PatrolEvent]:
        chosen_patrol = None
        used_frequencies = set()

        patrols_to_test = possible_patrols.copy()
        checked_patrols = set()
        outside_cats = [
            c
            for c in Cat.all_cats_list
            if (c.status.is_other_clancat or c.status.is_outsider) and not c.dead
        ]
        while not chosen_patrol:
            # make sure we still have possible patrols
            if not patrols_to_test and not patrol_override:
                if len(checked_patrols) >= len(possible_patrols):
                    # we have checked all possible patrols and found none possible
                    # hopefully this is because we were checking romance patrols, not normal patrols
                    return None
                patrols_to_test = possible_patrols.copy()
                # if we've circled back around to 4 then we need to reset the used patrols
                if 4 in used_frequencies and chosen_frequency == 4:
                    self.used_patrols.clear()
                    patrols_to_test = possible_patrols.copy()
>>>>>>> clangen-megamerge
                    used_frequencies.clear()
                else:
                    used_frequencies.add(chosen_frequency)
                    chosen_frequency = find_new_frequency(used_frequencies)
<<<<<<< HEAD

        # make sure the hunting patrols are balanced
        if patrol_type == "hunting":
            filtered_patrols = self.balance_hunting(filtered_patrols)

        return filtered_patrols, romantic_patrols

    def get_filtered_patrols(
        self, possible_patrols, biome, camp, current_season, patrol_type
    ):
        filtered_patrols, romantic_patrols = self._filter_patrols(
            possible_patrols, biome, camp, current_season, patrol_type
        )

        if patrol_type == "herb_gathering":
            target_herbs = game.clan.herb_supply.sorted_by_need
            herb_filtered_patrols = []
            herb_romance_patrols = []

            i = 0
            while not herb_filtered_patrols and i <= len(target_herbs):
                i += 1
                herb_filtered_patrols = [
                    patrol
                    for patrol in filtered_patrols
                    if target_herbs[i] in patrol.herbs_given
                    or "random_herbs" in patrol.herbs_given
                ]
                herb_romance_patrols = [
                    patrol
                    for patrol in romantic_patrols
                    if target_herbs[i] in patrol.herbs_given
                    or "random_herbs" in patrol.herbs_given
                ]

            if herb_filtered_patrols:
                filtered_patrols = herb_filtered_patrols
                romantic_patrols = herb_romance_patrols

                if self.debug_patrol and self.debug_patrol not in [
                    patrol.patrol_id for patrol in filtered_patrols + romantic_patrols
                ]:
                    print(
                        "DEBUG: requested patrol removed during herb filtering (not target herb)"
                    )

        if not filtered_patrols:
            print(
                "No normal patrols possible. Repeating filter with used patrols cleared."
            )
            self.used_patrols.clear()
            print("used patrols cleared", self.used_patrols)
            filtered_patrols, romantic_patrols = self._filter_patrols(
                possible_patrols, biome, camp, current_season, patrol_type
            )

            if not filtered_patrols:
                raise Exception(
                    "No matching patrols found! This may be a localization issue."
                )

        return filtered_patrols, romantic_patrols

    def generate_patrol_events(self, patrol_dict):
        all_patrol_events = []
        for patrol in patrol_dict:
            patrol_event = PatrolEvent(
                patrol_id=patrol.get("patrol_id"),
                biome=patrol.get("biome"),
                camp=patrol.get("camp"),
                season=patrol.get("season"),
                tags=patrol.get("tags"),
                frequency=patrol.get("frequency", 4),
                types=patrol.get("types"),
                intro_text=patrol.get("intro_text"),
                patrol_art=patrol.get("patrol_art"),
                patrol_art_clean=patrol.get("patrol_art_clean"),
                success_outcomes=PatrolOutcome.generate_from_info(
                    patrol.get("success_outcomes")
                ),
                fail_outcomes=PatrolOutcome.generate_from_info(
                    patrol.get("fail_outcomes"), success=False
                ),
                decline_text=patrol.get("decline_text"),
                chance_of_success=patrol.get("chance_of_success"),
                min_cats=patrol.get("min_cats", 1),
                max_cats=patrol.get("max_cats", 6),
                min_max_status=patrol.get("min_max_status"),
                antag_success_outcomes=PatrolOutcome.generate_from_info(
                    patrol.get("antag_success_outcomes"), antagonize=True
                ),
                antag_fail_outcomes=PatrolOutcome.generate_from_info(
                    patrol.get("antag_fail_outcomes"), success=False, antagonize=True
                ),
                relationship_constraints=patrol.get("relationship_constraint"),
                pl_skill_constraints=patrol.get("pl_skill_constraint"),
                pl_trait_constraints=patrol.get("pl_trait_constraints"),
            )

            all_patrol_events.append(patrol_event)

        return all_patrol_events

    def determine_outcome(
        self, antagonize=False
    ) -> Tuple[str, str, list, Optional[str]]:
        if self.patrol_event is None:
            raise Exception("No patrol event supplied")

        # First Step - Filter outcomes and pick a fail and success outcome
        success_outcomes = (
            self.patrol_event.antag_success_outcomes
            if antagonize
            else self.patrol_event.success_outcomes
        )
        fail_outcomes = (
            self.patrol_event.antag_fail_outcomes
            if antagonize
            else self.patrol_event.fail_outcomes
        )

        # Filter the outcomes. Do this only once - this is also where stat cats are determined
        success_outcomes = PatrolOutcome.prepare_allowed_outcomes(
            success_outcomes, self
        )
        fail_outcomes = PatrolOutcome.prepare_allowed_outcomes(fail_outcomes, self)

        chosen_success = None
        chosen_failure = None

        # Choose a success and fail outcome
        chosen_frequency = get_frequency()
        used_frequencies = set()
        while not chosen_success or not chosen_failure:
            if not chosen_success:
                possible_successes = [
                    x for x in success_outcomes if x.frequency == chosen_frequency
                ]
                if possible_successes:
                    chosen_success = choices(
                        possible_successes,
                        weights=[x.weight for x in possible_successes],
                    )[0]
            if not chosen_failure:
                possible_failures = [
                    x for x in fail_outcomes if x.frequency == chosen_frequency
                ]
                if possible_failures:
                    chosen_failure = choices(
                        possible_failures, weights=[x.weight for x in possible_failures]
                    )[0]
            if not chosen_success or not chosen_failure:
                used_frequencies.add(chosen_frequency)
                chosen_frequency = find_new_frequency(used_frequencies)

        final_event, success = self.calculate_success(chosen_success, chosen_failure)

        print(f"PATROL ID: {self.patrol_event.patrol_id} | SUCCESS: {success}")
        print(
            f"Patrol Frequency: {self.patrol_event.frequency} | Patrol Weight: {self.patrol_event.weight}"
        )
        if success:
            print(
                f"Outcome Frequency: {chosen_success.frequency} | Outcome Weight: {chosen_success.weight}"
            )
        else:
            print(
                f"Outcome Frequency: {chosen_failure.frequency} | Outcome Weight: {chosen_failure.weight}"
            )

        # Run the chosen outcome
        return final_event.execute_outcome(self)

    def calculate_success(
        self, success_outcome: PatrolOutcome, fail_outcome: PatrolOutcome
    ) -> Tuple[PatrolOutcome, bool]:
        """Returns both the chosen event, and a boolean that's True if success, and False is fail."""
=======
                continue

            if not patrol_override:
                test_patrol = choices(
                    patrols_to_test, [x.weight for x in patrols_to_test]
                )[0]
            else:
                test_patrol = patrol_override
                patrol_override = None

            # CHECK FREQUENCY AND ENSURE ID
            if test_patrol.frequency != chosen_frequency:
                if test_patrol in patrols_to_test:
                    patrols_to_test.remove(test_patrol)
                continue

            # CHECK REPEAT
            if (
                test_patrol.event_id in self.used_patrols
                and not self.debug_patrol_id == test_patrol.event_id
            ):
                if test_patrol in patrols_to_test:
                    patrols_to_test.remove(test_patrol)
                continue

            # CHECK IF CATS FIT

            involved_cats = find_cats(
                interactable_cats=[
                    c
                    for c in self.involved_cats["patrol_cats"]
                    if c != self.involved_cats["p_l"]
                ],
                involved_cats=self.involved_cats,
                outside_cats=outside_cats,
                event=test_patrol,
                other_clan=self.other_clan,
            )
            if involved_cats:
                chosen_patrol = test_patrol
                self.involved_cats = involved_cats
            else:
                if test_patrol in patrols_to_test:
                    patrols_to_test.remove(test_patrol)
                checked_patrols.add(test_patrol.event_id)

        return chosen_patrol

    def _patrol_pass_basic_constraints(
        self, patrol: PatrolEvent, patrol_type: str, is_debug_patrol: bool
    ) -> bool:
        # CHECK PATROL TYPE
        if patrol_type not in patrol.types:
            if is_debug_patrol:
                print("DEBUG: requested patrol does not meet constraints (patrol type)")
            return False

        # CHECK GENERAL
        if not passes_general_constraints(
            patrol,
            self.involved_cats["p_l"],
            self.involved_cats,
            self.other_clan,
            is_debug_patrol,
        ):
            return False

        # CHECK POI
        if not event_for_poi(patrol.poi):
            if is_debug_patrol:
                print("DEBUG: requested patrol does not meet constraints (PoI)")
            return False

        # CHECK NEEDED HERBS
        if patrol_type == "herb_gathering":
            # skip this if it's a debug patrol
            if is_debug_patrol:
                return True

            target_herbs = game.clan.herb_supply.sorted_by_need

            # if any herb can happen, then we return True
            if "random_herbs" in patrol.herbs_given:
                return True

            # if the patrol is not able to give herbs we need, we return False
            if not set(patrol.herbs_given).intersection(set(target_herbs)):
                return False

        return True

    def _find_allowed_outcomes(
        self, antagonize: bool = False
    ) -> tuple[TextPoolEvent, TextPoolEvent]:
        """
        Filters through possible outcomes to find appropriate outcomes for both failure and success
        :param antagonize: set True if the player chose to antagonize
        :return: success outcome, failure outcome
        """

        # find which set of outcomes we'll be using based on if the player choose to antagonize
        if antagonize:
            success_outcomes = self.patrol_event.antag_success_outcomes
            fail_outcomes = self.patrol_event.antag_fail_outcomes
        else:
            success_outcomes = self.patrol_event.success_outcomes
            fail_outcomes = self.patrol_event.fail_outcomes

        # for success and fail options we'll find what frequency is wanted
        # then pick an outcome of that frequency based on weight
        # then see if that outcome is allowed per constraints
        # if it isn't, then grab the next outcome and try again until we have one that passes.
        # this is the outcome we'll use!

        # we'll get an outcome for both success and failure
        chosen_success = None
        chosen_failure = None

        chosen_frequency = get_frequency()
        used_success_frequencies = set()
        used_fail_frequencies = set()

        tested_outcomes = set()
        while not chosen_success or not chosen_failure:
            if not chosen_success:
                possible_outcomes = [
                    x
                    for x in success_outcomes
                    if x.frequency == chosen_frequency
                    and x.event_id not in tested_outcomes
                ]
                if not possible_outcomes:
                    if len(used_success_frequencies) == 4:
                        raise Exception(
                            f"Valid success outcome could not be found for {self.patrol_event.event_id}"
                        )
                    used_success_frequencies.add(chosen_frequency)
                    chosen_frequency = find_new_frequency(used_success_frequencies)
                    continue

                test_outcome = choices(
                    possible_outcomes, weights=[x.weight for x in possible_outcomes]
                )[0]

                # try to filter
                if self._check_outcome_constraints(test_outcome, "success"):
                    chosen_success = test_outcome
                else:
                    tested_outcomes.add(test_outcome.event_id)
                    continue

            if not chosen_failure:
                possible_outcomes = [
                    x
                    for x in fail_outcomes
                    if x.frequency == chosen_frequency
                    and x.event_id not in tested_outcomes
                ]
                if not possible_outcomes:
                    if len(used_fail_frequencies) == 4:
                        raise Exception(
                            f"Valid fail outcome could not be found for {self.patrol_event.event_id}"
                        )
                    used_fail_frequencies.add(chosen_frequency)
                    chosen_frequency = find_new_frequency(used_fail_frequencies)
                    continue

                test_outcome = choices(
                    possible_outcomes, weights=[x.weight for x in possible_outcomes]
                )[0]
                # try to filter
                if self._check_outcome_constraints(test_outcome, "failure"):
                    chosen_failure = test_outcome
                else:
                    tested_outcomes.add(test_outcome.event_id)
                    continue

        return chosen_success, chosen_failure

    def _check_outcome_constraints(
        self, outcome: TextPoolEvent, outcome_type: Literal["success", "failure"]
    ) -> bool:
        """
        Checks the outcome constraints and attempts to find appropriate cats. If the outcome is valid and cats are
        found, the cats will be added to the matching `self.outcome_cats` dict
        :param outcome: outcome to check
        :param outcome_type: the outcome_cats dict that the valid cats should be added to
        """
        # BASICS
        if not passes_general_constraints(
            outcome, self.involved_cats["p_l"], self.involved_cats
        ):
            return False

        # CATS
        outside_cats = [
            c
            for c in Cat.all_cats_list
            if (c.status.is_other_clancat or c.status.is_outsider) and not c.dead
        ]
        temp_involved_cats = self.involved_cats.copy()

        temp_involved_cats = find_cats(
            interactable_cats=temp_involved_cats["patrol_cats"],
            involved_cats=temp_involved_cats,
            outside_cats=outside_cats,
            event=outcome,
            other_clan=self.other_clan,
        )
        if not temp_involved_cats:
            return False

        # if we're here, then we must have found all our cats!
        self.outcome_cats[outcome_type] = temp_involved_cats

        return True

    def determine_outcome(
        self, antagonize=False
    ) -> Tuple[str, str, list, pygame.Surface]:
        if self.patrol_event is None:
            raise Exception("No patrol event supplied")

        success_outcome, fail_outcome = self._find_allowed_outcomes(antagonize)

        chosen_outcome, success = self.calculate_success(success_outcome, fail_outcome)

        print(f"PATROL ID: {self.patrol_event.event_id} | SUCCESS: {success}")
        print(
            f"Patrol Frequency: {self.patrol_event.frequency} | Patrol Weight: {self.patrol_event.weight}"
        )
        print(
            f"Outcome Frequency: {chosen_outcome.frequency} | Outcome Weight: {chosen_outcome.weight}"
        )

        # Run the chosen outcome
        return handle_consequences.execute_outcome(
            chosen_outcome,
            self.outcome_cats["success" if success else "failure"],
            self.other_clan,
        ) + (self.get_patrol_art(chosen_outcome),)

    def calculate_success(
        self, success_outcome: TextPoolEvent, fail_outcome: TextPoolEvent
    ) -> Tuple[TextPoolEvent, bool]:
        """Returns both the chosen outcome, and a boolean that's True if success, and False if failure."""
>>>>>>> clangen-megamerge

        patrol_size = len(self.patrol_cats)
        total_exp = sum([x.experience for x in self.patrol_cats])
        path = (
            "patrol_generation.classic_difficulty_modifier"
            if game.clan.game_mode == "classic"
            else "patrol_generation.difficulty_modifier"
        )

        gm_modifier = get_config(path)

<<<<<<< HEAD
        exp_adustment = (
            (1 + 0.10 * patrol_size) * total_exp / (patrol_size * gm_modifier * 2)
        )

        success_chance = self.patrol_event.chance_of_success + int(exp_adustment)
=======
        exp_adjustment = (
            (1 + 0.10 * patrol_size) * total_exp / (patrol_size * gm_modifier * 2)
        )

        success_chance = self.patrol_event.chance_of_success + int(exp_adjustment)
>>>>>>> clangen-megamerge
        success_chance = min(success_chance, 90)

        # Now, apply success and fail skill
        print(
            "starting chance:",
            self.patrol_event.chance_of_success,
            "| EX_updated chance:",
            success_chance,
        )
<<<<<<< HEAD
        skill_updates = ""

        # Skill and trait stuff
        for kitty in self.patrol_cats:
            # SUCCESS OUTCOME
            is_exclusionary = any(
                value.find("-") == 0 for value in success_outcome.stat_skill
            )
            if is_exclusionary:
                skills_to_check = [
                    x.replace("-", "") for x in success_outcome.stat_skill
                ]
            else:
                skills_to_check = success_outcome.stat_skill

            hits = kitty.skills.check_skill_requirement_list(skills_to_check)

            if is_exclusionary and not hits:
                # if they don't have a disallowed skill, we increase the chance
                success_chance += (
                    1 * constants.CONFIG["patrol_generation"]["win_stat_cat_modifier"]
                )
            else:
                # if they had a required skill, we increase
                success_chance += (
                    hits
                    * constants.CONFIG["patrol_generation"]["win_stat_cat_modifier"]
                )

            # FAIL OUTCOME
            is_exclusionary = any(
                value.find("-") == 0 for value in fail_outcome.stat_skill
            )
            if is_exclusionary:
                skills_to_check = [x.replace("-", "") for x in fail_outcome.stat_skill]
            else:
                skills_to_check = fail_outcome.stat_skill
            hits = kitty.skills.check_skill_requirement_list(skills_to_check)

            if is_exclusionary and not hits:
                # if they don't have a disallowed skill, we decrease chance (fail mod is a negative)
                success_chance += (
                    1 * constants.CONFIG["patrol_generation"]["fail_stat_cat_modifier"]
                )
            else:
                # if they had the required skill, we decrease chance (fail mod is a negative)
                success_chance += (
                    hits
                    * constants.CONFIG["patrol_generation"]["fail_stat_cat_modifier"]
                )

            # SUCCESS OUTCOME
            is_exclusionary = any(
                value.find("-") == 0 for value in success_outcome.stat_trait
            )
            if is_exclusionary:
                trait_to_check = [
                    x.replace("-", "") for x in success_outcome.stat_trait
                ]
            else:
                trait_to_check = success_outcome.stat_trait

            if (is_exclusionary and kitty.personality.trait not in trait_to_check) or (
                kitty.personality.trait in trait_to_check
            ):
                success_chance += constants.CONFIG["patrol_generation"][
                    "win_stat_cat_modifier"
                ]

            # FAIL OUTCOME
            is_exclusionary = any(
                value.find("-") == 0 for value in fail_outcome.stat_trait
            )
            if is_exclusionary:
                trait_to_check = [x.replace("-", "") for x in fail_outcome.stat_trait]
            else:
                trait_to_check = fail_outcome.stat_trait

            if (is_exclusionary and kitty.personality.trait not in trait_to_check) or (
                kitty.personality.trait in trait_to_check
            ):
                success_chance += constants.CONFIG["patrol_generation"][
                    "fail_stat_cat_modifier"
                ]

            skill_updates += f"{kitty.name} updated chance to {success_chance} | "

        if success_chance >= 120:
            success_chance = 115
            skill_updates += "success chance over 120, updated to 115"

        print(skill_updates)
=======

        # Skill and trait stuff
        for abbr, constraints in success_outcome.involved_cats.items():
            # if this is present, then we know a cat must fulfill it
            if stat_block := constraints.get("stat"):
                cat = self.outcome_cats["success"][abbr]
                if "skill" in stat_block:
                    success_chance += get_config(
                        "patrol_generation.skill_cat_modifier"
                    ) * cat.skills.check_skill_requirement_list(stat_block["skill"])
                    print(f"success chance increase to {success_chance}")
                elif "trait" in stat_block:
                    success_chance += get_config("patrol_generation.trait_cat_modifier")
                    print(f"success chance increase to {success_chance}")

        if success_chance >= 120:
            success_chance = 115
            print("success chance over 120, updated to 115")
>>>>>>> clangen-megamerge

        success = int(random.random() * 120) < success_chance

        # This is a debug option, this will forcefully change the outcome of a patrol
        if isinstance(
            constants.CONFIG["patrol_generation"]["debug_ensure_patrol_outcome"], bool
        ):
            success = constants.CONFIG["patrol_generation"][
                "debug_ensure_patrol_outcome"
            ]
            # Logging
            print(
<<<<<<< HEAD
                f"The outcome of {self.patrol_event.patrol_id} was altered to {success}"
            )

        return (success_outcome if success else fail_outcome, success)

    def update_resources(self, biome_dir, leaf):
        resources = [
            ("HUNTING_SZN", f"{biome_dir}hunting/{leaf}.json"),
            ("HUNTING", f"{biome_dir}hunting/any.json"),
            ("BORDER_SZN", f"{biome_dir}border/{leaf}.json"),
            ("BORDER", f"{biome_dir}border/any.json"),
            ("TRAINING_SZN", f"{biome_dir}training/{leaf}.json"),
            ("TRAINING", f"{biome_dir}training/any.json"),
            ("MEDCAT_SZN", f"{biome_dir}med/{leaf}.json"),
            ("MEDCAT", f"{biome_dir}med/any.json"),
            ("NEW_CAT", "new_cat.json"),
            ("NEW_CAT_HOSTILE", "new_cat_hostile.json"),
            ("NEW_CAT_WELCOMING", "new_cat_welcoming.json"),
            ("OTHER_CLAN", "other_clan.json"),
            ("OTHER_CLAN_HOSTILE", "other_clan_hostile.json"),
            ("OTHER_CLAN_ALLIES", "other_clan_allies.json"),
            ("HUNTING_GEN", "general/hunting.json"),
            ("BORDER_GEN", "general/border.json"),
            ("MEDCAT_GEN", "general/medcat.json"),
            ("TRAINING_GEN", "general/training.json"),
            ("DISASTER", "disaster.json"),
        ]
        for patrol_property, location in resources:
            try:
                setattr(
                    self, patrol_property, load_lang_resource(f"patrols/{location}")
                )
            except:
                raise Exception("Something went wrong loading patrols!")

    def balance_hunting(self, possible_patrols: list):
=======
                f"The outcome of {self.patrol_event.event_id} was altered to {success}"
            )

        return success_outcome if success else fail_outcome, success

    def balance_hunting(self, possible_patrols: list[PatrolEvent]):
>>>>>>> clangen-megamerge
        """Filter the incoming hunting patrol list to balance the different kinds of hunting patrols.
        With this filtering, there should be more prey possible patrols.

            Parameters
            ----------
            possible_patrols : list
                list of patrols which should be filtered

            Returns
            ----------
            filtered_patrols : list
                list of patrols which is filtered
        """
        filtered_patrols = []

        # get first what kind of prey size which will be chosen
        biome = (
            game.clan.biome
            if not game.clan.override_biome
            else game.clan.override_biome
        )
        season = game.clan.current_season
<<<<<<< HEAD
        prey_size = ["very_small", "small", "medium", "large", "huge"]
=======
        prey_size = ["tiny", "small", "medium", "large", "huge"]
>>>>>>> clangen-megamerge
        prey_size_random_weights = PATROL_BALANCE[biome][season]

        chosen_prey_size = choices(prey_size, weights=prey_size_random_weights)[0]
        print(f"chosen filter prey size: {chosen_prey_size}")

        # filter all possible patrol depending on the needed prey size
        for patrol in possible_patrols:
            # count the outcomes + prey size
            prey_size_to_outcome_amounts = {}
            for outcome in patrol.success_outcomes:
<<<<<<< HEAD
                # ignore skill or trait outcomes
                if outcome.stat_trait or outcome.stat_skill:
                    continue
                if outcome.prey:
                    outcome_prey_size = outcome.prey[0]
                    if outcome_prey_size not in prey_size_to_outcome_amounts:
                        prey_size_to_outcome_amounts[outcome_prey_size] = 0
                    prey_size_to_outcome_amounts[outcome_prey_size] += 1
=======
                if outcome.supply:
                    for block in outcome.supply:
                        if block["type"] != "freshkill":
                            continue
                        outcome_prey_size = block["adjust"].replace("increase_", "")
                        if outcome_prey_size not in prey_size_to_outcome_amounts:
                            prey_size_to_outcome_amounts[outcome_prey_size] = 0
                        prey_size_to_outcome_amounts[outcome_prey_size] += 1
>>>>>>> clangen-megamerge

            # get the prey size with the most outcomes
            most_prey_size = ""
            max_occurrences = 0
            for size, amount in prey_size_to_outcome_amounts.items():
                if amount >= max_occurrences:
                    most_prey_size = size

            if chosen_prey_size == most_prey_size:
                filtered_patrols.append(patrol)
<<<<<<< HEAD
            elif self.debug_patrol and self.debug_patrol == patrol.patrol_id:
=======
            elif self.debug_patrol_id and self.debug_patrol_id == patrol.event_id:
>>>>>>> clangen-megamerge
                print(
                    "DEBUG: requested patrol does not meet constraints (failed prey balancing)"
                )
        # if the filtering results in an empty list, don't filter and return whole possible patrols
        if len(filtered_patrols) <= 0:
            print(
                "---- WARNING ---- filtering to balance out the hunting, didn't work."
            )
            filtered_patrols = possible_patrols
        return filtered_patrols

<<<<<<< HEAD
    def get_patrol_art(self) -> pygame.Surface:
=======
    def get_patrol_art(self, outcome: TextPoolEvent = None) -> Optional[pygame.Surface]:
>>>>>>> clangen-megamerge
        """Return's patrol art surface"""
        if not self.patrol_event or not isinstance(self.patrol_event.patrol_art, str):
            return pygame.Surface((600, 600), flags=pygame.SRCALPHA)

        root_dir = "resources/images/patrol_art/"

<<<<<<< HEAD
        if not game_setting_get("gore") and self.patrol_event.patrol_art_clean:
            file_name = self.patrol_event.patrol_art_clean
        else:
            file_name = self.patrol_event.patrol_art
=======
        clean_art = (
            self.patrol_event.patrol_art_clean
            if not outcome
            else outcome.outcome_art_clean
        )
        if not game_setting_get("gore") and clean_art:
            file_name = clean_art
        else:
            file_name = (
                self.patrol_event.patrol_art if not outcome else outcome.outcome_art
            )
>>>>>>> clangen-megamerge

        if not isinstance(file_name, str) or not path_exists(
            f"{root_dir}{file_name}.png"
        ):
<<<<<<< HEAD
=======
            if outcome:
                # we return None so that we don't overwrite the patrol's general art.
                # if we got here on an outcome, then the outcome had no attached art and we should just be using
                # the patrol's general art
                return None
>>>>>>> clangen-megamerge
            if "herb_gathering" in self.patrol_event.types:
                file_name = "med"
            elif "hunting" in self.patrol_event.types:
                file_name = "hunt"
            elif "border" in self.patrol_event.types:
                file_name = "bord"
            else:
                file_name = "train"

            file_name = f"{file_name}_general_intro"

        if is_today(SpecialDate.APRIL_FOOLS):
            april_fools_root_dir = "resources/images/patrol_art/april_fools/"
            if path_exists(f"{april_fools_root_dir}{file_name}.png"):
                return pygame.image.load(f"{april_fools_root_dir}{file_name}.png")

        return pygame.image.load(f"{root_dir}{file_name}.png")


# ---------------------------------------------------------------------------- #
#                               PATROL CLASS END                               #
# ---------------------------------------------------------------------------- #

PATROL_WEIGHT_ADAPTION = constants.CONFIG["prey"]["patrol_weight_adaption"]
PATROL_BALANCE = constants.CONFIG["prey"]["patrol_balance"]
