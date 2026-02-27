# pylint: disable=line-too-long
"""

TODO: Docs


"""
# testt
# pylint: enable=line-too-long

import os
import random
import statistics
from random import choice, randint

import pygame
import ujson
from scripts.cat_relations.inheritance import Inheritance
from scripts.game_structure.game_essentials import game
from scripts.housekeeping.version import get_version_info, SAVE_VERSION_NUMBER
from scripts.utility import update_sprite, get_current_season, quit, get_free_possible_mates, get_alive_status_cats, create_new_cat  # pylint: disable=redefined-builtin
from scripts.cat.cats import Cat, cat_class, BACKSTORIES
from scripts.cat.pelts import Pelt
from scripts.cat.cats import Cat, cat_class
from scripts.cat.history import History
from scripts.cat.names import names
from scripts.cat.sprites import sprites
from sys import exit  # pylint: disable=redefined-builtin
from scripts.cat.names import Name
from scripts.clan_resources.freshkill import FreshkillPile, Nutrition
from scripts.events_module.generate_events import OngoingEvent
from scripts.game_structure.game_essentials import game
from scripts.housekeeping.datadir import get_save_dir
from scripts.housekeeping.version import get_version_info, SAVE_VERSION_NUMBER
from scripts.utility import (
    get_current_season,
    quit,
    clan_symbol_sprite,
)  # pylint: disable=redefined-builtin
from scripts.cat.skills import SkillPath, CatSkills


class Clan:
    """

    TODO: Docs

    """

    BIOME_TYPES = ["Forest", "Plains", "Mountainous", "Beach", "Rainworld", "Desert", "Wetlands"]

    CAT_TYPES = [
        "newborn",
        "kitten",
        "apprentice",
        "warrior",
        "medicine",
        "deputy",
        "leader",
        "elder",
        "mediator",
        "queen",
        "general",
        "exiled",
        "former Clancat",
        
        # neon pink exclusive below
        "rival Clancat",
        "rival newborn", "rival kitten", "rival apprentice",
        "rival medicine cat apprentice", "rival queen's apprentice",
        "rival mediator apprentice", "rival medicine cat", "rival mediator",
        "rival deputy", "rival leader"
    ]
    

    leader_lives = 0
    clan_cats = []
    starclan_cats = []
    darkforest_cats = []
    unknown_cats = []
    seasons = [
        "Newleaf",
        "Newleaf",
        "Newleaf",
        "Greenleaf",
        "Greenleaf",
        "Greenleaf",
        "Leaf-fall",
        "Leaf-fall",
        "Leaf-fall",
        "Leaf-bare",
        "Leaf-bare",
        "Leaf-bare",
    ]

    temperament_dict = {
        "low_social": ["cunning", "proud", "bloodthirsty"],
        "mid_social": ["amiable", "stoic", "wary"],
        "high_social": ["gracious", "mellow", "logical"],
    }

    with open("resources/placements.json", "r") as read_file:
        layouts = ujson.loads(read_file.read())

    age = 0
    current_season = "Newleaf"
    all_clans = []

    def __init__(
            self,
            name="",
            leader=None,
            deputy=None,
            medicine_cat=None,
            biome='Forest',
            camp_bg=None,
            symbol=None,
            game_mode='classic',
            starting_members=[],
            starting_season='Newleaf',
            followingsc=True,
            your_cat=None,
            focus_cat=None,
            clan_age=None,
            self_run_init_functions = False
                ):
        
        self.history = History()
        self.your_cat = your_cat
        if name == "":
            return

        self.name = name
        self.leader = leader
        self.leader_lives = 9
        self.leader_predecessors = 0
        self.deputy = deputy
        self.deputy_predecessors = 0
        self.medicine_cat = medicine_cat
        self.med_cat_list = []
        self.med_cat_predecessors = 0

        self.med_cat_number = len(
            self.med_cat_list
        )  # Must do this after the medicine cat is added to the list.
        self.herbs = {}
        self.age = 0
        self.current_season = "Newleaf"
        self.starting_season = starting_season
        self.instructor = None
        # ^^ starclan guide
        self.demon = None
        # ^^ dark forest guide
        self.followingsc = followingsc
        self.biome = biome
        self.camp_bg = camp_bg
        self.chosen_symbol = symbol
        self.game_mode = game_mode
        self.pregnancy_data = {}
        self.inheritance = {}
        self.murdered = False
        self.exile_return = False
        self.affair = False
        self.achievements = []
        self.talks = []
        self.focus = ""
        self.focus_moons = 0
        self.focus_cat = focus_cat
        self.clan_age = clan_age if clan_age else "established"
        self.custom_pronouns = []

        # Init Settings
        self.clan_settings = {}
        self.setting_lists = {}
        with open("resources/clansettings.json", "r") as read_file:
            _settings = ujson.loads(read_file.read())

        for setting, values in _settings["__other"].items():
            self.clan_settings[setting] = values[0]
            self.setting_lists[setting] = values

        all_settings = []
        all_settings.append(_settings["general"])
        all_settings.append(_settings["role"])
        all_settings.append(_settings["relation"])
        all_settings.append(_settings["freshkill_tactics"])
        all_settings.append(_settings["clan_focus"])

        for setting in all_settings:  # Add all the settings to the settings dictionary
            for setting_name, inf in setting.items():
                self.clan_settings[setting_name] = inf[2]
                self.setting_lists[setting_name] = [inf[2], not inf[2]]

        # Reputation is for loners/kittypets/outsiders in general that wish to join the clan.
        # it's a range from 1-100, with 30-70 being neutral, 71-100 being "welcoming",
        # and 1-29 being "hostile". if you're hostile to outsiders, they will VERY RARELY show up.
        self._reputation = 35

        self.starting_members = starting_members
        self.freshkill_pile = FreshkillPile()
        self.primary_disaster = None
        self.secondary_disaster = None
        self.war = {
            "at_war": False,
            "enemy": None,
            "duration": 0,
        }
        self.last_focus_change = None
        self.clans_in_focus = []

        self.faded_ids = (
            []
        )  # Stores ID's of faded cats, to ensure these IDs aren't reused.
        if self_run_init_functions:
            self.post_initialization_functions()
        self.disaster = ""
        self.second_disaster = ""
        self.disaster_moon = 0
        self.second_disaster_moon = 0

    # The clan couldn't save itself in time due to issues arising, for example, from this function:
    # "if deputy is not None: self.deputy.status_change('deputy') -> game.clan.remove_med_cat(self)"
    def post_initialization_functions(self):
        if self.deputy is not None:
            self.deputy.status_change("deputy")
            self.clan_cats.append(self.deputy.ID)

        if self.leader:
            self.leader.status_change("leader")
            self.clan_cats.append(self.leader.ID)

        if self.medicine_cat is not None:
            self.clan_cats.append(self.medicine_cat.ID)
            self.med_cat_list.append(self.medicine_cat.ID)
            if self.medicine_cat.status != "medicine cat":
                Cat.all_cats[self.medicine_cat.ID].status_change("medicine cat")

    def create_clan(self):
        """
        This function is only called once a new clan is
        created in the 'clan created' screen, not every time
        the program starts
        """
        lowercaseName = self.name.lower()
        if ("neon" and "pink") in lowercaseName:
            neonpinkEasteregg(self)
        else:
            self.instructor = Cat(status=choice([
                "apprentice", "mediator apprentice", "medicine cat apprentice", "warrior",
                "medicine cat", "leader", "mediator", "queen", "queen's apprentice", "deputy", "elder"]),
                                )
            self.instructor.dead = True
            self.instructor.dead_for = randint(0, 500)
            if self.clan_age == "new":
                self.instructor.backstory = choice(BACKSTORIES["backstory_categories"]["new_sc_guide_backstories"])
            else:
                self.instructor.backstory = choice(BACKSTORIES["backstory_categories"]["starclan_backstories"])
            self.add_cat(self.instructor)
            self.add_to_starclan(self.instructor)
            self.all_clans = []
            
            self.demon = Cat(status=choice(["apprentice", "mediator apprentice", "medicine cat apprentice", "warrior",
                                                "medicine cat", "leader", "mediator", "queen", "queen's apprentice",
                                                "deputy", "elder"]),
                                )
            self.demon.df = True
            self.demon.dead = True
            self.demon.dead_for = randint(1, 500)
            if self.clan_age == "new":
                self.demon.backstory = choice(BACKSTORIES["backstory_categories"]["new_df_guide_backstories"])
            else:
                self.demon.backstory = choice(BACKSTORIES["backstory_categories"]["df_backstories"])
            self.add_cat(self.demon)
            self.add_to_darkforest(self.demon)
        self.all_clans = []
        
        
        if self.leader.status != "leader":
            self.leader.status_change('leader')

        key_copy = tuple(Cat.all_cats.keys())
        for i in key_copy:  # Going through all currently existing cats
            # cat_class is a Cat-object
            not_found = True
            for x in [self.leader, self.deputy, self.medicine_cat] + self.starting_members:
                if Cat.all_cats[i] == x:
                    self.add_cat(Cat.all_cats[i])
                    not_found = False
            if Cat.all_cats[i] != self.leader and Cat.all_cats[i] != \
                    self.medicine_cat and Cat.all_cats[i] != \
                    self.deputy and Cat.all_cats[i] != \
                    self.instructor and Cat.all_cats[i] != \
                    self.demon and Cat.all_cats[i] != self.focus_cat \
                    and not_found:
                Cat.all_cats[i].example = True
                self.remove_cat(Cat.all_cats[i].ID)

        # give thoughts,actions and relationships to cats
        for cat_id in Cat.all_cats:
            Cat.all_cats.get(cat_id).init_all_relationships()
            if Cat.all_cats.get(cat_id).backstory is None:
                Cat.all_cats.get(cat_id).backstory = 'clan_founder'

            if Cat.all_cats.get(cat_id).status == 'apprentice':
                Cat.all_cats.get(cat_id).status_change('apprentice')
            elif Cat.all_cats.get(cat_id).status == "queen's apprentice":
                Cat.all_cats.get(cat_id).status_change("queen's apprentice")
            elif Cat.all_cats.get(cat_id).status == 'medicine cat apprentice':
                Cat.all_cats.get(cat_id).status_change('medicine cat apprentice')
            Cat.all_cats.get(cat_id).thoughts()

        game.save_cats()
        number_other_clans = randint(3, 5)
        for _ in range(number_other_clans):
            other_clan_names = [str(i.name) for i in self.all_clans] + [game.clan.name]
            other_clan_name = choice(names.names_dict["normal_prefixes"])
            while other_clan_name in other_clan_names:
                other_clan_name = choice(names.names_dict["normal_prefixes"])
            other_clan = OtherClan(name=other_clan_name)
            self.all_clans.append(other_clan)
            # initializes the names of other clans

            # initializing other clans' cats should go here?

        if 'other_med' in game.switches:
            del game.switches['other_med']
        self.save_clan()
        game.save_clanlist(self.name)
        game.switches["clan_list"] = game.read_clans()

        # this has to be done after saving the first time
        # doing this without any previous clans will cause a crash otherwise
        if self.clan_age == "established":
            self.generate_mates()
            self.generate_families()
            self.populate_sc()
            self.populate_ur()
            self.populate_df()
            self.populate_rivalclan()
            self.generate_outsiders()
            self.generate_outsider_mates()
            self.generate_outsider_families()
        elif self.clan_age == "new":
            self.generate_outsiders()
            self.generate_outsider_mates()
            self.generate_outsider_families()

        game.save_cats()
        self.save_clan()

        # CHECK IF CAMP BG IS SET -fail-safe in case it gets set to None-
        if game.switches["camp_bg"] is None:
            random_camp_options = ["camp1", "camp2"]
            random_camp = choice(random_camp_options)
            game.switches["camp_bg"] = random_camp

        # if no game mode chosen, set to Classic
        if game.switches["game_mode"] is None:
            game.switches["game_mode"] = "classic"
            self.game_mode = "classic"

        # set the starting season
        season_index = self.seasons.index(self.starting_season)
        self.current_season = self.seasons[season_index]
    
    def generate_mates(self):
        """Generates up to three pairs of mates."""

        def get_adult_mateless_cat():
            alive_cats = [i for i in Cat.all_cats.values() if i.moons >= 14 and not i.dead and not i.outside and not i.mate]
            if alive_cats:
                return random.choice(alive_cats)
            return None

        num_mates = random.randint(0,3)

        for i in range(num_mates):
            random_cat = get_adult_mateless_cat()
            if random_cat:
                same_age_cats = get_free_possible_mates(random_cat)

            if same_age_cats:
                random_mate_cat = random.choice(same_age_cats)
                if random_cat.is_potential_mate(random_mate_cat):
                    random_cat.set_mate(random_mate_cat)

    def generate_families(self):

        def get_kit_parent():
            alive_cats = [i for i in Cat.all_cats.values() if i.moons >= 20 and i.moons <= 100 and not i.dead and not i.outside]

            for cat in alive_cats:
                if not cat.inheritance:
                    cat.inheritance = Inheritance(cat)

            alive_cats = [i for i in alive_cats if not i.inheritance.get_blood_kits()]

            if alive_cats:
                return random.choice(alive_cats)
            return None

        def get_app_parent():
            alive_cats = [i for i in Cat.all_cats.values() if i.moons >= 40 and i.moons <= 100 and not i.dead and not i.outside]

            for cat in alive_cats:
                if not cat.inheritance:
                    cat.inheritance = Inheritance(cat)

            alive_cats = [i for i in alive_cats if not i.inheritance.get_blood_kits()]

            if alive_cats:
                return random.choice(alive_cats)
            return None
        
        clan_kits = get_alive_status_cats(Cat, ["newborn", "kitten"])
        clan_apps = get_alive_status_cats(Cat, ["apprentice", "medicine cat apprentice", "mediator apprentice", "queen's apprentice"])

        if not clan_kits and not clan_apps:
            return
        
        if clan_kits:
            for kit in clan_kits:
                if not kit.inheritance:
                    kit.inheritance = Inheritance(kit)
                if kit.ID != game.clan.your_cat.ID and kit.backstory == "clanborn" and not kit.parent1:
                    parent = get_kit_parent()
                    if parent:
                        kit.parent1 = parent.ID
                        parent.inheritance.update_inheritance()

                        if parent.mate:
                            kit.parent2 = choice(parent.mate)
                            if not Cat.all_cats.get(kit.parent2).inheritance:
                                Cat.all_cats.get(kit.parent2).inheritance = Inheritance(Cat.all_cats.get(kit.parent2))
                            Cat.all_cats.get(kit.parent2).inheritance.update_inheritance()

                        for other_kit in clan_kits:
                            if other_kit.ID != kit.ID and other_kit.ID != game.clan.your_cat.ID and kit.moons == other_kit.moons and not other_kit.parent1 and other_kit.backstory == "clanborn":
                                other_kit.parent1 = parent.ID
                                parent.inheritance.update_inheritance()
                                if kit.parent2:
                                    other_kit.parent2 = kit.parent2
                                    Cat.all_cats.get(kit.parent2).inheritance.update_inheritance()
                                    if not other_kit.inheritance:
                                        other_kit.inheritance = Inheritance(other_kit)
                kit.inheritance.update_inheritance()



        if clan_apps:
            for app in clan_apps:
                if app.backstory == "clanborn":
                    parent = get_app_parent()
                    if parent:
                        app.parent1 = parent.ID
                        if not app.inheritance:
                            app.inheritance = Inheritance(app)
                        app.inheritance.update_inheritance()
                        parent.inheritance.update_inheritance()
                        if parent.mate:
                            app.parent2 = choice(parent.mate)
                            if not Cat.all_cats.get(app.parent2).inheritance:
                                Cat.all_cats.get(app.parent2).inheritance = Inheritance(Cat.all_cats.get(app.parent2))
                            app.inheritance.update_inheritance()
                            Cat.all_cats.get(app.parent2).inheritance.update_inheritance()

    def populate_sc(self):
        for i in range(randint(0,5)):
            random_backstory = choice(["dead1",
                "dead3",
                "dead4",
                "dead6",
                "dead8",
                "dead10",
                "dead12",
                "dead15"])
            sc_cats = create_new_cat(
                Cat,
                new_name=True,
                alive=False,
                backstory=random_backstory,
                thought="Watches over the Clan"
                )
            sc_cats[0].history.beginning = None
            sc_cats[0].dead_for = randint(20, 200)

    def populate_ur(self):
        for i in range(randint(0,5)):
            random_backstory = choice(["dead1",
                "dead2",
                "dead3",
                "dead4",
                "dead5",
                "dead6",
                "dead8",
                "dead9",
                "dead10",
                "dead11",
                "dead12"])
            status = random.choice(["loner","kittypet"])
            ur_cats = create_new_cat(
                Cat,
                alive=False,
                status = status,
                loner=True if status == "loner" else False,
                kittypet=True if status == "kittypet" else False,
                outside=True,
                backstory=random_backstory,
                thought="Wanders the Unknown Residence"
                )
            ur_cats[0].history.beginning = None
            ur_cats[0].dead_for = randint(20,100)

    def populate_df(self):
        for i in range(randint(0,5)):
            random_backstory = choice(["dead2",
                "dead5",
                "dead7",
                "dead8",
                "dead9",
                "dead11",
                "dead12",
                "dead13",
                "dead14"])
            df_cats = create_new_cat(
                Cat,
                new_name=True,
                alive=False,
                df=True,
                backstory=random_backstory,
                thought="Watches the Clan from the gloom"
                )
            df_cats[0].history.beginning = None
            df_cats[0].dead_for = randint(20, 200)

    def generate_outsiders(self):
        for i in range(randint(0,5)):
            outsider = create_new_cat(
                Cat,
                status=random.choice(["loner", "kittypet",  "rogue"]),
                age=randint(15, 120),
                outside=True,
                thought="Wanders around beyond the Clan's borders"
                )[0]
            outsider.history.beginning = None

    def populate_rivalclan(self):
        for i in range(randint(1,5)):
            randAge = randint(1, 130)
            uncommonStart = randint(1,30)
            if randAge > 5 and uncommonStart != 1:
                random_backstory = choice(["clanborn","clanborn","clanborn","clanborn","clanborn","clanborn",
                                            "halfclan1","halfclan2","halfclan3","halfclan4","halfclan5",
                                            "halfclan6","halfclan7","halfclan8","halfclan9","halfclan10",
                                            "outsider_roots1","outsider_roots2","outsider_roots3","outsider_roots4",
                                            "outsider_roots5","outsider_roots6","outsider_roots7","outsider_roots8",
                                            "loner1","loner2","loner3","loner4","loner6","loner7",
                                            "rogue1","rogue2","rogue3","rogue4","rogue5","rogue6","rogue8",
                                            "kittypet1","kittypet2","kittypet3","kittypet4","kittypet5","kittypet6","kittypet7",
                                            "kittypet8","kittypet9",
                                            "otherclan1","otherclan2","otherclan3","otherclan4","otherclan5","otherclan6",
                                            "otherclan7","otherclan8","otherclan9","otherclan10","otherclan12",
                                            "outsider1","outsider2","outsider3","outsider4","outsider5","outsider6",

                                            "tragedy_survivor1","tragedy_survivor2","tragedy_survivor3","tragedy_survivor4",
                                            "tragedy_survivor5",
                                            "tragedy_survivor6",
                                            "guided1","guided2","guided3","guided4","guided5","guided6",
                                            "refugee1","refugee2","refugee3","refugee4","refugee5","refugee6","refugee7",

                                           "orphaned1","orphaned2","orphaned3","orphaned4","orphaned5","orphaned6","orphaned7",
                                           "abandoned1","abandoned2","abandoned3","abandoned4"
                                            ])
            elif randAge > 24 and uncommonStart == 1:
                # for older cats and cats at least 2 years old. includes exiled stories
                # "otherclan11" should not be used since it names the clan
                random_backstory = choice(["clanborn","clanborn","clanborn","clanborn",
                                            "retired_leader","ostracized_warrior","medicine_cat",
                                            "wandering_healer2","wandering_healer1",
                                            "disgraced1","disgraced2","disgraced3",
                                            "otherclan13","rogue7",
                                            ])
            else: # kitten backstories!
                random_backstory = choice(["clanborn","clanborn","clanborn","clanborn","clanborn","clanborn","clanborn",
                                           "clanborn","clanborn","clanborn","clanborn","clanborn","clanborn","clanborn",
                                           "orphaned1","orphaned2","orphaned3","orphaned4","orphaned5","orphaned6","orphaned7",
                                           "abandoned1","abandoned2","abandoned3","abandoned4",

                                           "otherclan9",
                                           ])
            setstatus="rival Clancat"
            if randAge == 0:
                setstatus="rival newborn"
            elif randAge < 6:
                setstatus="rival kitten"
            elif randAge < 12:
                setstatus="rival apprentice"
            # im sure theres an easier way to do all this. i dont really care too much tho. not at the moment
            r1_cats = create_new_cat(
                Cat,
                status=setstatus,
                age=randAge,
                backstory=random_backstory,
                new_name=True,
                outside=True,
                thought="Business as usual",
                outClan=1
                )[0]
            r1_cats.history.beginning = None

    def generate_outsider_mates(self):
        """Generates up to three pairs of mates."""

        def get_adult_mateless_cat():
            alive_cats = [i for i in Cat.all_cats.values() if i.moons >= 14 and not i.dead and not i.mate]
            if alive_cats:
                return random.choice(alive_cats)
            return None

        num_mates = random.randint(0,3)

        for i in range(num_mates):
            random_cat = get_adult_mateless_cat()
            if random_cat:
                same_age_cats = get_free_possible_mates(random_cat)

            if same_age_cats:
                random_mate_cat = random.choice(same_age_cats)
                if random_cat.is_potential_mate(random_mate_cat):
                    random_cat.set_mate(random_mate_cat)

    def generate_outsider_families(self):
        def get_kit_parent():
            alive_cats = [i for i in Cat.all_cats.values() if i.moons >= 20 and i.moons <= 100 and not i.dead]

            for cat in alive_cats:
                if not cat.inheritance:
                    cat.inheritance = Inheritance(cat)

            alive_cats = [i for i in alive_cats if not i.inheritance.get_blood_kits()]

            if alive_cats:
                return random.choice(alive_cats)
            return None

        def get_app_parent():
            alive_cats = [i for i in Cat.all_cats.values() if i.moons >= 40 and i.moons <= 100 and not i.dead]

            for cat in alive_cats:
                if not cat.inheritance:
                    cat.inheritance = Inheritance(cat)

            alive_cats = [i for i in alive_cats if not i.inheritance.get_blood_kits()]

            if alive_cats:
                return random.choice(alive_cats)
            return None
        
        clan_kits = get_alive_status_cats(Cat, ["newborn", "kitten"])
        clan_apps = get_alive_status_cats(Cat, ["apprentice", "medicine cat apprentice", "mediator apprentice", "queen's apprentice"])

        if not clan_kits and not clan_apps:
            return
        
        if clan_kits:
            for kit in clan_kits:
                if not kit.inheritance:
                    kit.inheritance = Inheritance(kit)
                if kit.ID != game.clan.your_cat.ID and not kit.parent1:
                    parent = get_kit_parent()
                    if parent:
                        kit.parent1 = parent.ID
                        parent.inheritance.update_inheritance()

                        if parent.mate:
                            kit.parent2 = choice(parent.mate)
                            if not Cat.all_cats.get(kit.parent2).inheritance:
                                Cat.all_cats.get(kit.parent2).inheritance = Inheritance(Cat.all_cats.get(kit.parent2))
                            Cat.all_cats.get(kit.parent2).inheritance.update_inheritance()

                        for other_kit in clan_kits:
                            if other_kit.ID != kit.ID and other_kit.ID != game.clan.your_cat.ID and kit.moons == other_kit.moons and not other_kit.parent1:
                                other_kit.parent1 = parent.ID
                                parent.inheritance.update_inheritance()
                                if kit.parent2:
                                    other_kit.parent2 = kit.parent2
                                    Cat.all_cats.get(kit.parent2).inheritance.update_inheritance()
                                    if not other_kit.inheritance:
                                        other_kit.inheritance = Inheritance(other_kit)
                kit.inheritance.update_inheritance()

        if clan_apps:
            for app in clan_apps:
                parent = get_app_parent()
                if parent:
                    app.parent1 = parent.ID
                    if not app.inheritance:
                        app.inheritance = Inheritance(app)
                    app.inheritance.update_inheritance()
                    parent.inheritance.update_inheritance()
                    if parent.mate:
                        app.parent2 = choice(parent.mate)
                        if not Cat.all_cats.get(app.parent2).inheritance:
                            Cat.all_cats.get(app.parent2).inheritance = Inheritance(Cat.all_cats.get(app.parent2))
                        app.inheritance.update_inheritance()
                        Cat.all_cats.get(app.parent2).inheritance.update_inheritance()


    def add_cat(self, cat):  # cat is a 'Cat' object
        """Adds cat into the list of clan cats"""
        if cat.ID in Cat.all_cats and cat.ID not in self.clan_cats:
            self.clan_cats.append(cat.ID)

    def add_pronouns(self, pronouns):  # pronouns is a dict
        self.custom_pronouns.append(pronouns)

    def add_to_starclan(self, cat):  # Same as add_cat
        """
        Places the dead cat into StarClan.
        It should not be removed from the list of cats in the clan
        """
        if (
            cat.ID in Cat.all_cats
            and cat.dead
            and cat.ID not in self.starclan_cats
            and cat.df is False
        ):
            # The dead-value must be set to True before the cat can go to starclan
            self.starclan_cats.append(cat.ID)
            if cat.ID in self.darkforest_cats:
                self.darkforest_cats.remove(cat.ID)
            if cat.ID in self.unknown_cats:
                self.unknown_cats.remove(cat.ID)
            if cat.ID in self.med_cat_list:
                self.med_cat_list.remove(cat.ID)
                self.med_cat_predecessors += 1

    def add_to_darkforest(self, cat):  # Same as add_cat
        """
        Places the dead cat into the dark forest.
        It should not be removed from the list of cats in the clan
        """
        if cat.ID in Cat.all_cats and cat.dead and cat.df:
            self.darkforest_cats.append(cat.ID)
            if cat.ID in self.starclan_cats:
                self.starclan_cats.remove(cat.ID)
            if cat.ID in self.unknown_cats:
                self.unknown_cats.remove(cat.ID)
            if cat.ID in self.med_cat_list:
                self.med_cat_list.remove(cat.ID)
                self.med_cat_predecessors += 1
            #update_sprite(Cat.all_cats[str(cat)])
            # The dead-value must be set to True before the cat can go to starclan

    def add_to_unknown(self, cat):
        """
        Places dead cat into the unknown residence.
        It should not be removed from the list of cats in the clan
        :param cat: cat object
        """
        if cat.ID in Cat.all_cats and cat.dead and cat.outside:
            self.unknown_cats.append(cat.ID)
            if cat.ID in self.starclan_cats:
                self.starclan_cats.remove(cat.ID)
            if cat.ID in self.darkforest_cats:
                self.darkforest_cats.remove(cat.ID)
            if cat.ID in self.med_cat_list:
                self.med_cat_list.remove(cat.ID)
                self.med_cat_predecessors += 1

    def add_to_clan(self, cat):
        """
        TODO: DOCS
        """
        if (
            cat.ID in Cat.all_cats
            and not cat.outside
            and not cat.dead
            and cat.ID in Cat.outside_cats
        ):
            # The outside-value must be set to True before the cat can go to cotc
            Cat.outside_cats.pop(cat.ID)
            cat.clan = str(game.clan.name)

    def add_to_outside(self, cat):  # same as add_cat
        """
        Places the gone cat into cotc.
        It should not be removed from the list of cats in the clan
        """
        if cat.ID in Cat.all_cats and cat.outside and cat.ID not in Cat.outside_cats:
            # The outside-value must be set to True before the cat can go to cotc
            Cat.outside_cats.update({cat.ID: cat})

    def remove_cat(self, ID):  # ID is cat.ID
        """
        This function is for completely removing the cat from the game,
        it's not meant for a cat that's simply dead
        """

        if Cat.all_cats[ID] in Cat.all_cats_list:
            Cat.all_cats_list.remove(Cat.all_cats[ID])

        if ID in Cat.all_cats:
            Cat.all_cats.pop(ID)

        if ID in self.clan_cats:
            self.clan_cats.remove(ID)
        if ID in self.starclan_cats:
            self.starclan_cats.remove(ID)
        if ID in self.unknown_cats:
            self.unknown_cats.remove(ID)
        if ID in self.darkforest_cats:
            self.darkforest_cats.remove(ID)

    def __repr__(self):
        if self.name is not None:
            _ = (
                f"{self.name}: led by {self.leader.name}"
                f"with {self.medicine_cat.name} as med. cat"
            )
            return _

        else:
            return "No Clan"

    def new_leader(self, leader):
        """
        TODO: DOCS
        """
        if leader:
            self.history.add_lead_ceremony(leader)
            self.leader = leader
            Cat.all_cats[leader.ID].status_change("leader")
            self.leader_predecessors += 1
            self.leader_lives = 9
            for clan_cat in game.clan.clan_cats:
                clan_cat_cat = Cat.fetch_cat(clan_cat)
                if clan_cat_cat:
                    if game.clan.followingsc:
                        clan_cat_cat.faith += round(random.uniform(0,1), 2)
                    else:
                        clan_cat_cat.faith -= round(random.uniform(0,1), 2)
        game.switches['new_leader'] = None

    def new_deputy(self, deputy):
        """
        TODO: DOCS
        """
        if deputy:
            self.deputy = deputy
            Cat.all_cats[deputy.ID].status_change("deputy")
            self.deputy_predecessors += 1

    def new_medicine_cat(self, medicine_cat):
        """
        TODO: DOCS
        """
        if medicine_cat:
            if medicine_cat.status != "medicine cat":
                Cat.all_cats[medicine_cat.ID].status_change("medicine cat")
            if medicine_cat.ID not in self.med_cat_list:
                self.med_cat_list.append(medicine_cat.ID)
            medicine_cat = self.med_cat_list[0]
            self.medicine_cat = Cat.all_cats[medicine_cat]
            self.med_cat_number = len(self.med_cat_list)

    def remove_med_cat(self, medicine_cat):
        """
        Removes a med cat. Use when retiring, or switching to warrior
        """
        if medicine_cat:
            if medicine_cat.ID in game.clan.med_cat_list:
                game.clan.med_cat_list.remove(medicine_cat.ID)
                game.clan.med_cat_number = len(game.clan.med_cat_list)
            if self.medicine_cat:
                if medicine_cat.ID == self.medicine_cat.ID:
                    if game.clan.med_cat_list:
                        game.clan.medicine_cat = Cat.fetch_cat(
                            game.clan.med_cat_list[0]
                        )
                        game.clan.med_cat_number = len(game.clan.med_cat_list)
                    else:
                        game.clan.medicine_cat = None

    @staticmethod
    def switch_clans(clan):
        """
        TODO: DOCS
        """
        game.save_clanlist(clan)
        quit(savesettings=False, clearevents=True)

    def save_clan(self):
        """
        TODO: DOCS
        """

        clan_data = {
            "clanname": self.name,
            "clanage": self.age,
            "biome": self.biome,
            "camp_bg": self.camp_bg,
            "clan_symbol": self.chosen_symbol,
            "gamemode": self.game_mode,
            "last_focus_change": self.last_focus_change,
            "clans_in_focus": self.clans_in_focus,
            "instructor": self.instructor.ID,
            "demon": self.demon.ID,
            "reputation": self.reputation,
            "following_starclan": self.followingsc, 
            "mediated": game.mediated,
            "starting_season": self.starting_season,
            "temperament": self.temperament,
            "version_name": SAVE_VERSION_NUMBER,
            "version_commit": get_version_info().version_number,
            "source_build": get_version_info().is_source_build,
            "your_cat": self.your_cat.ID,
            "murdered": self.murdered,
            "exile_return": self.exile_return,
            "affair": self.affair,
            "custom_pronouns": self.custom_pronouns,
            "clan_age": self.clan_age
        }

        # LEADER DATA
        if self.leader:
            clan_data["leader"] = self.leader.ID
            clan_data["leader_lives"] = self.leader_lives
        else:
            clan_data["leader"] = None

        clan_data["leader_predecessors"] = self.leader_predecessors

        # DEPUTY DATA
        if self.deputy:
            clan_data["deputy"] = self.deputy.ID
        else:
            clan_data["deputy"] = None

        clan_data["deputy_predecessors"] = self.deputy_predecessors

        # MED CAT DATA
        if self.medicine_cat:
            clan_data["med_cat"] = self.medicine_cat.ID
        else:
            clan_data["med_cat"] = None
        clan_data["med_cat_number"] = self.med_cat_number
        clan_data["med_cat_predecessors"] = self.med_cat_predecessors

        # LIST OF CLAN CATS
        clan_data["clan_cats"] = ",".join([str(i) for i in self.clan_cats])

        clan_data["faded_cats"] = ",".join([str(i) for i in self.faded_ids])

        # Patrolled cats
        clan_data["patrolled_cats"] = [str(i) for i in game.patrolled]

        # OTHER CLANS
        # Clan Names
        clan_data["other_clans_names"] = ",".join([str(i.name) for i in self.all_clans])
        clan_data["other_clans_relations"] = ",".join(
            [str(i.relations) for i in self.all_clans]
        )
        clan_data["other_clan_temperament"] = ",".join(
            [str(i.temperament) for i in self.all_clans]
        )
        clan_data["other_clan_chosen_symbol"] = ",".join(
            [str(i.chosen_symbol) for i in self.all_clans]
        )
        clan_data["war"] = self.war
        clan_data['achievements'] = self.achievements
        clan_data['talks'] = self.talks
        clan_data["disaster"] = self.disaster
        clan_data["disaster_moon"] = self.disaster_moon
        clan_data["focus"] = self.focus
        clan_data["focus_moons"] = self.focus_moons

        if self.focus_cat:
            clan_data["focus_cat"] = self.focus_cat.ID
        else:
            clan_data["focus_cat"] = None

        if "other_med" in game.switches:
            other_med = []
            for other_clan in game.switches["other_med"]:
                cats = []
                for c in other_clan:
                    cats.append(c.prefix + "," + c.suffix + "," + c.status)
                other_med.append(cats)
            clan_data["other_med"] = other_med

        self.save_herbs(game.clan)
        self.save_disaster(game.clan)
        self.save_pregnancy(game.clan)

        self.save_clan_settings()
        self.save_freshkill_pile(game.clan)

        game.safe_save(f"{get_save_dir()}/{self.name}clan.json", clan_data)

        if os.path.exists(get_save_dir() + f"/{self.name}clan.txt") & (self.name != 'current'):
            os.remove(get_save_dir() + f"/{self.name}clan.txt")

    def switch_setting(self, setting_name):
        """Call this function to change a setting given in the parameter by one to the right on it's list"""
        self.settings_changed = True

        # Give the index that the list is currently at
        list_index = self.setting_lists[setting_name].index(
            self.clan_settings[setting_name]
        )

        if (
            list_index == len(self.setting_lists[setting_name]) - 1
        ):  # The option is at the list's end, go back to 0
            self.clan_settings[setting_name] = self.setting_lists[setting_name][0]
        else:
            # Else move on to the next item on the list
            self.clan_settings[setting_name] = self.setting_lists[setting_name][
                list_index + 1
            ]

    def save_clan_settings(self):
        game.safe_save(
            get_save_dir() + f"/{self.name}/clan_settings.json", self.clan_settings
        )

    def load_clan(self):
        """
        TODO: DOCS
        """

        version_info = None
        if os.path.exists(
            get_save_dir() + "/" + game.switches["clan_list"][0] + "clan.json"
        ):
            version_info = self.load_clan_json()
        elif os.path.exists(
            get_save_dir() + "/" + game.switches["clan_list"][0] + "clan.txt"
        ):
            self.load_clan_txt()
        else:
            game.switches["error_message"] = "There was an error loading the clan.json"

        game.clan.load_clan_settings()

        return version_info

    def load_clan_txt(self):
        """
        TODO: DOCS
        """
        other_clans = []
        if game.switches["clan_list"] == "":
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_clans.append(OtherClan())
            return
        if game.switches["clan_list"][0].strip() == "":
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_clans.append(OtherClan())
            return
        game.switches["error_message"] = "There was an error loading the clan.txt"
        with open(
            get_save_dir() + "/" + game.switches["clan_list"][0] + "clan.txt",
            "r",
            encoding="utf-8",
        ) as read_file:  # pylint: disable=redefined-outer-name
            clan_data = read_file.read()
        clan_data = clan_data.replace('\t', ',')
        sections = clan_data.split('\n')
        if len(sections) == 8:
            general = sections[0].split(',')
            leader_info = sections[1].split(',')
            deputy_info = sections[2].split(',')
            med_cat_info = sections[3].split(',')
            instructor_info = sections[4]
            members = sections[5].split(',')
            demon_info = sections[6]
            other_clans = []
        elif len(sections) == 7:
            general = sections[0].split(',')
            leader_info = sections[1].split(',')
            deputy_info = sections[2].split(',')
            med_cat_info = sections[3].split(',')
            instructor_info = sections[4]
            members = sections[5].split(',')
            demon_info = sections[6]
            other_clans = []
        else:
            general = sections[0].split(",")
            leader_info = sections[1].split(",")
            deputy_info = 0, 0
            med_cat_info = sections[2].split(",")
            instructor_info = sections[3]
            members = sections[4].split(',')
            demon_info = sections[5]
            other_clans = []
        if len(general) == 9:
            if general[3] == "None":
                general[3] = "camp1"
            elif general[4] == "None":
                general[4] = 0
            elif general[7] == "None":
                general[7] = "classic"
            elif general[8] == "None":
                general[8] = 50
            game.clan = Clan(
                name=general[0],
                leader=Cat.all_cats[leader_info[0]],
                deputy=Cat.all_cats.get(deputy_info[0], None),
                medicine_cat=Cat.all_cats.get(med_cat_info[0], None),
                biome=general[2],
                camp_bg=general[3],
                game_mode=general[7],
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
            game.clan.reputation = general[8]
        elif len(general) == 8:
            if general[3] == "None":
                general[3] = "camp1"
            elif general[4] == "None":
                general[4] = 0
            elif general[7] == "None":
                general[7] = "classic"
            game.clan = Clan(
                name=general[0],
                leader=Cat.all_cats[leader_info[0]],
                deputy=Cat.all_cats.get(deputy_info[0], None),
                medicine_cat=Cat.all_cats.get(med_cat_info[0], None),
                biome=general[2],
                camp_bg=general[3],
                game_mode=general[7],
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
        elif len(general) == 7:
            if general[4] == "None":
                general[4] = 0
            elif general[3] == "None":
                general[3] = "camp1"
            game.clan = Clan(
                name=general[0],
                leader=Cat.all_cats[leader_info[0]],
                deputy=Cat.all_cats.get(deputy_info[0], None),
                medicine_cat=Cat.all_cats.get(med_cat_info[0], None),
                biome=general[2],
                camp_bg=general[3],
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
        elif len(general) == 3:
            game.clan = Clan(
                name=general[0],
                leader=Cat.all_cats[leader_info[0]],
                deputy=Cat.all_cats.get(deputy_info[0], None),
                medicine_cat=Cat.all_cats.get(med_cat_info[0], None),
                biome=general[2],
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
        else:
            game.clan = Clan(
                general[0],
                Cat.all_cats[leader_info[0]],
                Cat.all_cats.get(deputy_info[0], None),
                Cat.all_cats.get(med_cat_info[0], None),
                self_run_init_functions=False,
            )
            game.clan.post_initialization_functions()
        game.clan.age = int(general[1])
        if not game.config["lock_season"]:
            game.clan.current_season = game.clan.seasons[game.clan.age % 12]
        else:
            game.clan.current_season = game.clan.starting_season
        game.clan.leader_lives, game.clan.leader_predecessors = int(
            leader_info[1]
        ), int(leader_info[2])

        if len(deputy_info) > 1:
            game.clan.deputy_predecessors = int(deputy_info[1])
        if len(med_cat_info) > 1:
            game.clan.med_cat_predecessors = int(med_cat_info[1])
        if len(med_cat_info) > 2:
            game.clan.med_cat_number = int(med_cat_info[2])
        if len(sections) > 4:
            if instructor_info in Cat.all_cats:
                game.clan.instructor = Cat.all_cats[instructor_info]
                game.clan.add_cat(game.clan.instructor)
        else:
            game.clan.instructor = Cat(status=choice(["warrior", "warrior", "elder"]))
            # update_sprite(game.clan.instructor)
            game.clan.instructor.dead = True
            game.clan.add_cat(game.clan.instructor)
            
        if len(sections) > 4:
            if demon_info in Cat.all_cats:
                game.clan.demon = Cat.all_cats[demon_info]
                game.clan.add_cat(game.clan.demon)
        else:
            game.clan.demon = Cat(
                status=choice(["warrior", "warrior", "elder"]))
            # update_sprite(game.clan.demon)
            game.clan.demon.dead = True
            game.clan.add_cat(game.clan.demon)

        if other_clans != [""]:
            for other_clan in other_clans:
                other_clan_info = other_clan.split(";")
                self.all_clans.append(
                    OtherClan(
                        other_clan_info[0], int(other_clan_info[1]), other_clan_info[2]
                    )
                )

        else:
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_clans.append(OtherClan())

        for cat in members:
            if cat in Cat.all_cats:
                game.clan.add_cat(Cat.all_cats[cat])
                game.clan.add_to_starclan(Cat.all_cats[cat])
            else:
                print("WARNING: Cat not found:", cat)
        self.load_pregnancy(game.clan)

        # assigning a symbol, since this save would be too old to have a chosen symbol
        game.clan.chosen_symbol = clan_symbol_sprite(game.clan, return_string=True)

        game.switches["error_message"] = ""

    def load_clan_json(self):
        """
        TODO: DOCS
        """
        other_clans = []
        if game.switches["clan_list"] == "":
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_clans.append(OtherClan())
            return
        if game.switches["clan_list"][0].strip() == "":
            number_other_clans = randint(3, 5)
            for _ in range(number_other_clans):
                self.all_clans.append(OtherClan())
            return

        game.switches["error_message"] = "There was an error loading the clan.json - json error"
        with open(
            get_save_dir() + "/" + game.switches["clan_list"][0] + "clan.json",
            "r",
            encoding="utf-8",
        ) as read_file:  # pylint: disable=redefined-outer-name
            clan_data = ujson.loads(read_file.read())

        if clan_data["leader"]:
            leader = Cat.all_cats[clan_data["leader"]]
            leader_lives = clan_data["leader_lives"]
        else:
            leader = None
            leader_lives = 0

        if clan_data["deputy"]:
            deputy = Cat.all_cats[clan_data["deputy"]]
        else:
            deputy = None

        if clan_data["med_cat"]:
            med_cat = Cat.all_cats[clan_data["med_cat"]]
        else:
            med_cat = None

        game.switches["error_message"] = "Error loading ---clan.json. Check clanname/biome/camp_bg/gamemode"
        game.clan = Clan(
            name=clan_data["clanname"],
            leader=leader,
            deputy=deputy,
            medicine_cat=med_cat,
            biome=clan_data["biome"],
            camp_bg=clan_data["camp_bg"],
            game_mode=clan_data["gamemode"],
            self_run_init_functions=False,
        )
        game.clan.post_initialization_functions()

        if "following_starclan" in clan_data:
            game.clan.followingsc = clan_data['following_starclan']
        else:
            game.clan.followingsc = True
        game.clan.reputation = int(clan_data["reputation"])

        game.switches["error_message"] = "Error loading ---clan.json. Check clan age"
        game.clan.age = clan_data["clanage"]
        game.switches["error_message"] = "Error loading ---clan.json. Check season"
        game.clan.starting_season = (
            clan_data["starting_season"]
            if "starting_season" in clan_data
            else "Newleaf"
        )
        get_current_season()

        game.switches["error_message"] = "Error loading ---clan.json. Check Leader related info"
        game.clan.leader_lives = leader_lives
        game.clan.leader_predecessors = clan_data["leader_predecessors"]

        game.switches["error_message"] = "Error loading ---clan.json. Check Deputy related info"
        game.clan.deputy_predecessors = clan_data["deputy_predecessors"]
        game.switches["error_message"] = "Error loading ---clan.json. Check Medcat related info"
        game.clan.med_cat_predecessors = clan_data["med_cat_predecessors"]
        game.clan.med_cat_number = clan_data["med_cat_number"]
        # Allows for the custom pronouns to show up in the add pronoun list after the game has closed and reopened.
        if "custom_pronouns" in clan_data.keys():
            if clan_data["custom_pronouns"]:
                game.clan.custom_pronouns = clan_data["custom_pronouns"]

        # Instructor Info
        if clan_data["instructor"] in Cat.all_cats:
            game.clan.instructor = Cat.all_cats[clan_data["instructor"]]
            game.clan.add_cat(game.clan.instructor)
        else:
            game.clan.instructor = Cat(status=choice(["warrior", "warrior", "elder"]))
            # update_sprite(game.clan.instructor)
            game.clan.instructor.dead = True
            game.clan.add_cat(game.clan.instructor)
            
        # demon Info
        if "demon" in clan_data and clan_data["demon"] in Cat.all_cats:
            game.clan.demon = Cat.all_cats[clan_data["demon"]]
            game.clan.add_cat(game.clan.demon)
            game.clan.demon.df = True
        else:
            game.clan.demon = Cat(
                status=choice(["warrior", "warrior", "elder"]))
            game.clan.demon.dead = True
            game.clan.add_cat(game.clan.demon)
            game.clan.demon.df = True
   
        ##Commented this out because I don't know why it's in here twice. If lead/dep/med stuff starts sobbing... ye ##
        # game.clan.leader_lives = leader_lives
        # game.clan.leader_predecessors = clan_data["leader_predecessors"]

        # game.clan.deputy_predecessors = clan_data["deputy_predecessors"]
        # game.clan.med_cat_predecessors = clan_data["med_cat_predecessors"]
        # game.clan.med_cat_number = clan_data["med_cat_number"]

        # check for symbol
        if "clan_symbol" in clan_data:
            game.clan.chosen_symbol = clan_data["clan_symbol"]
        else:
            game.clan.chosen_symbol = clan_symbol_sprite(game.clan, return_string=True)

        if "other_clan_chosen_symbol" not in clan_data:
            for name, relation, temper in zip(
                clan_data["other_clans_names"].split(","),
                clan_data["other_clans_relations"].split(","),
                clan_data["other_clan_temperament"].split(","),
            ):
                game.clan.all_clans.append(
                    OtherClan(name, int(relation), temper))
        else:
            for name, relation, temper, symbol in zip(
                clan_data["other_clans_names"].split(","),
                clan_data["other_clans_relations"].split(","),
                clan_data["other_clan_temperament"].split(","),
                clan_data["other_clan_chosen_symbol"].split(","),
            ):
                game.clan.all_clans.append(
                    OtherClan(name, int(relation), temper, symbol)
                )

        for cat in clan_data["clan_cats"].split(","):
            if cat in Cat.all_cats:
                game.clan.add_cat(Cat.all_cats[cat])
                game.clan.add_to_starclan(Cat.all_cats[cat])
                game.clan.add_to_darkforest(Cat.all_cats[cat])
                game.clan.add_to_unknown(Cat.all_cats[cat])
            else:
                print("WARNING: Cat not found:", cat)
                game.switches["error_message"] = "Error loading ---clan.json. Cat not found:", cat
        game.switches["error_message"] = "Error loading ---clan.json. Check War related info"
        if "war" in clan_data:
            game.clan.war = clan_data["war"]

        game.switches["error_message"] = "Error loading ---clan.json. Faded cat error"
        if "faded_cats" in clan_data:
            if clan_data["faded_cats"].strip():  # Check for empty string
                for cat in clan_data["faded_cats"].split(","):
                    game.clan.faded_ids.append(cat)

        game.switches["error_message"] = "Error loading ---clan.json. Check Clan focus info"
        game.clan.last_focus_change = clan_data.get("last_focus_change")
        game.clan.clans_in_focus = clan_data.get("clans_in_focus", [])

        game.switches["error_message"] = "Error loading ---clan.json. Check Patrolled_Cats"
        # Patrolled cats
        if "patrolled_cats" in clan_data:
            game.patrolled = clan_data["patrolled_cats"]

        game.switches["error_message"] = "Error loading ---clan.json. Check Mediated"
        # Mediated flag
        if "mediated" in clan_data:
            if not isinstance(clan_data["mediated"], list):
                game.mediated = []
            else:
                game.mediated = clan_data["mediated"]
        game.clan.clan_age = clan_data["clan_age"] if "clan_age" in clan_data else "established"
        
        game.switches["error_message"] = "Error loading ---clan.json. Check Pregnancy.json"
        self.load_pregnancy(game.clan)
        game.switches["error_message"] = "Error loading ---clan.json. Check Herbs.json"
        self.load_herbs(game.clan)
        game.switches["error_message"] = "Error loading ---clan.json. Check Disasters jsons"
        self.load_disaster(game.clan)
        game.switches["error_message"] = "Error loading ---clan.json. Accessories???"
        self.load_accessories()
        game.switches["error_message"] = "Error loading ---clan.json. Check freshkill_pile.json"
        if game.clan.game_mode != "classic":
            self.load_freshkill_pile(game.clan)
        
        game.switches["error_message"] = "Error loading ---clan.json. Check player cat info"
        if "your_cat" in clan_data:
            game.clan.your_cat = Cat.all_cats[clan_data["your_cat"]]

        if "murdered" in clan_data:
            game.clan.murdered = clan_data["murdered"]

        if "affair" in clan_data:
            game.clan.murdered = clan_data["affair"]

        if "exile_return" in clan_data:
            game.clan.murdered = clan_data["exile_return"]
        
        game.switches["error_message"] = "Error loading ---clan.json. Check achievements"
        if "achievements" in clan_data:
            game.clan.achievements = clan_data["achievements"]
        
        game.switches["error_message"] = "Error loading ---clan.json. Check talks"
        if "talks" in clan_data:
            game.clan.talks = clan_data["talks"]

        game.switches["error_message"] = "Error loading ---clan.json. Check Disaster info"
        if "disaster" in clan_data:
            game.clan.disaster = clan_data["disaster"]
        
        if "disaster_moon" in clan_data:
            game.clan.disaster_moon = clan_data["disaster_moon"]

        game.switches["error_message"] = "Error loading ---clan.json. Check Focus info"
        if "focus" in clan_data:
            game.clan.focus = clan_data["focus"]

        if "focus_moons" in clan_data:
            game.clan.focus_moons = clan_data["focus_moons"]

        if "focus_cat" in clan_data:
            if clan_data["focus_cat"] is None:
                game.clan.focus_cat = None
            else:
                game.clan.focus_cat = Cat.all_cats[clan_data["focus_cat"]]

        game.switches["error_message"] = "Error loading ---clan.json. Check other clan meds(?)"
        if "other_med" in clan_data:
            other_med = []
            for c in clan_data["other_med"]:
                other_clan_meds = []
                for other_clan_med in c:
                    other_clan_med = other_clan_med.split(",")
                    n = Name(status = other_clan_med[2], prefix = other_clan_med[0], suffix = other_clan_med[1])
                    other_clan_meds.append(n)
                other_med.append(other_clan_meds)
            game.switches["other_med"] = other_med
        game.switches["error_message"] = ""

        # Return Version Info.
        return {
            "version_name": clan_data.get("version_name"),
            "version_commit": clan_data.get("version_commit"),
            "source_build": clan_data.get("source_build"),
        }
    
    def load_accessories(self):
        if game.clan.clan_settings['all accessories']:
            for c in Cat.all_cats_list:
                cat = c
                age = cat.age
                cat_sprite = str(cat.pelt.cat_sprites[cat.age])

                # setting the cat_sprite (bc this makes things much easier)
                if cat.not_working() and age != 'newborn' and game.config['cat_sprites']['sick_sprites']:
                    if age in ['kitten', 'adolescent']:
                        cat_sprite = str(19)
                    else:
                        cat_sprite = str(18)
                elif cat.pelt.paralyzed and age != 'newborn':
                    if age in ['kitten', 'adolescent']:
                        cat_sprite = str(17)
                    else:
                        if cat.pelt.length == 'long':
                            cat_sprite = str(16)
                        else:
                            cat_sprite = str(15)
                else:
                    if age == 'elder' and not game.config['fun']['all_cats_are_newborn']:
                        age = 'senior'

                    if game.config['fun']['all_cats_are_newborn']:
                        cat_sprite = str(cat.pelt.cat_sprites['newborn'])
                    else:
                        cat_sprite = str(cat.pelt.cat_sprites[age])

                possible_accs = ["WILD", "PLANT", "COLLAR", "FLOWER", "PLANT2", "SNAKE", "SMALLANIMAL", "DEADINSECT",
                                 "ALIVEINSECT", "FRUIT", "CRAFTED", "TAIL2", "NEONPINK"]
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
                if "NOTAIL" in c.pelt.scars or "HALFTAIL" in c.pelt.scars:
                    for acc in Pelt.tail_accessories + Pelt.tail2_accessories:
                        if acc in acc_list:
                            try:
                                acc_list.remove(acc)
                            except ValueError:
                                print(f'attempted to remove {acc} from possible acc list, but it was not in the list!')

                if not c.pelt.inventory:
                    c.pelt.inventory = []
                for acc in acc_list:
                    if acc not in c.pelt.inventory:
                        c.pelt.inventory.append(acc)

    def load_clan_settings(self):
        if os.path.exists(
            get_save_dir() + f'/{game.switches["clan_list"][0]}/clan_settings.json'
        ):
            with open(
                get_save_dir() + f'/{game.switches["clan_list"][0]}/clan_settings.json',
                "r",
                encoding="utf-8",
            ) as write_file:
                _load_settings = ujson.loads(write_file.read())

        for key, value in _load_settings.items():
            if key in self.clan_settings:
                self.clan_settings[key] = value

    def load_herbs(self, clan):
        """
        TODO: DOCS
        """
        if not game.clan.name:
            return
        file_path = get_save_dir() + f"/{game.clan.name}/herbs.json"
        if os.path.exists(file_path):
            with open(
                file_path, "r", encoding="utf-8"
            ) as read_file:  # pylint: disable=redefined-outer-name
                clan.herbs = ujson.loads(read_file.read())

        else:
            # generate a random set of herbs since the Clan didn't have any saved
            herbs = {}
            random_herbs = random.choices(HERBS, k=random.randrange(3, 8))
            for herb in random_herbs:
                herbs.update({herb: random.randint(1, 3)})
            with open(file_path, "w", encoding="utf-8") as rel_file:
                json_string = ujson.dumps(herbs, indent=4)
                rel_file.write(json_string)
            clan.herbs = herbs

    def save_herbs(self, clan):
        """
        TODO: DOCS
        """
        if not game.clan.name:
            return

        game.safe_save(f"{get_save_dir()}/{game.clan.name}/herbs.json", clan.herbs)

    def load_pregnancy(self, clan):
        """
        Load the information about what cat is pregnant and in what 'state' they are in the pregnancy.
        """
        if not game.clan.name:
            return
        file_path = get_save_dir() + f"/{game.clan.name}/pregnancy.json"
        if os.path.exists(file_path):
            with open(
                file_path, "r", encoding="utf-8"
            ) as read_file:  # pylint: disable=redefined-outer-name
                clan.pregnancy_data = ujson.load(read_file)
        else:
            clan.pregnancy_data = {}

    def save_pregnancy(self, clan):
        """
        Save the information about what cat is pregnant and in what 'state' they are in the pregnancy.
        """
        if not game.clan.name:
            return

        game.safe_save(
            f"{get_save_dir()}/{game.clan.name}/pregnancy.json", clan.pregnancy_data
        )

    def load_disaster(self, clan):
        """
        TODO: DOCS
        """
        if not game.clan.name:
            return

        file_path = get_save_dir() + f"/{game.clan.name}/disasters/primary.json"
        try:
            if os.path.exists(file_path):
                with open(
                    file_path, "r", encoding="utf-8"
                ) as read_file:  # pylint: disable=redefined-outer-name
                    disaster = ujson.load(read_file)
                    if disaster:
                        clan.primary_disaster = OngoingEvent(
                            event=disaster["event"],
                            tags=disaster["tags"],
                            duration=disaster["duration"],
                            current_duration=(
                                disaster["current_duration"]
                                if "current_duration"
                                else disaster["duration"]
                            ),  # pylint: disable=using-constant-test
                            trigger_events=disaster["trigger_events"],
                            progress_events=disaster["progress_events"],
                            conclusion_events=disaster["conclusion_events"],
                            secondary_disasters=disaster["secondary_disasters"],
                            collateral_damage=disaster["collateral_damage"],
                        )
                    else:
                        clan.primary_disaster = {}
            else:
                os.makedirs(get_save_dir() + f"/{game.clan.name}/disasters")
                clan.primary_disaster = None
                with open(file_path, "w", encoding="utf-8") as rel_file:
                    json_string = ujson.dumps(clan.primary_disaster, indent=4)
                    rel_file.write(json_string)
        except:
            clan.primary_disaster = None

        file_path = get_save_dir() + f"/{game.clan.name}/disasters/secondary.json"
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as read_file:
                    disaster = ujson.load(read_file)
                    if disaster:
                        clan.secondary_disaster = OngoingEvent(
                            event=disaster["event"],
                            tags=disaster["tags"],
                            duration=disaster["duration"],
                            current_duration=(
                                disaster["current_duration"]
                                if "current_duration"
                                else disaster["duration"]
                            ),  # pylint: disable=using-constant-test
                            progress_events=disaster["progress_events"],
                            conclusion_events=disaster["conclusion_events"],
                            collateral_damage=disaster["collateral_damage"],
                        )
                    else:
                        clan.secondary_disaster = {}
            else:
                os.makedirs(get_save_dir() + f"/{game.clan.name}/disasters")
                clan.secondary_disaster = None
                with open(file_path, "w", encoding="utf-8") as rel_file:
                    json_string = ujson.dumps(clan.secondary_disaster, indent=4)
                    rel_file.write(json_string)

        except:
            clan.secondary_disaster = None

    def save_disaster(self, clan=game.clan):
        """
        TODO: DOCS
        """
        if not clan.name:
            return
        file_path = get_save_dir() + f"/{clan.name}/disasters/primary.json"
        if not os.path.isdir(f"{get_save_dir()}/{clan.name}/disasters"):
            os.mkdir(f"{get_save_dir()}/{clan.name}/disasters")
        if clan.primary_disaster:
            disaster = {
                "event": clan.primary_disaster.event,
                "tags": clan.primary_disaster.tags,
                "duration": clan.primary_disaster.duration,
                "current_duration": clan.primary_disaster.current_duration,
                "trigger_events": clan.primary_disaster.trigger_events,
                "progress_events": clan.primary_disaster.progress_events,
                "conclusion_events": clan.primary_disaster.conclusion_events,
                "secondary_disasters": clan.primary_disaster.secondary_disasters,
                "collateral_damage": clan.primary_disaster.collateral_damage,
            }
        else:
            disaster = {}

        game.safe_save(f"{get_save_dir()}/{clan.name}/disasters/primary.json", disaster)

        if clan.secondary_disaster:
            disaster = {
                "event": clan.secondary_disaster.event,
                "tags": clan.secondary_disaster.tags,
                "duration": clan.secondary_disaster.duration,
                "current_duration": clan.secondary_disaster.current_duration,
                "trigger_events": clan.secondary_disaster.trigger_events,
                "progress_events": clan.secondary_disaster.progress_events,
                "conclusion_events": clan.secondary_disaster.conclusion_events,
                "secondary_disasters": clan.secondary_disaster.secondary_disasters,
                "collateral_damage": clan.secondary_disaster.collateral_damage,
            }
        else:
            disaster = {}

        game.safe_save(
            f"{get_save_dir()}/{clan.name}/disasters/secondary.json", disaster
        )

    def load_freshkill_pile(self, clan):
        """
        TODO: DOCS
        """
        if not game.clan.name or clan.game_mode == "classic":
            return

        file_path = get_save_dir() + f"/{game.clan.name}/freshkill_pile.json"
        try:
            if os.path.exists(file_path):
                with open(
                    file_path, "r", encoding="utf-8"
                ) as read_file:  # pylint: disable=redefined-outer-name
                    pile = ujson.load(read_file)
                    clan.freshkill_pile = FreshkillPile(pile)

                file_path = get_save_dir() + f"/{game.clan.name}/nutrition_info.json"
                if os.path.exists(file_path) and clan.freshkill_pile:
                    with open(file_path, "r", encoding="utf-8") as read_file:
                        nutritions = ujson.load(read_file)
                        for k, nutr in nutritions.items():
                            nutrition = Nutrition()
                            nutrition.max_score = nutr["max_score"]
                            nutrition.current_score = nutr["current_score"]
                            clan.freshkill_pile.nutrition_info[k] = nutrition
                        if len(nutritions) <= 0:
                            for cat in Cat.all_cats_list:
                                clan.freshkill_pile.add_cat_to_nutrition(cat)
            else:
                clan.freshkill_pile = FreshkillPile()
        except:
            clan.freshkill_pile = FreshkillPile()

    def save_freshkill_pile(self, clan):
        """
        TODO: DOCS
        """
        if clan.game_mode == "classic" or not clan.freshkill_pile:
            return

        game.safe_save(
            f"{get_save_dir()}/{game.clan.name}/freshkill_pile.json",
            clan.freshkill_pile.pile,
        )

        data = {}
        for k, nutr in clan.freshkill_pile.nutrition_info.items():
            data[k] = {
                "max_score": nutr.max_score,
                "current_score": nutr.current_score,
                "percentage": nutr.percentage
            }

        game.safe_save(f"{get_save_dir()}/{game.clan.name}/nutrition_info.json", data)

    ## Properties

    @property
    def reputation(self):
        return self._reputation

    @reputation.setter
    def reputation(self, a: int):
        self._reputation = int(a)
        if self._reputation > 100:
            self._reputation = 100
        elif self._reputation < 0:
            self._reputation = 0

    @property
    def temperament(self):
        """Temperament is determined whenever it's accessed. This makes sure it's always accurate to the
        current cats in the Clan. However, determining Clan temperament is slow!
        Clan temperament should be used as sparsely as possible, since
        it's pretty resource-intensive to determine it."""

        all_cats = [
            i
            for i in Cat.all_cats_list
            if i.status not in ["leader", "deputy"] and not i.dead and not i.outside
        ]
        leader = (
            Cat.fetch_cat(self.leader)
            if isinstance(Cat.fetch_cat(self.leader), Cat)
            else None
        )
        deputy = (
            Cat.fetch_cat(self.deputy)
            if isinstance(Cat.fetch_cat(self.deputy), Cat)
            else None
        )

        weight = 0.3

        if (leader or deputy) and all_cats:
            clan_sociability = round(
                weight
                * statistics.mean(
                    [i.personality.sociability for i in [leader, deputy] if i]
                )
                + (1 - weight)
                * statistics.median([i.personality.sociability for i in all_cats])
            )
            clan_aggression = round(
                weight
                * statistics.mean(
                    [i.personality.aggression for i in [leader, deputy] if i]
                )
                + (1 - weight)
                * statistics.median([i.personality.aggression for i in all_cats])
            )
        elif leader or deputy:
            clan_sociability = round(
                statistics.mean(
                    [i.personality.sociability for i in [leader, deputy] if i]
                )
            )
            clan_aggression = round(
                statistics.mean(
                    [i.personality.aggression for i in [leader, deputy] if i]
                )
            )
        elif all_cats:
            clan_sociability = round(
                statistics.median([i.personality.sociability for i in all_cats])
            )
            clan_aggression = round(
                statistics.median([i.personality.aggression for i in all_cats])
            )
        else:
            print("returned default temper: stoic")
            return "stoic"

        # _temperament = ['low_aggression', 'med_aggression', 'high_aggression', ]
        if 11 <= clan_sociability:
            _temperament = self.temperament_dict["high_social"]
        elif 7 <= clan_sociability:
            _temperament = self.temperament_dict["mid_social"]
        else:
            _temperament = self.temperament_dict["low_social"]

        if 11 <= clan_aggression:
            _temperament = _temperament[2]
        elif 7 <= clan_aggression:
            _temperament = _temperament[1]
        else:
            _temperament = _temperament[0]

        return _temperament

    @temperament.setter
    def temperament(self, val):
        return


class OtherClan:
    """
    TODO: DOCS
    """

    interaction_dict = {
        "ally": ["offend", "praise"],
        "neutral": ["provoke", "befriend"],
        "hostile": ["antagonize", "appease", "declare"],
    }

    temperament_list = [
        "cunning",
        "wary",
        "logical",
        "proud",
        "stoic",
        "mellow",
        "bloodthirsty",
        "amiable",
        "gracious",
    ]

    def __init__(self, name="", relations=0, temperament="", chosen_symbol=""):
        clan_names = names.names_dict["normal_prefixes"]
        clan_names.extend(names.names_dict["clan_prefixes"])
        self.name = name or choice(clan_names)
        self.relations = relations or randint(8, 12)
        self.temperament = temperament or choice(self.temperament_list)
        if self.temperament not in self.temperament_list:
            self.temperament = choice(self.temperament_list)

        self.chosen_symbol = (
            None  # have to establish None first so that clan_symbol_sprite works
        )
        self.chosen_symbol = (
            chosen_symbol
            if chosen_symbol
            else clan_symbol_sprite(self, return_string=True)
        )

    def __repr__(self):
        return f"{self.name}Clan"


class StarClan:
    """
    TODO: DOCS
    """

    forgotten_stages = {
        0: [0, 100],
        10: [101, 200],
        30: [201, 300],
        60: [301, 400],
        90: [401, 500],
        100: [501, 502],
    }  # Tells how faded the cat will be in StarClan by months spent
    dead_cats = {}

    def __init__(self):
        """
        TODO: DOCS
        """
        self.instructor = None
        self.demon = None

    def fade(self, cat):
        """
        TODO: DOCS
        """
        white = pygame.Surface((sprites.size, sprites.size))
        fade_level = 0
        if cat.dead:
            for f in self.forgotten_stages:  # pylint: disable=consider-using-dict-items
                if cat.dead_for in range(
                    self.forgotten_stages[f][0], self.forgotten_stages[f][1]
                ):
                    fade_level = f
        white.fill((255, 255, 255, fade_level))
        return white


clan_class = Clan()
clan_class.remove_cat(cat_class.ID)

HERBS = None
with open("resources/dicts/herbs.json", "r", encoding="utf-8") as read_file:
    HERBS = ujson.loads(read_file.read())

def neonpinkEasteregg(self):
    self.instructor = Cat(
        prefix="Arson",suffix="above",moons=23,status="warrior",
        gender="intersex",gender_align="intersex"
            )
    self.instructor.get_permanent_condition("born without a tail", born_with=True, event_triggered=True)
    self.instructor.permanent_condition['born without a tail']["moons_until"] = -1
    self.instructor.permanent_condition['born without a tail']["moons_with"] = -1
    self.instructor.get_permanent_condition("born without an eye", born_with=True, event_triggered=True)
    self.instructor.permanent_condition['born without an eye']["moons_until"] = -1
    self.instructor.permanent_condition['born without an eye']["moons_with"] = -1

    self.instructor.pelt = Pelt(
        name="Tortie",colour="SILVER",tortiepattern="sokoke",tortiebase="sokoke",
        pattern="SHADEDPATTERN",tortiecolour="PEACH",
        length="long",eye_color="BALLSGREEN",eye_colour2="CLOSED",
        scars=["NOTAIL"], accessories=["BULB ORANGE"])
    self.instructor.dead = True
    self.instructor.dead_for = 0
    self.instructor.backstory = "dead9"
    self.instructor.personality.trait = "meek"
    self.instructor.skills = CatSkills(primary_path=SkillPath.LANGUAGE)
    self.add_cat(self.instructor)
    self.add_to_starclan(self.instructor)
    self.all_clans = []
    
    self.demon = Cat(
        prefix="Sun",suffix="bellow",moons=23,status="medicine cat",gender_align="nonbinary"
                        )
    self.demon.pelt=Pelt(name="Goldshaded",length="short",eye_color="STARCLANWARM",eye_colour2="STARCLANWARM",
                    colour="VOID",tint="purple")
    self.demon.df = True
    self.demon.dead = True
    self.demon.dead_for = 0
    self.demon.backstory = "oldstarclan2"
    self.demon.skills= CatSkills(primary_path=SkillPath.NPMORBID)
    self.add_cat(self.demon)
    self.add_to_darkforest(self.demon)
    self.all_clans = []

    print("Hello, world!")