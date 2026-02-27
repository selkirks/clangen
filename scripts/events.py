# pylint: disable=line-too-long
"""

TODO: Docs


"""

import random
# pylint: enable=line-too-long
import traceback
from collections import Counter

import ujson
import re

from scripts.clan import Clan
from scripts.clan import HERBS
from scripts.events_module.relation_events import Relation_Events
from scripts.events_module.condition_events import Condition_Events
from scripts.cat.pelts import Pelt
#from scripts.events_module.disaster_events import DisasterEvents
from scripts.events_module.outsider_events import OutsiderEvents
from scripts.event_class import Single_Event
from scripts.game_structure.game_essentials import game
from scripts.cat_relations.relationship import Relationship
from scripts.cat.cats import Cat, cat_class, BACKSTORIES
from scripts.cat.history import History
from scripts.cat.names import Name
from scripts.clan_resources.freshkill import FRESHKILL_EVENT_ACTIVE
from scripts.conditions import (
    medical_cats_condition_fulfilled,
    get_amount_cat_for_one_medic,
)
from scripts.events_module.generate_events import GenerateEvents, generate_events
from scripts.clan_resources.freshkill import FreshkillPile, Nutrition
from scripts.events_module.handle_short_events import handle_short_events
from scripts.events_module.relationship.pregnancy_events import Pregnancy_Events
from scripts.game_structure.windows import SaveError
from scripts.game_structure.windows import RetireScreen, DeputyScreen, NameKitsWindow, PickPath
from enum import Enum, auto

class BirthType(Enum):
    NO_PARENTS = "birth_no_parents"
    ONE_PARENT = "birth_one_parent"
    TWO_PARENTS = "birth_two_parents"
    ONE_ADOPTIVE_PARENT = "birth_one_adoptive_parent"
    TWO_ADOPTIVE_PARENTS = "birth_two_adoptive_parents"
    ONE_OUTSIDER_PARENT = "birth_one_parent_outsider"
    TWO_OUTSIDER_PARENTS = "birth_two_parent_outsiders"
from scripts.patrol.patrol import Patrol
from scripts.utility import (
    change_clan_relations,
    change_clan_reputation,
    get_alive_status_cats,
    get_living_clan_cat_count,
    get_random_moon_cat,
    ceremony_text_adjust,
    get_current_season,
    adjust_list_text,
    ongoing_event_text_adjust,
    event_text_adjust,
    get_other_clan,
    history_text_adjust,
    unpack_rel_block,
    pronoun_repl,
    create_new_cat,
    adjust_txt,
    get_cluster
)


class Events:
    """
    TODO: DOCS
    """

    all_events = {}
    game.switches["timeskip"] = False
    new_cat_invited = False
    ceremony_accessory = False
    CEREMONY_TXT = None
    WAR_TXT = None

    def __init__(self):
        self.load_ceremonies()
        self.load_war_resources()
        self.c_txt = None
        self.d_txt = None
        self.checks = [-1,-1,-1]
        self.cat_dict = {}
        self.current_events = []

    def one_moon(self):
        """
        Handles the moon skipping of the whole Clan.
        """
        if self.checks == [-1,-1,-1] and game.clan.your_cat and game.clan.your_cat.inheritance:
            self.checks = [len(game.clan.your_cat.apprentice), len(game.clan.your_cat.mate), len(game.clan.your_cat.inheritance.get_blood_kits()), None]
            if game.clan.leader:
                self.checks[3] = game.clan.leader.ID
        elif game.clan.your_cat.inheritance:
            self.checks = [len(game.clan.your_cat.apprentice), len(game.clan.your_cat.mate), len(game.clan.your_cat.inheritance.get_blood_kits()), None]
            if game.clan.leader:
                self.checks[3] = game.clan.leader.ID
        else:
            self.checks = [len(game.clan.your_cat.apprentice), len(game.clan.your_cat.mate), 0, None]
            if game.clan.leader:
                self.checks[3] = game.clan.leader.ID
        game.cur_events_list = [] + game.next_events_list
        game.next_events_list = []
        game.herb_events_list = []
        game.freshkill_events_list = []
        game.mediated = []
        game.switches["saved_clan"] = False
        self.new_cat_invited = False
        Relation_Events.clear_trigger_dict()
        Patrol.used_patrols.clear()
        game.patrolled.clear()
        game.just_died.clear()
        # 1 = reg patrol 2 = lifegen patrol 3 = df patrol 4 = date
        game.switches['patrolled'] = []
        game.switches['window_open'] = False
        if game.clan.your_cat.status == "medicine cat apprentice" or game.clan.your_cat.status == "medicine cat":
            game.switches["attended half-moon"] = False
        
        if any(
                str(cat.status) in {
                    'leader', 'deputy', 'warrior', 'medicine cat',
                    'medicine cat apprentice', 'apprentice', 'mediator',
                    'mediator apprentice', "queen", "queen's apprentice"
                } and not cat.dead and not cat.outside and not cat.shunned
                for cat in Cat.all_cats.values()):
            game.switches['no_able_left'] = False

        # age up the clan, set current season
        game.clan.age += 1
        get_current_season()
        Pregnancy_Events.handle_pregnancy_age(game.clan)
        self.check_war()
        if 'freshkill' in game.clan.clan_settings:
            if game.clan.clan_settings['freshkill']:
                self.add_freshkill()

        if (
            game.clan.game_mode in ["expanded", "cruel season"]
            and game.clan.freshkill_pile
        ):
            # feed the cats and update the nutrient status
            relevant_cats = list(
                filter(
                    lambda _cat: _cat.is_alive()
                    and not _cat.exiled
                    and not _cat.outside,
                    Cat.all_cats.values(),
                )
            )
            game.clan.freshkill_pile.time_skip(relevant_cats, game.freshkill_event_list)
            # get the moonskip freshkill
            self.get_moon_freshkill()


        # checking if a lost cat returns on their own
        rejoin_upperbound = game.config["lost_cat"]["rejoin_chance"]
        if random.randint(1, rejoin_upperbound) == 1:
            self.handle_lost_cats_return()

        # Calling of "one_moon" functions.
        resource_dir = "resources/dicts/events/disasters/"
        disaster_text = {}
        with open(f"{resource_dir}forest.json",
                  encoding="ascii") as read_file:
            disaster_text = ujson.loads(read_file.read())
        if not game.clan.disaster and random.randint(1,50) == 1:
            for clan_cat in game.clan.clan_cats:
                clan_cat_cat = Cat.fetch_cat(clan_cat)
                if clan_cat_cat:
                    clan_cat_cat.faith -= round(random.uniform(-1,0), 2)
            game.clan.disaster = random.choice(list(disaster_text.keys()))
            if "next_possible_disaster" in game.switches and game.switches["next_possible_disaster"]:
                current_disaster =  disaster_text.get(game.switches["next_possible_disaster"])
            else:
                current_disaster = disaster_text.get(game.clan.disaster)
            while not current_disaster or not disaster_text[game.clan.disaster]["trigger_events"] or (get_current_season() not in current_disaster["season"]):
                game.clan.disaster = random.choice(list(disaster_text.keys()))
                current_disaster = disaster_text.get(game.clan.disaster)
        if game.clan.disaster and game.clan.disaster != "":
            if "next_possible_disaster" in game.switches and game.clan.disaster == game.switches["next_possible_disaster"]:
                game.switches["next_possible_disaster"] = None
            for clan_cat in game.clan.clan_cats:
                clan_cat_cat = Cat.fetch_cat(clan_cat)
                if clan_cat_cat:
                    clan_cat_cat.faith -= round(random.uniform(-0.1,0), 2)
            self.handle_disaster()
        
        for cat in Cat.all_cats.copy().values():
            if not cat.outside or cat.dead:
                self.one_moon_cat(cat)
            else:
                self.one_moon_outside_cat(cat)

        # Adding in any potential lead den events that have been saved
        if "lead_den_interaction" in game.clan.clan_settings:
            if game.clan.clan_settings["lead_den_interaction"]:
                self.handle_lead_den_event()

        # keeping this commented out till disasters are more polished
        # self.disaster_events.handle_disasters()

        # Handle grief events.
        if Cat.grief_strings:
            # Grab all the dead or outside cats, who should not have grief text
            for ID in Cat.grief_strings.copy():
                check_cat = Cat.all_cats.get(ID)
                if isinstance(check_cat, Cat):
                    if check_cat.dead or check_cat.outside:
                        Cat.grief_strings.pop(ID)

            # Generate events

            for cat_id, values in Cat.grief_strings.items():
                for _val in values:
                    if _val[2] == "minor":
                        # Apply the grief message as a thought to the cat
                        text = event_text_adjust(
                            Cat,
                            _val[0],
                            main_cat=Cat.fetch_cat(cat_id),
                            random_cat=Cat.fetch_cat(_val[1][0]))

                        Cat.fetch_cat(cat_id).thought = text
                    else:
                        game.cur_events_list.append(
                            Single_Event(_val[0], ["birth_death", "relation"],
                                        _val[1]))
                        Cat.fetch_cat(cat_id).faith -= round(random.uniform(-1,0), 2)
            
            
                
            Cat.grief_strings.clear()

        if Cat.dead_cats:
            ghost_names = []
            shaken_cats = []
            extra_event = None
            event = None
            for ghost in Cat.dead_cats:
                if not ghost.dead_for > 1:
                    ghost_names.append(str(ghost.name))
                else:
                    continue # keeps cats who generate as dead out of death events
            insert = ""
            if ghost_names:
                insert = adjust_list_text(ghost_names)

            if len(Cat.dead_cats) > 1 and insert:
                event = f"The past moon, {insert} have taken their place in StarClan. {game.clan.name}Clan mourns their " \
                        f"loss, and their Clanmates will miss where they had been in their lives. Moments of their " \
                        f"lives are shared in stories around the circle of mourners as those that were closest to them " \
                        f"take them to their final resting place."
    
                if len(ghost_names) > 2:
                    alive_cats = list(
                        filter(
                            lambda kitty: (
                                kitty.status != "leader"
                                and not kitty.dead
                                and not kitty.outside
                                and not kitty.exiled
                            ),
                            Cat.all_cats.values(),
                        )
                    )
                    # finds a percentage of the living Clan to become shaken

                    if len(alive_cats) == 0:
                        return
                    else:
                        shaken_cats = random.sample(
                            alive_cats,
                            k=max(
                                int((len(alive_cats) * random.choice([4, 5, 6])) / 100),
                                1,
                            ),
                        )

                    shaken_cat_names = []
                    for cat in shaken_cats:
                        shaken_cat_names.append(str(cat.name))
                        cat.get_injured(
                            "shock",
                            event_triggered=False,
                            lethal=False,
                            severity="minor",
                        )

                    insert = adjust_list_text(shaken_cat_names)

                    if len(shaken_cats) == 1:
                        extra_event = f"So much grief and death has taken its toll on the cats of {game.clan.name}Clan. {insert} is particularly shaken by it."
                    else:
                        extra_event = f"So much grief and death has taken its toll on the cats of {game.clan.name}Clan. {insert} are particularly shaken by it. "

            elif insert:
                event = (
                    f"The past moon, {insert} has taken their place in StarClan. {game.clan.name}Clan mourns their "
                    f"loss, and their Clanmates will miss the spot they took up in their lives. Moments of their "
                    f"life are shared in stories around the circle of mourners as those that were closest to them "
                    f"take them to their final resting place."
                )

            if event:
                game.cur_events_list.append(
                    Single_Event(event, ["birth_death"], [i.ID for i in Cat.dead_cats])
                )
            if extra_event:
                game.cur_events_list.append(
                    Single_Event(
                        extra_event, ["birth_death"], [i.ID for i in shaken_cats]
                    )
                )
            Cat.dead_cats.clear()

        if game.clan.game_mode in ['expanded', 'cruel season'] and game.clan.freshkill_pile:
            # make a notification if the Clan does not have enough prey
            if FRESHKILL_EVENT_ACTIVE and not game.clan.freshkill_pile.clan_has_enough_food():
                event_string = f"{game.clan.name}Clan doesn't have enough prey for next moon!"
                game.cur_events_list.insert(0, Single_Event(event_string))
                game.freshkill_event_list.append(event_string)

        self.herb_gather()
        self.handle_focus()
        game.switches['have kits'] = True
        
        # Clear the list of cats that died this moon.
        game.just_died.clear()

        for cat in Cat.all_cats.copy().values():
            if cat.shunned == 2:
                if cat.status == "leader":
                    string = f"Due to the cries of outrage from their Clan after the reveal of their crime, {cat.name} has stepped down as leader of {game.clan.name}Clan."
                    cat.specsuffix_hidden = True
                    game.clan.leader_lives = 1
                    # ^^ to keep the leader status for dialogue but take away "star".
                    # they can also only die once now
                    game.cur_events_list.insert(0, Single_Event(string, "alert", cat.ID))

                elif cat.status == "deputy":
                    string = f"{game.clan.leader.name} has thrown {cat.name} from their position as {game.clan.name}Clan's deputy."
                    game.cur_events_list.insert(0, Single_Event(string, "alert", cat.ID))
                
                elif cat.status in ["medicine cat", "medicine cat apprentice"]:
                    string = f"{cat.name} has been forced to step down as a medicine cat due to their crimes."
                    
                    game.cur_events_list.insert(0, Single_Event(string, "alert", cat.ID))

                elif cat.status in ["mediator", "mediator appentice"]:
                    string = f"{cat.name} has been forced to step down as a mediator due to their crimes."
                    game.cur_events_list.insert(0, Single_Event(string, "alert", cat.ID))

                elif cat.status in ["queen", "queen's apprentice"]:
                    string = f"{cat.name} can no longer be trusted with the Clan's youngest, and has been stripped of their status as a queen."
                    game.cur_events_list.insert(0, Single_Event(string, "alert", cat.ID))

                elif cat.status in ["warrior", "apprentice", "kitten"]:
                    string = f"{cat.name} has been shunned from the Clan."
                    
                    game.cur_events_list.insert(0, Single_Event(string, "alert", cat.ID))

        # Promote leader and deputy, if needed.
        self.check_and_promote_leader()
        self.check_and_promote_deputy()

        if game.clan.game_mode in ["expanded", "cruel season"]:
            amount_per_med = get_amount_cat_for_one_medic(game.clan)
            med_fullfilled = medical_cats_condition_fulfilled(
                Cat.all_cats.values(), amount_per_med
            )
            if not med_fullfilled:
                string = (
                    f"{game.clan.name}Clan does not have enough healthy medicine cats! Cats will be sick/hurt "
                    f"for longer and have a higher chance of dying. "
                )
                game.cur_events_list.insert(0, Single_Event(string, ["health", "alert"]))
        else:
            has_med = any(
                str(cat.status) in {"medicine cat", "medicine cat apprentice"}
                and not cat.dead
                and not cat.outside
                for cat in Cat.all_cats.values()
            )
            if not has_med:
                string = f"{game.clan.name}Clan has no medicine cat!"
                game.cur_events_list.insert(0, Single_Event(string, ["health", "alert"]))

        # Clear the list of cats that died this moon.
        game.just_died.clear()

        resource_dir = "resources/dicts/events/lifegen_events/"
        with open(f"{resource_dir}ceremonies.json",
                  encoding="ascii") as read_file:
            self.b_txt = ujson.loads(read_file.read())
        with open(f"{resource_dir}events.json",
                  encoding="ascii") as read_file:
            self.c_txt = ujson.loads(read_file.read())
        with open(f"{resource_dir}df.json",
                  encoding="ascii") as read_file:
            self.df_txt = ujson.loads(read_file.read())
        if not game.clan.your_cat.dead and game.clan.your_cat.status != 'exiled' and not game.clan.your_cat.outside:
            if game.clan.your_cat.moons == 0:
                self.generate_birth_event()
            elif game.clan.your_cat.moons < 6:
                self.generate_events() 
            elif game.clan.your_cat.moons == 6:
                self.generate_app_ceremony()
            elif game.clan.your_cat.status in ['apprentice', 'medicine cat apprentice', 'mediator apprentice', "queen's apprentice"]:
                self.generate_events()
            elif game.clan.your_cat.status in ['warrior', 'medicine cat', 'mediator', "queen"] and not game.clan.your_cat.w_done and game.clan.your_cat.shunned == 0:
                self.generate_ceremony()
            elif game.clan.your_cat.status != 'elder' and game.clan.your_cat.moons != 119:
                self.generate_events()
            elif game.clan.your_cat.moons == 119 and not game.clan.your_cat.outside and game.clan.your_cat.shunned == 0:
                if not game.switches['window_open']:
                    RetireScreen('events screen')
                else:
                    game.switches['windows_dict'].append('retire')
            elif game.clan.your_cat.moons == 120 and game.clan.your_cat.status == 'elder' and game.clan.your_cat.shunned == 0:
                self.generate_elder_ceremony()
            elif game.clan.your_cat.status == 'elder':
                self.generate_events()
            
            if game.clan.your_cat.joined_df:
                self.generate_df_events()
            
            if game.clan.your_cat.moons >= 12:
                self.check_leader(self.checks)
                if game.clan.your_cat.shunned == 0:
                    self.check_gain_app(self.checks)
                self.check_gain_mate(self.checks)
                self.check_gain_kits(self.checks)
                self.generate_mate_events()
                if game.clan.your_cat.shunned == 0:
                    self.check_retire()

            if random.randint(1,15) == 1 and game.clan.your_cat.status != "newborn":
                self.gain_acc()

        elif game.clan.your_cat.dead and game.clan.your_cat.dead_for == 0:
            self.generate_death_event()
        elif game.clan.your_cat.dead:
            self.generate_events()
        elif game.clan.your_cat.status == 'exiled':
            self.generate_exile_event()
            
        game.clan.murdered = False
        game.clan.affair = False
        game.clan.exile_return = False
        
        self.current_events.clear()
        self.check_achievements()
        self.generate_dialogue_focus()
        self.checks = [len(game.clan.your_cat.apprentice), len(game.clan.your_cat.mate), len(game.clan.your_cat.inheritance.get_blood_kits()), None]
        if game.clan.leader:
            self.checks[3] = game.clan.leader.ID
            
        # Resort
        if game.sort_type != "id":
            Cat.sort_cats()

        # Clear all the loaded event dicts.
        GenerateEvents.clear_loaded_events()

        # autosave
        if game.clan.clan_settings.get("autosave") and game.clan.age % 5 == 0:
            try:
                game.save_cats()
                game.clan.save_clan()
                game.clan.save_pregnancy(game.clan)
                game.save_events()
            except:
                SaveError(traceback.format_exc())
    
    def add_freshkill(self):
        """Adds amount of freshkill needed for the Clan"""
        if not game.clan.freshkill_pile:
            game.clan.freshkill_pile = FreshkillPile()

        game.clan.freshkill_pile.add_freshkill(game.clan.freshkill_pile.amount_food_needed())

    def generate_dialogue_focus(self):
        """Handles dialogue focus for each moon, generating conditional focuses for specific events (war, starving) or random chance focuses (valentines, quality of leadership)"""
        resource_dir = "resources/dicts/"
        with open(f"{resource_dir}dialogue_focuses.json",
                encoding="ascii") as read_file:
            dialogue_focuses = ujson.loads(read_file.read())
        
        # Handle lost focus for conditional focuses that have no set duration
        if game.clan.focus == "war" and not game.clan.war.get("at_war"):
            game.clan.focus = ""
            game.clan.focus_moons = 0
        if game.clan.focus == "starving" and game.clan.freshkill_pile.total_amount > game.clan.freshkill_pile.amount_food_needed()*0.5:
            game.clan.focus = ""
            game.clan.focus_moons = 0
            for clan_cat in game.clan.clan_cats:
                clan_cat_cat = Cat.fetch_cat(clan_cat)
                if clan_cat_cat:
                    clan_cat_cat.faith -= round(random.uniform(-1,0), 2)

        # Handle lost focus for focuses that have set duration
        if game.clan.focus and dialogue_focuses[game.clan.focus]["duration"] != -1 and game.clan.focus_moons >= dialogue_focuses[game.clan.focus]["duration"]:
            if "focus_loss" in dialogue_focuses[game.clan.focus]:
                game.cur_events_list.append(Single_Event(self.process_text(random.choice(dialogue_focuses[game.clan.focus]["focus_loss"])), "misc"))
            game.clan.focus = ""
            game.clan.focus_moons = 0
            game.clan.focus_cat = None
            
        if not game.clan.focus:
            if game.clan.war.get("at_war"):
                game.clan.focus = "war"
            elif game.clan.freshkill_pile.total_amount < game.clan.freshkill_pile.amount_food_needed()*0.5:
                game.clan.focus = "starving"
            elif random.randint(1,30) == 1:
                possible_focuses = ["valentines", "hailstorm"]
                if game.clan.leader and not game.clan.leader.dead and not game.clan.leader.outside and game.clan.leader.ID != game.clan.your_cat.ID:
                    possible_focuses.append("leader")
                focus_chosen = random.choice(possible_focuses)
                if dialogue_focuses[focus_chosen]["season"] == "Any" or dialogue_focuses[focus_chosen]["season"] == game.clan.current_season:
                    game.clan.focus = focus_chosen

        if game.clan.focus:
            game.clan.focus_moons += 1
            if game.clan.focus_moons == 1 and dialogue_focuses[game.clan.focus]["moon_event"]:
                game.cur_events_list.insert(0, Single_Event(self.process_text(random.choice(dialogue_focuses[game.clan.focus]["moon_event"])), "misc"))

                
    def gain_acc(self):
        if game.clan.clan_settings["all accessories"]:
            return
        possible_accs = ["WILD", "PLANT", "COLLAR", "FLOWER", "PLANT2", "SNAKE", "SMALLANIMAL", "DEADINSECT", "ALIVEINSECT",
                         "FRUIT", "CRAFTED", "TAIL2", "NEONPINK"]
        acc_list = []
        if "WILD" in possible_accs:
            acc_list.extend(Pelt.wild_accessories)
        if "PLANT" in possible_accs:
            acc_list.extend(Pelt.plant_accessories)
        if "COLLAR" in possible_accs:
            acc_list.extend(Pelt.collars)
        if "FLOWER" in possible_accs:
            acc_list.extend(Pelt.flower_accessories)
        if "PLANT2" in possible_accs:
            acc_list.extend(Pelt.plant2_accessories)
        if "SNAKE" in possible_accs:
            acc_list.extend(Pelt.snake_accessories)
        if "SMALLANIMAL" in possible_accs:
            acc_list.extend(Pelt.smallAnimal_accessories)
        if "DEADINSECT" in possible_accs:
            acc_list.extend(Pelt.deadInsect_accessories)
        if "ALIVEINSECT" in possible_accs:
            acc_list.extend(Pelt.aliveInsect_accessories)
        if "FRUIT" in possible_accs:
            acc_list.extend(Pelt.fruit_accessories)
        if "CRAFTED" in possible_accs:
            acc_list.extend(Pelt.crafted_accessories)
        if "TAIL2" in possible_accs:
            acc_list.extend(Pelt.tail2_accessories)
        if "NEONPINK" in possible_accs:
            acc_list.extend(Pelt.np_autism)
        if "NOTAIL" in game.clan.your_cat.pelt.scars or "HALFTAIL" in game.clan.your_cat.pelt.scars:
            for acc in Pelt.tail_accessories + Pelt.tail2_accessories:
                if acc in acc_list:
                    try:
                        acc_list.remove(acc)
                    except ValueError:
                        print(f'attempted to remove {acc} from possible acc list, but it was not in the list!')

        if not game.clan.your_cat.pelt.inventory:
            game.clan.your_cat.pelt.inventory = []
        acc = random.choice(acc_list)
        counter = 0
        while acc in game.clan.your_cat.pelt.inventory:
            counter+=1
            if counter == 30:
                break
            acc = random.choice(acc_list)
        game.clan.your_cat.pelt.inventory.append(acc)
        ACC_DISPLAY = None
        with open(f"resources/dicts/acc_display.json", 'r') as read_file:
            ACC_DISPLAY = ujson.loads(read_file.read())
        string = f"You found a new accessory, acc_singular! You choose to store it in a safe place for now."
        string = string.replace("acc_singular", str(ACC_DISPLAY[acc]["singular"]))
        game.cur_events_list.insert(0, Single_Event(string, "alert", game.clan.your_cat.ID))
    
    def check_achievements(self):
        you = game.clan.your_cat
        achievements = set()
        murder_history = History.get_murders(you)
        clan_cats = game.clan.clan_cats
        count_alive_cats = 0
        if murder_history:
            if 'is_murderer' in murder_history:
                num_victims = len(murder_history["is_murderer"])
                if num_victims >= 0:
                    achievements.add("1")
                if num_victims >= 5:
                    achievements.add("2")
                if num_victims >= 20:
                    achievements.add("3")
                if num_victims >= 50:
                    achievements.add("4")
        else:
            if you.moons >= 120:
                achievements.add("25")
            

        for cat in clan_cats:
            if Cat.all_cats.get(cat).pelt.tortiebase and Cat.all_cats.get(cat).gender == 'male':
                achievements.add("5")
            if Cat.all_cats.get(cat).insulted == True:
                achievements.add("29")
            if (Cat.all_cats.get(cat).name.prefix == "Coffee" and Cat.all_cats.get(cat).name.suffix == "dot") or (Cat.all_cats.get(cat).name.prefix == "Chibi" and Cat.all_cats.get(cat).name.suffix == "Galaxies"):
                achievements.add("30")
            if Cat.all_cats.get(cat).status == 'apprentice' and Cat.all_cats.get(cat).name.prefix == "Pea" and Cat.all_cats.get(cat).pelt.white_colours:
                achievements.add("33")
            if Cat.all_cats.get(cat).status == 'kitten' and Cat.all_cats.get(cat).moons > 5:
                achievements.add("34")
            ##WILDCARD check, because I've lost control of my life
            ##Declare Lists of wildcard combos for comparison. (Will be made more professional later.)
            not_wildcard_patterns = ['tabby', 'ticked', 'mackerel', 'classic', 'agouti', 'smoke', 'single']
            ##Actual check for wildcardness
            if Cat.all_cats.get(cat).pelt.name == "Tortie" or Cat.all_cats.get(cat).pelt.name == "Calico":
                ID_check = Cat.all_cats.get(cat).ID 
                ##Check if wildcard colour combo
                if (Cat.all_cats.get(cat).pelt.colour == "WHITE" and not Cat.all_cats.get(cat).pelt.tortiecolour == "WHITE"):
                    achievements.add("6")
                elif ((Cat.all_cats.get(cat).pelt.colour in Pelt.black_colours or Cat.all_cats.get(cat).pelt.colour in Pelt.white_colours) and Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.black_colours or Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.white_colours):
                    achievements.add("6")
                elif ((Cat.all_cats.get(cat).pelt.colour in Pelt.ginger_colours) and Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.ginger_colours or Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.white_colours):
                    achievements.add("6")
                elif ((Cat.all_cats.get(cat).pelt.colour in Pelt.brown_colours) and Cat.all_cats.get(cat).pelt.tortiecolour in Pelt.white_colours):
                    achievements.add("6")
                ##Check if wildcard pattern combo       
                ##rewritten wildcard pattern combo
                if Cat.all_cats.get(cat).pelt.tortiebase in Pelt.tabbies and not Cat.all_cats.get(cat).pelt.tortiepattern == "single" and Cat.all_cats.get(cat).pelt.tortiebase != Cat.all_cats.get(cat).pelt.tortiepattern:
                    achievements.add("6")
                if Cat.all_cats.get(cat).pelt.tortiebase in Pelt.spotted and not Cat.all_cats.get(cat).pelt.tortiepattern == "single" and Cat.all_cats.get(cat).pelt.tortiebase != Cat.all_cats.get(cat).pelt.tortiepattern:
                    achievements.add("6")
                if Cat.all_cats.get(cat).pelt.tortiebase in Pelt.exotic and not Cat.all_cats.get(cat).pelt.tortiepattern == "single" and Cat.all_cats.get(cat).pelt.tortiebase != Cat.all_cats.get(cat).pelt.tortiepattern:
                    achievements.add("6")
                if Cat.all_cats.get(cat).pelt.tortiebase in Pelt.plain and not Cat.all_cats.get(cat).pelt.tortiepattern in not_wildcard_patterns and Cat.all_cats.get(cat).pelt.tortiebase != Cat.all_cats.get(cat).pelt.tortiepattern:
                    achievements.add("6")
            ##code block for achievement 31
            achieve31RankList = ['warrior', 'mediator', 'leader']
            achieve31UsedRanks = []
            if len(Cat.all_cats.get(cat).mate) >= 2:
                catMateIDs = Cat.all_cats.get(cat).mate.copy()
                if Cat.all_cats.get(cat).status in achieve31RankList:
                    achieve31UsedRanks.append(Cat.all_cats.get(cat).status)
                    for cat in clan_cats:
                        if Cat.all_cats.get(cat).ID in catMateIDs:
                            if (Cat.all_cats.get(cat).status in achieve31RankList) and (Cat.all_cats.get(cat).status not in achieve31UsedRanks):
                                achieve31UsedRanks.append(Cat.all_cats.get(cat).status)
                        countranks = 0
                        for i in achieve31UsedRanks:
                            if i in achieve31RankList:
                                countranks += 1
                            if countranks >= 3:
                                achievements.add("31")
            #code for achievement 23 + 24
            if Clan.age >= 1:
                if not Cat.all_cats.get(cat).dead and not Cat.all_cats.get(cat).outside:
                    count_alive_cats += 1
                if count_alive_cats == 1 and Cat.all_cats.get(cat).ID == you.ID:
                    achievements.add('23')
                elif count_alive_cats >= 100:
                    achievements.add('24')

        if you.joined_df:
            achievements.add("7")
        
        if len(you.former_apprentices) >= 1:
            achievements.add("8")
        if len(you.former_apprentices) >= 5:
            achievements.add("9")
        
        if you.inheritance.get_children():
            achievements.add("10")
        for i in you.relationships.keys():
            if you.relationships.get(i).dislike >= 60:
                achievements.add("11")
            if you.relationships.get(i).romantic_love >= 60:
                achievements.add('12')
            
        if len(you.mate) >= 5:
            achievements.add('13')
        if you.status == 'warrior':
            achievements.add('14')
        elif you.status == 'medicine cat':
            achievements.add('15')
        elif you.status == 'mediator':
            achievements.add('16')
        elif you.status == 'deputy':
            achievements.add('17')
        elif you.status == 'leader':
            achievements.add('18')
        elif you.status == 'elder':
            achievements.add('19')
        elif you.status == 'queen':
            achievements.add('32')
        
        if you.moons >= 200:
            achievements.add('20')
        if you.exiled:
            achievements.add('21')
        elif you.outside:
            achievements.add('22')
            
        if you.experience >= 100:
            achievements.add('26')
        if you.experience >= 200:
            achievements.add('27')
        if you.experience >= 300:
            achievements.add('28')
        
        for i in game.clan.achievements:
            achievements.add(i)
        
        game.clan.achievements = list(achievements)
                

    def generate_birth_event(self):
        '''Handles birth event generation and creation of inheritance for your cat'''
        possible_birth_types = list(BirthType)
        if not game.clan.clan_settings["single parentage"]:
            possible_birth_types.remove(BirthType.ONE_PARENT)
            possible_birth_types.remove(BirthType.ONE_OUTSIDER_PARENT)
        birth_type = random.choice(possible_birth_types)

        def create_siblings(parent1, parent2, adoptive_parents):
            '''Creates siblings for your cat'''
            num_siblings = random.randint(1,5)
            kits = Pregnancy_Events.get_kits(kits_amount=num_siblings, cat=parent1, other_cat=parent2, adoptive_parents=adoptive_parents, clan=game.clan)
            return kits

        def pick_valid_parent(other_parent=None):
            MAX_ATTEMPTS = 50
            
            def is_valid_parent(candidate_id, other_parent_gender=None, other_parent_id=None, other_parent_age=None):
                cat = Cat.all_cats[candidate_id]
                is_age_compatible = (other_parent_age is None) or (cat.age == other_parent_age)
                is_gender_compatible = True
                is_relation_compatible = cat.is_potential_mate(Cat.all_cats.get(other_parent_id)) if other_parent_id else True
                if not game.clan.clan_settings["same sex birth"]:
                    is_gender_compatible = (other_parent_gender is None) or (cat.gender != other_parent_gender)
                return (cat.ID != game.clan.your_cat.ID and cat.ID != other_parent_id and not cat.dead and not cat.outside
                        and cat.age in ["young adult", "adult", "senior adult"] and cat.moons > 17
                        and "apprentice" not in cat.status and is_age_compatible and is_gender_compatible and is_relation_compatible)

            for _ in range(MAX_ATTEMPTS):
                if other_parent and other_parent.mate:
                    candidate_id = random.choice(other_parent.mate)
                    if is_valid_parent(candidate_id, other_parent.gender if other_parent else None, other_parent.ID if other_parent else None, other_parent.age if other_parent else None):
                        return Cat.all_cats.get(candidate_id)
                candidate_id = random.choice(Cat.all_cats_list).ID
                if is_valid_parent(candidate_id, other_parent.gender if other_parent else None, other_parent.ID if other_parent else None, other_parent.age if other_parent else None):
                    return Cat.all_cats.get(candidate_id)
            
            return None

        def get_parents(birth_type):
            '''Handles creating inheritance for your cat'''
            try:
                parent1 = None
                parent2 = None
                adoptive_parents = []
                if birth_type == BirthType.NO_PARENTS:
                    thought = "Is glad that their kits are safe"
                    parent1 = create_new_cat(Cat,
                                                loner=True,
                                                status=random.choice(["loner", "kittypet"]),
                                                alive=False,
                                                thought=thought,
                                                age=random.randint(15,120),
                                                outside=True)[0]
                    parent1.backstory = random.choice(["refugee2", "refugee3", "refugee4"])
                    
                elif birth_type == BirthType.ONE_PARENT:
                    parent1 = pick_valid_parent()
                
                elif birth_type == BirthType.TWO_PARENTS:
                    parent1 = pick_valid_parent()
                    parent2 = pick_valid_parent(parent1)
                    if not parent2:
                        for i in range(5):
                            if not parent2:
                                parent1 = pick_valid_parent()
                                parent2 = pick_valid_parent(parent1)
                            else:
                                break
                    parent1.set_mate(parent2)

                elif birth_type == BirthType.ONE_ADOPTIVE_PARENT:
                    adoptive_parent1 = pick_valid_parent()
                    adoptive_parents = [adoptive_parent1.ID]
                    thought = "Is glad that their kits are safe"
                    parent1 = create_new_cat(Cat,
                                                loner=True,
                                                status=random.choice(["loner", "kittypet"]),
                                                alive=False,
                                                thought=thought,
                                                age=random.randint(15,120),
                                                outside=True)[0]
                    parent1.backstory = random.choice(["refugee2", "refugee3", "refugee4"])
                    parent2 = create_new_cat(Cat,
                                                loner=True,
                                                status=random.choice(["loner", "kittypet"]),
                                                alive=False,
                                                thought=thought,
                                                age=random.randint(15,120),
                                                outside=True)[0]
                    if not game.clan.clan_settings["same sex birth"]:
                        if parent1.gender == parent2.gender:
                            if parent1.gender == "female":
                                parent1.gender = "male"
                                parent1.genderalign = "male"
                            else:
                                parent1.gender = "female"
                                parent1.genderalign = "female"
                    parent2.backstory = random.choice(["refugee2", "refugee3", "refugee4"])
                

                elif birth_type == BirthType.TWO_ADOPTIVE_PARENTS:
                    adoptive_parent1 = pick_valid_parent()
                    adoptive_parent2 = pick_valid_parent(adoptive_parent1)
                    if not adoptive_parent2:
                        for i in range(5):
                            if not adoptive_parent2:
                                adoptive_parent1 = pick_valid_parent()
                                adoptive_parent2 = pick_valid_parent(adoptive_parent1)
                            else:
                                break
                    adoptive_parent1.set_mate(adoptive_parent2)
                    adoptive_parents = [adoptive_parent1.ID, adoptive_parent2.ID]
                    thought = "Is glad that their kits are safe"
                    parent1 = create_new_cat(Cat,
                                                loner=True,
                                                status=random.choice(["loner", "kittypet"]),
                                                alive=False,
                                                thought=thought,
                                                age=random.randint(15,120),
                                                outside=True)[0]
                    parent1.backstory = random.choice(["refugee2", "refugee3", "refugee4"])
                    parent2 = create_new_cat(Cat,
                                                loner=True,
                                                status=random.choice(["loner", "kittypet"]),
                                                alive=False,
                                                thought=thought,
                                                age=random.randint(15,120),
                                                outside=True)[0]
                    if not game.clan.clan_settings["same sex birth"]:
                        if parent1.gender == parent2.gender:
                            if parent1.gender == "female":
                                parent1.gender = "male"
                                parent1.genderalign = "male"
                            else:
                                parent1.gender = "female"
                                parent1.genderalign = "female"
                    parent2.backstory = random.choice(["refugee2", "refugee3", "refugee4"])

                elif birth_type == BirthType.ONE_OUTSIDER_PARENT:
                    parent1 = create_new_cat(Cat,
                                                status="warrior",
                                                alive=True,
                                                age=random.randint(15,120),
                                                outside=False)[0]
                    parent1.backstory = random.choice(["loner1", "loner2", "loner4", "kittypet1", "kittypet2", "kittypet3", "kittypet4", "kittypet6", "rogue1", "rogue2", "rogue3", "rogue5", "rogue8", "refugee2", "refugee3", "refugee4"])

                elif birth_type == BirthType.TWO_OUTSIDER_PARENTS:
                    parent1 = create_new_cat(Cat,
                                                status="warrior",
                                                alive=True,
                                                age=random.randint(15,120),
                                                outside=False)[0]
                    parent1.backstory = random.choice(["loner1", "loner2", "loner4", "kittypet1", "kittypet2", "kittypet3", "kittypet4", "kittypet6", "rogue1", "rogue2", "rogue3", "rogue5", "rogue8", "refugee2", "refugee3", "refugee4"])
                    parent2 = create_new_cat(Cat,
                                                status="warrior",
                                                alive=True,
                                                age=parent1.moons + random.randint(1,5),
                                                outside=False)[0]
                    parent2.backstory = random.choice(["loner1", "loner2", "loner4", "kittypet1", "kittypet2", "kittypet3", "kittypet4", "kittypet6", "rogue1", "rogue2", "rogue3", "rogue5", "rogue8", "refugee2", "refugee3", "refugee4"])
                    parent1.init_all_relationships()
                    parent2.init_all_relationships()
                    parent1.set_mate(parent2)

                return birth_type, parent1, parent2, adoptive_parents
            except Exception as e:
                birth_type = random.choice(list(BirthType))
                return get_parents(birth_type)



        def handle_backstory(siblings):
            '''Handles creating backstories for your cat'''
            if birth_type in [BirthType.NO_PARENTS, BirthType.ONE_ADOPTIVE_PARENT, BirthType.TWO_ADOPTIVE_PARENTS]:
                backstory = random.choice(["abandoned1", "abandoned2", "abandoned4", "loner3", "orphaned1", "orphaned2", "orphaned3", "orphaned4", "orphaned5", "orphaned6", "orphaned7", "outsider1"])
            elif birth_type == BirthType.ONE_PARENT:
                backstory = random.choice(["halfclan1", "halfclan4", "halfclan4", "halfclan5", "halfclan6", "halfclan7", "halfclan8", "halfclan9", "halfclan10", "outsider_roots1", "outsider_roots3", "outsider_roots4", "outsider_roots5", "outsider_roots6", "outsider_roots7", "outsider_roots8", "clanborn"])
            elif birth_type == BirthType.TWO_PARENTS:
                backstory = "clanborn"
            elif birth_type == BirthType.ONE_OUTSIDER_PARENT:
                backstory = "outsider1"
            elif birth_type == BirthType.TWO_OUTSIDER_PARENTS:
                backstory = "outsider1"
            
            game.clan.your_cat.backstory = backstory
            if siblings:
                for sibling in siblings:
                    sibling.backstory = backstory
        
        def handle_inheritance(parent1, parent2, adoptive_parents, siblings):            
            for c in siblings + [game.clan.your_cat]:
                if parent1:
                    c.parent1 = parent1.ID
                if parent2:
                    c.parent2 = parent2.ID
                if adoptive_parents:
                    c.adoptive_parents = adoptive_parents
                c.create_inheritance_new_cat()
                c.init_all_relationships()
            
        def handle_birth_event(birth_type, parent1, parent2, adoptive_parents, siblings):
            replacements = {}
            replacements["y_c"] = str(game.clan.your_cat.name)
            birth_value = birth_type.value
            if parent1 and not parent1.dead:
                self.cat_dict["parent1"] = parent1
                replacements["parent1"] = str(parent1.name)
            if parent2 and not parent2.dead:
                self.cat_dict["parent2"] = parent2
                replacements["parent2"] = str(parent2.name)
            if len(adoptive_parents) == 1:
                self.cat_dict["parent1"] = Cat.all_cats.get(adoptive_parents[0])
                replacements["parent1"] = str(Cat.all_cats.get(adoptive_parents[0]).name)
            if len(adoptive_parents) == 2:
                self.cat_dict["parent1"] = Cat.all_cats.get(adoptive_parents[0])
                self.cat_dict["parent2"] = Cat.all_cats.get(adoptive_parents[1])
                replacements["parent1"] = str(Cat.all_cats.get(adoptive_parents[0]).name)
                replacements["parent2"] = str(Cat.all_cats.get(adoptive_parents[1]).name)
            if siblings:
                birth_value += "_siblings"
                num_siblings = len(siblings)
                if num_siblings == 1:
                    replacements["insert_siblings"] = f"{siblings[0].name}"
                if num_siblings == 2:
                    replacements["insert_siblings"] = f"{siblings[0].name} and {siblings[1].name}"
                if num_siblings == 3:
                    replacements["insert_siblings"] = f"{siblings[0].name}, {siblings[1].name}, and {siblings[2].name}"
                if num_siblings == 4:
                    replacements["insert_siblings"] = f"{siblings[0].name}, {siblings[1].name}, {siblings[2].name}, and {siblings[3].name}"
                if num_siblings == 5:
                    replacements["insert_siblings"] = f"{siblings[0].name}, {siblings[1].name}, {siblings[2].name}, {siblings[3].name}, and {siblings[4].name}"
            
            birth_txt = random.choice(self.b_txt[birth_value])

            process_text_dict = self.cat_dict.copy()
            for abbrev in process_text_dict.keys():
                abbrev_cat = process_text_dict[abbrev]
                process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
            birth_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), birth_txt)

            birth_txt = self.process_text_birth(birth_txt)

            for key, value in replacements.items():
                birth_txt = birth_txt.replace(key, str(value))

            MAX_ATTEMPTS = 10
            if not birth_txt:
                for _ in range(MAX_ATTEMPTS):
                    birth_txt = random.choice(self.b_txt[birth_value])
                    process_text_dict = self.cat_dict.copy()
                    for abbrev in process_text_dict.keys():
                        abbrev_cat = process_text_dict[abbrev]
                        process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
                    birth_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), birth_txt)
                    birth_txt = self.process_text_birth(birth_txt)

                    for key, value in replacements.items():
                        birth_txt = birth_txt.replace(key, str(value))
                    
                    if birth_txt:
                        break

            
            game.cur_events_list.insert(0, Single_Event(birth_txt, ["alert", "birth_death"], game.clan.your_cat.ID))

        birth_type, parent1, parent2, adoptive_parents = get_parents(birth_type)
        siblings = create_siblings(parent1, parent2, adoptive_parents) if random.randint(1,4) != 1 else []
        handle_inheritance(parent1, parent2, adoptive_parents, siblings)
        handle_backstory(siblings)
        handle_birth_event(birth_type, parent1, parent2, adoptive_parents, siblings)
        if parent1 and not parent1.dead and parent1.gender == "female":
            parent1.get_injured("recovering from birth")
        elif parent2 and not parent2.dead and parent2.gender == "female":
            parent2.get_injured("recovering from birth")
        adoptive_parents_cats = []
        for c in adoptive_parents:
            adoptive_parents_cats.append(Cat.fetch_cat(c))
        for c in [parent1, parent2] + adoptive_parents_cats:
            for s in siblings + [game.clan.your_cat]:
                if s and c and not c.dead and not c.outside:
                    y = random.randrange(0, 20)
                    start_relation = Relationship(c, s, False, True)
                    start_relation.platonic_like += 30 + y
                    start_relation.comfortable = 10 + y
                    start_relation.admiration = 15 + y
                    start_relation.trust = 10 + y
                    c.relationships[s.ID] = start_relation
                    y = random.randrange(0, 20)
                    start_relation = Relationship(s, c, False, True)
                    start_relation.platonic_like += 30 + y
                    start_relation.comfortable = 10 + y
                    start_relation.admiration = 15 + y
                    start_relation.trust = 10 + y
                    s.relationships[c.ID] = start_relation
        game.clan.your_cat.w_done = False
        game.clan.your_cat.age = "newborn"
        game.switches['continue_after_death'] = False
        self.cat_dict.clear()
        
    def get_living_cats(self):
        living_cats = []
        for the_cat in Cat.all_cats_list:
            if not the_cat.dead and not the_cat.outside and not the_cat.moons == -1:
                living_cats.append(the_cat)
        return living_cats

    def process_text_birth(self, text):
        process_text_dict = self.cat_dict.copy()
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))

        text = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), text)

        text = text.replace("c_n", str(game.clan.name))
        if "w_c" in text:
            if game.clan.war.get("at_war", True):
                text = text.replace("w_c", str(game.clan.war["enemy"]))
        return text

    def process_text(self, text):
        self.cat_dict.clear()
        text = adjust_txt(Cat, text, game.clan.your_cat, self.cat_dict, r_c_allowed=True, o_c_allowed=True)

        process_text_dict = self.cat_dict.copy()
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))

        text = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), text)

        text = text.replace("c_n", str(game.clan.name))
        if "w_c" in text:
            if game.clan.war.get("at_war", True):
                text = text.replace("w_c", str(game.clan.war["enemy"]))

        return text
    
    def generate_events(self):
        resource_dir = "resources/dicts/events/lifegen_events/events/"
        
        if game.clan.your_cat.dead:
            if not game.clan.your_cat.df and not game.clan.your_cat.outside:
                resource_dir = "resources/dicts/events/lifegen_events/events_dead_sc/"
            elif game.clan.your_cat.df and not game.clan.your_cat.outside:
                resource_dir = "resources/dicts/events/lifegen_events/events_dead_df/"
            elif not game.clan.your_cat.df and game.clan.your_cat.ID in game.clan.unknown_cats:
                resource_dir = "resources/dicts/events/lifegen_events/events_dead_ur/"

        elif game.clan.your_cat.shunned > 0 and not game.clan.your_cat.outside and not game.clan.your_cat.dead:
            resource_dir = "resources/dicts/events/lifegen_events/shunned/"

        
        all_events = {}
        if game.clan.your_cat.status != 'exiled' and game.clan.your_cat.status != 'newborn' or (game.clan.your_cat.status == "newborn" and game.clan.your_cat.dead):
            with open(f"{resource_dir}{game.clan.your_cat.status}.json",
                    encoding="ascii") as read_file:
                all_events = ujson.loads(read_file.read())
        
        if game.clan.your_cat.status not in ["newborn", "kitten"] and game.clan.your_cat.shunned == 0 and not game.clan.your_cat.dead:
            with open(f"{resource_dir}general_no_kit.json", encoding="ascii") as read_file:
                general_no_kit_events = ujson.loads(read_file.read())

        with open(f"{resource_dir}general.json",
                encoding="ascii") as read_file:
            general_events = ujson.loads(read_file.read())

        status = game.clan.your_cat.status
        if game.clan.your_cat.status == 'elder' and game.clan.your_cat.moons < 100:
            status = "young elder"
            with open(f"{resource_dir}{status}.json", encoding="ascii") as read_file:
                all_events = ujson.loads(read_file.read())

        possible_events = []
        try:
            possible_events = all_events[f"{status} general"]
        except:
            pass
        possible_events += general_events["general general"]
        if game.clan.your_cat.status not in ["newborn", "kitten"] and game.clan.your_cat.shunned == 0 and not game.clan.your_cat.dead:
            possible_events += general_no_kit_events["general general"]

        # Add old events
        if not all_events:
            return
        if f"{status} old" in all_events:
            possible_events = possible_events + all_events[f"{status} old"]

        cluster, second_cluster = get_cluster(game.clan.your_cat.personality.trait)

        if cluster:
            possible_events = possible_events + all_events[f"{status} {cluster}"] + general_events[f"general {cluster}"]
        if second_cluster:
            possible_events = possible_events + all_events[f"{status} {second_cluster}"] + general_events[f"general {second_cluster}"]

        for i in range(random.randint(0,5)):
            involved_cats = []
            if possible_events:
                involved_cats.append(game.clan.your_cat.ID)
                event = random.choice(possible_events)
                current_event = self.process_text(event)

                while current_event == "":
                    event = random.choice(possible_events)
                    current_event = self.process_text(event)

                if event not in self.current_events:
                    # add the cats from lifegen events to involved cats
                    for i in self.cat_dict.items():
                        involved_cats.append(i[1].ID)
                    self.current_events.insert(0, event)
                    game.cur_events_list.insert(0, Single_Event(current_event, "alert", [i for i in involved_cats]))
            else:
                print('No possible events?')
  
            
    def generate_kit_events(self):
        # Parent events for moons 1-5
        if game.clan.your_cat.parent1:
            moons_list = range(2, 6)
            parents_txt = {1: "one_parent", 2: "two_parents"}
            for moons in moons_list:
                if game.clan.your_cat.moons == moons:
                    for parents in parents_txt.keys():
                        if (game.clan.your_cat.parent1 and not game.clan.your_cat.parent2 and not Cat.all_cats[game.clan.your_cat.parent1].dead and not Cat.all_cats[game.clan.your_cat.parent1].outside) or \
                        (parents == 2 and game.clan.your_cat.parent1 and game.clan.your_cat.parent2 and not Cat.all_cats[game.clan.your_cat.parent1].dead and not Cat.all_cats[game.clan.your_cat.parent1].outside and not Cat.all_cats[game.clan.your_cat.parent2].dead and not Cat.all_cats[game.clan.your_cat.parent2].outside):
                            kit_event1 = random.choice(self.c_txt[f"moon_{moons}_{parents_txt[parents]}"])
                            if game.clan.your_cat.parent1:
                                kit_event1 = re.sub(r'(?<!\/)parent1(?!\/)', str(Cat.all_cats[game.clan.your_cat.parent1].name), kit_event1)
                                self.cat_dict["parent1"] = Cat.all_cats[game.clan.your_cat.parent1]
                            if game.clan.your_cat.parent2:
                                kit_event1 = re.sub(r'(?<!\/)parent2(?!\/)', str(Cat.all_cats[game.clan.your_cat.parent2].name), kit_event1)
                                self.cat_dict["parent2"] = Cat.all_cats[game.clan.your_cat.parent2]

                            kit_event = kit_event1
                            
                            if kit_event not in game.cur_events_list:
                                process_text_dict = self.cat_dict.copy()
                                for abbrev in process_text_dict.keys():
                                    abbrev_cat = process_text_dict[abbrev]
                                    process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
                                kit_event = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), kit_event)
                                game.cur_events_list.insert(0, Single_Event(kit_event, "alert", game.clan.your_cat.ID))
                            break

    def generate_app_ceremony(self):
        try:
            ceremony_txt = ""
            if game.clan.your_cat.shunned != 0:
                ceremony_txt = ceremony_txt = random.choice(self.b_txt['apprentice ceremony shunned'])
            else:
                if game.clan.your_cat.mentor:
                    ceremony_txt = random.choice(self.b_txt[game.clan.your_cat.status + ' ceremony'])
                else:
                    ceremony_txt = random.choice(self.b_txt[game.clan.your_cat.status + ' ceremony no mentor'])
            ceremony_txt = ceremony_txt.replace('c_n', str(game.clan.name))
            ceremony_txt = ceremony_txt.replace('y_c', str(game.clan.your_cat.name))
            if game.clan.leader and not game.clan.leader.dead and not game.clan.leader.outside:
                ceremony_txt = re.sub(r'(?<!\/)l_n(?!\/)', str(game.clan.leader.name), ceremony_txt)
                self.cat_dict["l_n"] = game.clan.leader
            elif game.clan.deputy and not game.clan.deputy.dead and not game.clan.deputy.outside:
                ceremony_txt = re.sub(r'(?<!\/)l_n(?!\/)', str(game.clan.deputy.name), ceremony_txt)
                self.cat_dict["d_n"] = game.clan.deputy
            if game.clan.your_cat.mentor:
                ceremony_txt = re.sub(r'(?<!\/)m_n(?!\/)', str(Cat.all_cats[game.clan.your_cat.mentor].name), ceremony_txt)
                self.cat_dict["m_n"] = Cat.all_cats[game.clan.your_cat.mentor]

            process_text_dict = self.cat_dict.copy()
            for abbrev in process_text_dict.keys():
                abbrev_cat = process_text_dict[abbrev]
                process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
            ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
            
            game.cur_events_list.insert(0, Single_Event(ceremony_txt, ["alert", "ceremony"], game.clan.your_cat.ID))
        except:
            print("ERROR with app ceremony")
                
    def generate_ceremony(self):
        if game.clan.your_cat.former_mentor:
            if Cat.all_cats[game.clan.your_cat.former_mentor[-1]].dead and game.clan.your_cat.status == 'medicine cat':
                ceremony_txt = random.choice(self.b_txt[game.clan.your_cat.status + '_ceremony_no_mentor'])

            if game.clan.your_cat.forgiven < 10 and game.clan.your_cat.forgiven > 0:
                try:
                    ceremony_txt = random.choice(self.b_txt[game.clan.your_cat.status + '_ceremony forgiven'])
                except:
                    ceremony_txt = random.choice(self.b_txt[game.clan.your_cat.status + '_ceremony'])
            else:
                ceremony_txt = random.choice(self.b_txt[game.clan.your_cat.status + '_ceremony'])
            former_mentor = Cat.all_cats[game.clan.your_cat.former_mentor[-1]]
            ceremony_txt = re.sub(r'(?<!\/)m_n(?!\/)', str(former_mentor.name), ceremony_txt)
            self.cat_dict["m_n"] = former_mentor
        else:
            if game.clan.your_cat.forgiven < 10:
                try:
                    ceremony_txt = random.choice(self.b_txt[game.clan.your_cat.status + '_ceremony_no_mentor forgiven'])
                except:
                    ceremony_txt = random.choice(self.b_txt[game.clan.your_cat.status + '_ceremony_no_mentor'])
            else:
                ceremony_txt = random.choice(self.b_txt[game.clan.your_cat.status + '_ceremony_no_mentor'])
        
        ceremony_txt = ceremony_txt.replace('c_n', str(game.clan.name))
        ceremony_txt = ceremony_txt.replace('y_c', str(game.clan.your_cat.name))
        
        if game.clan.leader and not game.clan.leader.dead and not game.clan.leader.outside:
            ceremony_txt = re.sub(r'(?<!\/)l_n(?!\/)', str(game.clan.leader.name), ceremony_txt)
            self.cat_dict["l_n"] = game.clan.leader
        elif game.clan.deputy and not game.clan.deputy.dead and not game.clan.deputy.outside:
            ceremony_txt = re.sub(r'(?<!\/)l_n(?!\/)', str(game.clan.deputy.name), ceremony_txt)
            self.cat_dict["d_n"] = game.clan.deputy


        random_honor = None
        resource_dir = "resources/dicts/events/ceremonies/"
        with open(f"{resource_dir}ceremony_traits.json",
                encoding="ascii") as read_file:
            TRAITS = ujson.loads(read_file.read())
        try:
            random_honor = random.choice(TRAITS[game.clan.your_cat.personality.trait])
        except KeyError:
            random_honor = "hard work"
        ceremony_txt = ceremony_txt.replace('honor1', random_honor)
        process_text_dict = self.cat_dict.copy()
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
        ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
        game.cur_events_list.insert(0, Single_Event(ceremony_txt, ["alert", "ceremony"], game.clan.your_cat.ID))
        game.clan.your_cat.w_done = True
        
    def generate_elder_ceremony(self):
        ceremony_txt = random.choice(self.b_txt['elder_ceremony'])
        ceremony_txt = ceremony_txt.replace('c_n', str(game.clan.name))
        ceremony_txt = ceremony_txt.replace('y_c', str(game.clan.your_cat.name))
        if game.clan.leader and not game.clan.leader.dead and not game.clan.leader.outside:
            ceremony_txt = re.sub(r'(?<!\/)l_n(?!\/)', str(game.clan.leader.name), ceremony_txt)
            self.cat_dict["l_n"] = game.clan.leader
        elif game.clan.deputy and not game.clan.deputy.dead and not game.clan.deputy.outside:
            ceremony_txt = re.sub(r'(?<!\/)l_n(?!\/)', str(game.clan.deputy.name), ceremony_txt)
            self.cat_dict["l_n"] = game.clan.deputy
        process_text_dict = self.cat_dict.copy()
        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
        ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
        game.cur_events_list.insert(0, Single_Event(ceremony_txt, ["alert", "ceremony"], game.clan.your_cat.ID))
    
    
    def check_gain_app(self, checks):
        if game.clan.your_cat.dead or game.clan.your_cat.outside:
            return
        if len(game.clan.your_cat.apprentice) == checks[0] + 1:
            if 'request apprentice' in game.switches:
                game.switches['request apprentice'] = False
            resource_dir = "resources/dicts/events/lifegen_events/"
            with open(f"{resource_dir}ceremonies.json",
                    encoding="ascii") as read_file:
                self.d_txt = ujson.loads(read_file.read())
            ceremony_txt = random.choice(self.d_txt['gain_app ' + game.clan.your_cat.status])
            if game.clan.leader and not game.clan.leader.dead and not game.clan.leader.outside:
                ceremony_txt = re.sub(r'(?<!\/)l_n(?!\/)', str(game.clan.leader.name), ceremony_txt)
                self.cat_dict["l_n"] = game.clan.leader
            elif game.clan.deputy and not game.clan.deputy.dead and not game.clan.deputy.outside:
                ceremony_txt = re.sub(r'(?<!\/)l_n(?!\/)', str(game.clan.deputy.name), ceremony_txt)
                self.cat_dict["l_n"] = game.clan.deputy
            app = Cat.all_cats[game.clan.your_cat.apprentice[-1]]
            self.cat_dict["app1"] = app
            ceremony_txt = re.sub(r'(?<!\/)app1(?!\/)', str(app.name), ceremony_txt)
            process_text_dict = self.cat_dict.copy()
            for abbrev in process_text_dict.keys():
                abbrev_cat = process_text_dict[abbrev]
                process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
            ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
            game.cur_events_list.insert(0, Single_Event(ceremony_txt, ["alert", "ceremony"], game.clan.your_cat.ID))

    def check_gain_mate(self, checks):
        
        if len(game.clan.your_cat.mate) == checks[1] + 1:
            try:
                resource_dir = "resources/dicts/events/lifegen_events/"
                with open(f"{resource_dir}ceremonies.json",
                        encoding="ascii") as read_file:
                    self.d_txt = ujson.loads(read_file.read())
                try:
                    ceremony_txt = random.choice(self.d_txt["gain_mate " + game.clan.your_cat.status.replace(" ", "") + " " + Cat.all_cats[game.clan.your_cat.mate[-1]].status.replace(" ", "")])
                except:
                    ceremony_txt = random.choice(self.d_txt["gain_mate general"])
                mate = Cat.all_cats[game.clan.your_cat.mate[-1]]
                self.cat_dict["mate1"] = mate
                ceremony_txt = re.sub(r'(?<!\/)mate1(?!\/)', str(mate.name), ceremony_txt)
                process_text_dict = self.cat_dict.copy()
                for abbrev in process_text_dict.keys():
                    abbrev_cat = process_text_dict[abbrev]
                    process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
                ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
                game.cur_events_list.insert(0, Single_Event(ceremony_txt, "alert", game.clan.your_cat.ID))
            except:
                print("You gained a new mate but an event could not be shown1")
        elif 'accept' in game.switches and game.switches['accept']:
            try:
                resource_dir = "resources/dicts/events/lifegen_events/"
                with open(f"{resource_dir}ceremonies.json",
                        encoding="ascii") as read_file:
                    self.d_txt = ujson.loads(read_file.read())
                try:
                    ceremony_txt = random.choice(self.d_txt["gain_mate " + game.clan.your_cat.status.replace(" ", "") + " " + Cat.all_cats[game.clan.your_cat.mate[-1]].status.replace(" ", "")])
                except:
                    ceremony_txt = random.choice(self.d_txt["gain_mate general"])
                mate = Cat.all_cats[game.clan.your_cat.mate[-1]]
                self.cat_dict["mate1"] = mate
                ceremony_txt = re.sub(r'(?<!\/)mate1(?!\/)', str(mate.name), ceremony_txt)
                process_text_dict = self.cat_dict.copy()
                for abbrev in process_text_dict.keys():
                    abbrev_cat = process_text_dict[abbrev]
                    process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
                ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
                game.cur_events_list.insert(0, Single_Event(ceremony_txt, "alert", game.clan.your_cat.ID))
                game.switches['accept'] = False
                checks[1] = len(game.clan.your_cat.mate)
            except:
                print("You gained a new mate but an event could not be shown1")

        elif 'reject' in game.switches and game.switches['reject']:
            try:
                resource_dir = "resources/dicts/events/lifegen_events/"
                with open(f"{resource_dir}mate_lifegen.json",
                        encoding="ascii") as read_file:
                    self.f_txt = ujson.loads(read_file.read())
                r = random.randint(1,3)
                if r == 1:
                    game.switches['new_mate'].relationships[game.clan.your_cat.ID].romantic_love -= 8
                elif r == 2:
                    game.switches['new_mate'].relationships[game.clan.your_cat.ID].romantic_love -= 8
                    game.switches['new_mate'].relationships[game.clan.your_cat.ID].platonic_like -= 8
                    game.clan.your_cat.relationships[game.switches['new_mate'].ID].comfortable -= 5
                elif r == 3:
                    game.switches['new_mate'].relationships[game.clan.your_cat.ID].romantic_love -= 5
                    game.switches['new_mate'].relationships[game.clan.your_cat.ID].platonic_like -= 10
                    game.clan.your_cat.relationships[game.switches['new_mate'].ID].platonic_like -= 10
                    game.clan.your_cat.relationships[game.switches['new_mate'].ID].dislike += 10

                ceremony_txt = random.choice(self.f_txt['reject' + str(r)])
                mate = game.switches['new_mate']
                self.cat_dict["mate1"] = mate
                ceremony_txt = re.sub(r'(?<!\/)mate1(?!\/)', str(mate.name), ceremony_txt)
                process_text_dict = self.cat_dict.copy()
                for abbrev in process_text_dict.keys():
                    abbrev_cat = process_text_dict[abbrev]
                    process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
                ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
                game.cur_events_list.insert(0, Single_Event(ceremony_txt, "alert", game.clan.your_cat.ID))
                game.switches['reject'] = False
            except:
                print("You rejected a cat but an event could not be shown")
    
    def check_leader(self, checks):
        if game.clan.leader:
            if checks[3] != game.clan.leader.ID and game.clan.your_cat.status == 'leader' and not game.switches['window_open'] and game.clan.your_cat.shunned == 0:
                DeputyScreen('events screen')
            elif checks[3] != game.clan.leader.ID and game.clan.your_cat.status == 'leader' and game.clan.your_cat.shunned == 0:
                game.switches['windows_dict'].append('deputy')
            
    def check_gain_kits(self, checks):
        if len(game.clan.your_cat.inheritance.get_blood_kits()) > checks[2] and not game.switches['window_open']:
            NameKitsWindow('events screen')
        elif len(game.clan.your_cat.inheritance.get_blood_kits()) > checks[2]:
            game.switches['windows_dict'].append('name kits')

    def generate_mate_events(self):
        if len(game.clan.your_cat.mate) > 0:
            if random.randint(1,20) == 1:
                mate1 = Cat.all_cats.get(random.choice(game.clan.your_cat.mate))
                if mate1.dead or mate1.outside:
                    return
                ceremony_txt = random.choice(self.c_txt['mate_events'])
                self.cat_dict["mate1"] = mate1
                ceremony_txt = re.sub(r'(?<!\/)mate1(?!\/)', str(mate1.name), ceremony_txt)
                process_text_dict = self.cat_dict.copy()
                for abbrev in process_text_dict.keys():
                    abbrev_cat = process_text_dict[abbrev]
                    process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
                ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
                game.cur_events_list.insert(1, Single_Event(ceremony_txt, "alert", game.clan.your_cat.ID))
            if game.clan.clan_settings['affair']:
                if random.randint(1,50) == 1:
                    mate1 = Cat.all_cats.get(random.choice(game.clan.your_cat.mate))
                    if mate1.dead or mate1.outside:
                        return
                    ceremony_txt = random.choice(self.c_txt['affair_events'])
                    self.cat_dict["mate1"] = mate1
                    ceremony_txt = re.sub(r'(?<!\/)mate1(?!\/)', str(mate1.name), ceremony_txt)
                    process_text_dict = self.cat_dict.copy()
                    for abbrev in process_text_dict.keys():
                        abbrev_cat = process_text_dict[abbrev]
                        process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
                    ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
                    game.cur_events_list.insert(1, Single_Event(ceremony_txt, "alert", game.clan.your_cat.ID))
        if random.randint(1,30) == 1:
            if (len(game.clan.your_cat.mate) > 0 and game.clan.clan_settings['affair']) or (len(game.clan.your_cat.mate) == 0):
                if len(game.clan.your_cat.mate) > 0:
                    if random.randint(1,50) != 1:
                        return
                    mate1 = Cat.all_cats.get(random.choice(game.clan.your_cat.mate))
                    if mate1.dead or mate1.outside:
                        return
                c = Cat.all_cats.get(random.choice(game.clan.clan_cats))
                counter = 0
                while not c.relationships.get(game.clan.your_cat.ID) or c.relationships.get(game.clan.your_cat.ID).romantic_love < 10 or c.outside:
                    if counter == 15:
                        return
                    c = Cat.all_cats.get(random.choice(game.clan.clan_cats))
                    counter+=1
                ceremony_txt = random.choice(self.c_txt['crush_events'])
                self.cat_dict["crush1"] = c
                ceremony_txt = re.sub(r'(?<!\/)crush1(?!\/)', str(c.name), ceremony_txt)
                process_text_dict = self.cat_dict.copy()
                for abbrev in process_text_dict.keys():
                    abbrev_cat = process_text_dict[abbrev]
                    process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
                ceremony_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), ceremony_txt)
                game.cur_events_list.insert(1, Single_Event(ceremony_txt, "alert", game.clan.your_cat.ID))
                
                
    def check_retire(self):
        if 'retire' in game.switches:
            if game.switches['retire']:
                game.switches['retire'] = False
        if 'retire_reject' in game.switches:
            if game.switches['retire_reject']:              
                game.switches['retire_reject'] = False
    
    def generate_death_event(self):
        if game.clan.your_cat.status == 'kitten':
            ceremony_txt = random.choice(self.b_txt['death_kit'])
            game.cur_events_list.insert(1, Single_Event(ceremony_txt, game.clan.your_cat.ID))
        elif game.clan.your_cat.status == 'medicine cat apprentice':
            ceremony_txt = random.choice(self.b_txt['death_medapp'])
            game.cur_events_list.insert(1, Single_Event(ceremony_txt, game.clan.your_cat.ID))
        elif game.clan.your_cat.status == 'apprentice':
            ceremony_txt = random.choice(self.b_txt['death_app'])
            game.cur_events_list.insert(1, Single_Event(ceremony_txt, game.clan.your_cat.ID))
        elif game.clan.your_cat.status == 'mediator apprentice':
            ceremony_txt = random.choice(self.b_txt['death_mediapp'])
            game.cur_events_list.insert(1, Single_Event(ceremony_txt, game.clan.your_cat.ID))
        elif game.clan.your_cat.status == 'elder':
            ceremony_txt = random.choice(self.b_txt['death_elder'])
            game.cur_events_list.insert(1, Single_Event(ceremony_txt, "alert", game.clan.your_cat.ID))
        else:
            ceremony_txt = random.choice(self.b_txt['death'])
            game.cur_events_list.insert(1, Single_Event(ceremony_txt, game.clan.your_cat.ID))
            
    def generate_exile_event(self):
        evt = Single_Event(random.choice(self.c_txt["exiled"]))
        if evt not in game.cur_events_list:
            game.cur_events_list.insert(0, evt)
            
    def generate_df_events(self):
        if random.randint(1,3) == 1:
            evt = self.process_text(random.choice(self.df_txt["general"]))
            if evt:
                involved_cats = []
                involved_cats.append(game.clan.your_cat.ID)
                for i in self.cat_dict.items():
                    involved_cats.append(i[1].ID)
                evt = Single_Event(evt, ["alert"], [i for i in involved_cats])
                if evt not in game.cur_events_list:
                    game.cur_events_list.insert(0, evt)
        if random.randint(1,30) == 1:
            r_clanmate = Cat.all_cats.get(random.choice(game.clan.clan_cats))
            counter = 0
            while r_clanmate.dead or r_clanmate.outside or r_clanmate.status in ['kitten', 'newborn', 'deputy', 'leader'] or r_clanmate.joined_df or r_clanmate.ID == game.clan.your_cat.ID:
                counter+=1
                if counter > 15:
                    return
                r_clanmate = Cat.all_cats.get(random.choice(game.clan.clan_cats))
            
            r_clanmate.joined_df = True
            r_clanmate.faith -= 1
            r_clanmate.update_df_mentor()
            self.cat_dict["c_m"] = r_clanmate
            evt_txt = random.choice(self.df_txt["clanmate"])
            evt_txt = re.sub(r'(?<!\/)c_m(?!\/)', str(r_clanmate.name), evt_txt)
            process_text_dict = self.cat_dict.copy()
            for abbrev in process_text_dict.keys():
                abbrev_cat = process_text_dict[abbrev]
                process_text_dict[abbrev] = (abbrev_cat, random.choice(abbrev_cat.pronouns))
            evt_txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), evt_txt)
            evt = Single_Event(evt_txt, ["alert"], r_clanmate.ID)
            if evt not in game.cur_events_list:
                game.cur_events_list.insert(0, evt)

    def handle_lead_den_event(self):
        """
        Handles the events that are chosen in the leaders den the previous moon and resets the relevant clan settings
        """
        if game.clan.clan_settings["lead_den_clan_event"]:
            info_dict = game.clan.clan_settings["lead_den_clan_event"]
            gathering_cat = Cat.fetch_cat(info_dict["cat_ID"])

            # drop the event if the gathering cat is no longer available
            if gathering_cat.exiled or gathering_cat.dead or gathering_cat.outside:
                return

            other_clan = get_other_clan(info_dict["other_clan"])

            # get events
            events = generate_events.possible_lead_den_events(
                cat=gathering_cat,
                other_clan_temper=other_clan.temperament,
                player_clan_temper=info_dict["player_clan_temper"],
                event_type="other_clan",
                interaction_type=info_dict["interaction_type"],
                success=info_dict["success"],
            )
            if events:
                chosen_event = random.choice(events)

                # get text
                event_text = chosen_event["event_text"]

                # change relations and append relation text
                rel_change = chosen_event["rel_change"]
                other_clan.relations += rel_change
                if rel_change > 0:
                    event_text += f" (o_c_n relations improved.)"
                elif rel_change == 0:
                    event_text += f" (o_c_n relations unchanged.)"
                else:
                    event_text += f" (o_c_n relations worsened.)"

                # adjust text and add to event list
                event_text = event_text_adjust(
                    Cat,
                    event_text,
                    main_cat=gathering_cat,
                    other_clan=other_clan,
                    clan=game.clan)
                game.cur_events_list.insert(4, Single_Event(event_text, "other_clans", [gathering_cat.ID]))

                game.clan.clan_settings["lead_den_clan_event"] = {}

        if game.clan.clan_settings["lead_den_outsider_event"]:
            info_dict = game.clan.clan_settings["lead_den_outsider_event"]
            outsider_cat = Cat.fetch_cat(info_dict["cat_ID"])
            involved_cats = [outsider_cat.ID]
            invited_cats = []

            events = generate_events.possible_lead_den_events(
                cat=outsider_cat,
                event_type="outsider",
                interaction_type=info_dict["interaction_type"],
                success=info_dict["success"],
            )
            chosen_event = random.choice(events)

            # get event text
            event_text = chosen_event["event_text"]
            cat_dict = chosen_event["m_c"]

            # ADJUST REP
            game.clan.reputation += chosen_event["rep_change"]

            additional_kits = None
            # SUCCESS/FAIL
            if info_dict["success"]:
                if info_dict["interaction_type"] == "hunt":
                    History.add_death(
                        outsider_cat,
                        death_text=history_text_adjust(
                            "m_c was killed by c_n.",
                            other_clan_name=None,
                            clan=game.clan,
                        ),
                    )
                    outsider_cat.die()

                elif info_dict["interaction_type"] == "drive":
                    outsider_cat.status = "exiled"
                    outsider_cat.exiled = True
                    outsider_cat.driven_out = True

                elif info_dict["interaction_type"] in ["invite", "search"]:
                    # ADD TO CLAN AND CHECK FOR KITS
                    additional_kits = outsider_cat.add_to_clan()

                    if additional_kits:
                        event_text += " m_c brings along {PRONOUN/m_c/poss} "
                        if len(additional_kits) > 1:
                            event_text += str(len(additional_kits)) + " kittens."
                        else:
                            event_text += "kit."

                        for kit_ID in additional_kits:
                            # add to involved cat list
                            involved_cats.append(kit_ID)
                            kit = Cat.fetch_cat(kit_ID)

                    invited_cats = [outsider_cat.ID]
                    invited_cats.extend(additional_kits)

                    for cat_ID in invited_cats:
                        invited_cat = Cat.fetch_cat(cat_ID)
                        if invited_cat.status.lower() in [
                            "kittypet",
                            "loner",
                            "rogue",
                            "former clancat",
                            "exiled",
                        ]:
                            if (
                                "guided" in invited_cat.backstory
                                and invited_cat.status != "exiled"
                            ):
                                invited_cat.backstory = "outsider1"

                            if (
                                invited_cat.backstory
                                in BACKSTORIES["backstory_categories"][
                                    "healer_backstories"
                                ]
                            ):
                                invited_cat.status = "medicine cat"

                            elif invited_cat.age in ["newborn", "kitten"]:
                                invited_cat.status = invited_cat.age
                                if not invited_cat.name.suffix:
                                    invited_cat.name = Name(
                                        invited_cat.status,
                                        invited_cat.name.prefix,
                                        invited_cat.name.suffix,
                                        invited_cat.pelt.colour,
                                        invited_cat.pelt.name,
                                        invited_cat.pelt.tortiepattern,
                                        game.clan.biome,
                                    )
                                    invited_cat.name.give_suffix(
                                        pelt=None,
                                        biome=game.clan.biome,
                                        tortiepattern=None,
                                    )
                                    invited_cat.specsuffix_hidden = False

                            elif invited_cat.age == "senior":
                                invited_cat.status = "elder"
                            elif invited_cat.age == "adolescent":
                                invited_cat.status = "apprentice"
                                invited_cat.update_mentor()
                            else:
                                invited_cat.status = "warrior"

                        invited_cat.create_relationships_new_cat()

                # this handles ceremonies for cats coming into the clan
                if invited_cats:
                    self.handle_lost_cats_return(invited_cats)

            # give new thought to cats
            if "new_thought" in cat_dict:
                outsider_cat.thought = event_text_adjust(
                    Cat,
                    text=cat_dict["new_thought"],
                    main_cat=outsider_cat,
                    clan=game.clan)

            if "kit_thought" in cat_dict:
                if additional_kits is None:
                    additional_kits = outsider_cat.get_children()
                if additional_kits:
                    for kit_ID in additional_kits:
                        kit = Cat.fetch_cat(kit_ID)
                        kit.thought = event_text_adjust(
                            Cat,
                            text=cat_dict["kit_thought"],
                            main_cat=kit,
                            clan=game.clan)

            if "relationships" in cat_dict:
                unpack_rel_block(Cat, cat_dict["relationships"], extra_cat=outsider_cat)

            # adjust text and add to event list
            event_text = event_text_adjust(
                Cat,
                text=event_text,
                main_cat=outsider_cat,
                clan=game.clan)

            game.cur_events_list.insert(4, Single_Event(event_text, "misc", involved_cats))

            game.clan.clan_settings["lead_den_outsider_event"] = {}

        game.clan.clan_settings["lead_den_interaction"] = False

    def mediator_events(self, cat):
        """Check for mediator events"""
        # If the cat is a mediator, check if they visited other clans
        if cat.status in ["mediator", "mediator apprentice"] and not cat.not_working():
            # 1 /10 chance
            if not int(random.random() * 10):
                increase = random.randint(-2, 6)
                clan = random.choice(game.clan.all_clans)
                clan.relations += increase
                dispute_type = random.choice(
                    ["hunting", "border", "personal", "herb-gathering"]
                )
                text = (
                    f"{cat.name} travels to {clan} to "
                    f"resolve some recent {dispute_type} disputes. "
                )
                if increase > 4:
                    text += (
                        f"The meeting goes better than expected, and "
                        f"{cat.name} returns with a plan to solve the "
                        f"issue for good."
                    )
                elif increase == 0:
                    text += "However, no progress was made."
                elif increase < 0:
                    text += f"However, it seems {cat.name} only made {clan} more upset."

                game.cur_events_list.append(Single_Event(text, "other_clans", cat.ID))

        if game.clan.clan_settings["become_mediator"]:
            # Note: These chances are large since it triggers every moon.
            # Checking every moon has the effect giving older cats more chances to become a mediator
            _ = game.config["roles"]["become_mediator_chances"]
            if cat.status in _ and not int(random.random() * _[cat.status]):
                game.cur_events_list.append(
                    Single_Event(
                        f"{cat.name} had chosen to use their skills and experience to help "
                        f"solve the Clan's disagreements. A meeting is called, and they "
                        f"become the Clan's newest mediator. ",
                        "ceremony",
                        cat.ID,
                    )
                )
                cat.status_change("mediator")
        if game.clan.clan_settings['become_med']:
            # Note: These chances are large since it triggers every moon.
            # Checking every moon has the effect giving older cats more chances to become a mediator
            _ = game.config["roles"]["become_med_chances"]
            if cat.status in _ and \
                    not int(random.random() * _[cat.status]):
                game.cur_events_list.append(
                    Single_Event(
                        f"{cat.name} had chosen to use their skills and experience to heal "
                        f"and commune with StarClan. A meeting is called, and they "
                        f"become the Clan's newest medicine cat. ", "ceremony",
                        cat.ID))
                cat.status_change("medicine cat")
        if game.clan.clan_settings['become_queen']:
            # Note: These chances are large since it triggers every moon.
            # Checking every moon has the effect giving older cats more chances to become a mediator
            _ = game.config["roles"]["become_queen_chances"]
            if cat.status in _ and \
                    not int(random.random() * _[cat.status]):
                game.cur_events_list.append(
                    Single_Event(
                        f"{cat.name} had chosen to use their skills and experience to help nuture the "
                        f"Clan's young. A meeting is called, and they "
                        f"become the Clan's newest queen. ", "ceremony",
                        cat.ID))
                cat.status_change("queen")

    def get_moon_freshkill(self):
        """Adding auto freshkill for the current moon."""
        healthy_hunter = list(
            filter(
                lambda c: c.status in ["warrior", "apprentice", "leader", "deputy"]
                and not c.dead
                and not c.outside
                and not c.exiled
                and not c.not_working(),
                Cat.all_cats.values(),
            )
        )

        prey_amount = 0
        for cat in healthy_hunter:
            lower_value = game.prey_config["auto_warrior_prey"][0]
            upper_value = game.prey_config["auto_warrior_prey"][1]
            if cat.status == "apprentice":
                lower_value = game.prey_config["auto_apprentice_prey"][0]
                upper_value = game.prey_config["auto_apprentice_prey"][1]

            prey_amount += random.randint(lower_value, upper_value)
        game.freshkill_event_list.append(
            f"The clan managed to catch {prey_amount} pieces of prey in this moon."
        )
        game.clan.freshkill_pile.add_freshkill(prey_amount)

    def herb_gather(self):
        """
        TODO: DOCS
        """
        
        event_list = []
        meds_available = get_alive_status_cats(Cat, ["medicine cat", "medicine cat apprentice"], working=True,
                                                sort=True)
        for med in meds_available:
            if game.clan.current_season in ["Newleaf", "Greenleaf"]:
                amount = random.choices([0, 1, 2, 3], [1, 2, 2, 2], k=1)
            elif game.clan.current_season == "Leaf-fall":
                amount = random.choices([0, 1, 2], [3, 2, 1], k=1)
            else:
                amount = random.choices([0, 1], [3, 1], k=1)
            if amount[0] != 0:
                herbs_found = random.sample(HERBS, k=amount[0])
                herb_display = []
                for herb in herbs_found:
                    if herb in ["blackberry"]:
                        continue
                    if game.clan.current_season in ["Newleaf", "Greenleaf"]:
                        amount = random.choices([1, 2, 3], [3, 3, 1], k=1)
                    else:
                        amount = random.choices([1, 2], [4, 1], k=1)
                    if herb in game.clan.herbs:
                        game.clan.herbs[herb] += amount[0]
                    else:
                        game.clan.herbs.update({herb: amount[0]})
                    herb_display.append(herb.replace("_", " "))
            else:
                herbs_found = []
                herb_display = []
            if not herbs_found:
                event_list.append(f"{med.name} could not find any herbs this moon.")
            else:
                try:
                    if len(herbs_found) == 1:
                        insert = f"{herb_display[0]}"
                    elif len(herbs_found) == 2:
                        insert = f"{herb_display[0]} and {herb_display[1]}"
                    else:
                        insert = f"{', '.join(herb_display[:-1])}, and {herb_display[-1]}"
                    event_list.append(f"{med.name} gathered {insert} this moon.")
                except IndexError:
                    event_list.append(
                        f"{med.name} could not find any herbs this moon."
                    )
                    return
        game.herb_events_list.extend(event_list)

    def handle_focus(self):
        """
        This function should be called late in the 'one_moon' function and handles all focuses which are possible to handle here:
            - business as usual
            - hunting
            - herb gathering
            - threaten outsiders
            - seek outsiders
            - sabotage other clans
            - aid other clans
            - raid other clans
            - hoarding
        Focus which are not able to be handled here:
            rest and recover - handled in:
                - 'self.handle_outbreaks'
                - 'condition_events.handle_injuries'
                - 'condition_events.handle_illnesses'
                - 'cat.moon_skip_illness'
                - 'cat.moon_skip_injury'
        """
        # if no focus is selected, skip all other
        focus_text = "This shouldn't show up, report a bug for the focus feature."
        if game.clan.clan_settings.get(
            "business as usual"
        ) or game.clan.clan_settings.get("rest and recover"):
            return
        elif game.clan.clan_settings.get("hunting"):
            # handle warrior
            healthy_warriors = list(
                filter(
                    lambda c: c.status in ["warrior", "leader", "deputy"]
                    and not c.dead
                    and not c.outside
                    and not c.exiled
                    and not c.not_working(),
                    Cat.all_cats.values(),
                )
            )
            warrior_amount = (
                len(healthy_warriors) * game.config["focus"]["hunting"]["warrior"]
            )

            # handle apprentices
            healthy_apprentices = list(
                filter(
                    lambda c: c.status == "apprentice"
                    and not c.dead
                    and not c.outside
                    and not c.exiled
                    and not c.not_working(),
                    Cat.all_cats.values(),
                )
            )
            app_amount = (
                len(healthy_apprentices) * game.config["focus"]["hunting"]["apprentice"]
            )

            # finish
            total_amount = warrior_amount + app_amount
            game.clan.freshkill_pile.add_freshkill(total_amount)
            if total_amount > 1:
                focus_text = f"With the heightened focus of the Clan, {total_amount} additional pieces of prey were gathered."
            elif total_amount == 1:
                focus_text = f"With the heightened focus of the Clan, {total_amount} additional piece of prey was gathered."
            else:
                focus_text = "Despite the additional focus of the Clan, no prey could be gathered."
            game.freshkill_event_list.append(focus_text)

        elif game.clan.clan_settings.get("herb gathering"):
            herbs_found = []

            # handle medicine cats
            healthy_meds = list(
                filter(
                    lambda c: c.status == "medicine cat"
                    and not c.dead
                    and not c.outside
                    and not c.exiled
                    and not c.not_working(),
                    Cat.all_cats.values(),
                )
            )
            med_amount = game.config["focus"]["herb gathering"]["med"]
            for med in healthy_meds:
                herbs_found.extend(random.sample(HERBS, k=med_amount))

            # handle medicine cat apprentices
            healthy_med_apps = list(
                filter(
                    lambda c: c.status == "medicine cat apprentice"
                    and not c.dead
                    and not c.outside
                    and not c.exiled
                    and not c.not_working(),
                    Cat.all_cats.values(),
                )
            )
            med_amount = game.config["focus"]["herb gathering"]["med_apprentice"]
            for med in healthy_med_apps:
                herbs_found.extend(random.sample(HERBS, k=med_amount))

            # finish
            herb_amount = len(herbs_found)
            herb_counter = Counter(herbs_found)
            game.clan.herbs.update(herb_counter)
            if herb_amount > 1:
                focus_text = f"With the additional focus of the Clan, {herb_amount} herbs were gathered."
            elif herb_amount == 1:
                focus_text = f"With the additional focus of the Clan, {herb_amount} herb was gathered."
            else:
                focus_text = f"Despite the additional focus of the Clan, no herbs could be gathered."

            log_text = (
                "With the additional focus of the Clan, following herbs were gathered: "
            )
            idx = 0
            for herb, amount in herb_counter.items():
                log_text += str(amount) + " " + herb.replace("_", " ")
                idx += 1
                if idx < len(herb_counter) - 1:
                    log_text += ", "
                elif idx < len(herb_counter):
                    log_text += " and "
            log_text += "."
            game.herb_events_list.append(log_text)

        elif game.clan.clan_settings.get("threaten outsiders"):
            amount = game.config["focus"]["outsiders"]["reputation"]
            change_clan_reputation(-amount)
            focus_text = None

        elif game.clan.clan_settings.get("seek outsiders"):
            amount = game.config["focus"]["outsiders"]["reputation"]
            change_clan_reputation(amount)
            focus_text = None

        elif game.clan.clan_settings.get(
            "sabotage other clans"
        ) or game.clan.clan_settings.get("aid other clans"):
            amount = game.config["focus"]["other clans"]["relation"]
            if game.clan.clan_settings.get("sabotage other clans"):
                amount = amount * -1
            for name in game.clan.clans_in_focus:
                clan = [clan for clan in game.clan.all_clans if clan.name == name][0]
                sabotage = game.clan.clan_settings.get("sabotage other clans")
                change_clan_relations(clan, amount)
            focus_text = None

        elif game.clan.clan_settings.get("hoarding") or game.clan.clan_settings.get(
            "raid other clans"
        ):
            info_dict = game.config["focus"]["hoarding"]
            if game.clan.clan_settings.get("raid other clans"):
                info_dict = game.config["focus"]["raid other clans"]

            involved_cats = {"injured": [], "sick": []}
            # handle prey
            healthy_warriors = list(
                filter(
                    lambda c: c.status in ["warrior", "leader", "deputy"]
                    and not c.dead
                    and not c.outside
                    and not c.exiled
                    and not c.not_working(),
                    Cat.all_cats.values(),
                )
            )
            warrior_amount = len(healthy_warriors) * info_dict["prey_warrior"]
            game.clan.freshkill_pile.add_freshkill(warrior_amount)
            if warrior_amount > 1:
                game.freshkill_event_list.append(
                    f"With the additional focus of the Clan, {warrior_amount} prey pieces were caught."
                )
            else:
                game.freshkill_event_list.append(
                    f"With the additional focus of the Clan, {warrior_amount} prey piece was caught."
                )

            # handle herbs
            herbs_found = []
            healthy_meds = list(
                filter(
                    lambda c: c.status == "medicine cat"
                    and not c.dead
                    and not c.outside
                    and not c.exiled
                    and not c.not_working(),
                    Cat.all_cats.values(),
                )
            )
            med_amount = info_dict["herb_medicine"]
            for med in healthy_meds:
                herbs_found.extend(random.sample(HERBS, k=med_amount))
            herb_amount = len(herbs_found)
            if herb_amount > 0:
                herb_counter = Counter(herbs_found)
                game.clan.herbs.update(herb_counter)
                log_text = "With the additional focus of the Clan, following herbs were gathered: "
                idx = 0
                for herb, amount in herb_counter.items():
                    log_text += str(amount) + " " + herb.replace("_", " ")
                    idx += 1
                    if idx < len(herb_counter) - 1:
                        log_text += ", "
                    elif idx < len(herb_counter):
                        log_text += " and "
                log_text += "."
                game.herb_events_list.append(log_text)

            # handle injuries / illness
            relevant_cats = healthy_warriors + healthy_meds
            if game.clan.clan_settings.get("raid other clans"):
                chance = info_dict[f"injury_chance_warrior"]
                # increase the chance of injuries depending on how many clans are raided
                increase = info_dict["chance_increase_per_clan"]
                chance -= increase * len(game.clan.clans_in_focus)
            for cat in relevant_cats:
                # if the raid setting or 50/50 for hoarding to get to the injury part
                if game.clan.clan_settings.get(
                    "raid other clans"
                ) or random.getrandbits(1):
                    status_use = cat.status
                    if status_use in ["deputy", "leader"]:
                        status_use = "warrior"
                    chance = info_dict[f"injury_chance_{status_use}"]
                    if game.clan.clan_settings.get("raid other clans"):
                        # increase the chance of injuries depending on how many clans are raided
                        increase = info_dict["chance_increase_per_clan"]
                        chance -= increase * len(game.clan.clans_in_focus)

                    if not int(random.random() * chance):  # 1/chance
                        possible_injuries = []
                        injury_dict = info_dict["injuries"]
                        for injury, amount in injury_dict.items():
                            possible_injuries.extend([injury] * amount)
                        chosen_injury = random.choice(possible_injuries)
                        cat.get_injured(chosen_injury)
                        involved_cats["injured"].append(cat.ID)
                else:
                    chance = game.config["focus"]["hoarding"]["illness_chance"]
                    if not int(random.random() * chance):  # 1/chance
                        possible_illnesses = []
                        injury_dict = game.config["focus"]["hoarding"]["illnesses"]
                        for illness, amount in injury_dict.items():
                            possible_illnesses.extend([illness] * amount)
                        chosen_illness = random.choice(possible_illnesses)
                        cat.get_ill(chosen_illness)
                        involved_cats["sick"].append(cat.ID)

            # if it is raiding, lower the relation to other clans
            if game.clan.clan_settings.get("raid other clans"):
                for name in game.clan.clans_in_focus:
                    clan = [clan for clan in game.clan.all_clans if clan.name == name][
                        0
                    ]
                    amount = -game.config["focus"]["raid other clans"]["relation"]
                    change_clan_relations(clan, amount)

            # finish
            text_snippet = "due the additional work of hoarding herbs and prey."
            if game.clan.clan_settings.get("raid other clans"):
                text_snippet = "while raiding other Clans to get additional prey."
            for condition_type, value in involved_cats.items():
                if len(value) == 1:
                    game.cur_events_list.append(
                        Single_Event(
                            f"One cat got {condition_type} during {text_snippet}",
                            "health",
                            value,
                        )
                    )
                elif len(value) > 1:
                    game.cur_events_list.append(
                        Single_Event(
                            f"Multiple cats got {condition_type} {text_snippet}",
                            "health",
                            value,
                        )
                    )

            if warrior_amount > 1 and herb_amount > 1:
                focus_text = f"With the additional focus of the Clan, {warrior_amount} pieces of prey and {herb_amount} herbs were gathered."
            elif warrior_amount > 1 and herb_amount == 1:
                focus_text = f"With the additional focus of the Clan, {warrior_amount} pieces of prey and {herb_amount} herb were gathered."
            elif warrior_amount > 1 and herb_amount <= 0:
                focus_text = f"With the additional focus of the Clan, {warrior_amount} pieces of prey and no herbs were gathered."
            elif warrior_amount == 1 and herb_amount > 1:
                focus_text = f"With the additional focus of the Clan, {warrior_amount} piece of prey and {herb_amount} herbs were gathered."
            elif warrior_amount <= 0 and herb_amount > 1:
                focus_text = f"With the additional focus of the Clan, no prey and {herb_amount} herbs were gathered."
            elif warrior_amount == 1 and herb_amount == 1:
                focus_text = f"With the additional focus of the Clan, {warrior_amount} piece of prey and {herb_amount} herb were gathered."
            elif warrior_amount <= 0 and herb_amount <= 0:
                focus_text = "Despite the additional focus of the Clan, neither prey nor herbs could be gathered."
            else:
                focus_text = "This is a bug, report it - focus feature"

        if focus_text:
            game.cur_events_list.insert(0, Single_Event(focus_text, "misc"))

    def handle_lost_cats_return(self, predetermined_cat_IDs: list = None):
        """
        TODO: DOCS
        """
        cat_IDs = []
        if predetermined_cat_IDs:
            cat_IDs = predetermined_cat_IDs

        if not predetermined_cat_IDs:
            eligible_cats = []
            for cat in Cat.all_cats.values():
                if cat.outside and cat.ID not in Cat.outside_cats:
                    # The outside-value must be set to True before the cat can go to cotc
                    Cat.outside_cats.update({cat.ID: cat})

                if (
                    cat.outside
                    and cat.status
                    not in [
                        "kittypet",
                        "loner",
                        "rogue",
                        "former Clancat",
                        "driven off",
                    ]
                    and not cat.exiled
                    and not cat.dead
                ):
                    eligible_cats.append(cat)

            if not eligible_cats:
                return

            lost_cat = random.choice(eligible_cats)
            cat_IDs.append(lost_cat.ID)

            text = [
                "After a long journey, m_c has finally returned home to c_n.",
                "m_c was found at the border, tired, but happy to be home.",
                "m_c strides into camp, much to the everyone's surprise. {PRONOUN/m_c/subject/CAP}{VERB/m_c/'re/'s} home!",
                "{PRONOUN/m_c/subject/CAP} met so many friends on {PRONOUN/m_c/poss} journey, but c_n is where m_c truly belongs. With a tearful goodbye, "
                "{PRONOUN/m_c/subject} {VERB/m_c/return/returns} home.",
            ]
            lost_cat.outside = False
            additional_cats = lost_cat.add_to_clan()
            cat_IDs.extend(additional_cats)
            text = random.choice(text)

            if additional_cats:
                text += " {PRONOUN/m_c/subject/CAP} {VERB/m_c/bring/brings} along {PRONOUN/m_c/poss} "
                if len(additional_cats) > 1:
                    text += str(len(additional_cats)) + " children."
                else:
                    text += "child."

            text = event_text_adjust(Cat, text, main_cat=lost_cat, clan=game.clan)

            game.cur_events_list.append(Single_Event(text, "misc", cat_IDs))

        # Perform a ceremony if needed
        for cat_ID in cat_IDs:
            x = Cat.fetch_cat(cat_ID)
            if x.status in [
                "apprentice",
                "medicine cat apprentice",
                "mediator apprentice",
                "kitten",
                "newborn",
            ]:
                if x.moons >= 15:
                    if x.status == "medicine cat apprentice":
                        self.ceremony(x, "medicine cat")
                    elif x.status == "mediator apprentice":
                        self.ceremony(x, "mediator")
                    elif x.status == "queen's apprentice":
                        self.ceremony(x, "queen")
                    else:
                        self.ceremony(x, "warrior")
                elif (
                    x.status
                    not in [
                        "apprentice",
                        "medicine cat apprentice",
                        "mediator apprentice",
                        "queen's apprentice"
                    ]
                    and x.moons >= 6
                ):
                    self.ceremony(x, "apprentice")
            elif x.status != "medicine cat":
                if x.moons == 0:
                    x.status = "newborn"
                elif x.moons < 6:
                    x.status = "kitten"
                elif x.moons < 12 and x.status != "apprentice":
                    x.status_change("apprentice")
                elif x.moons < 120 and x.status != "warrior":
                    x.status_change("warrior")
                elif x.moons > 120:
                    x.status_change("elder")

    def handle_fading(self, cat):
        """
        TODO: DOCS
        """
        if game.clan.clan_settings["fading"] and not cat.prevent_fading \
                and cat.ID != game.clan.instructor.ID and cat.ID != game.clan.demon.ID and not cat.faded:

            age_to_fade = game.config["fading"]["age_to_fade"]
            opacity_at_fade = game.config["fading"]["opacity_at_fade"]
            fading_speed = game.config["fading"]["visual_fading_speed"]
            # Handle opacity
            cat.pelt.opacity = int(
                (100 - opacity_at_fade)
                * (1 - (cat.dead_for / age_to_fade) ** fading_speed)
                + opacity_at_fade
            )

            # Deal with fading the cat if they are old enough.
            if cat.dead_for > age_to_fade:
                # If order not to add a cat to the faded list
                # twice, we can't remove them or add them to
                # faded cat list here. Rather, they are added to
                # a list of cats that will be "faded" at the next save.

                # Remove from med cat list, just in case.
                # This should never be triggered, but I've has an issue or
                # two with this, so here it is.
                if cat.ID in game.clan.med_cat_list:
                    game.clan.med_cat_list.remove(cat.ID)

                # Unset their mate, if they have one
                if len(cat.mate) > 0:
                    for mate_id in cat.mate:
                        if Cat.all_cats.get(mate_id):
                            cat.unset_mate(Cat.all_cats.get(mate_id))

                # If the cat is the current med, leader, or deputy, remove them
                if game.clan.leader:
                    if game.clan.leader.ID == cat.ID:
                        game.clan.leader = None
                if game.clan.deputy:
                    if game.clan.deputy.ID == cat.ID:
                        game.clan.deputy = None
                if game.clan.medicine_cat:
                    if game.clan.medicine_cat.ID == cat.ID:
                        if game.clan.med_cat_list:  # If there are other med cats
                            game.clan.medicine_cat = Cat.fetch_cat(
                                game.clan.med_cat_list[0]
                            )
                        else:
                            game.clan.medicine_cat = None

                game.cat_to_fade.append(cat.ID)
                cat.set_faded()

    def one_moon_outside_cat(self, cat):
        """
        exiled cat events
        """
        # aging the cat
        cat.one_moon()
        cat.manage_outside_trait()

        self.handle_outside_EX(cat)

        cat.skills.progress_skill(cat)
        Pregnancy_Events.handle_having_kits(cat, clan=game.clan)

        if not cat.dead:
            OutsiderEvents.killing_outsiders(cat)

    def one_moon_cat(self, cat):
        """
        Triggers various moon events for a cat.
        -If dead, cat is given thought, dead_for count increased, and fading handled (then function is returned)
        -Outbreak chance is handled, death event is attempted, and conditions are handled (if death happens, return)
        -cat.one_moon() is triggered
        -mediator events are triggered (this includes the cat choosing to become a mediator)
        -freshkill pile events are triggered
        -if the cat is injured or ill, they're given their own set of possible events to avoid unrealistic behavior.
        They will handle disability events, coming out, pregnancy, apprentice EXP, ceremonies, relationship events, and
        will generate a new thought. Then the function is returned.
        -if the cat was not injured or ill, then they will do all of the above *and* trigger misc events, acc events,
        and new cat events
        """

        if cat.dead:

            cat.thoughts()
            if cat.ID in game.just_died:
                cat.moons += 1
            else:
                cat.dead_for += 1
            self.handle_fading(cat)  # Deal with fading.
            cat.talked_to = False
            return
        
        if cat.forgiven > 0:
            cat.forgiven += 1
            # reset forgiven back to zero when it hits max to it doesnt just count up forever lol
            # that + 1 is because it technically starts at one
            if cat.forgiven >= game.config["shunned_cat"]["max_forgiven_moons"] + 1:
                cat.forgiven = 0
        
        if cat.shunned > 0 and cat.status != "former Clancat":
            cat.shunned += 1
            if cat.shunned >3:
                exilechance = random.randint(1,15)
                # Chance for a cat to be exiled, forgiven, or leave before the ten moon limit
                if exilechance == 1:
                    self.exile_or_forgive(cat)
                else:
                # Max number of moons a cat can be shunned before the clan makes up their damn mind
                    if cat.shunned >= game.config["shunned_cat"]["max_shunned_moons"]:
                        self.exile_or_forgive(cat)
        
        if cat.status == 'leader' and cat.shunned > 0 and cat.name.specsuffix_hidden is False:
            cat.name.specsuffix_hidden = True

        # corrects the name if the leader is shunned but their special suffix isnt hidden
        

        # all actions, which do not trigger an event display and
        # are connected to cats are located in there
        cat.one_moon()


        # Handle Mediator Events
        # TODO: this is not a great way to handle them, ideally they should be converted to ShortEvent format
        self.mediator_events(cat)

       

        # handle nutrition amount
        # (CARE: the cats have to be fed before this happens - should be handled in "one_moon" function)
        if game.clan.game_mode in ['expanded', 'cruel season'
                                   ] and game.clan.freshkill_pile:
            Condition_Events.handle_nutrient(cat, game.clan.freshkill_pile.nutrition_info)

            if cat.dead:
                return

        cat.talked_to = False
        cat.insulted = False
        cat.flirted = False
        cat.did_activity = False
        
        # prevent injured or sick cats from unrealistic Clan events
        if cat.is_ill() or cat.is_injured():
            if cat.is_ill() and cat.is_injured():
                if random.getrandbits(1):
                    triggered_death = Condition_Events.handle_injuries(cat)
                    if not triggered_death:
                        Condition_Events.handle_illnesses(cat)
                else:
                    triggered_death = Condition_Events.handle_illnesses(cat)
                    if not triggered_death:
                        Condition_Events.handle_injuries(cat)
            elif cat.is_ill():
                Condition_Events.handle_illnesses(cat)
            else:
                Condition_Events.handle_injuries(cat)
            game.switches["skip_conditions"].clear()
            if cat.dead:
                return
            self.handle_outbreaks(cat)
        elif cat.ID != game.clan.your_cat.ID and cat.status not in ['kitten', 'elder', 'newborn'] and not cat.outside and not cat.dead:
            cat.experience += random.randint(0,5)

        # newborns don't do much
        if cat.status == "newborn":
            cat.relationship_interaction()
            cat.thoughts()
            return
        
        if not cat.outside and not cat.exiled:
            if cat.shunned == 0:
                self.handle_apprentice_EX(cat)  # This must be before perform_ceremonies!
            # this HAS TO be before the cat.is_disabled() so that disabled kits can choose a med cat or mediator position
            self.perform_ceremonies(cat)
        cat.skills.progress_skill(cat) # This must be done after ceremonies. 

        # check for death/reveal/risks/retire caused by permanent conditions
        if cat.is_disabled():
            Condition_Events.handle_already_disabled(cat)
            if cat.dead:
                return

        self.coming_out(cat)
        Pregnancy_Events.handle_having_kits(cat, clan=game.clan)
        # Stop the timeskip if the cat died in childbirth
        if cat.dead:
            return

        cat.relationship_interaction()
        cat.thoughts()

        # relationships have to be handled separately, because of the ceremony name change
        if not cat.dead and not cat.outside:
            Relation_Events.handle_relationships(cat)

        # now we make sure ill and injured cats don't get interactions they shouldn't
        if cat.is_ill() or cat.is_injured():
            return

        if cat.exiled:
            Cat.handle_exile_returns(self)
        
        self.invite_new_cats(cat)
        self.other_interactions(cat)
        # self.gain_accessories(cat)

        # switches between the two death handles
        if random.getrandbits(1):
            triggered_death = self.handle_injuries_or_general_death(cat)
            if not triggered_death:
                self.handle_illnesses_or_illness_deaths(cat)
            else:
                game.switches["skip_conditions"].clear()
                return
        else:
            triggered_death = self.handle_illnesses_or_illness_deaths(cat)
            if not triggered_death:
                self.handle_injuries_or_general_death(cat)
            else:
                game.switches["skip_conditions"].clear()
                return

        self.handle_murder(cat)
        cat.faith += round(random.uniform(-0.2,0.2), 2)

        if cat.status == 'deputy' and cat.ID != game.clan.your_cat.ID and game.clan.your_cat.status == 'deputy' and not game.clan.your_cat.dead and not (game.clan.your_cat.outside or game.clan.your_cat.exiled):
            cat.status = 'warrior'

            if game.clan.deputy.ID != game.clan.your_cat.ID:
                game.clan.deputy = game.clan.your_cat

        game.switches["skip_conditions"].clear()

    def load_war_resources(self):
        resource_dir = "resources/dicts/events/"
        with open(f"{resource_dir}war.json", encoding="ascii") as read_file:
            self.WAR_TXT = ujson.loads(read_file.read())

    def check_war(self):
        """
        interactions with other clans
        """
        # if there are somehow no other clans, don't proceed
        if not game.clan.all_clans:
            return

        # Prevent wars from starting super early in the game.
        if game.clan.age <= 4:
            return

        # check that the save dict has all the things we need
        if "at_war" not in game.clan.war:
            game.clan.war["at_war"] = False
        if "enemy" not in game.clan.war:
            game.clan.war["enemy"] = None
        if "duration" not in game.clan.war:
            game.clan.war["duration"] = 0

        # check if war in progress
        war_events = None
        enemy_clan = None
        if game.clan.war["at_war"]:

            # Grab the enemy clan object
            for other_clan in game.clan.all_clans:
                if other_clan.name == game.clan.war["enemy"]:
                    enemy_clan = other_clan
                    break

            threshold = 5
            if enemy_clan.temperament == "bloodthirsty":
                threshold = 10
            if enemy_clan.temperament in ["mellow", "amiable", "gracious"]:
                threshold = 3

            threshold -= int(game.clan.war["duration"])
            if enemy_clan.relations < 0:
                enemy_clan.relations = 0

            # check if war should conclude, if not, continue
            if enemy_clan.relations >= threshold and game.clan.war["duration"] > 1:
                game.clan.war["at_war"] = False
                game.clan.war["enemy"] = None
                game.clan.war["duration"] = 0
                enemy_clan.relations += 12
                war_events = self.WAR_TXT["conclusion_events"]
            else:  # try to influence the relation with warring clan
                game.clan.war["duration"] += 1
                choice = random.choice(["rel_up", "rel_up", "neutral", "rel_down"])
                game.switches["war_rel_change_type"] = choice
                war_events = self.WAR_TXT["progress_events"][choice]
                if enemy_clan.relations < 0:
                    enemy_clan.relations = 0
                if choice == "rel_up":
                    enemy_clan.relations += 2
                elif choice == "rel_down" and enemy_clan.relations > 1:
                    enemy_clan.relations -= 1

        else:  # try to start a war if no war in progress
            for other_clan in game.clan.all_clans:
                threshold = 5
                if other_clan.temperament == "bloodthirsty":
                    threshold = 10
                if other_clan.temperament in ["mellow", "amiable", "gracious"]:
                    threshold = 3

                if int(other_clan.relations) <= threshold and not int(
                    random.random() * int(other_clan.relations)
                ):
                    enemy_clan = other_clan
                    game.clan.war["at_war"] = True
                    game.clan.war["enemy"] = other_clan.name
                    war_events = self.WAR_TXT["trigger_events"]

        # if nothing happened, return
        if not war_events or not enemy_clan:
            return

        if not game.clan.leader or not game.clan.deputy or not game.clan.medicine_cat:
            for event in war_events:
                if not game.clan.leader and "lead_name" in event:
                    war_events.remove(event)
                if not game.clan.deputy and "dep_name" in event:
                    war_events.remove(event)
                if not game.clan.medicine_cat and "med_name" in event:
                    war_events.remove(event)

        event = random.choice(war_events)
        event = ongoing_event_text_adjust(
            Cat, event, other_clan_name=f"{enemy_clan.name}Clan", clan=game.clan
        )
        game.cur_events_list.append(Single_Event(event, "other_clans"))

    def perform_ceremonies(self, cat):
        """
        ceremonies
        """
        # TODO: hardcoded events, not good, consider how to convert to ShortEvent
        #  we *do* have a ceremony dict and format, not sure why it isn't being used here
        # PROMOTE DEPUTY TO LEADER, IF NEEDED -----------------------
        if game.clan.leader:
            leader_dead = game.clan.leader.dead
            leader_outside = game.clan.leader.outside
            leader_shunned = game.clan.leader.shunned > 0
        else:
            leader_dead = True
            # If leader is None, treat them as dead (since they are dead - and faded away.)
            leader_outside = True
            leader_shunned = True

        # If a Clan deputy exists, and the leader is dead,
        #  outside, or doesn't exist, make the deputy leader.
        if game.clan.deputy:
            if game.clan.deputy is not None and \
                    not game.clan.deputy.dead and \
                    not game.clan.deputy.outside and \
                    game.clan.deputy.shunned == 0 and \
                    (leader_dead or leader_outside or leader_shunned):
                game.clan.new_leader(game.clan.deputy)
                game.clan.leader_lives = 9
                text = ''
                shunnedleader = cat.name if cat.shunned > 0 and cat.status == 'leader' and not cat.outside or cat.dead else None
                

                if cat.outside and not (cat.exiled or cat.df) and cat.status not in ['kittypet', 'loner', 'rogue','former Clancat']:
                    shuntext = ""
                elif leader_shunned and shunnedleader:
                    shuntext = f"After {shunnedleader}'s shun, the Clan's deputy has had to step up earlier than they expected. "
                else:
                    shuntext = ""

                if game.clan.deputy.personality.trait == 'bloodthirsty':
                    text = f'{game.clan.deputy.name} has become the new leader. ' \
                           f'They stare down at their Clanmates with unsheathed claws, ' \
                           f'promising a new era for the Clans.'
                else:
                    c = random.choice([1, 2, 3])
                    moonplace_dict = {
                        "Beach": "Mooncove",
                        "Mountainous": "Moonfalls",
                        "Forest": "Moonhollow",
                        "Plains": "Moongrove"
                    }
                    moonplace = moonplace_dict.get(game.clan.biome, "Moonplace")
                    if c == 1:
                        text = str(game.clan.deputy.name.prefix) + str(
                            game.clan.deputy.name.suffix) + \
                               ' has been promoted to the new leader of the Clan. ' \
                               f'They travel immediately to the {moonplace} to get their ' \
                               'nine lives and are hailed by their new name, ' + \
                               str(game.clan.deputy.name) + '.'
                    elif c == 2:
                        text = (
                            f"{game.clan.deputy.name} has become the new leader of the Clan. "
                            f"They vow that they will protect the Clan, "
                            f"even at the cost of their nine lives."
                        )
                    elif c == 3:
                        text = (
                            f"{game.clan.deputy.name} has received "
                            f"their nine lives and became the "
                            f"new leader of the Clan. They feel like "
                            f"they are not ready for this new "
                            f"responsibility, but will try their best "
                            f"to do what is right for the Clan."
                        )

                # game.ceremony_events_list.append(text)
                text += f"\nVisit {game.clan.deputy.name}'s " \
                        "profile to see their full leader ceremony."
                event = shuntext + text
                game.cur_events_list.append(
                    Single_Event(event, "ceremony", game.clan.deputy.ID))
                self.ceremony_accessory = True
                self.gain_accessories(cat)
                game.clan.deputy = None

        # OTHER CEREMONIES ---------------------------------------

        # Protection check, to ensure "None" cats won't cause a crash.
        if cat:
            cat_dead = cat.dead
        else:
            cat_dead = True

        if not cat_dead:
            if cat.status == "deputy" and game.clan.deputy is None:
                game.clan.deputy = cat
            if cat.status == "medicine cat" and game.clan.medicine_cat is None:
                game.clan.medicine_cat = cat

            # retiring to elder den
            if (
                not cat.no_retire
                and cat.status in ["warrior", "deputy"]
                and len(cat.apprentice) < 1
                and cat.moons > 114
            ):
                # There is some variation in the age.
                if cat.moons > 140 or not int(
                    random.random() * (-0.7 * cat.moons + 100)
                ):
                    if cat.status == "deputy":
                        game.clan.deputy = None
                    if cat.shunned != 0:
                        self.ceremony(cat, "elder", LG_TYPE="shunned")
                    else:
                        self.ceremony(cat, "elder", LG_TYPE="")


            # apprentice a kitten to either med or warrior
            if cat.moons == cat_class.age_moons["adolescent"][0]:
                if cat.status == 'kitten':

                    # change personality facets
                    if cat.courage != 0:
                        cat.personality.aggression = min(max(cat.personality.aggression + (1*cat.courage)%2, 0), 15)
                        cat.personality.sociability = min(max(cat.personality.sociability + (1*cat.courage)%2, 0), 15)
                        cat.personality.stability = min(max(cat.personality.stability + (-1*cat.courage)%2, 0), 15)
                        cat.personality.lawfulness = min(max(cat.personality.lawfulness + (-1*cat.courage)%2, 0), 15)
                    if cat.compassion != 0:
                        cat.personality.aggression = min(max(cat.personality.aggression + (-1*cat.compassion)%2, 0), 15)
                        cat.personality.sociability = min(max(cat.personality.sociability + (-1*cat.compassion)%2, 0), 15)
                        cat.personality.stability = min(max(cat.personality.stability + (1*cat.compassion)%2, 0), 15)
                        cat.personality.lawfulness = min(max(cat.personality.lawfulness + (1*cat.compassion)%2, 0), 15)
                    if cat.intelligence != 0:
                        cat.personality.aggression = min(max(cat.personality.aggression + (1*cat.intelligence)%2, 0), 15)
                        cat.personality.sociability = min(max(cat.personality.sociability + (-1*cat.intelligence)%2, 0), 15)
                        cat.personality.stability = min(max(cat.personality.stability + (1*cat.intelligence)%2, 0), 15)
                        cat.personality.lawfulness = min(max(cat.personality.lawfulness + (-1*cat.intelligence)%2, 0), 15)
                    if cat.empathy != 0:
                        cat.personality.aggression = min(max(cat.personality.aggression + (-1*cat.empathy)%2, 0), 15)
                        cat.personality.sociability = min(max(cat.personality.sociability + (1*cat.empathy)%2, 0), 15)
                        cat.personality.stability = min(max(cat.personality.stability + (-1*cat.empathy)%2, 0), 15)
                        cat.personality.lawfulness = min(max(cat.personality.lawfulness + (1*cat.empathy)%2, 0), 15)

                    med_cat_list = [i for i in Cat.all_cats_list if
                                    i.status in ["medicine cat", "medicine cat apprentice"] and not (
                                            i.dead or i.outside)]

                    # check if the medicine cat is an elder
                    has_elder_med = [
                        c
                        for c in med_cat_list
                        if c.age == "senior" and c.status == "medicine cat"
                    ]

                    very_old_med = [
                        c
                        for c in med_cat_list
                        if c.moons >= 150 and c.status == "medicine cat"
                    ]

                    # check if the Clan has sufficient med cats
                    has_med = medical_cats_condition_fulfilled(
                        Cat.all_cats.values(),
                        amount_per_med=get_amount_cat_for_one_medic(game.clan),
                    )

                    # check if a med cat app already exists
                    has_med_app = any(
                        cat.status == "medicine cat apprentice" for cat in med_cat_list
                    )

                    # assign chance to become med app depending on current med cat and traits
                    chance = game.config["roles"]["base_medicine_app_chance"]
                    if has_elder_med == med_cat_list:
                        # These chances apply if all the current medicine cats are elders.
                        if has_med:
                            chance = int(chance / 2.22)
                        else:
                            chance = int(chance / 13.67)
                    elif very_old_med == med_cat_list:
                        # These chances apply is all the current medicine cats are very old.
                        if has_med:
                            chance = int(chance / 3)
                        else:
                            chance = int(chance / 14)
                    # These chances will only be reached if the
                    # Clan has at least one non-elder medicine cat.
                    elif not has_med:
                        chance = int(chance / 7.125)
                    elif has_med:
                        chance = int(chance * 2.22)

                    if cat.personality.trait in [
                        "altruistic",
                        "compassionate",
                        "empathetic",
                        "wise",
                        "faithful",
                    ]:
                        chance = int(chance / 1.3)

                    chance += (cat.intelligence * -1)

                    if chance <= 0:
                        chance = 1

                    # edited below here for LG shunned ceremonies
                    self.ceremony_accessory = True
                    if not has_med_app and not int(random.random() * chance):
                        if cat.shunned != 0:
                            self.ceremony(cat, "medicine cat apprentice", LG_TYPE="shunned")
                        else:
                            self.ceremony(cat, "medicine cat apprentice", LG_TYPE="")
                            self.ceremony_accessory = True
                            self.gain_accessories(cat)
                    elif random.randint(1,40 + (cat.compassion*-1)) == 1:
                        if cat.shunned != 0:
                            self.ceremony(cat, "queen's apprentice", LG_TYPE="shunned")
                        else:
                            self.ceremony(cat, "queen's apprentice", LG_TYPE="")
                            self.ceremony_accessory = True
                            self.gain_accessories(cat)
                    else:
                        # Chance for mediator apprentice
                        mediator_list = list(
                            filter(
                                lambda x: x.status == "mediator"
                                and not x.dead
                                and not x.outside,
                                Cat.all_cats_list,
                            )
                        )

                        # This checks if at least one mediator already has an apprentice.
                        has_mediator_apprentice = False
                        for c in mediator_list:
                            if c.apprentice:
                                has_mediator_apprentice = True
                                break

                        chance = game.config["roles"]["mediator_app_chance"]
                        if cat.personality.trait in [
                            "charismatic",
                            "empathetic",
                            "responsible",
                            "wise",
                            "thoughtful",
                        ]:
                            chance = int(chance / 1.5)

                        chance += (cat.empathy * -1)
                        if chance <= 0:
                            chance = 1

                        # Only become a mediator if there is already one in the clan.
                        if (
                            mediator_list
                            and not has_mediator_apprentice
                            and not int(random.random() * chance)
                        ):
                            if cat.shunned != 0:
                                self.ceremony(cat, "mediator apprentice", LG_TYPE="shunned")
                            else:
                                self.ceremony(cat, "mediator apprentice", LG_TYPE="")
                                self.ceremony_accessory = True
                                self.gain_accessories(cat)
                        else:
                            if cat.shunned != 0:
                                self.ceremony(cat, "apprentice", LG_TYPE="shunned")
                            else:
                                self.ceremony(cat, "apprentice", LG_TYPE="")
                                self.ceremony_accessory = True
                                self.gain_accessories(cat)

            # graduate
            if cat.status in [
                "apprentice", "mediator apprentice",
                "medicine cat apprentice", "queen's apprentice"
            ] and cat.shunned == 0:

                if game.clan.clan_settings["12_moon_graduation"]:
                    _ready = cat.moons >= 12
                else:
                    _ready = (
                        cat.experience_level not in ["untrained", "trainee"]
                        and cat.moons >= game.config["graduation"]["min_graduating_age"]
                    ) or cat.moons >= game.config["graduation"]["max_apprentice_age"][
                        cat.status
                    ]

                if _ready:
                    if game.clan.clan_settings["12_moon_graduation"]:
                        preparedness = "prepared"
                    else:
                        if cat.moons == game.config["graduation"]["min_graduating_age"]:
                            preparedness = "early"
                        elif cat.experience_level in ["untrained", "trainee"]:
                            preparedness = "unprepared"
                        else:
                            preparedness = "prepared"

                    if cat.status == "apprentice":
                        self.ceremony(cat, "warrior", preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(cat)

                    # promote to med cat
                    elif cat.status == "medicine cat apprentice":
                        self.ceremony(cat, "medicine cat", preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(cat)

                    elif cat.status == "mediator apprentice":
                        self.ceremony(cat, "mediator", preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(cat)
                    
                    elif cat.status == "queen's apprentice":
                        self.ceremony(cat, "queen", preparedness)
                        self.ceremony_accessory = True
                        self.gain_accessories(cat)

    def load_ceremonies(self):
        """
        TODO: DOCS
        """
        if self.CEREMONY_TXT is not None:
            return

        resource_dir = "resources/dicts/events/ceremonies/"
        with open(f"{resource_dir}ceremony-master.json", encoding="ascii") as read_file:
            self.CEREMONY_TXT = ujson.loads(read_file.read())

        self.ceremony_id_by_tag = {}
        # Sorting.
        for ID in self.CEREMONY_TXT:
            for tag in self.CEREMONY_TXT[ID][0]:
                if tag in self.ceremony_id_by_tag:
                    self.ceremony_id_by_tag[tag].add(ID)
                else:
                    self.ceremony_id_by_tag[tag] = {ID}

    def ceremony(self, cat, promoted_to, preparedness="prepared", LG_TYPE=""):
        """
        promote cats and add to event list
        """
        # ceremony = []
        _ment = Cat.fetch_cat(cat.mentor) if cat.mentor else None # Grab current mentor, if they have one, before it's removed. 
        old_name = str(cat.name)
        cat.status_change(promoted_to)
        cat.rank_change_traits_skill(_ment)

        involved_cats = [cat.ID]  # Clearly, the cat the ceremony is about is involved.

        # Time to gather ceremonies. First, lets gather all the ceremony ID's.
        possible_ceremonies = set()
        dead_mentor = None
        mentor = None
        previous_alive_mentor = None
        dead_parents = []
        living_parents = []
        mentor_type = {
            "medicine cat": ["medicine cat"],
            "queen": ["queen"],
            "warrior": ["warrior", "deputy", "leader", "elder"],
            "mediator": ["mediator"],
        }

        try:
            # Get all the ceremonies for the role ----------------------------------------
            possible_ceremonies.update(self.ceremony_id_by_tag[promoted_to])

            # Get ones for prepared status ----------------------------------------------
            if promoted_to in ["warrior", "medicine cat", "mediator", "queen"]:
                possible_ceremonies = possible_ceremonies.intersection(
                    self.ceremony_id_by_tag[preparedness]
                )

            # Gather ones for mentor. -----------------------------------------------------
            tags = []

            # CURRENT MENTOR TAG CHECK
            if cat.mentor:
                if Cat.fetch_cat(cat.mentor).status == "leader":
                    tags.append("yes_leader_mentor")
                else:
                    tags.append("yes_mentor")
                mentor = Cat.fetch_cat(cat.mentor)
            else:
                tags.append("no_mentor")

            for c in reversed(cat.former_mentor):
                if Cat.fetch_cat(c) and Cat.fetch_cat(c).dead:
                    tags.append("dead_mentor")
                    dead_mentor = Cat.fetch_cat(c)
                    break

            # Unlike dead mentors, living mentors must be VALID
            # they must have the correct status for the role the cat
            # is being promoted too.
            valid_living_former_mentors = []
            for c in cat.former_mentor:
                if not (Cat.fetch_cat(c).dead or Cat.fetch_cat(c).outside or Cat.fetch_cat(c).shunned > 0):
                    if promoted_to in mentor_type:
                        if Cat.fetch_cat(c).status in mentor_type[promoted_to]:
                            valid_living_former_mentors.append(c)
                    else:
                        valid_living_former_mentors.append(c)

            # ALL FORMER MENTOR TAG CHECKS
            if valid_living_former_mentors:
                #  Living Former mentors. Grab the latest living valid mentor.
                previous_alive_mentor = Cat.fetch_cat(valid_living_former_mentors[-1])
                if previous_alive_mentor.status == "leader":
                    tags.append("alive_leader_mentor")
                else:
                    tags.append("alive_mentor")
            else:
                # This tag means the cat has no living, valid mentors.
                tags.append("no_valid_previous_mentor")

            # Now we add the mentor stuff:
            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_mentor"]
            )

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(
                        self.ceremony_id_by_tag[t]))

            possible_ceremonies = temp

            # Gather for parents ---------------------------------------------------------
            for p in [cat.parent1, cat.parent2]:
                if Cat.fetch_cat(p):
                    if Cat.fetch_cat(p).dead:
                        dead_parents.append(Cat.fetch_cat(p))
                    # For the purposes of ceremonies, living parents
                    # who are also the leader are not counted.
                    elif (
                        not Cat.fetch_cat(p).dead
                        and not Cat.fetch_cat(p).outside
                        and Cat.fetch_cat(p).status != "leader"
                    ):
                        living_parents.append(Cat.fetch_cat(p))

            tags = []
            if len(dead_parents) >= 1 and "orphaned" not in cat.backstory:
                tags.append("dead1_parents")
            if len(dead_parents) >= 2 and "orphaned" not in cat.backstory:
                tags.append("dead1_parents")
                tags.append("dead2_parents")

            if len(living_parents) >= 1:
                tags.append("alive1_parents")
            if len(living_parents) >= 2:
                tags.append("alive2_parents")

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_parents"]
            )

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(self.ceremony_id_by_tag[t])
                )

            possible_ceremonies = temp

            # Gather for leader ---------------------------------------------------------

            tags = []
            if game.clan.leader and not game.clan.leader.dead and not game.clan.leader.outside and game.clan.leader.shunned == 0:
                tags.append("yes_leader")
            else:
                tags.append("no_leader")

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_leader"]
            )

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(self.ceremony_id_by_tag[t])
                )

            possible_ceremonies = temp

            # Gather for backstories.json ----------------------------------------------------
            tags = []
            if cat.backstory == ["abandoned1", "abandoned2", "abandoned3"]:
                tags.append("abandoned")
            elif cat.backstory == "clanborn":
                tags.append("clanborn")

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["general_backstory"]
            )

            for t in tags:
                temp.update(
                    possible_ceremonies.intersection(self.ceremony_id_by_tag[t])
                )

            possible_ceremonies = temp
            # Gather for traits --------------------------------------------------------------

            temp = possible_ceremonies.intersection(
                self.ceremony_id_by_tag["all_traits"]
            )

            if cat.personality.trait in self.ceremony_id_by_tag:
                temp.update(
                    possible_ceremonies.intersection(
                        self.ceremony_id_by_tag[cat.personality.trait]
                    )
                )

            possible_ceremonies = temp
        except Exception as ex:
            traceback.print_exception(type(ex), ex, ex.__traceback__)
            print("Issue gathering ceremony text.", str(cat.name), promoted_to)

        # getting the random honor if it's needed
        random_honor = None
        if promoted_to in ['warrior', 'mediator', 'medicine cat', "queen"]:
            resource_dir = "resources/dicts/events/ceremonies/"
            with open(f"{resource_dir}ceremony_traits.json",
                    encoding="ascii") as read_file:
                TRAITS = ujson.loads(read_file.read())
            try:
                random_honor = random.choice(TRAITS[cat.personality.trait])
            except KeyError:
                random_honor = "hard work"

        if cat.status in ["warrior", "medicine cat", "mediator", "queen"]:
            History.add_app_ceremony(cat, random_honor)

        # lifegen filtering for shunned/forgiven
        # it's easier to do here lol
        new_ceremonies = []
        for ceremony in possible_ceremonies:
            tags = self.CEREMONY_TXT[ceremony][0]
            text = self.CEREMONY_TXT[ceremony][1]

            if LG_TYPE == "shunned":
                # a ceremony for a cat WHILE theyre shunned
                if "shunned" not in tags:
                    continue
            
            elif LG_TYPE == "forgiven":
                # a ceremony for a cat returning to work after being forgiven
                if "forgiven" not in tags:
                    continue
                if (cat.moons - cat.shunned) > 5:
                    if "shunned_as_apprentice" not in tags:
                        continue
                else:
                    if "shunned_as_kit" not in tags:
                        continue
            
            else:
                if "forgiven" in tags or "shunned" in tags:
                    continue
            
            new_ceremonies.append(ceremony)

        if promoted_to in [
            "apprentice",
            "medicine cat apprentice",
            "mediator apprentice",
            "queen's apprentice"
        ]:
            try:
                ceremony_tags, ceremony_text = self.CEREMONY_TXT[
                    random.choice(list(new_ceremonies))
                ]
                # print("working ceremony for", cat.name, LG_TYPE)
                # print(new_ceremonies)
            except IndexError:
                print("WARNING: A ceremony could not be chosen for", cat.name, LG_TYPE)
                print(new_ceremonies)
                print(cat.moons - cat.shunned)
                return
        else:
        # -------------------
            ceremony_tags, ceremony_text = self.CEREMONY_TXT[
                random.choice(list(possible_ceremonies))
            ]

        # This is a bit strange, but it works. If there is
        # only one parent involved, but more than one living
        # or dead parent, the adjust text function will pick
        # a random parent. However, we need to know the
        # parent to include in the involved cats. Therefore,
        # text adjust also returns the random parents it picked,
        # which will be added to the involved cats if needed.
        ceremony_text, involved_living_parent, involved_dead_parent = (
            ceremony_text_adjust(
                Cat,
                ceremony_text,
                cat,
                dead_mentor=dead_mentor,
                random_honor=random_honor,
                old_name=old_name,
                mentor=mentor,
                previous_alive_mentor=previous_alive_mentor,
                living_parents=living_parents,
                dead_parents=dead_parents,
            )
        )

        # Gather additional involved cats
        for tag in ceremony_tags:
            if tag == "yes_leader":
                involved_cats.append(game.clan.leader.ID)
            elif tag in ["yes_mentor", "yes_leader_mentor"]:
                involved_cats.append(cat.mentor)
            elif tag == "dead_mentor":
                involved_cats.append(dead_mentor.ID)
            elif tag in ["alive_mentor", "alive_leader_mentor"]:
                involved_cats.append(previous_alive_mentor.ID)
            elif tag == "alive2_parents" and len(living_parents) >= 2:
                for c in living_parents[:2]:
                    involved_cats.append(c.ID)
            elif tag == "alive1_parents" and involved_living_parent:
                involved_cats.append(involved_living_parent.ID)
            elif tag == "dead2_parents" and len(dead_parents) >= 2:
                for c in dead_parents[:2]:
                    involved_cats.append(c.ID)
            elif tag == "dead1_parent" and involved_dead_parent:
                involved_cats.append(involved_dead_parent.ID)

        # remove duplicates
        involved_cats = list(set(involved_cats))
        if cat.ID != game.clan.your_cat.ID and game.clan.your_cat.ID != cat.mentor:
            game.cur_events_list.append(
                Single_Event(f'{ceremony_text}', "ceremony", involved_cats))
        cat.faith += round(random.uniform(0,2), 2)
        game.ceremony_events_list.append(f'{cat.name}{ceremony_text}')


    def gain_accessories(self, cat):
        """
        accessories
        """

        if not cat:
            return

        if cat.dead or cat.outside:
            return
        
        if game.clan.clan_settings['all accessories']:
            return

        # check if cat already has acc
        # if cat.pelt.accessory:
        #     self.ceremony_accessory = False
        #     return

        # find random_cat
        random_cat = get_random_moon_cat(Cat, main_cat=cat)

        # chance to gain acc
        acc_chances = game.config["accessory_generation"]
        chance = acc_chances["base_acc_chance"]
        if cat.status in ["medicine cat", "medicine cat apprentice"]:
            chance += acc_chances["med_modifier"]
        if cat.age in ["kitten", "adolescent"]:
            chance += acc_chances["baby_modifier"]
        elif cat.age in ["senior adult", "senior"]:
            chance += acc_chances["elder_modifier"]
        if cat.personality.trait in [
            "adventurous",
            "childish",
            "confident",
            "daring",
            "playful",
            "attention-seeker",
            "bouncy",
            "sweet",
            "troublesome",
            "impulsive",
            "inquisitive",
            "strange",
            "shameless",
        ]:
            chance += acc_chances["happy_trait_modifier"]
        elif cat.personality.trait in [
            "cold",
            "strict",
            "bossy",
            "bullying",
            "insecure",
            "nervous",
        ]:
            chance += acc_chances["grumpy_trait_modifier"]
        if self.ceremony_accessory:
            chance += acc_chances["ceremony_modifier"]

        # increase chance of acc if the cat had a ceremony
        if chance <= 0:
            chance = 1
        if not int(random.random() * chance):

            sub_type = ["accessory"]
            if self.ceremony_accessory:
                sub_type.append("ceremony")

            handle_short_events.handle_event(event_type="misc",
                                             main_cat=cat,
                                             random_cat=random_cat,
                                             sub_type=sub_type,
                                             freshkill_pile=game.clan.freshkill_pile)

        self.ceremony_accessory = False

        return

    # This gives outsiders exp. There may be a better spot for it to go,
    # but I put it here to keep the exp functions together
    def handle_outside_EX(self, cat):
        if cat.outside:

            if cat.not_working() and int(random.random() * 3):
                return

            if cat.age == "kitten":
                return

            if cat.age == "adolescent":
                ran = game.config["outside_ex"]["base_adolescent_timeskip_ex"]
            elif cat.age == "senior":
                ran = game.config["outside_ex"]["base_senior_timeskip_ex"]
            else:
                ran = game.config["outside_ex"]["base_adult_timeskip_ex"]

            role_modifier = 1
            if cat.status == "kittypet":
                # Kittypets will gain exp at 2/3 the rate of loners or exiled cats, as this assumes they are
                # kept indoors at least part of the time and can't hunt/fight as much
                role_modifier = 0.6

            exp = random.choice(
                list(range(ran[0][0], ran[0][1] + 1))
                + list(range(ran[1][0], ran[1][1] + 1))
            )

            if game.clan.game_mode == "classic":
                exp += random.randint(0, 3)

            cat.experience += max(exp * role_modifier, 1)

    def handle_apprentice_EX(self, cat):
        """
        TODO: DOCS
        """
        if not cat:
            return
            
        if cat.status in [
            "apprentice", "medicine cat apprentice", "mediator apprentice", "queen's apprentice"
        ] and cat.shunned == 0:

            if cat.not_working() and int(random.random() * 3):
                return

            if cat.experience > cat.experience_levels_range["trainee"][1]:
                return

            if cat.status == "medicine cat apprentice":
                ran = game.config["graduation"]["base_med_app_timeskip_ex"]
            else:
                ran = game.config["graduation"]["base_app_timeskip_ex"]

            mentor_modifier = 1
            if not cat.mentor or Cat.fetch_cat(cat.mentor).not_working():
                # Sick mentor debuff
                mentor_modifier = 0.7
                mentor_skill_modifier = 0

            exp = random.choice(
                list(range(ran[0][0], ran[0][1] + 1))
                + list(range(ran[1][0], ran[1][1] + 1))
            )

            cat.experience += max(exp * mentor_modifier, 1)

    def invite_new_cats(self, cat):
        """
        new cats
        """
        chance = 200

        alive_cats = list(
            filter(
                lambda kitty: (
                    kitty.status != "leader" and not kitty.dead and not kitty.outside
                ),
                Cat.all_cats.values(),
            )
        )

        clan_size = len(alive_cats)

        base_chance = 700
        if clan_size < 10:
            base_chance = 200
        elif clan_size < 30:
            base_chance = 300

        reputation = game.clan.reputation
        reputation = 80
        # hostile
        if 1 <= reputation <= 30:
            if clan_size < 10:
                chance = base_chance
            else:
                rep_adjust = int(reputation / 2)
                if rep_adjust == 0:
                    rep_adjust = 1
                chance = base_chance + int(300 / rep_adjust)
        # neutral
        elif 31 <= reputation <= 70:
            if clan_size < 10:
                chance = base_chance - reputation
            else:
                chance = base_chance
        # welcoming
        elif 71 <= reputation <= 100:
            chance = base_chance - reputation

        chance = max(chance, 1)

        # choose other cat
        random_cat = get_random_moon_cat(Cat, main_cat=cat, parent_child_modifier=True, mentor_app_modifier=True)


        if (
            not int(random.random() * chance)
            and cat.age != "kitten"
            and cat.age != "adolescent"
            and not self.new_cat_invited
        ):
            self.new_cat_invited = True

            handle_short_events.handle_event(event_type="new_cat",
                                             main_cat=cat,
                                             random_cat=random_cat,
                                             freshkill_pile=game.clan.freshkill_pile)

    def other_interactions(self, cat):
        """
        TODO: DOCS
        """
        hit = int(random.random() * 30)
        if hit:
            return

        random_cat = get_random_moon_cat(Cat, main_cat=cat)

        handle_short_events.handle_event(event_type="misc",
                                         main_cat=cat,
                                         random_cat=random_cat,
                                         freshkill_pile=game.clan.freshkill_pile)

    def handle_injuries_or_general_death(self, cat):
        """
        decide if cat dies
        """

        # try to get the random_cat
        random_cat = get_random_moon_cat(Cat, cat, parent_child_modifier=True, mentor_app_modifier=True)

        # chance to kill leader: 1/50 by default
        if not int(random.random() * game.get_config_value("death_related", "leader_death_chance")) \
                and cat.status == 'leader' \
                and not cat.not_working():
            handle_short_events.handle_event(event_type="birth_death",
                                             main_cat=cat,
                                             random_cat=random_cat,
                                             freshkill_pile=game.clan.freshkill_pile)

            return True

        # chance to die of old age
        age_start = game.config["death_related"]["old_age_death_start"]
        death_curve_setting = game.config["death_related"]["old_age_death_curve"]
        death_curve_value = 0.001 * death_curve_setting
        # made old_age_death_chance into a separate value to make testing with print statements easier
        old_age_death_chance = ((1 + death_curve_value) ** (cat.moons - age_start)) - 1
        if random.random() <= old_age_death_chance:
            handle_short_events.handle_event(event_type="birth_death",
                                             main_cat=cat,
                                             random_cat=random_cat,
                                             sub_type=["old_age"],
                                             freshkill_pile=game.clan.freshkill_pile)
            return True
        # max age has been indicated to be 300, so if a cat reaches that age, they die of old age
        elif cat.moons >= 300:
            handle_short_events.handle_event(event_type="birth_death",
                                             main_cat=cat,
                                             random_cat=random_cat,
                                             sub_type=["old_age"],
                                             freshkill_pile=game.clan.freshkill_pile)
            return True

        # disaster death chance
        if game.clan.clan_settings.get('disasters'):
            if not random.getrandbits(10):  # 1/1010
                handle_short_events.handle_event(event_type="birth_death",
                                                 main_cat=cat,
                                                 random_cat=random_cat,
                                                 sub_type=["mass_death"],
                                                 freshkill_pile=game.clan.freshkill_pile)
                return True
        chance_death = game.get_config_value("death_related", f"{game.clan.game_mode}_death_chance")
        try:
            if cat.status == "kitten" or cat.status == "newborn":
                num_queens = 0
                for c in game.clan.clan_cats:
                    if not Cat.all_cats.get(c).outside and not Cat.all_cats.get(c).dead:
                        if Cat.all_cats.get(c).status == "queen" or Cat.all_cats.get(c).status == "queen's apprentice":
                            num_queens+=1
                chance_death+=(num_queens*5)
        except:
            print("couldn't handle queen mortality")
            
        # final death chance and then, if not triggered, head to injuries
        if not int(random.random() * chance_death) \
                and not cat.not_working():  # 1/400
            handle_short_events.handle_event(event_type="birth_death",
                                             main_cat=cat,
                                             random_cat=random_cat,
                                             freshkill_pile=game.clan.freshkill_pile)
            return True
        else:
            triggered_death = Condition_Events.handle_injuries(cat, random_cat)

            return triggered_death

    def handle_murder(self, cat):
        """ Handles murder """
        relationships = cat.relationships.values()
        targets = []

        if cat.age in ["kitten", "newborn"]:
            return
        if cat.ID == game.clan.your_cat.ID:
            return

        # if this cat is unstable and aggressive, we lower the random murder chance
        random_murder_chance = int(
            game.config["death_related"]["base_random_murder_chance"]
        )
        random_murder_chance -= 0.5 * (
            (cat.personality.aggression) + (16 - cat.personality.stability)
        )

        # Check to see if random murder is triggered.
        # If so, we allow targets to be anyone they have even the smallest amount of dislike for
        if random.getrandbits(max(1, int(random_murder_chance))) == 1:
            targets = [
                i
                for i in relationships
                if i.dislike > 1
                and not Cat.fetch_cat(i.cat_to).dead
                and not Cat.fetch_cat(i.cat_to).outside
            ]
            if not targets:
                return

            chosen_target = random.choice(targets)

            handle_short_events.handle_event(event_type="birth_death",
                                             main_cat=Cat.fetch_cat(chosen_target.cat_to),
                                             random_cat=cat,
                                             sub_type=["murder"],
                                             freshkill_pile=game.clan.freshkill_pile)

            return

        # will this cat actually murder? this takes into account stability and lawfulness
        murder_capable = 7
        if cat.personality.stability < 6:
            murder_capable -= 3
        if cat.personality.lawfulness < 6:
            murder_capable -= 2
        if cat.personality.aggression > 10:
            murder_capable -= 1
        elif cat.personality.aggression > 12:
            murder_capable -= 3

        murder_capable = max(1, murder_capable)

        if random.getrandbits(murder_capable) != 1:
            return

        if game.settings.get("higher murder moon chance"):
            murderTargetThreshold = 10
        else:
            murderTargetThreshold = 20
        # If random murder is not triggered, targets can only be those they have some dislike for
        hate_relation = [
            i
            for i in relationships
            if i.dislike > murderTargetThreshold
            and not Cat.fetch_cat(i.cat_to).dead
            and not Cat.fetch_cat(i.cat_to).outside
        ]
        targets.extend(hate_relation)
        resent_relation = [
            i
            for i in relationships
            if i.jealousy > murderTargetThreshold
            and not Cat.fetch_cat(i.cat_to).dead
            and not Cat.fetch_cat(i.cat_to).outside
        ]
        targets.extend(resent_relation)
        toxicity_relation = [
            i
            for i in relationships
            if i.toxicity > murderTargetThreshold
            and not Cat.fetch_cat(i.cat_to).dead
            and not Cat.fetch_cat(i.cat_to).outside
        ]
        targets.extend(toxicity_relation)

        # if we have some, then we need to decide if this cat will kill
        if targets:
            chosen_target = random.choice(targets)

            kill_chance = game.config["death_related"]["base_murder_kill_chance"]

            relation_modifier = int(
                0.5 * int(chosen_target.dislike + chosen_target.jealousy + chosen_target.toxicity)
            ) - int(
                0.5
                * int(
                    chosen_target.platonic_like
                    + chosen_target.trust
                    + chosen_target.comfortable
                )
            )
            kill_chance -= relation_modifier

            if (
                len(chosen_target.log) > 0
                and "" in chosen_target.log[-1]
            ):
                kill_chance -= 50

            if (
                len(chosen_target.log) > 0
                and "" in chosen_target.log[-1]
            ):
                kill_chance -= 20

            # little easter egg just for fun
            if (
                cat.personality.trait == "ambitious"
                and Cat.fetch_cat(chosen_target.cat_to).status == "leader"
            ):
                kill_chance -= 10

            kill_chance = max(1, int(kill_chance))

            if not int(random.random() * kill_chance):
                print(
                    cat.name, "TARGET CHOSEN", Cat.fetch_cat(chosen_target.cat_to).name
                )
                print("KILL KILL KILL")

                handle_short_events.handle_event(event_type="birth_death",
                                                 main_cat=Cat.fetch_cat(chosen_target.cat_to),
                                                 random_cat=cat,
                                                 sub_type=["murder"],
                                                 freshkill_pile=game.clan.freshkill_pile)

    def handle_disaster(self):
        if not game.clan.disaster:
            return

        resource_dir = "resources/dicts/events/disasters/"
        disaster_text = {}
        with open(f"{resource_dir}forest.json",
                  encoding="ascii") as read_file:
            disaster_text = ujson.loads(read_file.read())
        
        current_disaster = disaster_text.get(game.clan.disaster)
        current_moon = game.clan.disaster_moon
        if current_moon == 0:
            event_string = random.choice(current_disaster["trigger_events"])
            game.clan.disaster_moon += 1
        elif current_moon < current_disaster["duration"]:
            event_string = random.choice(current_disaster["progress_events"]["moon" + str(current_moon)])
            game.clan.disaster_moon += 1
            self.handle_disaster_impacts(current_disaster)
            if random.randint(1,30) == 1 and not game.clan.second_disaster and current_disaster["secondary_disasters"]:
                game.clan.second_disaster = random.choice(list(current_disaster["secondary_disasters"].keys()))
                secondary_event_string = random.choice(current_disaster["secondary_disasters"][game.clan.second_disaster]["trigger_events"])
                secondary_event_string = ongoing_event_text_adjust(Cat, secondary_event_string)
                game.cur_events_list.append(
                        Single_Event(secondary_event_string, "alert"))
        else:
            event_string = random.choice(current_disaster["conclusion_events"])
            game.clan.disaster_moon = 0
            game.clan.disaster = ""
        
        event_string = ongoing_event_text_adjust(Cat, event_string)
        game.cur_events_list.insert(0, 
                        Single_Event(event_string, "alert"))
        if game.clan.second_disaster:
            self.handle_second_disaster()
    
    def handle_disaster_impacts(self, current_disaster):      
        for i in range(random.randint(0,2)):
            cat = Cat.all_cats.get(random.choice(game.clan.clan_cats))
            for j in range(20):
                if cat.outside or cat.dead or cat.moons < 6:
                    cat = Cat.all_cats.get(random.choice(game.clan.clan_cats))
                else:
                    break
            if cat.outside or cat.dead or cat.moons < 6:
                return
            if current_disaster["collateral_damage"]:
                if random.randint(1,10) == 1:
                    if random.randint(1,5) == 1:
                        herbs = game.clan.herbs.copy()
                        for herb in herbs:
                            adjust_by = random.choices([-3, -2, -1], [1, 2, 3],
                                                    k=1)
                            game.clan.herbs[herb] += adjust_by[0]
                            if game.clan.herbs[herb] <= 0:
                                game.clan.herbs.pop(herb)
                    if random.randint(1,5) == 1:
                        game.clan.freshkill_pile.total_amount = game.clan.freshkill_pile.total_amount * 0.7
                if random.randint(1,10) != 1:
                    if "injuries" in current_disaster["collateral_damage"]:
                        cat.get_injured(random.choice(current_disaster["collateral_damage"]["injuries"]))
                else:
                    if "deaths" in current_disaster["collateral_damage"]:
                        if cat.status == "leader":
                            History.add_death(cat, death_text=current_disaster["collateral_damage"]["deaths"]["history_text"]["reg_death"][4:])
                        else:
                            History.add_death(cat, death_text=current_disaster["collateral_damage"]["deaths"]["history_text"]["reg_death"])
                        cat.die()
                        death_text = random.choice(current_disaster["collateral_damage"]["deaths"]["death_text"]).replace("m_c", str(cat.name)).replace("c_n", str(game.clan.name) + "Clan")
                        game.cur_events_list.insert(0,
                            Single_Event(death_text, "birth_death", cat.ID))

    def handle_second_disaster(self):
        resource_dir = "resources/dicts/events/disasters/"
        disaster_text = {}
        with open(f"{resource_dir}forest.json",
                encoding="ascii") as read_file:
            disaster_text = ujson.loads(read_file.read())
        current_disaster = disaster_text.get(game.clan.second_disaster)
        current_moon = game.clan.second_disaster_moon
        if current_moon > 0 and current_moon < current_disaster["duration"]:
            event_string = random.choice(current_disaster["progress_events"]["moon" + str(current_moon)])
            event_string = ongoing_event_text_adjust(Cat, event_string)
            game.clan.second_disaster_moon += 1
            game.cur_events_list.insert(0,
                        Single_Event(event_string, "alert"))
        elif current_moon == current_disaster["duration"]:
            event_string = random.choice(current_disaster["conclusion_events"])
            game.clan.second_disaster_moon = 0
            game.clan.second_disaster = ""
            event_string = ongoing_event_text_adjust(Cat, event_string)
            game.cur_events_list.insert(0,
                        Single_Event(event_string, "alert"))

    def handle_illnesses_or_illness_deaths(self, cat):
        """
        This function will handle:
            - expanded mode: getting a new illness (extra function in own class)
        Returns:
            - boolean if a death event occurred or not
        """
        # ---------------------------------------------------------------------------- #
        #                           decide if cat dies                                 #
        # ---------------------------------------------------------------------------- #
        # if triggered_death is True then the cat will die
        triggered_death = False
        triggered_death = Condition_Events.handle_illnesses(
            cat, game.clan.current_season
        )
        return triggered_death

    def handle_twoleg_capture(self, cat):
        """
        TODO: DOCS
        """
        cat.outside = True
        cat.gone()
        # The outside-value must be set to True before the cat can go to cotc
        cat.thought = "Is terrified as they are trapped in a large silver Twoleg den"
        # FIXME: Not sure what this is intended to do; 'cat_class' has no 'other_cats' attribute.
        # cat_class.other_cats[cat.ID] = cat

    def handle_outbreaks(self, cat):
        """Try to infect some cats."""
        # check if the cat is ill,
        # or if Clan has sufficient med cats
        if not cat.is_ill():
            return

        # check how many kitties are already ill
        already_sick = list(
            filter(
                lambda kitty: (not kitty.dead and not kitty.outside and kitty.is_ill()),
                Cat.all_cats.values(),
            )
        )
        already_sick_count = len(already_sick)

        # round up the living kitties
        alive_cats = list(
            filter(
                lambda kitty: (
                    not kitty.dead and not kitty.outside and not kitty.is_ill()
                ),
                Cat.all_cats.values(),
            )
        )
        alive_count = len(alive_cats)

        # if large amount of the population is already sick, stop spreading
        if already_sick_count >= alive_count * 0.25:
            return

        meds = get_alive_status_cats(Cat, ["medicine cat", "medicine cat apprentice"], working=True, sort=True)

        for illness in cat.illnesses:
            # check if illness can infect other cats
            if cat.illnesses[illness]["infectiousness"] == 0:
                continue
            chance = cat.illnesses[illness]["infectiousness"]
            chance += len(meds) * 7
            if not int(random.random() * chance):  # 1/chance to infect
                # fleas are the only condition allowed to spread outside of cold seasons
                if (
                    game.clan.current_season not in ["Leaf-bare", "Leaf-fall"]
                    and illness != "fleas"
                ):
                    continue

                if game.clan.clan_settings.get("rest and recover"):
                    stopping_chance = game.config["focus"]["rest and recover"][
                        "outbreak_prevention"
                    ]
                    if not int(random.random() * stopping_chance):
                        continue

                if illness == "kittencough":
                    # adjust alive cats list to only include kittens
                    alive_cats = list(
                        filter(
                            lambda kitty: (
                                kitty.status in ["kitten", "newborn"]
                                and not kitty.dead
                                and not kitty.outside
                            ),
                            Cat.all_cats.values(),
                        )
                    )
                    alive_count = len(alive_cats)

                max_infected = int(alive_count / 2)  # 1/2 of alive cats
                # If there are less than two cat to infect,
                # you are allowed to infect all the cats
                if max_infected < 2:
                    max_infected = alive_count
                # If, event with all the cats, there is less
                # than two cats to infect, cancel outbreak.
                if max_infected < 2:
                    return

                weights = []
                population = []
                for n in range(2, max_infected + 1):
                    population.append(n)
                    weight = 1 / (0.75 * n)  # Lower chance for more infected cats
                    weights.append(weight)
                infected_count = random.choices(population, weights=weights)[
                    0
                ]  # the infected..

                infected_names = []
                involved_cats = []
                infected_cats = random.sample(alive_cats, infected_count)
                for sick_meowmeow in infected_cats:
                    infected_names.append(str(sick_meowmeow.name))
                    involved_cats.append(sick_meowmeow.ID)
                    sick_meowmeow.get_ill(
                        illness, event_triggered=True
                    )  # SPREAD THE GERMS >:)

                # TODO: hardcoded text events, not good, need to consider how to convert
                #  should this be handled in condition_events.py?
                illness_name = str(illness).capitalize()
                if illness == "kittencough":
                    event = (
                        f"{illness_name} has spread around the nursery. "
                        f'{", ".join(infected_names[:-1])}, and '
                        f"{infected_names[-1]} have been infected."
                    )
                elif illness == "fleas":
                    event = (
                        f"Fleas have been hopping from pelt to pelt and now "
                        f'{", ".join(infected_names[:-1])}, '
                        f"and {infected_names[-1]} are all infested."
                    )
                else:
                    event = (
                        f"{illness_name} has spread around the camp. "
                        f'{", ".join(infected_names[:-1])}, and '
                        f"{infected_names[-1]} have been infected."
                    )

                game.cur_events_list.append(
                    Single_Event(event, "health", involved_cats)
                )
                # game.health_events_list.append(event)
                break
    
    def exile_or_forgive(self, cat):
        """ a shunned cat becoming exiled, or being forgiven"""
        resource_dir = "resources/dicts/events/lifegen_events/"
        with open(f"{resource_dir}ceremonies.json",
                  encoding="ascii") as read_file:
            self.b_txt = ujson.loads(read_file.read())
        if cat.shunned > 2:
            involved_cats = []
            involved_cats.append(cat.ID)

            if game.clan.your_cat.ID == cat.ID:
                fate = random.randint(1, int((game.config["shunned_cat"]["exile_chance"][cat.age]) * 1.75))
            else:
                fate = random.randint(1, int(game.config["shunned_cat"]["exile_chance"][cat.age]))

            if fate > 2:
                cat.shunned = 0
                cat.forgiven = 1
                cat.exiled = False
                cat.outside = False
                cat.add_to_clan()
                if cat.ID == game.clan.your_cat.ID:
                    text = "A Clan meeting is called one day, and your Clanmates vote to forgive you for what you did."
                else:
                    text = random.choice([
                        f"After showing genuine remorse and guilt, {cat.name} has been forgiven and welcomed back into {game.clan.name}Clan, though some are quicker to forgive than others.",
                        f"{game.clan.leader.name} has chosen to lift the shun on {cat.name}, but will be watching them closely."])\

                # Do they get their job back?
                if cat.status in ['medicine cat', 'deputy', 'mediator', 'queen']:
                
                    if random.randint(1,2) == 1:
                        if cat.ID == game.clan.your_cat.ID:
                            text = text + f" You have shown that you can be trusted and will rejoin the Clan as a {cat.status}."
                        else:
                            text = text + f" They have shown that they can be trusted and will rejoin the Clan as a {cat.status}."

                        if cat.status == 'deputy':
                            game.clan.deputy.status_change('warrior')
                    else:
                        if cat.moons < 119:
                            newstatus = 'warrior'
                        else:
                            newstatus = 'elder'
                        if cat.ID == game.clan.your_cat.ID:
                            text = text + f" You will not be allowed to be a {cat.status} and will instead rejoin the Clan as a {newstatus}."
                        else:
                            text = text + f" They will not be allowed to be a {cat.status} and will instead rejoin the Clan as a {newstatus}."
                        
                        cat.status_change(newstatus)

                elif cat.status != "leader":
                    if cat.status in [
                        "apprentice",
                        "medicine cat apprentice",
                        "mediator apprentice",
                        "queen's apprentice"
                        ]:
                        self.ceremony(cat, cat.status, LG_TYPE="forgiven")

                    elif cat.status in ["kitten", "newborn"] and cat.moons >= 6:
                        self.ceremony(cat, "apprentice", LG_TYPE="forgiven")
                
                elif cat.status == 'leader':
                    if random.randint(1,4) == 1:
                        if cat.ID == game.clan.your_cat.ID:
                            text = text + f" {game.clan.name}Clan will once more look to you for guidance."
                        else:
                            text = text + f" {game.clan.name}Clan will once more look to them for guidance."
                        cat.specsuffix_hidden = False
                        if game.clan.deputy:
                            game.clan.deputy.status_change('warrior')
                        if game.clan.leader:
                            game.clan.leader.status_change('deputy')
                        cat.status_change('leader')
                    else:
                        if cat.ID == game.clan.your_cat.ID:
                            text = text + " You will not return as the Clan's leader."
                        else:
                            text = text + " They will not return as the Clan's leader."
                        if cat.moons < 119:
                            cat.status_change('warrior')
                        else:
                            cat.status_change('elder')

                game.cur_events_list.insert(0, Single_Event(text, "alert", involved_cats))

            elif fate == 2 and cat.ID != game.clan.your_cat.ID:
                cat.outside = True
                cat.status = "former Clancat"
                game.clan.add_to_outside(cat)
                if cat.moons < 6:
                    if cat.ID == game.clan.your_cat.ID:
                        text = f"You know that {game.clan.name}Clan would be better off without you. As fast as your little legs can carry you, you run out of camp one night, never to return."
                    else:
                        text = f"{cat.name} knows that they will never be able to forgive themselves for what they've done. In the night, while the queens are sleeping, they sneak out of camp while stifling their tears. They'll miss {game.clan.name}Clan, but they know that they'll be better off without a killer in their nursery."
                else:
                    if cat.ID == game.clan.your_cat.ID:
                        text = "After enduring endless disrespect from your clanmates, you've given up at seeking forgiveness. When you leave camp one morning, no one calls out after you, and you don't feel very sad that you'll never be back."
                    else:
                        text = random.choice([
                            f"{cat.name} knows they'll never be forgiven. Packing up their favourite feathers and stones from their nest, they slip out of camp in the night, sure that none of their Clanmates will mind the abscence.",
                            f"Sick of being treated so poorly, {cat.name} leaves camp one day, not turning around to see if anyone has noticed, and vows never to come back."])
                    game.cur_events_list.insert(0, Single_Event(text, "alert", involved_cats))

            else:
                cat.shunned = 0
                Cat.exile(cat)
                if cat.ID == game.clan.your_cat.ID:
                    text = f"{game.clan.name}Clan has decided that they don't feel safe with you around after what you did. You have been exiled."
                else:
                    text = random.choice([
                    f"{game.clan.name}Clan has decided that they don't feel safe with {cat.name} around after what they did. {cat.name} has been exiled.",
                    f"{game.clan.leader.name} knows that {cat.name} does not plan to atone. They have been exiled from {game.clan.name}Clan for their crimes."])
                game.cur_events_list.insert(0, Single_Event(text, "alert", involved_cats))

    def coming_out(self, cat):
        """turnin' the kitties trans..."""
        # TODO: should figure out how to handle these as a ShortEvent, we don't want hardcoded text
        if cat.genderalign == cat.gender:
            if cat.moons < 6:
                return

            involved_cats = [cat.ID]
            if cat.age == "adolescent":
                transing_chance = random.getrandbits(8)  # 2/256
            elif cat.age == "young adult":
                transing_chance = random.getrandbits(9)  # 2/512
            else:
                # adult, senior adult, elder
                transing_chance = random.getrandbits(10)  # 2/1028

            if transing_chance:
                # transing_chance != 0, no trans kitties today...    L
                return

            if random.getrandbits(1):  # 50/50
                if cat.gender == "male":
                    cat.genderalign = "trans female"
                    cat.pronouns = [cat.default_pronouns[1].copy()]
                elif cat.gender == "intersex":
                    whichtrans = randint(0,1)
                    if whichtrans == 0:
                        cat.genderalign = "trans male"
                        cat.pronouns = [cat.default_pronouns[2].copy()]
                    elif whichtrans == 1:
                        cat.genderalign = "trans female"
                        cat.pronouns = [cat.default_pronouns[1].copy()]
                else:
                    cat.genderalign = "trans male"
                    cat.pronouns = [cat.default_pronouns[2].copy()]
            else:
                cat.genderalign = "nonbinary"
                pronounpref = randint(0,4)
                if pronounpref == 1:
                    cat.pronouns = [cat.default_pronouns[1].copy()]
                elif pronounpref == 2:
                    cat.pronouns = [cat.default_pronouns[2].copy()]
                elif pronounpref == 3:
                    cat.pronouns = [cat.default_pronouns[3].copy()]
                else:
                    cat.pronouns = [cat.default_pronouns[0].copy()]

            text = f"{cat.name} has decided to play with gender and switch things up."
            game.cur_events_list.append(Single_Event(text, "misc", involved_cats))
            # game.misc_events_list.append(text)

    def check_and_promote_leader(self):
        """Checks if a new leader need to be promoted, and promotes them, if needed."""
        # check for leader
        if game.clan.leader:
            leader_invalid = game.clan.leader.dead or game.clan.leader.outside or game.clan.leader.shunned > 0
        else:
            leader_invalid = True

        if leader_invalid:
            self.perform_ceremonies(
                game.clan.leader
            )  # This is where the deputy will be make leader

            if game.clan.leader:
                leader_dead = game.clan.leader.dead
                leader_outside = game.clan.leader.outside
                leader_shunned = game.clan.leader.shunned > 0
            else:
                leader_dead = True
                leader_outside = True
                leader_shunned = True


            if leader_dead or leader_outside or leader_shunned:
                game.cur_events_list.insert(
                    0, Single_Event(f"{game.clan.name}Clan has no leader!", "alert"))

    def check_and_promote_deputy(self):
        """Checks if a new deputy needs to be appointed, and appointed them if needed. """
        if (not game.clan.deputy or game.clan.deputy.dead or game.clan.deputy.shunned > 0
                or game.clan.deputy.outside or game.clan.deputy.status == "elder"):
            if game.clan.clan_settings['deputy']:
                text = ""

                # This determines all the cats who are eligible to be deputy.
                possible_deputies = list(
                    filter(
                        lambda x: not x.dead
                        and not x.outside
                        and x.status == "warrior"
                        and (x.apprentice or x.former_apprentices),
                        Cat.all_cats_list,
                    )
                )

                # If there are possible deputies, choose from that list.
                if possible_deputies:
                    random_cat = random.choice(possible_deputies)
                    involved_cats = [random_cat.ID]

                    # Gather deputy and leader status, for determination of the text.
                    if game.clan.leader:
                        if game.clan.leader.dead or game.clan.leader.outside or game.clan.leader.shunned > 0:
                            leader_status = "not_here"
                        else:
                            leader_status = "here"
                    else:
                        leader_status = "not_here"

                    if game.clan.deputy:
                        if game.clan.deputy.dead or game.clan.deputy.outside or game.clan.deputy.shunned > 0:
                            deputy_status = "not_here"
                        else:
                            deputy_status = "here"
                    else:
                        deputy_status = "not_here"

                    if leader_status == "here" and deputy_status == "not_here":

                        if random_cat.personality.trait == "bloodthirsty":
                            text = (
                                f"{random_cat.name} has been chosen as the new deputy. "
                                f"They look at the Clan leader with an odd glint in their eyes."
                            )
                            # No additional involved cats
                        else:
                            if game.clan.deputy:
                                if game.clan.deputy.shunned == 0:
                                    previous_deputy_mention = random.choice([
                                        f"They know that {game.clan.deputy.name} would approve.",
                                        f"They hope that {game.clan.deputy.name} would approve.",
                                        f"They don't know if {game.clan.deputy.name} would approve, "
                                        f"but life must go on. "
                                    ])
                                elif game.clan.deputy.shunned == 2:
                                    previous_deputy_mention = f"Since {game.clan.deputy.name}'s crime was revealed, a new cat must be chosen to take their place."
                                    
                                involved_cats.append(game.clan.deputy.ID)

                            else:
                                previous_deputy_mention = ""

                            if game.clan.deputy:
                                if game.clan.deputy.shunned == 0:
                                    text = f"{game.clan.leader.name} chooses " \
                                        f"{random_cat.name} to take over " \
                                        f"as deputy. " + previous_deputy_mention
                                elif game.clan.deputy.shunned == 2:
                                    text = previous_deputy_mention + f" {game.clan.leader.name} chooses " \
                                        f"{random_cat.name} to take over " \
                                        f"as deputy."
                            else:
                                text = f"{game.clan.leader.name} chooses " \
                                        f"{random_cat.name} to take over " \
                                        f"as deputy. " + previous_deputy_mention

                            involved_cats.append(game.clan.leader.ID)
                    elif leader_status == "not_here" and deputy_status == "here":
                        text = (
                            f"The Clan is without a leader, but a "
                            f"new deputy must still be named.  "
                            f"{random_cat.name} is chosen as the new deputy. "
                            f"The retired deputy nods their approval."
                        )
                    elif leader_status == "not_here" and deputy_status == "not_here":
                        text = (
                            f"Without a leader or deputy, the Clan has been directionless. "
                            f"They all turn to {random_cat.name} with hope for the future."
                        )
                    elif leader_status == "here" and deputy_status == "here":
                        possible_events = [
                            f"{random_cat.name} has been chosen as the new deputy. "  # pylint: disable=line-too-long
                            f"The Clan yowls their name in approval.",  # pylint: disable=line-too-long
                            f"{random_cat.name} has been chosen as the new deputy. "  # pylint: disable=line-too-long
                            f"Some of the older Clan members question the wisdom in this choice.",
                            # pylint: disable=line-too-long
                            f"{random_cat.name} has been chosen as the new deputy. "  # pylint: disable=line-too-long
                            f"They hold their head up high and promise to do their best for the Clan.",
                            # pylint: disable=line-too-long
                            f"{game.clan.leader.name} has been thinking deeply all day who they would "  # pylint: disable=line-too-long
                            f"respect and trust enough to stand at their side, and at sunhigh makes the "  # pylint: disable=line-too-long
                            f"announcement that {random_cat.name} will be the Clan's new deputy.",
                            # pylint: disable=line-too-long
                            f"{random_cat.name} has been chosen as the new deputy. They pray to "  # pylint: disable=line-too-long
                            f"StarClan that they are the right choice for the Clan.",  # pylint: disable=line-too-long
                            f"{random_cat.name} has been chosen as the new deputy. Although"  # pylint: disable=line-too-long
                            f"they are nervous, they put on a brave front and look forward to serving"  # pylint: disable=line-too-long
                            f"the clan.",
                        ]
                        # No additional involved cats
                        text = random.choice(possible_events)
                    else:
                        # This should never happen. Failsafe.
                        text = f"{random_cat.name} becomes deputy. "
                else:
                    # If there are no possible deputies, choose someone else, with special text.

                    all_warriors = list(
                        filter(
                            lambda x: not x.dead
                            and not x.outside
                            and x.status == "warrior",
                            Cat.all_cats_list,
                        )
                    )
                    if all_warriors:
                        random_cat = random.choice(all_warriors)
                        involved_cats = [random_cat.ID]
                        text = (
                            f"No cat is truly fit to be deputy, "
                            f"but the position can't remain vacant. "
                            f"{random_cat.name} is appointed as the new deputy. "
                        )

                    else:
                        # Is there are no warriors at all, no one is named deputy.
                        game.cur_events_list.append(
                            Single_Event(
                                "There are no cats fit to become deputy. ", "ceremony"
                            )
                        )
                        return

                random_cat.status_change("deputy")
                game.clan.deputy = random_cat

                game.cur_events_list.append(
                    Single_Event(text, "ceremony", involved_cats)
                )

            else:
                game.cur_events_list.insert(
                    0, Single_Event(f"{game.clan.name}Clan has no deputy!", "alert")
                )


events_class = Events()
