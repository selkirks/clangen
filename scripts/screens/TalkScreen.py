from random import choice, choices, randint
import pygame
import ujson
import re

from .Screens import Screens
from scripts.game_structure.audio import sound_manager

from scripts.cat.cats import Cat, ILLNESSES, INJURIES, PERMANENT
from ..cat.history import History
from scripts.game_structure import image_cache
from scripts.game_structure.ui_elements import (
    UIImageButton,
    UISurfaceImageButton,
)
import pygame_gui
from scripts.game_structure.game_essentials import game
from scripts.housekeeping.version import VERSION_NAME
from scripts.special_dates import get_special_date, contains_special_date_tag
# pylint: disable=consider-using-dict-items
# pylint: disable=consider-using-enumerate
from scripts.utility import (
    ui_scale,
    get_current_season,
    ui_scale_dimensions,
    change_relationship_values,
    generate_sprite,
    get_cluster,
    pronoun_repl,
    lifegen_text_adjust,
    shorten_text_to_fit
    )
from scripts.game_structure.screen_settings import MANAGER
from ..ui.generate_button import ButtonStyles, get_button_dict
from ..ui.get_arrow import get_arrow
from itertools import accumulate as _accumulate


class TalkScreen(Screens):

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
        self.speaking_cat = None
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
        self.cat_dict = {}
        self.replaced_index = (False, 0)
        self.other_dict = {}

        self.testing = False
        self.meow = False

    def screen_switches(self):
        super().screen_switches()
        self.the_cat = Cat.all_cats.get(game.switches['cat'])
        self.cat_dict.clear()
        self.other_dict.clear()
        self.update_camp_bg()
        self.hide_menu_buttons()
        self.text_index = 0
        self.frame_index = 0
        self.choicepanel = False
        self.created_choice_buttons = False
        self.profile_elements = {}

        self.meow = False

        self.clan_name_bg = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((115, 438), (190, 35))),
            pygame.transform.scale(
                image_cache.load_image(
                    "resources/images/clan_name_bg.png").convert_alpha(),
                (500, 870)),
            manager=MANAGER)
        
        self.speaking_cat = self.the_cat
        short_name = shorten_text_to_fit(str(self.speaking_cat.name), 320, 40)
        self.profile_elements["cat_name"] = pygame_gui.elements.UITextBox(
            short_name,
            ui_scale(pygame.Rect((115, 437), (190, 40))),
            object_id="#text_box_34_horizcenter_light",
            manager=MANAGER
            )


        self.text_type = ""
        if game.config["debug_meow_error_locating"]:
            self.debug_meow_error_locator(self.the_cat)
        else:
            self.texts = self.load_texts(self.the_cat)

        if game.switches["talk_category"] == "flirt":
            flirt_success = self.is_flirt_success(self.the_cat)
            if flirt_success is True:
                self.the_cat.relationships.get(game.clan.your_cat.ID).romantic_love += randint(1,10)
                if self.the_cat.ID in game.clan.your_cat.relationships:
                    game.clan.your_cat.relationships.get(self.the_cat.ID).romantic_love += randint(1,10)
            else:
                if game.clan.your_cat.ID in self.the_cat.relationships:
                    self.the_cat.relationships.get(game.clan.your_cat.ID).romantic_love -= randint(1,5)
                    self.the_cat.relationships.get(game.clan.your_cat.ID).comfortable -= randint(1,5)
                    self.the_cat.relationships.get(game.clan.your_cat.ID).dislike += randint(1,5)
                else:
                    print("no relationship :(")


        self.text_frames = [[text[:i+1] for i in range(len(text))] for text in self.texts]
        self.talk_box_img = image_cache.load_image("resources/images/talk_box.png").convert_alpha()

        self.talk_box = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((90, 470), (624, 151))),
                self.talk_box_img
            )

        self.back_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (153, 30))),
            get_arrow(5, arrow_left=True) + " Back",
            get_button_dict(ButtonStyles.SQUOVAL, (153, 30)),
            object_id="@buttonstyles_squoval",
            manager=MANAGER,
        )
        self.scroll_container = pygame_gui.elements.UIScrollingContainer(ui_scale(pygame.Rect((250, 475), (450, 150))))
        self.text = pygame_gui.elements.UITextBox("",
                                                ui_scale(pygame.Rect((0, 10), (450, -100))),
                                                object_id="#text_box_30_horizleft",
                                                container=self.scroll_container,
                                                manager=MANAGER)

        self.textbox_graphic = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((90, 471), (163, 150))),
                image_cache.load_image("resources/images/textbox_graphic.png").convert_alpha()
            )
        # self.textbox_graphic.hide()

        self.profile_elements["cat_image"] = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((35, 450), (200, 200))),
            pygame.transform.scale(
            generate_sprite(self.speaking_cat),
            (200, 200)),
            manager=MANAGER
            )

        self.paw = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((685, 590), (15, 15))),
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
        light_dark = "dark" if game.settings["dark mode"] else "light"

        camp_bg_base_dir = "resources/images/camp_bg/"
        leaves = ["newleaf", "greenleaf", "leafbare", "leaffall"]
        camp_nr = game.clan.camp_bg

        if camp_nr is None:
            camp_nr = "camp1"
            game.clan.camp_bg = camp_nr

        available_biome = ["Forest", "Mountainous", "Plains", "Beach"]
        biome = game.clan.biome
        if biome not in available_biome:
            biome = available_biome[0]
            game.clan.biome = biome
        biome = biome.lower()

        all_backgrounds = []
        for leaf in leaves:
            platform_dir = (
                f"{camp_bg_base_dir}/{biome}/{leaf}_{camp_nr}_{light_dark}.png"
            )
            all_backgrounds.append(platform_dir)
        
        #LG
        starclan_camp = "resources/images/dead_camps/scbackground_sunsetclouds.png"
        df_camp = "resources/images/dead_camps/dfbackground_eclipse.png"
        ur_camp = "resources/images/urbg.png"

        if (
            self.the_cat.dead and
            not self.the_cat.df and
            not self.the_cat.outside
            ):
            all_backgrounds = [
                starclan_camp,
                starclan_camp,
                starclan_camp,
                starclan_camp
            ]
        elif (
            self.the_cat.dead and
            not self.the_cat.df and
            self.the_cat.outside
        ):
            all_backgrounds = [
                ur_camp,
                ur_camp,
                ur_camp,
                ur_camp
            ]
        elif (
            self.the_cat.dead and
            self.the_cat.df
        ):
            all_backgrounds = [
                df_camp,
                df_camp,
                df_camp,
                df_camp
            ]

        self.add_bgs(
            {
                "Newleaf": pygame.transform.scale(
                    pygame.image.load(all_backgrounds[0]).convert(),
                    ui_scale_dimensions((800, 700)),
                ),
                "Greenleaf": pygame.transform.scale(
                    pygame.image.load(all_backgrounds[1]).convert(),
                    ui_scale_dimensions((800, 700)),
                ),
                "Leaf-bare": pygame.transform.scale(
                    pygame.image.load(all_backgrounds[2]).convert(),
                    ui_scale_dimensions((800, 700)),
                ),
                "Leaf-fall": pygame.transform.scale(
                    pygame.image.load(all_backgrounds[3]).convert(),
                    ui_scale_dimensions((800, 700)),
                ),
            },
            {
                "Newleaf": None,
                "Greenleaf": None,
                "Leaf-bare": None,
                "Leaf-fall": None,
            },
        )

        self.set_bg(get_current_season())

    def on_use(self):
        super().on_use()
        now = pygame.time.get_ticks()

        if self.texts:
            # print("CURRENT LINE:", self.texts[self.text_index])
            self.texts[self.text_index], self.speaking_cat = self.get_speaking_cat(self.texts[self.text_index])
            
            # Redo cat_name and cat_image to account for different cats speaking.
            self.profile_elements["cat_image"].kill()
            self.profile_elements["cat_image"] = pygame_gui.elements.UIImage(
                ui_scale(pygame.Rect((35, 450), (200, 200))),
                pygame.transform.scale(
                generate_sprite(self.speaking_cat),
                (200, 200)),
                manager=MANAGER
                )
            
            self.profile_elements["cat_name"].kill()
            short_name = shorten_text_to_fit(str(self.speaking_cat.name), 320, 40)
            self.profile_elements["cat_name"] = pygame_gui.elements.UITextBox(
                short_name,
                ui_scale(pygame.Rect((115, 437), (190, 40))),
                object_id="#text_box_34_horizcenter_light",
                manager=MANAGER
                )
            
            text_to_display = self.texts.copy()
            # now get rid of the |abbrev|
            if "|" in text_to_display[self.text_index]:
                text_to_display[self.text_index] = text_to_display[self.text_index].split("|")[-1]
            if self.texts[self.text_index][0] == "[" and self.texts[self.text_index][-1] == "]":
                self.profile_elements["cat_name"].hide()
                self.profile_elements["cat_image"].hide()
            else:
                self.profile_elements["cat_name"].show()
                self.profile_elements["cat_image"].show()
        else:
            text_to_display = self.texts.copy()

        self.text_frames = [[text[:i+1] for i in range(len(text))] for text in text_to_display]
        if self.text_index < len(self.text_frames):
            if now >= self.next_frame_time and self.frame_index < len(self.text_frames[self.text_index]) - 1:
                self.frame_index += 1
                self.next_frame_time = now + self.typing_delay
                # sound_manager.play("button_press")
        if self.text_index == len(self.text_frames) - 1:
            if self.frame_index == len(self.text_frames[self.text_index]) - 1:
                if self.text_type != "choices":
                    self.paw.visible = True
                if not self.created_choice_buttons and self.text_type == "choices":
                    self.create_choice_buttons()
                    self.created_choice_buttons = True
                if not self.meow:
                    if "[" not in self.texts[self.text_index]:
                        sound_manager.play("meow")
                    # this plays One meow sound effect at the end of dialogue
                    self.meow = True


        # Always render the current frame
        if self.text_frames:
            self.text.html_text = self.text_frames[self.text_index][self.frame_index]

        self.text.rebuild()
        self.clock.tick(60)


    def handle_event(self, event):
        if game.switches['window_open']:
            pass
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element == self.back_button:
                self.change_screen('profile screen')
            else:
                for key, button in self.choice_buttons.items():
                    if event.ui_element == button and self.chosen_text_key:
                        self.current_scene = self.possible_texts[self.chosen_text_key][f"{self.current_scene}_choices"][key]["next_scene"]
                        self.handle_choice(self.the_cat)
        elif event.type == pygame.KEYDOWN and game.settings['keybinds']:
            if event.key == pygame.K_ESCAPE:
                self.change_screen('profile screen')
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.text_frames:
                if self.frame_index == len(self.text_frames[self.text_index]) - 1:
                    if self.text_index < len(self.texts) - 1:
                        self.text_index += 1
                        self.frame_index = 0
                else:
                    self.frame_index = len(self.text_frames[self.text_index]) - 1  # Go to the last frame
            
        return
    
    def debug_meow_error_locator(self, cat):
        """
        When talking to one cat, searches through all cats and identifies if any of them would cause a meow error.
        """
        test_texts = {}
        for kitty in Cat.all_cats_list:
            if kitty == game.clan.your_cat:
                continue
            test_texts[kitty] = self.load_texts(kitty)
        meows = []
        for dialogue in test_texts.items():
            # print(dialogue[1])
            if "#dialogue-bugs" in str(dialogue[1]):
                # skip over the dialogue that doesnt need anything bc its impossible anyway
                if game.clan.your_cat.status == "newborn" and dialogue[0].dead:
                    continue
                if dialogue[0].outside and not dialogue[0].dead:
                    continue
                if game.clan.your_cat.dead and dialogue[0].status == "newborn":
                    continue
                if dialogue[0].dead and game.switches["talk_category"] in ["insult", "flirt"]:
                    continue
                if game.switches["talk_category"] == "flirt" and not dialogue[0].is_dateable(game.clan.your_cat):
                    continue
                self.text_type = ""
                meows.append(dialogue)
                print("----------------")
                print("Meow error!", game.switches["talk_category"].upper())
                print("You:", game.clan.your_cat.name)
                print("Them: ", dialogue[0].name)
                if self.the_cat == dialogue[0]:
                    text = self.load_and_replace_placeholders(
                        self.resource_dir + "general.json",
                        self.the_cat,
                        game.clan.your_cat
                        )[1]
                    self.texts = self.get_adjusted_txt(text, dialogue[0])
                else:
                    self.texts = [f"Meow error found for {game.clan.your_cat.name} and {dialogue[0].name}."]
        if not meows:
            print("No meows possible right neow!")
            self.text_type = ""
            self.texts = self.load_texts(self.the_cat)

    def get_cluster_list(self):
        return ["assertive", "brooding", "cool", "upstanding", "introspective", "neurotic", "silly", "stable", "sweet", "unabashed", "unlawful"]

    def get_cluster_list_they(self):
        return ["they_assertive", "they_brooding", "they_cool", "they_upstanding", "they_introspective", "they_neurotic", "they_silly", "they_stable", "they_sweet", "they_unabashed", "they_unlawful"]

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
            'trust': 30
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

    def display_intro(self, cat, texts_list, texts_chosen_key):
        chosen_text_intro = texts_list[texts_chosen_key]["intro"]
        # chosen_text_intro = self.get_adjusted_txt(chosen_text_intro, cat)
        self.current_scene = "intro"
        self.possible_texts = texts_list
        self.chosen_text_key = texts_chosen_key

        if f"{self.current_scene}_scene_effects" in self.possible_texts[self.chosen_text_key]:
            self.scene_effects(self.the_cat, self.possible_texts, self.chosen_text_key)

        return chosen_text_intro

    def create_choice_buttons(self):
        y_pos = 0
        if f"{self.current_scene}_choices" not in self.possible_texts[self.chosen_text_key]:
            self.paw.visible = True

            return
        for c in self.possible_texts[self.chosen_text_key][f"{self.current_scene}_choices"]:
            text = self.possible_texts[self.chosen_text_key][f"{self.current_scene}_choices"][c]['text']
            text = self.get_adjusted_txt([text], self.the_cat)
            text = text[0]

            #the background image for the text
            option_bg = pygame_gui.elements.UIImage(ui_scale(pygame.Rect((430, 427 + y_pos), (270, 35))),
                                                            pygame.transform.scale(
                                                                image_cache.load_image(
                                                                    "resources/images/option_bg.png").convert_alpha(),
                                                                (270, 35)), manager=MANAGER)
            self.option_bgs[c] = option_bg

            #the button for dialogue choices
            button = UIImageButton(ui_scale(pygame.Rect((390, 427 + y_pos), (34, 34))),
                                        text = "",
                                        object_id="#dialogue_choice_button", manager=MANAGER)
            self.choice_buttons[c] = button


            #the text for dialogue choices
            option = pygame_gui.elements.UITextBox(str(text),
                                                            ui_scale(pygame.Rect((435, 428 + y_pos), (270, 35))),
                                                            object_id="#text_box_30_horizleft",
                                                            manager=MANAGER)
            self.text_choices[c] = option

            y_pos -= 40

    def handle_choice(self, cat):
        for b in self.choice_buttons:
            self.choice_buttons[b].kill()
        for b in self.text_choices:
            self.text_choices[b].kill()
        for b in self.option_bgs:
            self.option_bgs[b].kill()

        self.choice_buttons = {}
        chosen_text = self.possible_texts[self.chosen_text_key][self.current_scene]
        chosen_text2 = self.get_adjusted_txt(chosen_text, cat)
        self.texts = chosen_text2
        self.text_frames = [[text[:i+1] for i in range(len(text))] for text in chosen_text2]
        self.text_index = 0
        self.frame_index = 0
        self.created_choice_buttons = False

        if f"{self.current_scene}_scene_effects" in self.possible_texts[self.chosen_text_key]:
            self.scene_effects(self.the_cat, self.possible_texts, self.chosen_text_key)

    def scene_effects(self, cat, texts_list, texts_chosen_key):
        """
        Adds accessories to inventory from dialogue
        """
        for block in texts_list[texts_chosen_key][f"{self.current_scene}_scene_effects"]:
            # INVENTORY
            if block == "inventory":
                inv_block = texts_list[texts_chosen_key][f"{self.current_scene}_scene_effects"]["inventory"]

                cats_to = []
                for kitty in inv_block["cats_to"]:
                    if kitty == "y_c":
                        cats_to.append(game.clan.your_cat)
                    elif kitty == "t_c":
                        cats_to.append(cat)
                    else:
                        cats_to.append(self.cat_dict[kitty])

                accessories = inv_block["accessory"]

                if inv_block["addition"] == "choice":
                    for kitty in cats_to:
                        acc = choice(accessories)
                        if acc not in kitty.pelt.inventory:
                            kitty.pelt.inventory.append(acc)
                elif inv_block["addition"] == "all":
                    for kitty in cats_to:
                        for acc in accessories:
                            if acc not in kitty.pelt.inventory:
                                kitty.pelt.inventory.append(acc)
                else:
                    print("Invalid 'addition' string for dialogue inventory block.")
            # REL
            if block == "relationship":
                rel_block = texts_list[texts_chosen_key][f"{self.current_scene}_scene_effects"]["relationship"]

                if game.clan.your_cat.ID not in cat.relationships:
                    cat.create_one_relationship(game.clan.your_cat)
                    if cat.ID not in game.clan.your_cat.relationships:
                        game.clan.your_cat.create_one_relationship(cat)

                cats_to = []
                for kitty in rel_block["cats_to"]:
                    if kitty == "y_c":
                        cats_to.append(game.clan.your_cat)
                    elif kitty == "t_c":
                        cats_to.append(cat)
                    else:
                        cats_to.append(self.cat_dict[kitty])

                cats_from = []
                for kitty in rel_block["cats_from"]:
                    if kitty == "y_c":
                        cats_from.append(game.clan.your_cat)
                    elif kitty == "t_c":
                        cats_from.append(cat)
                    else:
                        cats_from.append(self.cat_dict[kitty])

                romantic_value = rel_block["values"]["romantic"] if "romantic" in rel_block["values"] else 0
                platonic_value = rel_block["values"]["platonic"] if "platonic" in rel_block["values"] else 0
                dislike_value = rel_block["values"]["dislike"] if "dislike" in rel_block["values"] else 0
                respect_value = rel_block["values"]["respect"] if "respect" in rel_block["values"] else 0
                comfort_value = rel_block["values"]["comfort"] if "comfort" in rel_block["values"] else 0
                jealousy_value = rel_block["values"]["jealousy"] if "jealousy" in rel_block["values"] else 0
                trust_value = rel_block["values"]["trust"] if "trust" in rel_block["values"] else 0

                change_relationship_values(
                    cats_to,
                    cats_from,
                    romantic_value,
                    platonic_value,
                    dislike_value,
                    respect_value,
                    comfort_value,
                    jealousy_value,
                    trust_value,
                    log=None
                )

                if rel_block["mutual"]:
                    change_relationship_values(
                        cats_from,
                        cats_to,
                        romantic_value,
                        platonic_value,
                        dislike_value,
                        respect_value,
                        comfort_value,
                        jealousy_value,
                        trust_value,
                        log=None
                    )
            # DF
            if block == "dark_forest":
                df_block = texts_list[texts_chosen_key][f"{self.current_scene}_scene_effects"]["dark_forest"]
                
                joined_cats = []
                for kitty in df_block["join"]:
                    if kitty == "y_c":
                        joined_cats.append(game.clan.your_cat)
                    elif kitty == "t_c":
                        joined_cats.append(cat)
                    else:
                        joined_cats.append(self.cat_dict[kitty])
                left_cats = []
                for kitty in df_block["leave"]:
                    if kitty == "y_c":
                        left_cats.append(game.clan.your_cat)
                    elif kitty == "t_c":
                        left_cats.append(cat)
                    else:
                        left_cats.append(self.cat_dict[kitty])

                for kitty in joined_cats:
                    if kitty.joined_df:
                        print("ERROR:", kitty.name, "trying to join the DF from dialogue, but they're already in it.")
                        continue
                    kitty.joined_df = True
                    kitty.update_df_mentor()
                for kitty in left_cats:
                    if not kitty.joined_df:
                        print("ERROR:", kitty.name, "trying to lead the DF from dialogue, but they're not in it.")
                        continue
                    kitty.joined_df = False
                    kitty.update_df_mentor()


    def load_texts(self, cat):
        possible_texts = {}
        you = game.clan.your_cat

        special_date = get_special_date()

        if game.switches["talk_category"] == "insult":
            with open(f"{self.resource_dir}insults.json", 'r') as read_file:
                possible_texts = ujson.loads(read_file.read())
        elif game.switches["talk_category"] == "flirt":
            with open(f"{self.resource_dir}flirt.json", 'r') as read_file:
                possible_texts.update(ujson.loads(read_file.read()))
        else:
            if cat.status != 'exiled':
                with open(f"{self.resource_dir}{cat.status}.json", 'r') as read_file:
                    possible_texts = ujson.loads(read_file.read())

            if cat.status in ["rogue", "loner", "kittypet"]:
                # former clancats only get their own file so we can write general dialogue about not knowing what a clan is
                with open(f"{self.resource_dir}general_outsider.json", 'r') as read_file:
                    possible_texts4 = ujson.loads(read_file.read())
                    possible_texts.update(possible_texts4)
            else:
                if cat.status == "newborn":
                    # newborns will no longer participate in nuanced discussion (focus + choices)
                    with open(f"{self.resource_dir}newborn.json", 'r') as read_file:
                        possible_texts.update(ujson.loads(read_file.read()))
                else:
                    with open(f"{self.resource_dir}choice_dialogue.json", 'r') as read_file:
                        possible_texts.update(ujson.loads(read_file.read()))

                    if cat.status not in ['kitten', "newborn"] and you.status not in ['kitten', 'newborn']:
                        with open(f"{self.resource_dir}general_no_kit.json", 'r') as read_file:
                            possible_texts2 = ujson.loads(read_file.read())
                            possible_texts.update(possible_texts2)

                    if cat.status not in ["newborn"] and you.status not in ['newborn']:
                        with open(f"{self.resource_dir}general_no_newborn.json", 'r') as read_file:
                            possible_texts4 = ujson.loads(read_file.read())
                            possible_texts.update(possible_texts4)

                    if cat.status not in ['kitten', "newborn"] and you.status in ['kitten', 'newborn']:
                        with open(f"{self.resource_dir}general_you_kit.json", 'r') as read_file:
                            possible_texts3 = ujson.loads(read_file.read())
                            possible_texts.update(possible_texts3)

                    if cat.status not in ['kitten', 'newborn'] and you.status not in ['kitten', 'newborn'] and randint(1,3)==1:
                        with open(f"{self.resource_dir}crush.json", 'r') as read_file:
                            possible_texts3 = ujson.loads(read_file.read())
                            possible_texts.update(possible_texts3)

                    if game.clan.focus:
                        with open(f"{self.resource_dir}focuses/{game.clan.focus}.json", 'r') as read_file:
                            possible_texts5 = ujson.loads(read_file.read())
                            possible_texts.update(possible_texts5)

                    if special_date:
                        with open(f"{self.resource_dir}focuses/{special_date.patrol_tag}.json", 'r') as read_file:
                            special_dialogue = ujson.loads(read_file.read())
                            possible_texts.update(special_dialogue)
                            
                    if game.config['fun']['april_fools']:
                        with open(f"{self.resource_dir}focuses/aprilfools.json", 'r') as read_file:
                            aprilfools_dialogue = ujson.loads(read_file.read())
                            possible_texts.update(aprilfools_dialogue)
 
        texts = self.filter_texts(cat, possible_texts)
        return texts

    def filter_texts(self, cat, possible_texts):
        texts_list = {}
        you = game.clan.your_cat

        cat_cluster_1, cat_cluster_2 = get_cluster(cat.personality.trait)
        you_cluster_1, you_cluster_2 = get_cluster(you.personality.trait)

        possible_backstories = ["clanfounder",
            "clanborn",
            "outsiderroots",
            "half-clan",
            "formerlyaloner",
            "formerlyarogue",
            "formerlyakittypet",
            "formerlyaoutsider",
            "originallyfromanotherclan",
            "orphaned",
            "abandoned",
            "ancientspirit"
        ]
        special_date = get_special_date()
        for talk_key, talk in possible_texts.items():
            TAGS = talk["tags"] if "tags" in talk else {}

            # NEW
            YOU = talk["y_c"] if "y_c" in talk else {}
            CAT = talk["t_c"] if "t_c" in talk else {}
            REL = talk["relationship"] if "relationship" in talk else {}
            SEASON = talk["season"] if "season" in talk else {}
            BIOME = talk["biome"] if "biome" in talk else {}

            for i in range(len(TAGS)):
                TAGS[i] = TAGS[i].lower()

            # what if i just start over
            # old stuff
            if "debug_ensure_dialogue" in game.config and game.config["debug_ensure_dialogue"]:
                if game.config["debug_ensure_dialogue"] == talk_key:
                    pass
            
            if contains_special_date_tag(TAGS):
                if not special_date or special_date.patrol_tag not in TAGS:
                    continue

            if game.switches["talk_category"] == "talk" and (
                "insult" in TAGS or "reject" in TAGS or "accept" in TAGS
                ):
                continue

            if game.switches["talk_category"] == "insult" and (
                "insult" not in TAGS or "accept" in TAGS or "reject" in TAGS
                ):
                continue

            if game.switches["talk_category"] == "flirt" and (
                "insult" in TAGS or ("reject" not in TAGS and "accept" not in TAGS)
                ):
                continue

            # NEW CODE
            # STATUS
            if "status" in YOU:
                if not self.validate_status(YOU, you):
                    continue
            if "status" in CAT:
                if not self.validate_status(CAT, cat):
                    continue

            # AGE
            if "age" in YOU:
                if not self.validate_age(YOU, you):
                    continue

            if "age" in CAT:
                if not self.validate_age(CAT, cat):
                    continue

            # FAITH
            if "min_max_faith" in YOU:
                if YOU["min_max_faith"][0] < you.faith:
                    continue
                if YOU["min_max_faith"][1] > you.faith:
                    continue
            if "min_max_faith" in CAT:
                if CAT["min_max_faith"][0] < cat.faith:
                    continue
                if CAT["min_max_faith"][1] > cat.faith:
                    continue

            if game.switches["talk_category"] == "flirt":
                success = self.is_flirt_success(cat)
                if "heartbroken" not in cat.illnesses.keys() and ("condition" in CAT and "heartbroken" in CAT["condition"]):
                    continue
                elif not success and "reject" not in TAGS:
                    continue
                elif success and "reject" in TAGS:
                    continue
                elif not success and "reject" not in TAGS:
                    continue

            # DEMOTED FROM STATUS
            # this allows cats who were shunned and demoted from leader to
            # still get leaderlike dialogue
            # TODO: this is useless rn. do something
            if you.shunned != 0:
                murder_history = History.get_murders(you)
                history = None
                your_status = you.status
                if "is_murderer" in murder_history:
                    history = murder_history["is_murderer"]
                else:
                    your_status = you.status
                if history:
                    if "demoted_from" in history[-1] and history[-1]["demoted_from"]:
                        your_status = history[-1]["demoted_from"]
                    else:
                        your_status = you.status
                else:
                    your_status = you.status
            else:
                your_status = you.status

            if "grief stricken" in cat.illnesses:
                dead_cat = Cat.all_cats.get(cat.illnesses['grief stricken'].get("grief_cat"))
                if dead_cat:
                    if "grievingyou" in REL:
                        if dead_cat.ID != game.clan.your_cat.ID:
                            continue
                    else:
                        if dead_cat.ID == game.clan.your_cat.ID:
                            continue
            elif "grievingyou" in REL:
                continue

            if "grief stricken" in you.illnesses:
                dead_cat = Cat.all_cats.get(you.illnesses['grief stricken'].get("grief_cat"))
                if dead_cat:
                    if "grievingthem" in REL:
                        if dead_cat.name != cat.name:
                            continue
                    else:
                        if dead_cat.name == cat.name:
                            continue
            elif "grievingthem" in REL:
                continue

            # FORGIVEN TAGS
            youreforgiven = False
            theyreforgiven = False

            if you.forgiven < 11 and you.forgiven > 0:
                youreforgiven = True

            if cat.forgiven < 11 and cat.forgiven > 0:
                theyreforgiven = True

            if "forgiven" in YOU and YOU["forgiven"] is True and (you.shunned > 0 or not youreforgiven):
                continue

            if "forgiven" in CAT and CAT["forgiven"] is True and (cat.shunned > 0 or not theyreforgiven):
                continue

            # SHUNNED TAGS
            if "shunned" in YOU:
                if YOU["shunned"] is True and you.shunned == 0:
                    continue
                if YOU["shunned"] is False and you.shunned > 0:
                    continue
            else:
                if you.shunned > 0:
                    continue
            if "shunned" in CAT:
                if CAT["shunned"] is True and cat.shunned == 0:
                    continue
                if CAT["shunned"] is False and cat.shunned > 0:
                    continue
            else:
                if cat.shunned > 0:
                    continue

            # CONDITIONS
            # grief
            if "grief stricken" in you.illnesses and (
                "condition" not in YOU or
                ("condition" in YOU and "grief stricken" not in YOU["condition"])
            ):
                continue
            if "grief stricken" in cat.illnesses and (
                "condition" not in CAT or
                ("condition" in CAT and "grief stricken" not in CAT["condition"])
            ):
                continue

            # validate_conditions gets passed the conditions list, not the whole block
            if "condition" in CAT:
                CONDITIONS = CAT["condition"]
            else:
                CONDITIONS = []
            if not self.validate_conditions(CONDITIONS, cat):
                continue

            if "condition" in YOU:
                CONDITIONS = YOU["condition"]
            else:
                CONDITIONS = []
            if not self.validate_conditions(CONDITIONS, you):
                continue

            # CLUSTER/TRAITS
            if "cluster" in YOU:
                allowed = False
                if you.personality.trait == "sweet":
                    trait = "sweet_trait"
                else:
                    trait = you.personality.trait
                for item in [you_cluster_1, you_cluster_2, trait]:
                    if item is not None:
                        if item in YOU["cluster"]:
                            allowed = True
                            break
                if not allowed:
                    continue
            if "cluster" in CAT:
                allowed = False
                if cat.personality.trait == "sweet":
                    trait = "sweet_trait"
                else:
                    trait = cat.personality.trait
                for item in [cat_cluster_1, cat_cluster_2, trait]:
                    if item is not None:
                        if item in CAT["cluster"]:
                            allowed = True
                            break
                if not allowed:
                    continue

            # BACKSTORY
            if "backstory" in YOU:
                if any(i in possible_backstories for i in YOU["backstory"]):
                    bs_text = self.backstory_text(you).replace(" ", "").lower()
                    if not bs_text:
                        continue
                    if bs_text and bs_text not in YOU["backstory"]:
                        continue
            if "backstory" in CAT:
                if any(i in possible_backstories for i in CAT["backstory"]):
                    bs_text = self.backstory_text(cat).replace(" ", "").lower()
                    if not bs_text:
                        continue
                    if bs_text and bs_text not in CAT["backstory"]:
                        continue


            # SKILL
            if "skill" in YOU:
                has_skill = False
                for skill in YOU["skill"]:
                    split = skill.split(",")
                    if you.skills.meets_skill_requirement(split[0], int(split[1])):
                        has_skill = True
                if not has_skill:
                    continue

            if "skill" in CAT:
                has_skill = False
                for skill in CAT["skill"]:
                    split = skill.split(",")
                    if cat.skills.meets_skill_requirement(split[0], int(split[1])):
                        has_skill = True
                if not has_skill:
                    continue

            # SEASON
            if SEASON:
                season = game.clan.current_season.replace("-", "")
                if season.lower() not in SEASON:
                    continue

            # BIOME
            if BIOME:
                biome = game.clan.biome.lower()
                if biome not in BIOME:
                    continue

            # CONNECTED DIALOGUE
            if "~" in talk_key:
                talk_key_split = talk_key.split("~")
                if talk_key_split[0] in cat.connected_dialogue.keys():
                    if int(cat.connected_dialogue[talk_key_split[0]] + 1) != int(talk_key_split[1]):
                        continue
                elif int(talk_key_split[1]) != 1:
                    continue

            # REL
            # Misc
            if REL:
                murdered_them = False
                if you.history:
                    if you.history.murder:
                        if "is_murderer" in you.history.murder:
                            for murder_event in you.history.murder["is_murderer"]:
                                if cat.ID == murder_event.get("victim"):
                                    murdered_them = True
                                    break
                murdered_you = False
                if cat.history:
                    if cat.history.murder:
                        if "is_murderer" in cat.history.murder:
                            for murder_event in cat.history.murder["is_murderer"]:
                                if you.ID == murder_event.get("victim"):
                                    murdered_you = True
                                    break

                if "murderedthem" in REL and not murdered_them:
                    continue
                if "murderedyou" in REL and not murdered_you:
                    continue

                if "non-related" in REL:
                    if cat.ID in you.get_relatives():
                        continue
                if "non-mates" in REL:
                    if you.ID in cat.mates:
                        continue

                # Family tags:
                if any(i in [
                    "from_your_parent", "from_adopted_parent", "adopted_parent", "half_sibling",
                    "littermate", "siblings_mate", "cousin", "adopted_sibling", "parents_siblings",
                    "from_mentor", "from_df_mentor", "from_your_kit", "from_your_apprentice",
                    "from_df_apprentice", "from_mate", "from_parent", "adopted_parent", "from_kit",
                    "sibling", "from_adopted_kit"
                    ] for i in REL):

                    fam = False
                    if "from_mentor" in REL:
                        if you.mentor == cat.ID:
                            fam = True
                    if "from_df_mentor" in REL:
                        if you.df_mentor == cat.ID:
                            fam = True
                    if "from_your_apprentice" in REL:
                        if cat.mentor == you.ID:
                            fam = True
                    if "from_df_apprentice" in REL:
                        if cat.df_mentor == you.ID:
                            fam = True
                    if "from_mate" in REL:
                        if cat.ID in you.mates:
                            fam = True
                    if "from_parent" in REL or "from_your_parent" in REL:
                        if you.parent1:
                            if you.parent1 == cat.ID:
                                fam = True
                        if you.parent2:
                            if you.parent2 == cat.ID:
                                fam = True
                    if "adopted_parent" in REL or "from adopted_parent" in REL or "from_adopted_parent" in REL:
                        if cat.ID in you.inheritance.get_adoptive_parents():
                            fam = True
                    if "from_kit" in REL or "from_your_kit" in REL:
                        if cat.ID in you.inheritance.get_blood_kits():
                            fam = True
                    if "from_adopted_kit" in REL:
                        if cat.ID in you.inheritance.get_not_blood_kits():
                            fam = True
                    if "littermate" in REL:
                        if cat.ID in you.inheritance.get_siblings() and cat.moons == you.moons:
                            fam = True
                    if "sibling" in REL:
                        if cat.ID in you.inheritance.get_siblings():
                            fam = True
                    if "half_sibling" in REL:
                        c_p1 = cat.parent1
                        if not c_p1:
                            c_p1 = "no_parent1_cat"
                        c_p2 = cat.parent2
                        if not c_p2:
                            c_p2 = "no_parent2_cat"
                        y_p1 = you.parent1
                        if not y_p1:
                            y_p1 = "no_parent1_you"
                        y_p2 = you.parent2
                        if not y_p2:
                            y_p2 = "no_parent2_you"
                        if ((c_p1 == y_p1 or c_p1 == y_p2) or\
                            (c_p2 == y_p1 or c_p2 == y_p2)) and not\
                            (c_p1 == y_p1 and c_p2 == y_p2) and not\
                            (c_p2 == y_p1 and c_p1 == y_p2) and not\
                            (c_p1 == y_p2 and c_p2 == y_p1):
                            fam = True
                    if "adopted_sibling" in REL:
                        if cat.ID in you.inheritance.get_no_blood_siblings():
                            fam = True
                    if "parents_siblings" in REL:
                        if cat.ID in you.inheritance.get_parents_siblings():
                            fam = True
                    if "cousin" in REL:
                        if cat.ID in you.inheritance.get_cousins():
                            fam = True
                    if "siblings_mate" in REL:
                        if cat.ID in you.inheritance.get_siblings_mates():
                            fam = True
                    if "they_grandparent" in REL:
                        if cat.is_grandparent(game.clan.your_cat):
                            fam = True
                    if "they_grandchild" in REL:
                        if game.clan.your_cat.is_grandparent(cat):
                            fam = True
                    if not fam:
                        continue

                if "former_mate" in REL and cat.ID not in you.previous_mates:
                    continue

            # MURDER STUFF
            # this is all staying in tags for now
            if game.clan.murdered != {} and game.clan.age - game.clan.murdered["moon"] <= 5:
                # accomplice
                if cat.ID == game.clan.murdered["accomplice"][0]:
                    if "accomplice_agreed" in TAGS and game.clan.murdered["accomplice"][1] is False:
                        continue
                    if "accomplice_refused" in TAGS and game.clan.murdered["accomplice"][1] is True:
                        continue
                    if "not_accomplice" in TAGS:
                        continue
                else:
                    if any(t in TAGS for t in ["accomplice", "accomplice_refused", "accomplice_agreed"]):
                        continue

                # victim
                if cat.ID == game.clan.murdered["victim"][0]:
                    if "murder_victim" in TAGS and cat.ID != game.clan.murdered["victim"]:
                        continue
                    elif "not_murder_victim" in TAGS and cat.ID == game.clan.murdered["victim"]:
                        continue

                # success/fail
                if "murder_success" in TAGS and game.clan.murdered["success"] is False:
                    continue
                if "murder_fail" in TAGS and game.clan.murdered["success"] is True:
                    continue

                # discovered
                if "murder_discovered" in TAGS and game.clan.murdered["discovered"] is False:
                    continue
                if "murder_not_discovered" in TAGS and game.clan.murdered["discovered"] is True:
                    continue


                if any(tag in TAGS for tag in [
                    "accomplice_agreed", "accomplice_refused",
                    "accomplice", "murder_victim",
                    "not_murder_victim", "murder_success",
                    "murder_fail"
                    ]):
                    if game.clan.murdered["murderer"] != game.clan.your_cat.ID:
                        continue
            else:
                if any(tag in TAGS for tag in [
                    "accomplice_agreed", "accomplice_refused",
                    "accomplice", "murder_victim",
                    "not_murder_victim", "murder_success",
                    "murder_fail"
                    ]):
                    continue

            # ---

            if "war" in TAGS:
                if "at_war" in game.clan.war:
                    if not game.clan.war["at_war"]:
                        continue
                else:
                    continue

            if "clan_has_kits" in TAGS:
                clan_has_kits = False
                for c in Cat.all_cats_list:
                    if c.status == "kitten" and not c.dead and not c.outside:
                        clan_has_kits = True
                if not clan_has_kits:
                    continue


            # Relationship conditions
            if REL:
                if you.ID in cat.relationships:
                    # intial relationship stuff
                    # these tags shouldnt be used anymore-- they should be replace with min/max tags
                    # but ill keep these here in case someone goes rogue
                    if cat.relationships[you.ID].dislike < 30 and 'hate' in REL:
                        continue
                    if cat.relationships[you.ID].romantic_love < 15 and 'romantic_like' in REL:
                        continue
                    if cat.relationships[you.ID].platonic_like < 25 and 'platonic_like' in REL:
                        continue
                    if cat.relationships[you.ID].platonic_like < 40 and 'platonic_love' in REL:
                        continue
                    if cat.relationships[you.ID].jealousy < 5 and 'jealousy' in REL:
                        continue
                    if cat.relationships[you.ID].dislike < 20 and 'dislike' in REL:
                        continue
                    if cat.relationships[you.ID].comfortable < 40 and 'comfort' in REL:
                        continue
                    if cat.relationships[you.ID].admiration < 40 and 'respect' in REL:
                        continue
                    if cat.relationships[you.ID].trust < 40 and 'trust' in REL:
                        continue
                    if (cat.relationships[you.ID].platonic_like > 20 or cat.relationships[you.ID].dislike > 20) and "neutral" in REL:
                        continue

                    skip_rel = False
                    for tag in REL:
                        if tag.startswith("min_platonic_"):
                            min_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].platonic_like < min_value:
                                skip_rel = True
                                break
                        elif tag.startswith("max_platonic_"):
                            max_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].platonic_like > max_value:
                                skip_rel = True
                                break

                        if tag.startswith("min_romantic_"):
                            min_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].romantic_love < min_value:
                                skip_rel = True
                                break
                        elif tag.startswith("max_romantic_"):
                            max_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].romantic_love > max_value:
                                skip_rel = True
                                break

                        if tag.startswith("min_dislike_"):
                            min_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].dislike < min_value:
                                skip_rel = True
                                break
                        elif tag.startswith("max_dislike_"):
                            max_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].dislike > max_value:
                                skip_rel = True
                                break

                        if tag.startswith("min_jealousy_"):
                            min_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].jealousy < min_value:
                                skip_rel = True
                                break
                        elif tag.startswith("max_jealousy_"):
                            max_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].jealousy > max_value:
                                skip_rel = True
                                break

                        if tag.startswith("min_trust_"):
                            min_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].trust < min_value:
                                skip_rel = True
                                break
                        elif tag.startswith("max_trust_"):
                            max_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].trust > max_value:
                                skip_rel = True
                                break

                        if tag.startswith("min_comfort_"):
                            min_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].comfortable < min_value:
                                skip_rel = True
                                break
                        elif tag.startswith("max_comfort_"):
                            max_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].comfortable > max_value:
                                skip_rel = True
                                break

                        if tag.startswith("min_respect_"):
                            min_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].admiration < min_value:
                                skip_rel = True
                                break
                        elif tag.startswith("max_respect_"):
                            max_value = int(tag.split("_")[-1])
                            if cat.relationships[you.ID].admiration > max_value:
                                skip_rel = True
                                break
                    if skip_rel:
                        continue
                else:
                    if any(i in [
                        "hate","romantic_like","platonic_like","jealousy",
                        "dislike","comfort","respect","trust"
                        ] for i in REL):
                        continue
                    values = ["platonic", "romantic", "dislike", "jealousy", "comfort", "trust", "respect"]
                    for v in values:
                        for tag in REL:
                            if tag.startswith(f"max_{v}_"):
                                continue
                            if tag.startswith(f"min_{v}_"):
                                continue

            # FOCUS TAGS
            if game.clan.focus and game.clan.focus == "leader" and "focus" in TAGS:
                leader_id = game.clan.leader.ID
                if leader_id not in cat.relationships or cat.ID == leader_id:
                    continue
                if talk_key.startswith("good_opinion") and cat.relationships[leader_id].platonic_like < 30:
                    continue
                if talk_key.startswith("bad_opinion") and cat.relationships[leader_id].dislike < 30:
                    continue

            if game.clan.focus_cat:
                if "you_focuscat" in TAGS and game.clan.focus_cat.ID != game.clan.your_cat.ID:
                    continue
                if "they_focuscat" in TAGS and cat.ID != game.clan.focus_cat.ID:
                    continue
                if game.clan.focus == "unknown_murder":
                    focus_cat = game.clan.focus_cat
                    murdered_them = False
                    if you.history:
                        if you.history.murder:
                            if "is_murderer" in you.history.murder:
                                for murder_event in you.history.murder["is_murderer"]:
                                    if focus_cat.ID == murder_event.get("victim"):
                                        murdered_them = True
                                        break
                                    else:
                                        murdered_them = False
                            else:
                                murdered_them = False
                        else:
                            murdered_them = False
                    else:
                        murdered_them = False

                    if "you_murderer" in TAGS and murdered_them is False:
                        continue
                    if "you_not_murderer" in TAGS and murdered_them:
                        continue

                    # now THEY murderer
                    murdered_them = False
                    if cat.history:
                        if cat.history.murder:
                            if "is_murderer" in cat.history.murder:
                                for murder_event in cat.history.murder["is_murderer"]:
                                    if focus_cat.ID == murder_event.get("victim"):
                                        murdered_them = True
                                        break
                                    else:
                                        murdered_them = False
                            else:
                                murdered_them = False
                        else:
                            murdered_them = False
                    else:
                        murdered_them = False

                    if "they_murderer" in TAGS and murdered_them is False:
                        continue
                    if "they_not_murderer" in TAGS and murdered_them:
                        continue

            # dead moons tags!
            fadedage = game.config["fading"]["age_to_fade"]
            # this is for opacity tagging whenever i wanna do that
            skip_processing = False

            if "dead" in YOU:
                if not self.validate_dead(YOU, you):
                    continue
            else:
                if you.dead:
                    continue

            if "dead" in CAT:
                if not self.validate_dead(CAT, cat):
                    continue
            else:
                if cat.dead:
                    continue

            skip = False
            for item in talk:
                if isinstance(talk[item], list) and item not in ["relationship", "tags"]:
                    # checking the actual spoken dialogue
                    test_text = self.get_adjusted_txt(talk[item], cat)
                    if not test_text:
                        skip = True
                        break
            if skip:
                continue

            texts_list[talk_key] = talk

        return self.choose_text(cat, texts_list)
    
    def validate_dead(self, BLOCK, cat):
        if not cat.dead:
            return False
        if any(t in ["ur", "sc", "df"] for t in BLOCK["dead"]):
            if cat.df and "df" not in BLOCK["dead"]:
                return False
            elif cat.outside and "ur" not in BLOCK["dead"]:
                return False
            elif "sc" not in BLOCK["dead"]:
                return False
        else:
            if "any" not in BLOCK["dead"]:
                return False
        for tag in BLOCK["dead"]:
            if tag.startswith("min_deadfor_"):
                min_value = int(tag.split("_")[-1])
                if cat.dead_for < min_value:
                    return False
            elif tag.startswith("max_deadfor_"):
                max_value = int(tag.split("_")[-1])
                if cat.dead_for > max_value:
                    return False
        return True

    
    # Filter Helpers
    def validate_status(self, BLOCK, cat):
        """
        checks the "status" list
        """

        possible_statuses = [
            "leader", "deputy", "mediator", "queen", "warrior",
            "medicine cat", "newborn", "kitten", "mediator apprentice",
            "apprentice", "medicine cat apprentice", "queen's apprentice", "elder"
        ]

        if f"not_{cat.status}" in BLOCK["status"]:
            return False
        
        if f"not_{cat.status.replace(' ','_')}" in BLOCK["status"]:
            return False

        prev_status_skip = False
        for status in possible_statuses:
            if f"previously_{status}" in BLOCK["status"] and cat.old_status != status:
                prev_status_skip = True
        if prev_status_skip:
            return False

        if "df_trainee" in BLOCK["status"]:
            if not cat.joined_df:
                return False
        if "not_df_trainee" in BLOCK["status"]:
            if cat.joined_df:
                return False

        if "guide" in BLOCK["status"]:
            if cat.ID not in [game.clan.instructor.ID, game.clan.demon.ID]:
                return False

        if any(st in possible_statuses for st in BLOCK["status"]):
            if cat.status not in BLOCK["status"]:
                return False
        return True

    def validate_age(self, BLOCK, cat):
        """ checks the "age" list
        """
        if f"not_{cat.age}" in BLOCK["age"]:
            return False
        if "not_kitten" in BLOCK["age"] and cat.status == "newborn":
            return False

        if cat == game.clan.your_cat:
            if "younger" in BLOCK["age"] and cat.moons >= self.the_cat.moons:
                return False
            if "sameage" in BLOCK["age"] and cat.age != self.the_cat.age:
                return False
            if "older" in BLOCK["age"] and cat.moons <= self.the_cat.moons:
                return False
        else:
            if "younger" in BLOCK["age"] and cat.moons >= game.clan.your_cat.moons:
                return False
            if "sameage" in BLOCK["age"] and cat.age != game.clan.your_cat.age:
                return False
            if "older" in BLOCK["age"] and cat.moons <= game.clan.your_cat.moons:
                return False

        if any(st in [
            "newborn", "kitten", "adolescent", "young adult",
            "adult", "senior adult", "senior"
            ] for st in BLOCK["age"]
            ):
            if cat.age not in BLOCK["age"]:
                return False
        return True

    def validate_conditions(self, CONDITIONS, cat):
        """
        Checks the condition list
        """
        has_condition = False

        if "injury:any" in CONDITIONS and not cat.is_injured():
            return False
        if "illness:any" in CONDITIONS and not cat.is_ill():
            return False
        
        if "injury:none" in CONDITIONS and cat.is_injured():
            return False
        if "illness:none" in CONDITIONS and cat.is_ill():
            return False
        
        # exclusive tags
        if "pregnant" in CONDITIONS and cat.ID not in game.clan.pregnancy_data:
            return False
        if "grief stricken" in CONDITIONS and "grief stricken" not in cat.illnesses:
            return False

        reg_condition_check = False
        has_condition = False
        blind_valid = True
        deaf_valid = True

        # this sucks
        blind_tagged = False
        deaf_tagged = False
        for tag in CONDITIONS:
            if ":" in tag:
                condition_tag = tag.split(":")[0]
                if condition_tag == "blind" and "blind" in cat.permanent_condition:
                    blind_tagged = True
                if condition_tag == "deaf" and "deaf" in cat.permanent_condition:
                    deaf_tagged = True
        if not deaf_tagged:
            deaf_valid = False
        if not blind_tagged:
            blind_valid = False
        #  --

        if not CONDITIONS:
            blind_valid = False
            deaf_valid = False

        for tag in CONDITIONS:
            if isinstance(tag, list):
                # if a tag is a list, all of the conditions in the list
                # must be true for the dialogue to be attainable
                true = 0
                for item in tag:
                    looking_for = item
                    if ":" in item:
                        attributes = item.split(":")
                        looking_for = attributes[0]
                        if looking_for == "injury" and attributes[1] == "any" and cat.is_injured():
                            true += 1
                            continue
                        elif looking_for == "illness" and attributes[1] == "any" and cat.is_ill():
                            true += 1
                            continue
                        else:
                            if looking_for in cat.illnesses:
                                true += 1
                                continue
                            if looking_for in cat.injuries:
                                true += 1
                                continue
                            if looking_for in cat.permanent_condition:
                                true += 1
                                continue

                    else:
                        if looking_for in cat.illnesses:
                            true += 1
                            continue
                        if looking_for in cat.injuries:
                            true += 1
                            continue
                        if looking_for in cat.permanent_condition:
                            true += 1
                            continue
                if true == len(tag):
                    has_condition = True
            else:
                if ":" in tag:
                    # other than x:any and x:none, permanent condition tags are the only ones with colons
                    attributes = tag.split(":")
                    # not:condition
                    if attributes[0] == "not":
                        if attributes[1] in cat.illnesses:
                            return False
                        if attributes[1] in cat.injuries:
                            return False
                        if attributes[1] in cat.permanent_condition:
                            return False

                    elif attributes[0] in PERMANENT:
                        condition_name = attributes[0]
                        born_with = attributes[1] if len(attributes) > 1 else "any"
                        exclusive = attributes[2] if len(attributes) > 2 else "false"
                        if condition_name in cat.permanent_condition:
                            if "born_with" in cat.permanent_condition[condition_name]:
                                if cat.permanent_condition[condition_name]["born_with"] is False and born_with == "true":
                                    if condition_name == "blind":
                                        blind_valid = False
                                    if condition_name == "deaf":
                                        deaf_valid = False
                                elif cat.permanent_condition[condition_name]["born_with"] is True and born_with == "false":
                                    if condition_name == "blind":
                                        blind_valid = False
                                    if condition_name == "deaf":
                                        deaf_valid = False
                        else:
                            if exclusive == "true":
                                if condition_name == "blind":
                                    blind_valid = False
                                    return False
                                if condition_name == "deaf":
                                    deaf_valid = False
                                    return False
                                return False
                else:
                    reg_condition_check = True
                    # regular conditions
                    if tag in INJURIES:
                        if tag in cat.injuries:
                            has_condition = True
                    elif tag in ILLNESSES:
                        if tag in cat.illnesses:
                            has_condition = True
                    elif tag in PERMANENT and tag not in ["deaf", "blind"]:
                        if tag in cat.permanent_condition:
                            has_condition = True
                    elif tag == "hearing":
                        if "deaf" in cat.permanent_condition:
                            return False

        if "blind" in cat.permanent_condition and not blind_valid:
            return False
        if "deaf" in cat.permanent_condition and not deaf_valid:
            return False

        if reg_condition_check and not has_condition:
            return False

        return True

    def load_and_replace_placeholders(self, file_path, cat, you):
        with open(file_path, 'r') as read_file:
            possible_texts = ujson.loads(read_file.read())

            y_c_text = f"y_c: {you.status} "
            t_c_text = f"t_c: {cat.status} "

            cat_cluster_1, cat_cluster_2 = get_cluster(cat.personality.trait)
            you_cluster_1, you_cluster_2 = get_cluster(you.personality.trait)
            clusters_1 = f"{you_cluster_1}, {you_cluster_2}" if you_cluster_2 else f"{you_cluster_1}"
            clusters_2 = f"{cat_cluster_1}, {cat_cluster_2}" if cat_cluster_2 else f"{cat_cluster_1}"

            y_c_text += clusters_1
            t_c_text += clusters_2

            add_on_map = {
                (True, True, False): " df",
                (True, True, True): " df",
                (True, False, False): " sc",
                (True, False, True): " ur"
            }
            add_on = add_on_map.get((you.dead, you.df, you.outside), "")
            if "grief stricken" in you.illnesses:
                add_on += " g"
            if you.shunned > 0:
                add_on += " sh"
            if "blind" in you.permanent_condition:
                add_on += " b"
            if "deaf" in you.permanent_condition:
                add_on += " d"
            y_c_text += add_on
            add_on2 = add_on_map.get((cat.dead, cat.df, cat.outside), "")
            if "grief stricken" in cat.illnesses:
                add_on2 += " g"
            if cat.shunned > 0:
                add_on2 += " sh"
            if "blind" in cat.permanent_condition:
                add_on2 += " b"
            if "deaf" in cat.permanent_condition:
                add_on2 += " d"
            t_c_text += add_on2
            possible_texts['general']["intro"][0] += f" {VERSION_NAME} {(game.switches['talk_category']).upper()}"
            possible_texts['general']["intro"][0] += "\n"
            possible_texts['general']["intro"][0] += y_c_text + f" {you.moons}"
            possible_texts['general']["intro"][0] += "\n"
            possible_texts['general']["intro"][0] += t_c_text + f" {cat.moons}"
            possible_texts['general']["intro"][0] += "\n"

        return possible_texts['general']

    def choose_text(self, cat, texts_list):
        MAX_RETRIES = 30
        you = game.clan.your_cat

        if len(game.clan.talks) > 100:
            game.clan.talks.clear()

        weights = []
        if not texts_list:
            texts_list['general'] = self.load_and_replace_placeholders(f"{self.resource_dir}general.json", cat, you)
            weights = [1]
        else:
            # Assign weights based on tags
            weighted_tags = [
                "you_pregnant", "they_pregnant", "from_mentor", "from_your_parent",
                "from_adopted_parent", "adopted_parent", "half sibling", "littermate",
                "siblings_mate", "cousin", "adopted_sibling", "parents_siblings",
                "from_df_mentor", "from_your_kit", "from_your_apprentice",
                "from_df_apprentice", "from_mate", "from_parent", "adopted_parent",
                "from_kit", "sibling", "from_adopted_kit", "they_injured", "they_ill",
                "you_injured", "you_ill", "you_grieving", "they_grieving", "you_forgiven",
                "they_forgiven", "murderedyou", "murderedthem"
            ] # List of tags that increase the weight

            special_date = get_special_date()
            if special_date:
                weighted_tags.append(special_date)

            # print("------")
            for dialogue_id, item in texts_list.items():
                tags = item["tags"] if "tags" in item else {}
                weight = 1
                if any(tag in weighted_tags for tag in tags):
                    weight += 3
                if "focus" in tags or "connected" in tags:
                    weight += 6

                # im gonna attempt to up the weight for dialogue with a lot of constraints
                # like scribble just did in clangen for shortevents
                # but, of course, worse
                for constraint in item:
                    if constraint.endswith("inventory_changes"):
                        break
                    if constraint not in ["y_c", "t_c", "relationship", "tags", "season"]:
                        continue
                    for tag in item[constraint]:
                        weight += 2
                # print(dialogue_id + ": ", weight)

                weights.append(weight)

        # Check for debug mode
        if game.config.get("debug_ensure_dialogue") in texts_list:
            text_chosen_key = game.config["debug_ensure_dialogue"]
            text = texts_list[text_chosen_key]["intro"] if "intro" in texts_list[text_chosen_key] else texts_list[text_chosen_key][1]
            new_text = self.get_adjusted_txt(text, cat)
            if new_text:
                self.display_intro(cat, texts_list, text_chosen_key)
                if "intro" in texts_list[text_chosen_key]:
                    self.text_type = "choices"
                if "~" in text_chosen_key:
                    text_chosen_key_split = text_chosen_key.split("~")
                    cat.connected_dialogue[text_chosen_key_split[0]] = int(text_chosen_key_split[1])
                print("Debug:", text_chosen_key)
                return new_text
            print("Could not find debug ensure dialogue '" + game.config["debug_ensure_dialogue"] + "' within possible dialogues")
        elif game.config["debug_ensure_dialogue"]:
            print("Could not find debug ensure dialogue '" + game.config["debug_ensure_dialogue"] + "' within possible dialogues")

        # Try to find a valid, unused text
        for _ in range(MAX_RETRIES):
            if len(list(texts_list.keys())) == len(weights) and list(_accumulate(weights))[-1] + 0.0 > 0:
                text_chosen_key = choices(list(texts_list.keys()), weights=weights)[0]
            else:
                text_chosen_key = choice(list(texts_list.keys()))
            text = texts_list[text_chosen_key]["intro"] if "intro" in texts_list[text_chosen_key] else texts_list[text_chosen_key][1]
            new_text = self.get_adjusted_txt(text, cat)
            
            if "intro" in texts_list[text_chosen_key]:
                for choice_key, choice_text in texts_list[text_chosen_key].items():
                    if isinstance(choice_text, list) and choice_key != "tags":
                        choice_text = new_text
                        if not choice_text:
                            new_text = ""
                            break
            
            if text_chosen_key not in game.clan.talks and new_text:
                game.clan.talks.append(text_chosen_key)
                if "intro" in texts_list[text_chosen_key]:
                    self.text_type = "choices"
                    self.display_intro(cat, texts_list, text_chosen_key)
                if "~" in text_chosen_key:
                    text_chosen_key_split = text_chosen_key.split("~")
                    cat.connected_dialogue[text_chosen_key_split[0]] = int(text_chosen_key_split[1])
                # print("CHOSE:", text_chosen_key)
                return new_text

        # If no valid text found, choose one based on tag weights
        weights = []
        for item in texts_list.values():
            tags = item["tags"] if "tags" in item else []
            weights.append(len(tags))
        
        if len(list(texts_list.keys())) == len(weights) and list(_accumulate(weights))[-1] + 0.0 > 0:
                text_chosen_key = choices(list(texts_list.keys()), weights=weights)[0]
        else:
            text_chosen_key = choice(list(texts_list.keys()))
        text = texts_list[text_chosen_key]["intro"] if "intro" in texts_list[text_chosen_key] else texts_list[text_chosen_key][1]
        if text is None:
            text = self.load_and_replace_placeholders(f"{self.resource_dir}general.json", cat, you)[1]
        
        new_text = self.get_adjusted_txt(text, cat)
        for _ in range(MAX_RETRIES):
            if new_text:
                break
            if len(list(texts_list.keys())) == len(weights) and list(_accumulate(weights))[-1] + 0.0 > 0:
                text_chosen_key = choices(list(texts_list.keys()), weights=weights)[0]
            else:
                text_chosen_key = choice(list(texts_list.keys()))
            text = texts_list[text_chosen_key]["intro"] if "intro" in texts_list[text_chosen_key] else texts_list[text_chosen_key][1]
            new_text = self.get_adjusted_txt(text, cat)
        else:
            text = self.load_and_replace_placeholders(f"{self.resource_dir}general.json", cat, you)[1]
            new_text = self.get_adjusted_txt(text, cat)

        if "~" in text_chosen_key:
            text_chosen_key_split = text_chosen_key.split("~")
            cat.connected_dialogue[text_chosen_key_split[0]] = int(text_chosen_key_split[1])
        game.clan.talks.append(text_chosen_key)

        return new_text
    
    def get_speaking_cat(self, text_string):
        """ gets the current cat speaking for multi-character dialogue """
        if "|" in text_string:
            fragments = text_string.split("|")
            if fragments[1] in self.cat_dict:
                cat = self.cat_dict[fragments[1]]
            else:
                self.get_adjusted_txt([fragments[1]], self.the_cat)
                if fragments[1] in self.cat_dict:
                    cat = self.cat_dict[fragments[1]]
                else:
                    cat = self.the_cat
        else:
            cat = self.the_cat
        return text_string, cat

    def get_adjusted_txt(self, text, cat):
        you = game.clan.your_cat
        for i in range(len(text)):
            text[i] = lifegen_text_adjust(Cat, text[i], cat, self.cat_dict, r_c_allowed=True, o_c_allowed=True)
            if text[i] == "":
                return ""
        # for item in self.cat_dict.items():
            # print("final", item[0], ":", item[1].name)

        process_text_dict = self.cat_dict.copy()

        for abbrev in process_text_dict.keys():
            abbrev_cat = process_text_dict[abbrev]
            process_text_dict[abbrev] = (abbrev_cat, choice(abbrev_cat.pronouns))

        process_text_dict["y_c"] = (game.clan.your_cat, choice(game.clan.your_cat.pronouns))
        process_text_dict["t_c"] = (cat, choice(cat.pronouns))

        for i in range(len(text)):
            text[i] = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), text[i])
        
        text = [t1.replace("c_n", game.clan.name + "Clan") for t1 in text]
        text = [t1.replace("y_c", str(you.name)) for t1 in text]
        text = [t1.replace("t_c", str(cat.name)) for t1 in text]

        return text

    def get_living_cats(self):
        living_cats = []
        for the_cat in Cat.all_cats_list:
            if not the_cat.dead and not the_cat.outside and not the_cat.moons == -1:
                living_cats.append(the_cat)
        return living_cats

    

    def backstory_text(self, cat):
        with open(f"resources/dicts/backstories.json", 'r') as read_file:
            BACKSTORIES = ujson.loads(read_file.read())

        backstory = cat.backstory
        if backstory is None:
            return ''
        bs_category = None

        for category in BACKSTORIES["backstory_categories"]:
            if backstory in BACKSTORIES["backstory_categories"][category]:
                bs_category = category
                break
        if bs_category is not None:
            bs_display = BACKSTORIES["backstory_display"][bs_category]
        else:
            bs_display = None
            print("ERROR: Backstory category was not found.")
        if not bs_display:
            return "clanfounder"
        return bs_display

    def is_flirt_success(self, cat):
        cat_relationships = cat.relationships.get(game.clan.your_cat.ID)
        chance = 40
        if cat_relationships:
            if cat_relationships.romantic_love > 10:
                chance += 50
            if cat_relationships.platonic_like > 10:
                chance += 20
            if cat_relationships.comfortable > 10:
                chance += 20
            if cat_relationships.admiration > 10:
                chance += 20
            if cat_relationships.dislike > 10:
                chance -= 30
            r = randint(1,100) < chance
            if r:
                return True
            else:
                return False
        else:
            return False
