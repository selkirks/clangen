from random import choice, choices, randint
import pygame
import ujson
import re
from scripts.utility import scale

from .Screens import Screens

from scripts.utility import generate_sprite, get_cluster, get_alive_status_cats, get_alive_cats, pronoun_repl
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
import pygame_gui
from scripts.game_structure.game_essentials import game, screen_x, screen_y, MANAGER, screen
from enum import Enum  # pylint: disable=no-name-in-module
from scripts.cat.names import names, Name
from scripts.game_structure.ui_elements import UIImageButton, UITextBoxTweaked


class RelationType(Enum):
    """An enum representing the possible age groups of a cat"""

    BLOOD = ''                      # direct blood related - do not need a special print
    ADOPTIVE = 'adoptive'       	# not blood related but close (parents, kits, siblings)
    HALF_BLOOD = 'half sibling'   	# only one blood parent is the same (siblings only)
    NOT_BLOOD = 'not blood related'	# not blood related for parent siblings
    RELATED = 'blood related'   	# related by blood (different mates only)

BLOOD_RELATIVE_TYPES = [RelationType.BLOOD, RelationType.HALF_BLOOD, RelationType.RELATED]

class MoonplaceScreen(Screens):

    def __init__(self, name=None):
        super().__init__(name)
        self.back_button = None
        self.resource_dir = "resources/dicts/lifegen_talk/"
        self.texts = ""
        self.text_frames = [[text[:i+1] for i in range(len(text))] for text in self.texts]
        self.scroll_container = None
        self.life_text = None
        self.header = None
        self.the_cat = None
        self.text_index = 0
        self.frame_index = 0
        self.typing_delay = 20
        self.next_frame_time = pygame.time.get_ticks() + self.typing_delay
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 32)
        self.text = None
        self.profile_elements = {}
        self.talk_box_img = None
        self.possible_texts = {}
        self.chosen_text_key = ""
        self.choice_buttons = {}
        self.text_choices = {}
        self.option_bgs = {}
        self.current_scene = ""
        self.created_choice_buttons = False
        self.choicepanel = False
        self.textbox_graphic = None



    def screen_switches(self):
        self.the_cat = Cat.all_cats.get(choice(game.clan.starclan_cats))
        game.switches["attended half-moon"] = True
        self.update_camp_bg()
        self.hide_menu_buttons()
        self.handle_other_med()
        self.text_index = 0
        self.frame_index = 0
        self.choicepanel = False
        self.created_choice_buttons = False
        self.profile_elements = {}
        self.clan_name_bg = pygame_gui.elements.UIImage(
            scale(pygame.Rect((230, 875), (380, 70))),
            pygame.transform.scale(
                image_cache.load_image(
                    "resources/images/clan_name_bg.png").convert_alpha(),
                (500, 870)),
            manager=MANAGER)
        self.profile_elements["cat_name"] = pygame_gui.elements.UITextBox(str(self.the_cat.name),
                                                                    scale(pygame.Rect((300, 870), (-1, 80))),
                                                                          object_id="#text_box_34_horizcenter_light",
                                                                          manager=MANAGER)

        self.text_type = ""
        self.texts = self.load_texts(self.the_cat)
        self.text_frames = [[text[:i+1] for i in range(len(text))] for text in self.texts]
        self.talk_box_img = image_cache.load_image("resources/images/talk_box.png").convert_alpha()

        self.talk_box = pygame_gui.elements.UIImage(
                scale(pygame.Rect((178, 942), (1248, 302))),
                self.talk_box_img
            )

        self.back_button = UIImageButton(scale(pygame.Rect((50, 50), (210, 60))), "",
                                        object_id="#back_button", manager=MANAGER)
        self.scroll_container = pygame_gui.elements.UIScrollingContainer(scale(pygame.Rect((500, 970), (900, 300))))
        self.text = pygame_gui.elements.UITextBox("",
                                                scale(pygame.Rect((0, 0), (900, -100))),
                                                object_id="#text_box_30_horizleft",
                                                container=self.scroll_container,
                                                manager=MANAGER)

        self.textbox_graphic = pygame_gui.elements.UIImage(
                scale(pygame.Rect((170, 942), (346, 302))),
                image_cache.load_image("resources/images/textbox_graphic.png").convert_alpha()
            )
        # self.textbox_graphic.hide()

        self.profile_elements["cat_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((70, 900), (400, 400))),
                                                                        pygame.transform.scale(
                                                                            generate_sprite(self.the_cat),
                                                                            (400, 400)), manager=MANAGER)
        self.paw = pygame_gui.elements.UIImage(
                scale(pygame.Rect((1370, 1180), (30, 30))),
                image_cache.load_image("resources/images/cursor.png").convert_alpha()
            )
        self.paw.visible = False


    def exit_screen(self):
        self.text.kill()
        del self.text
        self.scroll_container.kill()
        del self.scroll_container
        self.back_button.kill()
        del self.back_button
        self.profile_elements["cat_image"].kill()
        self.profile_elements["cat_name"].kill()
        del self.profile_elements
        self.clan_name_bg.kill()
        del self.clan_name_bg
        self.talk_box.kill()
        del self.talk_box
        self.textbox_graphic.kill()
        del self.textbox_graphic
        self.paw.kill()
        del self.paw
        for button in self.choice_buttons:
            self.choice_buttons[button].kill()
        self.choice_buttons = {}
        for option in self.text_choices:
            self.text_choices[option].kill()
        self.text_choices = {}
        for option_bg in self.option_bgs:
            self.option_bgs[option_bg].kill()
        self.option_bgs = {}

    def update_camp_bg(self):
        light_dark = "light"
        if game.settings["dark mode"]:
            light_dark = "dark"

        camp_bg_base_dir = 'resources/images/camp_bg/'
        leaves = ["newleaf", "greenleaf", "leafbare", "leaffall"]
        camp_nr = game.clan.camp_bg

        if camp_nr is None:
            camp_nr = 'camp1'
            game.clan.camp_bg = camp_nr

        available_biome = ['Forest', 'Mountainous', 'Plains', 'Beach', 'Rainworld', 'Desert', 'Wetlands']
        biome = game.clan.biome
        if biome not in available_biome:
            biome = available_biome[0]
            game.clan.biome = biome
        biome = biome.lower()

        all_backgrounds = []
        for leaf in leaves:
            if game.clan.biome == "Forest":
                platform_dir = "resources/images/moonplace/moonhollow.png"
            # elif game.clan.biome == "Plains":
            #     platform_dir = "resources/images/moonplace/moongrove.png"
            elif game.clan.biome == "Beach":
                platform_dir = "resources/images/moonplace/moonstone.png"
            # elif game.clan.biome == "Mountainous":
            #     platform_dir = "resources/images/moonplace/moonplace1.png"
            else:
                platform_dir = "resources/images/moonplace/moonplace1.png"
            
            all_backgrounds.append(platform_dir)

        self.newleaf_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[0]).convert(), (screen_x, screen_y))
        self.greenleaf_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[1]).convert(), (screen_x, screen_y))
        self.leafbare_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[2]).convert(), (screen_x, screen_y))
        self.leaffall_bg = pygame.transform.scale(
            pygame.image.load(all_backgrounds[3]).convert(), (screen_x, screen_y))

    def on_use(self):
        if game.clan.clan_settings['backgrounds']:
            if game.clan.current_season == 'Newleaf':
                screen.blit(self.newleaf_bg, (0, 0))
            elif game.clan.current_season == 'Greenleaf':
                screen.blit(self.greenleaf_bg, (0, 0))
            elif game.clan.current_season == 'Leaf-bare':
                screen.blit(self.leafbare_bg, (0, 0))
            elif game.clan.current_season == 'Leaf-fall':
                screen.blit(self.leaffall_bg, (0, 0))
        now = pygame.time.get_ticks()
        try:
            if self.texts[self.text_index][0] == "[" and self.texts[self.text_index][-1] == "]":
                self.profile_elements["cat_image"].hide()
                self.clan_name_bg.hide()
                self.profile_elements["cat_name"].hide()
                # self.textbox_graphic.show()
            else:
                self.profile_elements["cat_image"].show()
                self.clan_name_bg.show()
                self.profile_elements["cat_name"].show()
                # self.textbox_graphic.hide()
        except:
            pass
        if self.text_index < len(self.text_frames):
            if now >= self.next_frame_time and self.frame_index < len(self.text_frames[self.text_index]) - 1:
                self.frame_index += 1
                self.next_frame_time = now + self.typing_delay
        try:
            if self.text_index == len(self.text_frames) - 1:
                if self.frame_index == len(self.text_frames[self.text_index]) - 1:
                    self.paw.visible = True

        except:
            pass

        # Always render the current frame
        try:
            self.text.html_text = self.text_frames[self.text_index][self.frame_index]
        except:
            pass
        self.text.rebuild()
        self.clock.tick(60)

    def handle_event(self, event):
        if game.switches['window_open']:
            pass
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.change_screen('profile screen')
        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if event.key == pygame.K_ESCAPE:
                self.change_screen('profile screen')
        elif event.type == pygame.MOUSEBUTTONDOWN:
            try:
                if self.frame_index == len(self.text_frames[self.text_index]) - 1:
                    if self.text_index < len(self.texts) - 1:
                        self.text_index += 1
                        self.frame_index = 0
                else:
                    self.frame_index = len(self.text_frames[self.text_index]) - 1  # Go to the last frame
            except:
                pass
        return

    def get_cluster_list(self):
        return ["assertive", "brooding", "cool", "upstanding", "introspective", "neurotic", "silly", "stable", "sweet", "unabashed", "unlawful"]

    def get_cluster_list_you(self):
        return ["you_assertive", "you_brooding", "you_cool", "you_upstanding", "you_introspective", "you_neurotic", "you_silly", "you_stable", "you_sweet", "you_unabashed", "you_unlawful"]


    def relationship_check(self, talk, cat_relationship):
        relationship_conditions = {
            'hate': 50,
            'romantic_like': 30,
            'platonic_like': 30,
            'jealousy': 30,
            'dislike': 30,
            'comfort': 30,
            'respect': 30,
            'trust': 30,
            'toxicity': 30
        }
        tags = talk["intro"] if "intro" in talk else talk[0]
        for key, value in relationship_conditions.items():
            if key in tags and cat_relationship < value:
                return True
        return False

    def handle_random_cat(self, cat):
        random_cat = Cat.all_cats.get(choice(game.clan.clan_cats))
        counter = 0
        while random_cat.outside or random_cat.dead or random_cat.ID in [game.clan.your_cat.ID, cat.ID]:
            counter += 1
            if counter == 15:
                break
            random_cat = Cat.all_cats.get(choice(game.clan.clan_cats))
        return random_cat

    def get_med_type(self, you):
        med_type = "you_single_med"

        if you.status == "medicine cat apprentice" and not you.mentor:
            med_type = "you_app_mentorless"
        elif you.status == "medicine cat apprentice":
            med_type = "you_app_mentor"
        elif you.status == "medicine cat" and len(get_alive_status_cats(Cat, ["medicine cat", "medicine cat apprentice"], working=False)) == 2:
            med_type = "two_meds"
        elif you.status == "medicine cat" and len(get_alive_status_cats(Cat, ["medicine cat", "medicine cat apprentice"], working=False)) > 2:
            med_type = "multi_meds"

        return med_type

    def load_texts(self, cat):
        you = game.clan.your_cat

        resource_dir = "resources/dicts/events/lifegen_events/moonplace/moonplace.json"
        possible_texts = {}
        with open(f"{resource_dir}", 'r') as read_file:
            possible_texts = ujson.loads(read_file.read())

        if you.status in ["apprentice", "queen's apprentice", "mediator apprentice"]:
            return self.get_adjusted_txt(choice(possible_texts["apprentice_halfmoon"]), cat)

        med_type = self.get_med_type(you)

        other_med_greeting = self.get_other_med_greeting(possible_texts)

        if randint(1,2) == 1:
            # No message
            return self.get_adjusted_txt(choice(possible_texts["intros"][med_type]) + other_med_greeting + choice(possible_texts["moonplace"]["starclan_no_message"]), cat)

        resource_dir = "resources/dicts/events/lifegen_events/moonplace/prophecies.json"
        possible_texts2 = {}
        with open(f"{resource_dir}", 'r') as read_file:
            possible_texts2 = ujson.loads(read_file.read())
        game.switches["next_possible_disaster"] = choice(list(possible_texts2.keys()))
        prophecy = choice(possible_texts2[game.switches["next_possible_disaster"]]["text"])
        return self.get_adjusted_txt(choice(possible_texts["intros"][med_type]) + other_med_greeting + choice(possible_texts["moonplace"]["starclan_general"]) + prophecy, cat)

    def get_other_med_greeting(self, possible_texts):
        """ Handles other medicine cat greetings at the Moonplace """
        other_clan_random = choice(game.switches["other_med_clan"])
        other_clan_random_index = game.switches["other_med_clan"].index(other_clan_random)
        other_meds = game.switches["other_med"][other_clan_random_index]
        possible_greetings = []
        if len(other_meds) == 1:
            possible_greetings.extend(possible_texts["med_cat_greetings"]["general_greeting_one_med"])
            possible_greetings.extend(possible_texts["med_cat_greetings"][f"general_greeting_{other_clan_random.temperament}_one_med"])
            if game.clan.war.get("at_war", True) and other_clan_random.name == game.clan.war["enemy"]:
                possible_greetings.extend(possible_texts["med_cat_greetings"]["general_greeting_war_one_med"])
            if other_clan_random.relations > 16:
                possible_greetings.extend(possible_texts["med_cat_greetings"]["general_greeting_friendly_one_med"])
            elif other_clan_random.relations < 7:
                possible_greetings.extend(possible_texts["med_cat_greetings"]["general_greeting_unfriendly_one_med"])
        else:
            possible_greetings.extend(possible_texts["med_cat_greetings"]["general_greeting_multi_med"])
            possible_greetings.extend(possible_texts["med_cat_greetings"][f"general_greeting_{other_clan_random.temperament}_multi_med"])
            if game.clan.war.get("at_war", True) and other_clan_random.name == game.clan.war["enemy"]:
                possible_greetings.extend(possible_texts["med_cat_greetings"]["general_greeting_war_multi_med"])
            if other_clan_random.relations > 16:
                possible_greetings.extend(possible_texts["med_cat_greetings"]["general_greeting_friendly_multi_med"])
            elif other_clan_random.relations < 7:
                possible_greetings.extend(possible_texts["med_cat_greetings"]["general_greeting_unfriendly_multi_med"])

        greeting = [choice(possible_greetings)]

        if len(other_meds) == 1:
            greeting = [s.replace("o_cn", str(other_clan_random.name) + "Clan").replace("o_c_m", str(other_meds[0])) for s in greeting]
        elif len(other_meds) == 2:
            greeting = [s.replace("o_cn", str(other_clan_random.name) + "Clan").replace("o_c_m", f"{other_meds[0]} and {other_meds[1]}") for s in greeting]
        elif len(other_meds) == 3:
            greeting = [s.replace("o_cn", str(other_clan_random.name) + "Clan").replace("o_c_m", f"{other_meds[0]}, {other_meds[1]}, and {other_meds[2]}") for s in greeting]

        return greeting
    

    def get_adjusted_txt(self, text, cat):
        you = game.clan.your_cat
        process_text_dict = {}
        process_text_dict["t_c"] = cat

        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, choice(abbrev_cat.pronouns))
        
        for i in range(len(text)):
            text[i] = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), text[i])

        text = [t1.replace("c_n", game.clan.name) for t1 in text]
        text = [t1.replace("y_c", str(you.name)) for t1 in text]
        text = [t1.replace("t_c", str(cat.name)) for t1 in text]

        for i in range(len(text)):
            text[i] = self.adjust_txt(text[i], cat)
            if text[i] == "":
                return ""

        r_c_found = False
        for i in range(len(text)):
            if "r_c" in text[i]:
                r_c_found = True
        if r_c_found:
            alive_cats = self.get_living_cats()
            alive_cat = choice(alive_cats)
            while alive_cat.ID == game.clan.your_cat.ID or alive_cat.ID == cat.ID:
                alive_cat = choice(alive_cats)
            text = [t1.replace("r_c", str(alive_cat.name)) for t1 in text]

        if "grief stricken" in cat.illnesses:
            try:
                dead_cat = Cat.all_cats.get(cat.illnesses['grief stricken'].get("grief_cat"))
                text = [t1.replace("d_c", str(dead_cat.name)) for t1 in text]
            except:
                return ""
        elif "grief stricken" in you.illnesses:
            try:
                dead_cat = Cat.all_cats.get(you.illnesses['grief stricken'].get("grief_cat"))
                text = [t1.replace("d_c", str(dead_cat.name)) for t1 in text]
            except:
                return ""
        d_c_found = False
        for t in text:
            if "d_c" in t:
                d_c_found = True
        if d_c_found:
            dead_cat = str(Cat.all_cats.get(game.clan.starclan_cats[-1]).name)
            text = [t1.replace("d_c", dead_cat) for t1 in text]
        return text

    def get_living_cats(self):
        living_cats = []
        for the_cat in Cat.all_cats_list:
            if not the_cat.dead and not the_cat.outside and not the_cat.moons == -1:
                living_cats.append(the_cat)
        return living_cats

    def adjust_txt(self, text, cat):
        try:
            if "moonplace" in text or "Moonplace" in text:
                moonplace_dict = {
                        "Beach": "Mooncove",
                        "Mountainous": "Moonfalls",
                        "Forest": "Moonhollow",
                        "Plains": "Moongrove",
                        "Rainworld": "Voidpool"
                    }
                moonplace = moonplace_dict.get(game.clan.biome, "Moonplace")
                text = text.replace("moonplace", moonplace)
                text = text.replace("Moonplace", moonplace)
            if "your_crush" in text:
                if len(game.clan.your_cat.mate) > 0 or game.clan.your_cat.no_mates:
                    return ""
                crush = None
                for c in self.get_living_cats():
                    if c.ID == game.clan.your_cat.ID or c.ID == cat.ID:
                        continue
                    relations = game.clan.your_cat.relationships.get(c.ID)
                    if not relations:
                        continue
                    if relations.romantic_love > 10:
                        crush = c
                        break
                if crush:
                    text = text.replace("your_crush", str(crush.name))
                else:
                    return ""
            if "their_crush" in text:
                if len(cat.mate) > 0 or cat.no_mates:
                    return ""
                crush = None
                for c in self.get_living_cats():
                    if c.ID == game.clan.your_cat.ID or c.ID == cat.ID:
                        continue
                    relations = cat.relationships.get(c.ID)
                    if not relations:
                        continue
                    if relations.romantic_love > 10:
                        crush = c
                        break
                if crush:
                    text = text.replace("their_crush", str(crush.name))
                else:
                    return ""


            if "r_c1" in text:
                alive_apps = self.get_living_cats()
                if len(alive_apps) <= 2:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID:
                    counter+=1
                    if counter==30:
                        return ""
                    alive_app = choice(alive_apps)
                alive_apps.remove(alive_app)
                text = text.replace("r_c1", str(alive_app.name))
                if "r_c2" in text:
                    alive_app2 = choice(alive_apps)
                    counter = 0
                    while alive_app2.ID == game.clan.your_cat.ID or alive_app2.ID == cat.ID:
                        alive_app2 = choice(alive_apps)
                        counter+=1
                        if counter==30:
                            return ""
                    text = text.replace("r_c2", str(alive_app2.name))
                if "r_c3" in text:
                    alive_app3 = choice(alive_apps)
                    counter = 0
                    while alive_app3.ID == game.clan.your_cat.ID or alive_app3.ID == cat.ID:
                        alive_app3 = choice(alive_apps)
                        counter+=1
                        if counter==30:
                            return ""
                    text = text.replace("r_c3", str(alive_app3.name))
            if "r_k" in text:
                alive_kits = get_alive_status_cats(Cat, ["kitten","newborn"])
                if len(alive_kits) <= 1:
                    return ""
                alive_kit = choice(alive_kits)
                counter = 0
                while alive_kit.ID == game.clan.your_cat.ID or alive_kit.ID == cat.ID:
                    counter+=1
                    if counter==30:
                        return ""
                    alive_kit = choice(alive_kits)
                text = text.replace("r_k", str(alive_kit.name))
            if "r_a" in text:
                alive_apps = get_alive_status_cats(Cat, ["apprentice"])
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID:
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                text = text.replace("r_a", str(alive_app.name))
            if "r_w1" in text:
                alive_apps = get_alive_status_cats(Cat, ["warrior"])
                if len(alive_apps) <= 2:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat or alive_app.ID == cat.ID:
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                alive_apps.remove(alive_app)
                text = text.replace("r_w1", str(alive_app.name))
                if "r_w2" in text:
                    alive_app2 = choice(alive_apps)
                    counter = 0
                    while alive_app2.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID:
                        alive_app2 = choice(alive_apps)
                        counter+=1
                        if counter == 30:
                            return ""
                    text = text.replace("r_w2", str(alive_app2.name))
                if "r_w3" in text:
                    alive_app3 = choice(alive_apps)
                    counter = 0
                    while alive_app3.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID:
                        counter+=1
                        if counter == 30:
                            return ""
                        alive_app3 = choice(alive_apps)
                    text = text.replace("r_w3", str(alive_app3.name))
            if "r_w" in text:
                alive_apps = get_alive_status_cats(Cat, ["warrior"])
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID:
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                text = text.replace("r_w", str(alive_app.name))
            if "r_m" in text:
                alive_apps = get_alive_status_cats(Cat, ["medicine cat", "medicine cat apprentice"])
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID:
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                text = text.replace("r_m", str(alive_app.name))
            if "r_d" in text:
                alive_apps = get_alive_status_cats(Cat, ["mediator", "mediator apprentice"])
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID:
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                text = text.replace("r_d", str(alive_app.name))
            if "r_q" in text:
                alive_apps = get_alive_status_cats(Cat, ["queen", "queen's apprentice"])
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID:
                    counter+=1
                    if counter == 30:
                        return ""
                    alive_app = choice(alive_apps)
                text = text.replace("r_q", str(alive_app.name))
            if "r_e" in text:
                alive_apps = get_alive_status_cats(Cat, ["elder"])
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID:
                    alive_app = choice(alive_apps)
                    counter+=1
                    if counter==30:
                        return ""
                text = text.replace("r_e", str(alive_app.name))
            if "r_s" in text:
                alive_apps = get_alive_cats(Cat)
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID or not alive_app.is_ill():
                    alive_app = choice(alive_apps)
                    counter+=1
                    if counter == 30:
                        return ""
                text = text.replace("r_s", str(alive_app.name))
            if "r_i" in text:
                alive_apps = get_alive_cats(Cat)
                if len(alive_apps) <= 1:
                    return ""
                alive_app = choice(alive_apps)
                counter = 0
                while alive_app.ID == game.clan.your_cat.ID or alive_app.ID == cat.ID or not alive_app.is_injured():
                    alive_app = choice(alive_apps)
                    counter+=1
                    if counter == 30:
                        return ""
                text = text.replace("r_i", str(alive_app.name))
            if "l_n" in text:
                if game.clan.leader is None:
                    return ""
                if game.clan.leader.dead or game.clan.leader.outside or game.clan.leader.ID == game.clan.your_cat.ID or game.clan.leader.ID == cat.ID:
                    return ""
                text = text.replace("l_n", str(game.clan.leader.name))
            if "d_n" in text:
                if game.clan.deputy is None:
                    return ""
                if game.clan.deputy.dead or game.clan.deputy.outside or game.clan.deputy.ID == game.clan.your_cat.ID or game.clan.deputy.ID == cat.ID:
                    return ""
                text = text.replace("d_n", str(game.clan.deputy.name))
            if "y_s" in text:
                if len(game.clan.your_cat.inheritance.get_siblings()) == 0:
                    return ""
                sibling = Cat.fetch_cat(choice(game.clan.your_cat.inheritance.get_siblings()))
                if sibling.outside or sibling.dead or sibling.ID == cat.ID:
                    return ""
                text = text.replace("y_s", str(sibling.name))
            if "t_s" in text:
                if len(cat.inheritance.get_siblings()) == 0:
                    return ""
                sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                if sibling.outside or sibling.dead or sibling.ID == game.clan.your_cat.ID:
                    return ""
                text = text.replace("t_s", str(sibling.name))
            if "y_a" in text:
                if len(game.clan.your_cat.apprentice) == 0:
                    return ""
                text = text.replace("y_a", str(Cat.fetch_cat(choice(game.clan.your_cat.apprentice)).name))
            if "y_l" in text:
                if len(game.clan.your_cat.inheritance.get_siblings()) == 0:
                    return ""
                sibling = Cat.fetch_cat(choice(game.clan.your_cat.inheritance.get_siblings()))
                counter = 0
                while sibling.moons != game.clan.your_cat.moons or sibling.outside or sibling.dead:
                    sibling = Cat.fetch_cat(choice(game.clan.your_cat.inheritance.get_siblings()))
                    counter+=1
                    if counter == 15:
                        return ""
                text = text.replace("y_l", str(sibling.name))

            if "t_l" in text:
                if len(cat.inheritance.get_siblings()) == 0:
                    return ""
                sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                counter = 0
                while sibling.moons != cat.moons or sibling.outside or sibling.dead:
                    sibling = Cat.fetch_cat(choice(cat.inheritance.get_siblings()))
                    counter+=1
                    if counter == 15:
                        return ""
                text = text.replace("t_l", str(sibling.name))

            if "y_p" in text:
                parent = Cat.fetch_cat(choice(game.clan.your_cat.inheritance.get_parents()))
                if len(game.clan.your_cat.inheritance.get_parents()) == 0:
                    return ""

                if parent.outside or parent.dead or parent.ID==cat.ID:
                    return ""
                text = text.replace("y_p", str(parent.name))


            if "t_p_positive" in text:
                if len(cat.inheritance.get_parents()) == 0:
                    return ""
                parent = Cat.fetch_cat(choice(cat.inheritance.get_parents()))
                if parent.outside or parent.dead or parent.ID==game.clan.your_cat.ID:
                    return ""
                relations = cat.relationships.get(parent.ID)
                if not relations:
                    return ""
                if relations.platonic_like < 10:
                    return ""
                text = text.replace("t_p_positive", str(parent.name))
            if "t_p_negative" in text:
                if len(cat.inheritance.get_parents()) == 0:
                    return ""
                parent = Cat.fetch_cat(choice(cat.inheritance.get_parents()))
                if parent.outside or parent.dead or parent.ID==game.clan.your_cat.ID:
                    return ""
                relations = cat.relationships.get(parent.ID)
                if not relations:
                    return ""
                if relations.dislike < 20:
                    return ""
                text = text.replace("t_p_negative", str(parent.name))
            if "t_p" in text:
                if len(cat.inheritance.get_parents()) == 0:
                    return ""
                parent = Cat.fetch_cat(choice(cat.inheritance.get_parents()))
                if parent.outside or parent.dead or parent.ID==game.clan.your_cat.ID:
                    return ""
                text = text.replace("t_p", str(parent.name))
            if "y_m" in text:
                if game.clan.your_cat.mate is None or len(game.clan.your_cat.mate) == 0 or cat.ID in game.clan.your_cat.mate:
                    return ""
                text = text.replace("y_m", str(Cat.fetch_cat(choice(game.clan.your_cat.mate)).name))
            if "tm_n" in text:
                if cat.mentor is None:
                    return ""
                text = text.replace("tm_n", str(Cat.fetch_cat(cat.mentor).name))
            if "tm_n" in text:
                if cat.mentor is None:
                    return ""
                text = text.replace("tm_n", str(Cat.fetch_cat(cat.mentor).name))
            if "m_n" in text:
                if game.clan.your_cat.mentor is None:
                    return ""
                text = text.replace("m_n", str(Cat.fetch_cat(game.clan.your_cat.mentor).name))
            if "o_c" in text:
                other_clan = choice(game.clan.all_clans)
                if not other_clan:
                    return ""
                text = text.replace("o_c", str(other_clan.name))

            #their mate
            if "t_m" in text:
                if cat.mate is None or len(cat.mate) == 0 or cat.ID in game.clan.your_cat.mate:
                    return ""
                mate1 = Cat.fetch_cat(choice(cat.mate))
                if mate1.outside or mate1.dead:
                    return ""
                text = text.replace("t_m", str(mate1.name))
            #their kit


            #their kit-- apprentice
            if "t_ka" in text:
                if cat.inheritance.get_children() is None or len(cat.inheritance.get_children()) == 0:
                    return ""
                kit = Cat.fetch_cat(choice(cat.inheritance.get_children()))
                if kit.moons < 12 or kit.outside or kit.dead or kit.ID == game.clan.your_cat.ID:
                    return ""
                text = text.replace("t_ka", str(kit.name))

            #their kit-- kit aged
            if "t_kk" in text:
                if cat.inheritance.get_children() is None or len(cat.inheritance.get_children()) == 0:
                    return ""
                kit = Cat.fetch_cat(choice(cat.inheritance.get_children()))
                if kit.moons >= 6 or kit.outside or kit.dead or kit.ID == game.clan.your_cat.ID:
                    return ""
                text = text.replace("t_kk", str(kit.name))

            if "t_k" in text:
                if cat.inheritance.get_children() is None or len(cat.inheritance.get_children()) == 0:
                    return ""
                kit = Cat.fetch_cat(choice(cat.inheritance.get_children()))
                if kit.outside or kit.dead or kit.ID == game.clan.your_cat.ID:
                    return ""
                text = text.replace("t_k", str(kit.name))

            if "y_k" in text:
                if game.clan.your_cat.inheritance.get_children() is None or len(game.clan.your_cat.inheritance.get_children()) == 0:
                    return ""
                kit = Cat.fetch_cat(choice(game.clan.your_cat.inheritance.get_children()))
                if kit.outside or kit.dead or kit.ID == cat.ID:
                    return ""

                text = text.replace("y_k", str(kit.name))


            #random cats 1 and 2
            if "n_r1" in text:
                if "n_r2" not in text:
                    return ""
                random_cat1 = choice(self.get_living_cats())
                random_cat2 = choice(self.get_living_cats())
                counter = 0
                while not random_cat1.is_potential_mate(random_cat2) or random_cat2.age != random_cat1.age:
                    random_cat1 = choice(self.get_living_cats())
                    random_cat2 = choice(self.get_living_cats())
                    counter +=1
                    if counter > 40:
                        return ""
                if random_cat1.ID == game.clan.your_cat.ID or random_cat1.ID == cat.ID or random_cat2.ID == game.clan.your_cat.ID or random_cat2.ID == cat.ID:
                    return ""
                text = text.replace("n_r1", str(random_cat1.name))
                text = text.replace("n_r2", str(random_cat2.name))

                #random cat
                #this does not work in any other location or indent level. i dont know.
                #just dont move it unless youve got a better way
                if "r_c" in text:

                    random_cat = choice(self.get_living_cats())
                    counter = 0
                    while random_cat.ID == game.clan.your_cat.ID or random_cat.ID == cat.ID:
                        if counter == 30:
                            return ""
                        random_cat = choice(self.get_living_cats())
                        counter +=1
                    text = text.replace("r_c", str(random_cat.name))


        except Exception as e:
            print(e)
            print("ERROR: could not replace abbrv.")
            return ""


        return text
    
    def handle_other_med(self):
        if "other_med" not in game.switches:
            game.switches["other_med"] = []
            game.switches["other_med_clan"] = []
            game.switches["last_visited_moonplace"] = game.clan.age

            for clan_name in game.clan.all_clans:
                other_clan_meds = []
                for i in range(randint(1,3)):
                    if randint(1,4) != 1:
                        other_clan_meds.append(Name(status = "medicine cat"))
                    else:
                        other_clan_meds.append(Name(status = "medicine cat apprentice"))
                game.switches["other_med"].append(other_clan_meds)
                game.switches["other_med_clan"].append(clan_name)
        else:
            if "other_med_clan" not in game.switches:
                game.switches['other_med_clan'] = []
                for clan_name in game.clan.all_clans:
                    game.switches["other_med_clan"].append(clan_name)

            for i in range(len(game.switches["other_med_clan"])):
                for cat_name in game.switches["other_med"][i]:
                    if cat_name.status == "medicine cat apprentice":
                        if randint(1,2) == 1:
                            cat_name.status = "medicine cat"

            game.switches["other_med"] = self.randomly_remove_string(game.switches["other_med"])
            for clan_meds in game.switches["other_med"]:
                if len(clan_meds) == 0:
                    clan_meds.append(Name(status = "medicine cat apprentice"))
                if len(clan_meds) < 3:
                    if randint(1, 5) == 1:
                        clan_meds.append(Name(status = "medicine cat apprentice"))

    def randomly_remove_string(self, lists_of_strings):
        for sublist in lists_of_strings:
            new_sublist = [s for s in sublist if randint(1, 10) != 1]
            sublist[:] = new_sublist
        return lists_of_strings
