from copy import copy
import random
from random import randint, choice


import os.path

import pygame
import ujson
import pygame_gui
from pygame import Rect
from pygame_gui.elements import UIDropDownMenu, UITextBox

from scripts.cat.cats import Cat
from scripts.cat.pelts import Pelt
from scripts.cat.sprites import sprites
from scripts.cat.personality import Personality
from scripts.cat.skills import SkillPath, Skill
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import UISurfaceImageButton, UIImageButton
from scripts.screens.Screens import Screens
from scripts.ui.generate_box import get_box, BoxStyles
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.get_arrow import get_arrow
from scripts.utility import ui_scale, generate_sprite, ui_scale_dimensions, get_text_box_theme

""" Cat customization UI """

# generate UI elements
def create_text_box(text, pos, size, theme, anchors=None):
    return UITextBox(
        text,
        ui_scale(Rect(pos, size)),
        manager=MANAGER,
        object_id=get_text_box_theme(theme),
        anchors=anchors
    )


def create_button(pos, size, text, style, anchors=None, sound_id=None):
    return UISurfaceImageButton(
        ui_scale(Rect(pos, size)),
        text,
        get_button_dict(style, size),
        object_id=f"@buttonstyles_{style.name.lower()}",
        manager=MANAGER,
        anchors=anchors,
        sound_id=sound_id
    )


def create_dropdown(pos, size, options, selected_option, style=None):
    return UIDropDownMenu(
        options,
        selected_option,
        ui_scale(Rect(pos, size)),
        object_id=f"#{style}",
        manager=MANAGER
    )

# creates a list with display names and values of cat pelt attributes
def create_options_list(attribute, case):
    if case == "upper":
        return [(option.capitalize(), option.upper()) for option in attribute]
    elif case == "lower":
        return [(option.capitalize(), option.lower()) for option in attribute]
    else:
        return [(option.capitalize(), option) for option in attribute]

# returns the name and value; returns none if dropdown is disabled
def get_selected_option(attribute, case):
    if isinstance(attribute, list):
        if len(attribute) > 0:  # selects an option in scar dropdowns for any existing scars
            return attribute[0].capitalize(), attribute[0].upper()
        else:
            return "None", "NONE"
    if attribute:
        if case == "upper":
            return attribute.capitalize(), attribute.upper()
        elif case == "lower":
            return attribute.capitalize(), attribute.lower()
        else:
            return attribute.capitalize(), attribute
    else:
        if case == "upper":
            return "None", "NONE"
        elif case == "lower":
            return "None", "none"
        else:
            return "None", "None"

# screen rendering
class CustomizeStatsScreen(Screens):
    def __init__(self, name=None):
        super().__init__(name)
        self.the_cat = None
        self.next_cat = None
        self.previous_cat = None
        self.life_stage = None
        self.initial_state = None
        self.cat_elements = {}

        # UI elements
        self.frame_image = None
        self.cat_image = None
        self.previous_cat_button = None
        self.back_button = None
        self.next_cat_button = None

        scarless_conditions = [
            "weak leg",
            "paralyzed",
            "raspy lungs",
            "wasting disease",
            "blind",
            "failing eyesight",
            "one bad eye",
            "partial hearing loss",
            "deaf",
            "constant joint pain",
            "constantly dizzy",
            "recurring shock",
            "lasting grief",
            "wobbly cat syndrome", "cleft palate",
            "persistent headaches", "intersex"]
        self.permanent_conditions = copy(scarless_conditions) + ["one bad eye", "lost a leg", "lost their tail", "twisted leg", "declawed", "constant rash"]
        self.permanent_conditions.sort()
        self.permanent_conditions.insert(0, "none")
        self.permanent_conditions_label = None
        
        self.skills = ["TEACHER", "FIGHTER","CLIMBER", "SPEAKER","CLEVER", "SENSE","STORY", "CAMP", "STAR", "OMEN", "CLAIRVOYANT", "GHOST", "UNKNOWN",
                       "DELIVERER", "LEADERSHIP", "STEALTHY", "MESSENGER", "HISTORIAN", "PATIENT", "HERBALIST", "PRODIGY", "TRACKER", "GUARDIAN", "NAVIGATOR",
                       "GRACE", "INNOVATOR", "MATCHMAKER", "COOPERATIVE", "TIME", "FISHER", "SLEEPER", "PYRO", "WEATHER", "VIBES", "IMMUNE", "MUSICVIBES",
                       "ANIMALTAKER", "ANIMALMAGNET", "VET", "AURAVIBES", "HIDER", "STARGAZER", "GIFTGIVER", "HYDRO", "DISGUISE", "LANGUAGE", "TREASURE",
                       "SCHOLAR", "THINKER", "COMFORTER", "CLEAN", "SONG", "TUNNELER", "ARTISAN", "EXPLORER", "CHEF", "DETECTIVE", "BOOKMAKER", "ASSIST",
                       "MEMORY", "AGILE", "DECORATOR", "WAKEFUL", "GARDENER", "PROPHET", "DREAM", "DARK", "HEALER", "LORE", "KIT", "INSIGHTFUL", "MEDIATOR",
                       "SWIMMER", "RUNNER", "HUNTER"]
        self.skill_strings_dict = {
                "TEACHER": SkillPath.TEACHER,
                "FIGHTER": SkillPath.FIGHTER,
                "CLIMBER": SkillPath.CLIMBER,
                "SPEAKER": SkillPath.SPEAKER,
                "CLEVER": SkillPath.CLEVER,
                "SENSE": SkillPath.SENSE,
                "STORY": SkillPath.STORY,
                "CAMP": SkillPath.CAMP,
                "STAR": SkillPath.STAR,
                "OMEN": SkillPath.OMEN,
                "CLAIRVOYANT": SkillPath.CLAIRVOYANT,
                "GHOST": SkillPath.GHOST,
                "UNKNOWN": SkillPath.UNKNOWN,
                "DELIVERER": SkillPath.DELIVERER,
                "LEADERSHIP": SkillPath.LEADERSHIP,
                "MESSENGER": SkillPath.MESSENGER,
                "HISTORIAN": SkillPath.HISTORIAN,
                "PATIENT": SkillPath.PATIENT,
                "HERBALIST": SkillPath.HERBALIST,
                "PRODIGY": SkillPath.PRODIGY,
                "TRACKER": SkillPath.TRACKER,
                "GUARDIAN": SkillPath.GUARDIAN,
                "NAVIGATOR": SkillPath.NAVIGATOR,
                "GRACE": SkillPath.GRACE,
                "INNOVATOR": SkillPath.INNOVATOR,
                "MATCHMAKER": SkillPath.MATCHMAKER,
                "COOPERATIVE": SkillPath.COOPERATIVE,
                "TIME": SkillPath.TIME,
                "FISHER": SkillPath.FISHER,
                "SLEEPER": SkillPath.SLEEPER,
                "PYRO": SkillPath.PYRO,
                "WEATHER": SkillPath.WEATHER,
                "VIBES": SkillPath.VIBES,
                "IMMUNE": SkillPath.IMMUNE,
                "MUSICVIBES": SkillPath.MUSICVIBES,
                "ANIMALTAKER": SkillPath.ANIMALTAKER,
                "ANIMALMAGNET": SkillPath.ANIMALMAGNET,
                "VET": SkillPath.VET,
                "AURAVIBES": SkillPath.AURAVIBES,
                "HIDER": SkillPath.HIDER,
                "STARGAZER": SkillPath.STARGAZER,
                "GIFTGIVER": SkillPath.GIFTGIVER,
                "HYDRO": SkillPath.HYDRO,
                "DISGUISE": SkillPath.DISGUISE,
                "LANGUAGE": SkillPath.LANGUAGE,
                "TREASURE": SkillPath.TREASURE,
                "SCHOLAR": SkillPath.SCHOLAR,
                "THINKER": SkillPath.THINKER,
                "COMFORTER": SkillPath.COMFORTER,
                "CLEAN": SkillPath.CLEAN,
                "SONG": SkillPath.SONG,
                "DIGGER": SkillPath. DIGGER,
                "ARTISAN": SkillPath.ARTISAN,
                "EXPLORER": SkillPath.EXPLORER,
                "STEALTH": SkillPath.STEALTH,
                "CHEF": SkillPath.CHEF,
                "AGILED": SkillPath.AGILED,
                "DETECTIVE": SkillPath.DETECTIVE,
                "BOOKMAKER": SkillPath.BOOKMAKER,
                "ASSIST": SkillPath.ASSIST,
                "MEMORY": SkillPath.MEMORY,
                "DECORATOR": SkillPath.DECORATOR,
                "WAKEFUL": SkillPath.WAKEFUL,
                "GARDENER": SkillPath.GARDENER,
                "PROPHET": SkillPath.PROPHET,
                "DREAM": SkillPath.DREAM,
                "DARK": SkillPath.DARK,
                "HEALER": SkillPath.HEALER,
                "LORE": SkillPath.LORE,
                "KIT": SkillPath.KIT,
                "INSIGHTFUL": SkillPath.INSIGHTFUL,
                "MEDIATOR": SkillPath.MEDIATOR,
                "SWIMMER": SkillPath.SWIMMER,
                "RUNNER": SkillPath.RUNNER,
                "HUNTER": SkillPath.HUNTER
            }
        self.skills.sort()
        self.skills.insert(0, "None")
        self.skills_label1 = None
        self.skills_label2 = None
        self.skills_label3 = None
        
        self.adult_traits = ["troublesome", "lonesome", "fierce", "bloodthirsty", "cold", "childish", "playful", "charismatic", "bold", "daring", "nervous", "righteous",
                       "insecure", "strict", "compassionate", "thoughtful", "ambitious", "confident", "adventurous", "calm", "careful", "faithful", "loving", "loyal",
                       "responsible", "shameless", "sneaky", "strange", "vengeful", "wise", "arrogant", "competitive", "grumpy", "cunning", "oblivious", "gloomy",
                       "sincere", "flamboyant", "alert", "angry", "appreciative", "bubbly", "absent-minded", "carefree", "cryptic", "dedicated", "distracted", "dramatic",
                       "dynamic", "easy-going", "elegant", "escapist", "fair", "forceful", "forgiving", "casual", "dry", "chummy", "complex", "emotional", "folksy",
                       "hypnotic", "intense", "nurturing", "old-fashioned", "neutral", "moralistic", "soft", "unaggressive", "gentle", "unreligious", "reserved", "generous",
                       "gracious", "hearty", "heroic", "idealistic", "innocent", "logical", "benevolent", "farsighted", "fun-loving", "open", "optimistic", "gallant",
                       "free-thinking", "passive-aggressive", "pessimistic", "passionate", "hardworking", "genuine", "peaceful", "polished", "protective", "relaxed",
                       "sarcastic", "high-minded", "incisive", "sassy", "sensitive", "serious", "incorruptible", "leaderly", "stoic", "tidy", "warm", "organized", "patient",
                       "persuasive", "principled", "practical", "goofy", "romantic", "scholarly", "destructive", "grim", "forgetful", "greedy", "judgemental", "thoughtless",
                       "nerdy", "philosophical", "overthinker", "cheeky", "snobbish", "reliable", "punctual", "supportive", "spiteful", "remorseless", "weak-willed",
                       "hyper", "superficial", "fearful", "clumsy", "unpredictable", "cool", "cooperative", "energetic", "talkative", "amoral", "tranquil", "antagonistic",
                       "wrongful", "fatalistic", "rebellious", "silly", "confused", "sleepy", "chaotic", "scary", "cheerful", "coward", "manipulative", "delicate",
                       "hypocrite", "flirty", "honest", "mysterious", "polite", "enthusiastic", "vulnerable", "creative", "perfectionist", "sappy", "sentient", "annoying",
                       "lazy", "faithless", "moody", "aloof", "whimsical", "fancy", "methodical", "malicious", "frustrated", "self-reliant", "sentimental", "spontainious",
                       "stable", "strong", "fox-hearted", "sympathetic", "macabre", "civil", "teacherly", "tolerant", "unfoolable", "witty", "youthful", "enigmatic",
                       "ordinary", "private", "loud", "questioning", "predictable", "airy", "anxious", "argumentative", "bizarre", "blunt", "calculating", "crude", "deceitful",
                       "cruel", "devious", "messy", "opinionated", "overimaginative", "power-hungry", "quirky", "reactive", "resentful", "regretful", "ritualistic", "selfish",
                       "sadistic", "scheming", "sloppy", "suspicious", "thievish", "transparent", "vague", "venomous", "envious",
                       "artificial", "aimless", "boring", "charmless",
                       "unreliable", "dependant", "disgusted", "self-pitying", "colorless", "obnoxious", "small-thinking", "uncaring", "unimaginative", "desolate", "monotone",
                       "dull", "misguided", "humorous"]
        self.adult_traits.sort()
        self.kit_traits = ["troublesome", "lonesome", "impulsive", "bullying", "attention-seeker", "daydreamer", "dreary", "abrupt", "solemn", "wishful", "indecisive",
                           "entitled", "distrusting", "charming", "nervous", "quiet", "insecure", "sweet", "goody-no-claws", "chaotic", "nosy", "moody", "nasty", "silly",
                           "know-it-all", "spoiled", "sly", "mature", "apologetic", "salty", "whiny", "spicy", "bubbly", "picky", "cheeky", "shy", "fearless", "skittish",
                           "self-conscious", "impressionable", "high-spirited", "crybaby", "tiny", "morbid", "obedient", "colorful", "zoomy", "clingy", "curious", "slug",
                           "defiant", "sinister", "prim", "tender", "jokester", "wild", "bright", "earnest", "rowdy", "sloppy", "complex", "emotional", "protective", "bossy",
                           "CHAOS CHAOS"]
        self.kit_traits.sort()
        self.traits = copy(self.adult_traits)
        self.traits_label1 = None
        self.traits_label2 = None
        
        self.backstories = ["clan_founder", "clanborn", "halfclan1", "halfclan2", "outsider_roots1", "outsider_roots2", "loner1", "loner2", "loner3", "loner4", "kittypet1",
                            "kittypet2", "kittypet3", "kittypet4", "rogue1", "rogue2", "rogue3", "abandoned1", "abandoned2", "abandoned3", "abandoned4", "abandoned5", "otherclan1",
                            "otherclan2", "otherclan3", "otherclan4", "otherclan5", "disgraced1", "disgraced2", "disgraced3", "retired_leader", "medicine_cat", "ostracized_warrior",
                            "refugee1", "refugee2", "refugee3", "refugee4", "refugee5", "refugee6", "tragedy_survivor1", "tragedy_survivor2", "tragedy_survivor3", "tragedy_survivor4",
                            "wandering_healer1", "wandering_healer2", "guided1", "guided2", "guided3", "guided4", "orphaned1", "orphaned2", "orphaned3", "orphaned4", "orphaned5",
                            "orphaned6", "outsider1", "outsider2", "outsider3", "unknown"]
        self.backstories.sort()
        self.backstory_label = None
        
        self.fur_textures = ["soft", "curly", "rough", "silky", "sleek", "wavy", "sparse", "tangled", "fuzzy", "spiky"]
        self.fur_textures.sort()
        self.fur_textures_label = None
        
        self.builds = ["stocky", "slender", "lithe", "wiry", "muscular", "lanky", "delicate", "hunched", "hefty", "burly", "bulky", "plump", "brawny", "stout", "broad", "chubby", "fat", "stocky", "chunky", "big-boned"]
        self.builds.sort()
        self.builds_label = None
        
        self.heights = ["petite", "short", "average", "tall", "towering"]
        self.heights.sort()
        self.heights_label = None
        
        self.genders = ["male", "female", "intersex"]
        self.genders_label = None

    def screen_switches(self):
        super().screen_switches()
        self.setup_labels()
        self.frame_image = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((25, 120), (270, 270))), get_box(BoxStyles.FRAME, (250, 250)), starting_height=1
        )
        self.build_cat_page()

    def build_cat_page(self):
        self.the_cat = Cat.fetch_cat(game.switches["cat"])
        (self.next_cat, self.previous_cat) = self.the_cat.determine_next_and_previous_cats()
        self.cat_elements["cat_name"] = create_text_box("customize " + str(self.the_cat.name), (0, 40), (400, 40),
                                                        "#text_box_34_horizcenter", {"centerx": "centerx"})
        self.setup_buttons()
        self.setup_next_and_previous_cat()
        self.setup_dropdowns()
        self.setup_cat()
        self.capture_initial_state()

    def setup_labels(self):
        """------------------------------------------------------------------------------------------------------------#
        #                                              LABEL SETUP START                                               #
        # ------------------------------------------------------------------------------------------------------------"""
        self.permanent_condition_label = create_text_box("permanent conditions", (320, 100), (135, 40), "#text_box_22_horizleft")
        self.trait1_label = create_text_box("trait 1", (480, 100), (135, 40), "#text_box_22_horizleft")
        #self.pelt_length_label = create_text_box("trait 2", (224, 500), (135, 40), "#text_box_22_horizleft")
        #self.trait2_label = create_text_box("trait 2", (640, 100), (135, 40), "#text_box_22_horizleft")
        self.skill1_label = create_text_box("skill 1", (320, 175), (135, 40), "#text_box_22_horizleft")
        self.skill2_label = create_text_box("skill 2", (480, 175), (135, 40), "#text_box_22_horizleft")
        #self.skill3_label = create_text_box("skill 3", (640, 175), (135, 40), "#text_box_22_horizleft")
        
        self.fur_texture_label = create_text_box("fur texture", (320, 260), (135, 40), "#text_box_22_horizleft")
        self.build_label = create_text_box("build", (480, 260), (135, 40), "#text_box_22_horizleft")
        self.height_label = create_text_box("height", (640, 260), (135, 40), "#text_box_22_horizleft")
        
        self.backstory_label = create_text_box("backstory", (320, 335), (135, 40),
                                                        "#text_box_22_horizleft")
        self.gender_label = create_text_box("biological sex", (480, 335), (135, 40), "#text_box_22_horizleft")
        
        #self.skin_label = create_text_box("skin", (640, 335), (135, 40), "#text_box_22_horizleft")
        self.reset_message = create_text_box("Changes cannot be reset after leaving this cat's customization page.",
                                             (25, 395), (270, 60), "#text_box_26_horizcenter")
        
        self.heal_message = create_text_box("Clears all injuries and illnesses. This cannot be undone.",
                                             (325, 395), (270, 60), "#text_box_26_horizcenter")
        
        self.reset_facets_message = create_text_box("Changing facets will redo the cat's facets to match the FIRST (primary) trait. This will likely change the cat's secondary trait.",
                                             (25, 495), (270, 90), "#text_box_26_horizcenter")
        #self.eye_colour1_label = create_text_box("eye colour 1", (320, 420), (135, 40), "#text_box_22_horizleft")
        #self.heterochromia_text = create_text_box("heterochromia", (495, 451), (135, 40), "#text_box_26_horizcenter")
        #self.eye_colour2_label = create_text_box("eye colour 2", (640, 420), (135, 40), "#text_box_22_horizleft")
        #self.accessory_label = create_text_box("accessory", (568, 500), (135, 40), "#text_box_22_horizleft")
        #self.pose_label = create_text_box("pose", (406, 500), (110, 40), "#text_box_22_horizleft")
        #self.reverse_label = create_text_box("reverse", (52, 500), (135, 40), "#text_box_22_horizleft")
        #self.scar_message = create_text_box("Adding/removing scars will not affect a cat's conditions or history.",
                                            #(52, 650), (500, 40), "#text_box_26_horizleft")
        #self.scar1_label = create_text_box("scar 1", (46, 580), (135, 40), "#text_box_22_horizleft")
        #self.scar2_label = create_text_box("scar 2", (196, 580), (135, 40), "#text_box_22_horizleft")
        #self.scar3_label = create_text_box("scar 3", (346, 580), (135, 40), "#text_box_22_horizleft")
        #self.scar4_label = create_text_box("scar 4", (496, 580), (135, 40), "#text_box_22_horizleft")
        
        #self.powers_label = create_text_box("powers", (646, 580), (135, 40), "#text_box_22_horizleft")
        """------------------------------------------------------------------------------------------------------------#
        #                                              LABEL SETUP END                                                 #
        # ------------------------------------------------------------------------------------------------------------"""

    def setup_buttons(self):
        self.previous_cat_button = create_button((25, 25), (153, 30), get_arrow(2, arrow_left=True) + " Previous Cat",
                                                 ButtonStyles.SQUOVAL, sound_id="page_flip")
        self.back_button = create_button((25, 60), (105, 30), get_arrow(2) + " Back", ButtonStyles.SQUOVAL)
        self.next_cat_button = create_button((622, 25), (153, 30), "Next Cat " + get_arrow(3, arrow_left=False),
                                             ButtonStyles.SQUOVAL, sound_id="page_flip")
        #self.pelt_length_left_button = create_button((224, 530), (30, 30), get_arrow(1), ButtonStyles.ROUNDED_RECT)
        #self.pelt_length_right_button = create_button((324, 530), (30, 30), get_arrow(1, False),
                                                      #ButtonStyles.ROUNDED_RECT)
        #self.pose_left_button = create_button((406, 530), (30, 30), get_arrow(1), ButtonStyles.ROUNDED_RECT)
        #self.pose_right_button = create_button((486, 530), (30, 30), get_arrow(1, False), ButtonStyles.ROUNDED_RECT)
        #self.reverse_button = create_button((105, 530), (70, 30), "Reverse", ButtonStyles.ROUNDED_RECT)
        self.reset_button = create_button((110, 450), (105, 30), "Reset", ButtonStyles.SQUOVAL)
        self.heal_button = create_button((410, 450), (105, 30), "Heal", ButtonStyles.SQUOVAL)
        self.reset_facets_button = create_button((110, 575), (105, 30), "Reset Facets", ButtonStyles.SQUOVAL)

    def setup_dropdowns(self):
        """------------------------------------------------------------------------------------------------------------#
        #                                              DROPDOWN SETUP START                                            #
        # ------------------------------------------------------------------------------------------------------------"""
        disabilities_list = []
        for con in self.permanent_conditions:
            if con in self.the_cat.permanent_condition:
                disabilities_list.append(con)
        
        disability = "none"
        if len(disabilities_list) > 1:
            disability = choice(disabilities_list)
        elif len(disabilities_list) == 1:
            disability = disabilities_list[0]
        
        self.permanent_condition_dropdown = create_dropdown((320, 125), (135, 40),
                                                  create_options_list(self.permanent_conditions, "capitalize"),
                                                  get_selected_option(disability, "capitalize"))
        if self.the_cat.status in ["newborn", "kitten"]:
            self.traits = copy(self.kit_traits)
        else:
            self.traits = copy(self.adult_traits)
        self.trait1_dropdown = create_dropdown((480, 125), (135, 40),
                                                    create_options_list(self.traits, "upper"),
                                                    get_selected_option(self.the_cat.personality.trait, "upper"))
        #self.trait2_dropdown = create_dropdown((640, 125), (135, 40), create_options_list(self.traits, "upper"),
                                                #get_selected_option(self.the_cat.personality.trait2, "upper"))
        
        
        self.skill1_dropdown = create_dropdown((320, 200), (135, 40),
                                                    create_options_list(self.skills, "lower"),
                                                    get_selected_option(self.the_cat.skills.primary.path.name, "lower"))
        secondary_skill = "none"
        if self.the_cat.skills.secondary:
            secondary_skill = self.the_cat.skills.secondary.path.name
        self.skill2_dropdown = create_dropdown((480, 200), (135, 40),
                                                      create_options_list(self.skills, "upper"),
                                                      get_selected_option(secondary_skill, "upper"))
        #tertiary_skill = "none"
        #if self.the_cat.skills.tertiary:
            #tertiary_skill = self.the_cat.skills.tertiary.path.name
        #self.skill3_dropdown = create_dropdown((640, 200), (135, 40),
                                                       #create_options_list(self.skills, "lower"),
                                                       #get_selected_option(tertiary_skill, "lower"))
        
        self.fur_texture_dropdown = create_dropdown((320, 285), (135, 40),
                                                      create_options_list(self.fur_textures, "upper"),
                                                      get_selected_option(self.the_cat.pelt.fur_texture, "upper"))
        self.build_dropdown = create_dropdown((480, 285), (135, 40),
                                                 create_options_list(self.builds, "upper"),
                                                 get_selected_option(self.the_cat.pelt.build, "upper"))
        self.height_dropdown = create_dropdown((640, 285), (135, 40),
                                               create_options_list(self.heights, "upper"),
                                               get_selected_option(self.the_cat.pelt.height, "upper"))
        
        self.backstory_dropdown = create_dropdown((320, 360), (135, 40),
                                                           create_options_list(self.backstories, "lower"),
                                                           get_selected_option(self.the_cat.backstory,
                                                                               "lower"))
        self.gender_dropdown = create_dropdown((480, 360), (135, 40), create_options_list(self.genders, "lower"),
                                             get_selected_option(self.the_cat.gender, "lower"))
        
        '''
        self.skin_dropdown = create_dropdown((640, 360), (135, 40), create_options_list(self.skins, "upper"),
                                             get_selected_option(self.the_cat.pelt.skin, "upper"))
        self.eye_colour1_dropdown = create_dropdown((320, 445), (135, 40),
                                                    create_options_list(self.eye_colours, "upper"),
                                                    get_selected_option(self.the_cat.pelt.eye_colour, "upper"))
        self.eye_colour2_dropdown = create_dropdown((640, 445), (135, 40),
                                                    create_options_list(self.eye_colours, "upper"), (
                                                        get_selected_option(self.the_cat.pelt.eye_colour2,
                                                                            "upper") if self.the_cat.pelt.eye_colour2 else get_selected_option(
                                                            self.the_cat.pelt.eye_colour, "upper")))
        self.accessory_dropdown = create_dropdown((568, 525), (180, 40), create_options_list(self.accessories, "upper"),
                                                  get_selected_option(self.the_cat.pelt.accessory, "upper"), "dropup")

        scars = self.the_cat.pelt.scars
        self.scar1_dropdown = create_dropdown((42, 605), (135, 40), create_options_list(self.scars, "upper"),
                                              get_selected_option(scars, "upper"), "dropup")
        self.scar2_dropdown = create_dropdown((192, 605), (135, 40), create_options_list(self.scars, "upper"),
                                              get_selected_option(scars[1:], "upper"), "dropup")
        self.scar3_dropdown = create_dropdown((342, 605), (135, 40), create_options_list(self.scars, "upper"),
                                              get_selected_option(scars[2:], "upper"), "dropup")
        self.scar4_dropdown = create_dropdown((492, 605), (135, 40), create_options_list(self.scars, "upper"),
                                              get_selected_option(scars[3:], "upper"), "dropup")
        
        powers = "none"
        if self.the_cat.awakened:
            powers = self.the_cat.awakened["type"]
        self.powers_dropdown = create_dropdown((642, 605), (135, 40), create_options_list(self.powers, "upper"),
                                              get_selected_option(powers, "upper"), "dropup")
        '''
        """------------------------------------------------------------------------------------------------------------#
        #                                              DROPDOWN SETUP END                                              #
        # ------------------------------------------------------------------------------------------------------------"""

        # stores current scar state
        #self.initial_scar_selection[self.scar1_dropdown] = self.scar1_dropdown.selected_option[1]
        #self.initial_scar_selection[self.scar2_dropdown] = self.scar2_dropdown.selected_option[1]
        #self.initial_scar_selection[self.scar3_dropdown] = self.scar3_dropdown.selected_option[1]
        #self.initial_scar_selection[self.scar4_dropdown] = self.scar4_dropdown.selected_option[1]

    def setup_cat(self):
        self.get_cat_age()
        self.make_cat_sprite()
        self.setup_cat_elements()

    def setup_next_and_previous_cat(self):
        if self.next_cat == 0:
            self.next_cat_button.disable()
        else:
            self.next_cat_button.enable()

        if self.previous_cat == 0:
            self.previous_cat_button.disable()
        else:
            self.previous_cat_button.enable()

    def setup_cat_elements(self):
        self.capture_initial_state()

    # store state for reset
    # TODO: append values to a list with identifier to retain values between cat pages
    def capture_initial_state(self):
        self.initial_state = {
            "permanent_condition": self.the_cat.permanent_condition,
            "trait": self.the_cat.personality.trait,
            #"trait2": self.the_cat.personality.trait2,
            "skill1": self.the_cat.skills.primary.path.name,
            "skill2": self.the_cat.skills.secondary.path.name if self.the_cat.skills.secondary else "NONE",
            #"skill3": self.the_cat.skills.tertiary.path.name if self.the_cat.skills.tertiary else "NONE",
            "fur_texture": self.the_cat.pelt.fur_texture,
            "build": self.the_cat.pelt.build,
            "height": self.the_cat.pelt.height,
            "backstory": self.the_cat.backstory,
            "gender": self.the_cat.gender,
            "genderalign":self.the_cat.genderalign
        }


    def update_ui_elements(self):
        self.kill_cat_elements()
        self.kill_buttons()
        self.kill_dropdowns()
        self.cat_elements["cat_name"] = create_text_box("customize " + str(self.the_cat.name), (0, 40), (400, 40), "#text_box_34_horizcenter", {"centerx": "centerx"})
        self.setup_buttons()
        self.setup_dropdowns()
        self.setup_cat_elements()
        self.make_cat_sprite()

    def get_cat_age(self):
        self.life_stage = "adult" if self.the_cat.age in ["young adult", "adult", "senior adult"] else self.the_cat.age

    def make_cat_sprite(self):
        if "cat_image" in self.cat_elements:
            self.cat_elements["cat_image"].kill()
        self.cat_image = generate_sprite(self.the_cat, self.life_stage, False, False, True, True)
        self.cat_elements["cat_image"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((35, 130), (250, 250))),
            pygame.transform.scale(self.cat_image, ui_scale_dimensions((250, 250))),
            manager=MANAGER
        )

    # TODO: create a subclass for dropdowns, create a function to regenerate dropdowns with specific data
    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.previous_cat_button:
                if isinstance(Cat.fetch_cat(self.previous_cat), Cat):
                    game.switches["cat"] = self.previous_cat
                    self.kill_cat_elements()
                    self.kill_buttons()
                    self.kill_dropdowns()
                    self.build_cat_page()
                else:
                    print("invalid previous cat", self.previous_cat)
            elif event.ui_element == self.next_cat_button:
                if isinstance(Cat.fetch_cat(self.next_cat), Cat):
                    game.switches["cat"] = self.next_cat
                    self.kill_cat_elements()
                    self.kill_buttons()
                    self.kill_dropdowns()
                    self.build_cat_page()
                else:
                    print("invalid next cat", self.previous_cat)
            elif event.ui_element == self.back_button:
                self.handle_back_button()
            elif event.ui_element == self.reset_button:
                self.reset_attributes()
            elif event.ui_element == self.reset_facets_button:
                self.reset_facets()
            elif event.ui_element == self.heal_button:
                self.the_cat.illnesses.clear()
                if "pregnant" not in self.the_cat.injuries:
                    self.the_cat.injuries.clear()
            
                
            #self.print_pelt_attributes()  # for testing purposes
        elif event.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if event.ui_element in [self.permanent_condition_dropdown, self.trait1_dropdown, self.skill1_dropdown, self.skill2_dropdown,self.fur_texture_dropdown, self.build_dropdown, self.height_dropdown, self.backstory_dropdown, self.gender_dropdown]:
                self.handle_dropdown_change(event.ui_element)
            #self.print_pelt_attributes()  # for testing purposes
                
    
    def reset_attributes(self):
        self.the_cat.personality.trait = self.initial_state["trait"]
        #self.the_cat.personality.trait2 = self.initial_state["trait2"]
        
        self.the_cat.pelt.fur_texture = self.initial_state["fur_texture"]
        self.the_cat.pelt.build = self.initial_state["build"]
        self.the_cat.pelt.height = self.initial_state["height"]
        
        self.the_cat.gender = self.initial_state["gender"]
        self.the_cat.genderalign = self.initial_state["genderalign"]
        
        self.the_cat.backstory = self.initial_state["backstory"]
        self.the_cat.permanent_condition = self.initial_state["permanent_condition"]
        
        self.the_cat.skills.primary = Skill(self.skill_strings_dict[self.initial_state["skill1"]], self.the_cat.skills.primary.points, self.the_cat.skills.primary.interest_only)
        
        if self.initial_state["skill2"] == "NONE":
            self.the_cat.skills.secondary = None
        else:
            self.the_cat.skills.secondary = Skill(self.skill_strings_dict[self.initial_state["skill2"]], self.the_cat.skills.secondary.points, self.the_cat.skills.secondary.interest_only)
        
        #if self.initial_state["skill3"] == "NONE":
            #self.the_cat.skills.tertiary = None
        #else:
            #self.the_cat.skills.tertiary = Skill(self.skill_strings_dict[self.initial_state["skill3"]], self.the_cat.skills.tertiary.points, self.the_cat.skills.tertiary.interest_only)
        
        self.update_ui_elements()
    
    def reset_facets(self):
        self.the_cat.personality = Personality(
                        trait=self.the_cat.personality.trait, kit_trait=self.the_cat.age in ["newborn", "kitten"]
                    )
        self.update_ui_elements()

    def handle_dropdown_change(self, dropdown):
        selected_option = dropdown.selected_option[1].lower()
        
        
        if dropdown == self.trait1_dropdown:
            self.the_cat.personality.trait = selected_option
        #if dropdown == self.trait2_dropdown:
            #self.the_cat.personality.trait2 = selected_option
        
        if dropdown == self.gender_dropdown:
            self.the_cat.gender = selected_option
            self.the_cat.genderalign = selected_option
        if dropdown == self.backstory_dropdown:
            self.the_cat.backstory = selected_option
        
        if dropdown == self.fur_texture_dropdown:
            self.the_cat.pelt.fur_texture = selected_option
        if dropdown == self.height_dropdown:
            self.the_cat.pelt.height = selected_option
        if dropdown == self.build_dropdown:
            self.the_cat.pelt.build = selected_option
        
        if dropdown == self.permanent_condition_dropdown:
            if selected_option == "none":
                self.the_cat.permanent_condition.clear()
            elif selected_option not in self.the_cat.permanent_condition:
                self.the_cat.get_permanent_condition(selected_option, born_with=True)
                
        if dropdown in [self.skill1_dropdown, self.skill2_dropdown]:
            selected_option = selected_option.upper()
            skill_path = None
            if selected_option in self.skill_strings_dict:
                skill_path = self.skill_strings_dict[selected_option]
                if dropdown == self.skill1_dropdown:
                    self.the_cat.skills.primary = Skill(skill_path, self.the_cat.skills.primary.points, self.the_cat.skills.primary.interest_only)
                elif dropdown == self.skill2_dropdown:
                    if self.the_cat.skills.secondary:
                        self.the_cat.skills.secondary = Skill(skill_path, self.the_cat.skills.secondary.points, self.the_cat.skills.secondary.interest_only)
                    else:
                        self.the_cat.skills.secondary = Skill(skill_path, self.the_cat.skills.primary.points, self.the_cat.skills.primary.interest_only)
                #elif dropdown == self.skill3_dropdown:
                    #if self.the_cat.skills.tertiary:
                        #self.the_cat.skills.tertiary = Skill(skill_path, self.the_cat.skills.tertiary.points, self.the_cat.skills.tertiary.interest_only)
                    #else:
                        #self.the_cat.skills.tertiary = Skill(skill_path, self.the_cat.skills.primary.points, self.the_cat.skills.primary.interest_only)
            elif selected_option == "NONE":
                if dropdown == self.skill1_dropdown:
                    print("Your cat can't be completely skillless...")
                elif dropdown == self.skill2_dropdown:
                    if self.the_cat.skills.secondary:
                        self.the_cat.skills.secondary = None
                #elif dropdown == self.skill3_dropdown:
                    #if self.the_cat.skills.tertiary:
                        #self.the_cat.skills.tertiary = None
        

    def handle_back_button(self):
        self.change_screen("profile screen")

    def exit_screen(self):
        self.kill_cat_elements()
        self.kill_labels()
        self.kill_buttons()
        self.kill_dropdowns()
        self.frame_image.kill()

    def kill_cat_elements(self):
        elements_to_kill = [
            "cat_name", "cat_image"
        ]
        for element in elements_to_kill:
            self.kill_cat_element(element)

    def kill_cat_element(self, element_name):
        if element_name in self.cat_elements:
            self.cat_elements[element_name].kill()

    def kill_labels(self):
        labels = [
            self.permanent_condition_label, self.trait1_label, self.skill1_label, self.skill2_label,
            self.fur_texture_label, self.build_label, self.height_label, self.backstory_label, self.gender_label,
            self.reset_message, self.reset_facets_message, self.heal_message
        ]
        for label in labels:
            label.kill()

    def kill_buttons(self):
        buttons = [
            self.previous_cat_button, self.back_button, self.next_cat_button, self.reset_button,self.reset_facets_button, self.heal_button
        ]
        for button in buttons:
            button.kill()

    def kill_dropdowns(self):
        dropdowns = [
            self.permanent_condition_dropdown, self.trait1_dropdown, self.skill1_dropdown, self.skill2_dropdown,
            self.fur_texture_dropdown, self.build_dropdown, self.height_dropdown, self.backstory_dropdown, self.gender_dropdown
        ]
        for dropdown in dropdowns:
            dropdown.kill()
