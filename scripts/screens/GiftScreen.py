import pygame.transform
import pygame_gui.elements
from random import choice, randint
import ujson
import math
import re

from .Screens import Screens
from scripts.utility import get_text_box_theme, scale, get_cluster, pronoun_repl
from scripts.cat.cats import Cat
from scripts.game_structure import image_cache
from scripts.game_structure.game_essentials import game, screen, screen_x, screen_y, MANAGER
from scripts.game_structure.ui_elements import UIImageButton, UISpriteButton
from scripts.cat.sprites import sprites

with open(f"resources/dicts/acc_display.json", "r") as read_file:
    ACC_DISPLAY = ujson.loads(read_file.read())

with open(f"resources/dicts/events/lifegen_events/gift.json", "r") as read_file:
    ACC_REACTION_TXT = ujson.loads(read_file.read())

with open(f"resources/dicts/accessory_preferences.json", "r") as read_file:
    ACC_REACTION = ujson.loads(read_file.read())

class GiftScreen(Screens):
    selected_cat = None
    current_page = 1
    list_frame = pygame.transform.scale(image_cache.load_image("resources/images/choosing_frame.png").convert_alpha(),
                                        (1300 / 1600 * screen_x, 452 / 1400 * screen_y))
    apprentice_details = {}
    selected_details = {}
    selected_acc_details = {}
    cat_list_buttons = {}
    stage = 'choose gift cat'

    def __init__(self, name=None):
        super().__init__(name)
        self.list_page = None
        self.next_cat = None
        self.previous_cat = None
        self.next_page_button = None
        self.previous_page_button = None
        self.select_button = None
        self.gift_again_button = None
        self.back_button = None
        self.next_cat_button = None
        self.previous_cat_button = None
        self.mentor_frame = None
        self.reaction_box = None
        self.reaction_icon = None
        self.reaction_text = None
        self.reaction = None
        self.info = None
        self.heading = None
        self.mentor = None
        self.the_cat = None
        self.next = None
        self.screen_art = None
        self.page = 0
        self.max_pages = 1
        self.search_bar_image = None
        self.search_bar = None
        self.previous_page_button = None
        self.next_page_button = None
        self.accessory_tab_button = None
        self.previous_search_text = "search"
        self.cat_list_buttons = {}
        self.search_inventory = []
        self.accessory_buttons = {}
        self.selected_accessory = None
        self.cat_sprite = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            if event.ui_element in self.cat_list_buttons.values():
                self.selected_cat = event.ui_element.return_cat_object()
                self.update_selected_cat()

            elif event.ui_element in self.accessory_buttons.values():
                self.selected_accessory = event.ui_element
                self.update_selected_accessory()

            elif event.ui_element == self.select_button and self.selected_cat and self.stage == 'choose gift cat':
                if not self.selected_cat.dead:
                    self.exit_screen()
                    self.stage = 'choose gift'
                    self.screen_switches()
                    self.update_selected_cat()

            elif event.ui_element == self.select_button and self.selected_accessory and self.stage == 'choose gift':
                self.exit_screen()
                self.stage = 'gift reaction'
                self.screen_switches()
                self.update_selected_cat()

            elif event.ui_element == self.back_button:
                self.change_screen('profile screen')
                self.stage = 'choose gift cat'
            elif event.ui_element == self.gift_again_button and self.stage == 'gift reaction':
                self.exit_screen()
                self.stage = 'choose gift cat'
                self.screen_switches()
                self.selected_cat = None
                self.selected_accessory = None
                self.cat_sprite = None

            elif event.ui_element == self.next_cat_button:
                if isinstance(Cat.fetch_cat(self.next_cat), Cat):
                    game.switches['cat'] = self.next_cat
                    self.update_cat_list()
                    self.update_selected_cat()
                else:
                    print("invalid next cat", self.next_cat)
            elif event.ui_element == self.previous_cat_button:
                if isinstance(Cat.fetch_cat(self.previous_cat), Cat):
                    game.switches['cat'] = self.previous_cat
                    self.update_cat_list()
                    self.update_selected_cat()
                else:
                    print("invalid previous cat", self.previous_cat)
            elif event.ui_element == self.next_page_button:
                if self.stage == "choose gift cat":
                    self.current_page += 1
                    self.update_cat_list()
                    self.update_selected_cat()
                elif self.stage == "choose gift":
                    self.page += 1

                    if self.page == 0 and self.max_pages in [0, 1]:
                        self.previous_page_button.disable()
                        self.next_page_button.disable()
                    elif self.page == 0:
                        self.previous_page_button.disable()
                        self.next_page_button.enable()
                    elif self.page == self.max_pages - 1:
                        self.previous_page_button.enable()
                        self.next_page_button.disable()
                    else:
                        self.previous_page_button.enable()
                        self.next_page_button.enable()
                    for i in self.cat_list_buttons:
                        self.cat_list_buttons[i].kill()
                    for i in self.accessory_buttons:
                        self.accessory_buttons[i].kill()
                    self.update_accessory_list()
            elif event.ui_element == self.previous_page_button:
                if self.stage == "choose gift cat":
                    self.current_page -= 1
                    self.update_cat_list()

                elif self.stage == "choose gift":
                    self.page -= 1
                    if self.page == 0 and self.max_pages in [0, 1]:
                        self.previous_page_button.disable()
                        self.next_page_button.disable()
                    elif self.page == 0:
                        self.previous_page_button.disable()
                        self.next_page_button.enable()
                    elif self.page == self.max_pages - 1:
                        self.previous_page_button.enable()
                        self.next_page_button.disable()
                    else:
                        self.previous_page_button.enable()
                        self.next_page_button.enable()
                    for i in self.cat_list_buttons:
                        self.cat_list_buttons[i].kill()
                    for i in self.accessory_buttons:
                        self.accessory_buttons[i].kill()
                    self.update_accessory_list()

    def screen_switches(self):

        if self.stage == 'choose gift cat':
            self.the_cat = game.clan.your_cat
            self.selected_cat = None
            self.selected_accessory = None
            self.screen_art = None
            self.reaction_text = None
            self.reaction = None
            self.reaction_icon = None

            self.heading = pygame_gui.elements.UITextBox(
                "Choose who to gift",
                scale(pygame.Rect((300, 50), (1000, 80))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER
            )
            self.mentor_frame = pygame_gui.elements.UIImage(
                scale(pygame.Rect((180, 180), (344, 399))),
                pygame.transform.scale(
                image_cache.load_image(
                "resources/images/gift_frame.png").convert_alpha(),
                (569, 399)), manager=MANAGER
            )

            self.reaction_box = pygame_gui.elements.UIImage(
                scale(pygame.Rect((560, 490), (500, 150))),
                pygame.transform.scale(
                image_cache.load_image(
                "resources/images/gift_reaction_frame.png").convert_alpha(),
                (569, 399)),
                manager=MANAGER
                )
            
            self.screen_art = pygame_gui.elements.UIImage(
                scale(pygame.Rect((1100, 190), (340, 394))),
                pygame.transform.scale(
                image_cache.load_image(
                "resources/images/gift_artwork.png").convert_alpha(),
                (569, 399)),
                manager=MANAGER
                )

            self.back_button = UIImageButton(
                scale(pygame.Rect((50, 1290), (210, 60))),
                "",
                object_id="#back_button"
            )
            self.select_button = UIImageButton(
                scale(pygame.Rect((250, 610), (208, 52))),
                "",
                object_id="#gift_select_button"
            )
            self.gift_again_button = UIImageButton(
                scale(pygame.Rect((1160, 610), (208, 52))),
                "",
                object_id="#gift_again_button"
            )

            self.previous_page_button = UIImageButton(
                scale(pygame.Rect((630, 1155), (68, 68))),
                "",
                object_id="#relation_list_previous",
                manager=MANAGER
            )
            self.next_page_button = UIImageButton(
                scale(pygame.Rect((902, 1155), (68, 68))),
                "",
                object_id="#relation_list_next",
                manager=MANAGER
            )

            self.update_selected_cat()  # Updates the image and details of selected cat
            self.update_cat_list()
            self.gift_again_button.disable()
        elif self.stage == "choose gift":
            self.selected_accessory = None
            self.the_cat = game.clan.your_cat
            self.screen_art = None
            self.reaction_text = None
            self.reaction = None
            self.reaction_icon = None

            self.heading = pygame_gui.elements.UITextBox(
                "Choose what to gift",
                scale(pygame.Rect((300, 50), (1000, 80))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER
            )

            # Layout Images:
            self.mentor_frame = pygame_gui.elements.UIImage(
                scale(pygame.Rect((180, 180), (344, 399))),
                pygame.transform.scale(
                image_cache.load_image(
                "resources/images/gift_frame.png").convert_alpha(),
                (569, 399)), manager=MANAGER
            )

            self.reaction_box = pygame_gui.elements.UIImage(
                scale(pygame.Rect((560, 490), (500, 150))),
                pygame.transform.scale(
                image_cache.load_image(
                "resources/images/gift_reaction_frame.png").convert_alpha(),
                (569, 399)), manager=MANAGER
            )
            self.screen_art = pygame_gui.elements.UIImage(
                scale(pygame.Rect((1100, 190), (340, 394))),
                pygame.transform.scale(
                image_cache.load_image(
                "resources/images/gift_artwork.png").convert_alpha(),
                (569, 399)),
                manager=MANAGER
            )
            self.back_button = UIImageButton(
                scale(pygame.Rect((50, 1290), (210, 60))),
                "",
                object_id="#back_button"
            )
            self.select_button = UIImageButton(
                scale(pygame.Rect((250, 610), (208, 52))),
                "",
                object_id="#give_gift_button"
            )
            self.gift_again_button = UIImageButton(
                scale(pygame.Rect((1160, 610), (208, 52))),
                "",
                object_id="#gift_again_button"
            )
            self.previous_page_button = UIImageButton(
                scale(pygame.Rect((630, 1155), (68, 68))),
                "",
                object_id="#relation_list_previous",
                manager=MANAGER
            )
            self.next_page_button = UIImageButton(
                scale(pygame.Rect((902, 1155), (68, 68))),
                "",
                object_id="#relation_list_next",
                manager=MANAGER
            )
            self.search_bar_image = pygame_gui.elements.UIImage(
                scale(pygame.Rect((219, 680), (236, 68))),
                pygame.image.load(
                "resources/images/search_bar.png").convert_alpha(),
                manager=MANAGER
            )
            self.search_bar = pygame_gui.elements.UITextEntryLine(
                scale(pygame.Rect((239, 685), (205, 55))),
                object_id="#search_entry_box",
                initial_text="search",
                manager=MANAGER
            )

            self.update_selected_cat() # Updates the image and details of selected cat
            self.update_selected_accessory()  
            self.update_accessory_list()
            self.gift_again_button.disable()
        elif self.stage == "gift reaction":
            self.the_cat = game.clan.your_cat

            self.heading = pygame_gui.elements.UITextBox(
                "Choose what to gift",
                scale(pygame.Rect((300, 50), (1000, 80))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
                manager=MANAGER
            )

            self.mentor_frame = pygame_gui.elements.UIImage(
                scale(pygame.Rect((180, 180), (344, 399))),
                pygame.transform.scale(
                image_cache.load_image(
                "resources/images/gift_frame.png").convert_alpha(),
                (569, 399)), manager=MANAGER
            )
            self.screen_art = pygame_gui.elements.UIImage(
                scale(pygame.Rect((1100, 190), (340, 394))),
                pygame.transform.scale(
                image_cache.load_image(
                "resources/images/gift_artwork.png").convert_alpha(),
                (569, 399)),
                manager=MANAGER
            )

            reaction_txt, reaction, acc = self.gift_acc()

            self.reaction_text = pygame_gui.elements.UITextBox(
                self.adjust_txt(reaction_txt),
                scale(pygame.Rect((580, 500), (460, 120))),
                object_id=get_text_box_theme("#text_box_22_horizcenter_vertcenter_spacing_95"),
                manager=MANAGER
            )

            icon_png = ""
            pos = False
            neutral = False
            neg = False

            if reaction in ["accept_like", "accept_favourite"]:
                icon_png = "giftreaction_pos"
                pos = True
            elif reaction in ["accept_neutral", "already_have"]:
                icon_png = "giftreaction_neutral"
                neutral = True
            elif reaction in ["accept_dislike"]:
                icon_png = "giftreaction_neg"
                neg = True

            result = self.get_reaction_display(pos, neutral, neg)

            self.reaction_icon = pygame_gui.elements.UIImage(
                scale(pygame.Rect((650, 655), (40, 40))),
                pygame.transform.scale(
                image_cache.load_image(
                f"resources/images/{icon_png}.png").convert_alpha(),
                (569, 399)), manager=MANAGER
            )

            self.reaction = pygame_gui.elements.UITextBox(result,
                scale(pygame.Rect((700, 650), (460, 50))),
                object_id=get_text_box_theme("#text_box_22_horizleft"),
                manager=MANAGER
            )

            self.reaction_box = pygame_gui.elements.UIImage(
                scale(pygame.Rect((560, 490), (500, 150))),
                pygame.transform.scale(
                image_cache.load_image(
                "resources/images/gift_reaction_frame.png").convert_alpha(),
                (569, 399)), manager=MANAGER
            )

            self.back_button = UIImageButton(
                scale(pygame.Rect((50, 1290), (210, 60))),
                "",
                object_id="#back_button"
            )
            self.select_button = UIImageButton(
                scale(pygame.Rect((250, 610), (208, 52))),
                "",
                object_id="#give_gift_button"
            )
            self.gift_again_button = UIImageButton(
                scale(pygame.Rect((1160, 610), (208, 52))),
                "",
                object_id="#gift_again_button"
            )
            self.previous_page_button = UIImageButton(
                scale(pygame.Rect((630, 1155), (68, 68))),
                "",
                object_id="#relation_list_previous", manager=MANAGER
            )
            self.next_page_button = UIImageButton(
                scale(pygame.Rect((902, 1155), (68, 68))),
                "",
                object_id="#relation_list_next",
                manager=MANAGER
            )
            self.search_bar_image = pygame_gui.elements.UIImage(
                scale(pygame.Rect((219, 680), (236, 68))),
                pygame.image.load(
                "resources/images/search_bar.png").convert_alpha(),
                manager=MANAGER
            )
            self.search_bar = pygame_gui.elements.UITextEntryLine(
                scale(pygame.Rect((239, 685), (205, 55))),
                object_id="#search_entry_box",
                initial_text="search",
                manager=MANAGER
            )

            self.update_selected_accessory()
            self.select_button.disable()
            self.gift_again_button.enable()

    def exit_screen(self):
        # self.selected_accessory = None
        self.previous_search_text = "search"

        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        for ele in self.apprentice_details:
            self.apprentice_details[ele].kill()
        self.apprentice_details = {}

        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}

        for ele in self.selected_acc_details:
            self.selected_acc_details[ele].kill()
        self.selected_acc_details = {}

        for ele in self.accessory_buttons:
            self.accessory_buttons[ele].kill()
        self.accessory_buttons = {}

        if self.heading:
            self.heading.kill()
            del self.heading

        if self.screen_art:
            self.screen_art.kill()
            del self.screen_art

        if self.mentor_frame:
            self.mentor_frame.kill()
            del self.mentor_frame

        if self.reaction_box:
            self.reaction_box.kill()
            del self.reaction_box

        if self.reaction_icon:
            self.reaction_icon.kill()
            del self.reaction_icon

        if self.reaction_text:
            self.reaction_text.kill()
            del self.reaction_text

        if self.reaction:
            self.reaction.kill()
            del self.reaction

        if self.back_button:
            self.back_button.kill()
            del self.back_button

        if self.select_button:
            self.select_button.kill()
            del self.select_button

        if self.gift_again_button:
            self.gift_again_button.kill()
            del self.gift_again_button

        if self.previous_page_button:
            self.previous_page_button.kill()
            del self.previous_page_button

        if self.next_page_button:
            self.next_page_button.kill()
            del self.next_page_button

        if self.search_bar_image:
            self.search_bar_image.kill()

        if self.search_bar:
            self.search_bar.kill()

        if self.next:
            self.next.kill()
            del self.next

    def find_next_previous_cats(self):
        """Determines where the previous and next buttons lead"""
        is_instructor = False
        if self.the_cat.dead and game.clan.instructor.ID == self.the_cat.ID:
            is_instructor = True

        self.previous_cat = 0
        self.next_cat = 0
        if self.the_cat.dead and not is_instructor and not self.the_cat.df:
            self.previous_cat = game.clan.instructor.ID

        if is_instructor:
            self.next_cat = 1

        for check_cat in Cat.all_cats_list:
            if check_cat.ID == self.the_cat.ID:
                self.next_cat = 1

            if self.next_cat == 0 and check_cat.ID != self.the_cat.ID and\
                check_cat.dead == self.the_cat.dead and check_cat.ID != game.clan.instructor.ID and\
                    not check_cat.exiled and check_cat.status in\
                    ["apprentice", "medicine cat apprentice", "mediator apprentice", "queen's apprentice"]\
                    and check_cat.df == self.the_cat.df:
                self.previous_cat = check_cat.ID

            elif self.next_cat == 1 and check_cat.ID != self.the_cat.ID and check_cat.dead == self.the_cat.dead and \
                    check_cat.ID != game.clan.instructor.ID and not check_cat.exiled and check_cat.status in \
                    ["apprentice", "medicine cat apprentice", "mediator apprentice", "queen's apprentice"] \
                    and check_cat.df == self.the_cat.df:
                self.next_cat = check_cat.ID

            elif int(self.next_cat) > 1:
                break

        if self.next_cat == 1:
            self.next_cat = 0

    def relationship_changes(self, reaction):
        """Handles changing the cats' feelings towards you depending on their reaction to the gift. """
        cat = self.selected_cat
        you = game.clan.your_cat
        neutral = False
        pos = False
        neg = False

        if game.clan.your_cat.ID not in self.selected_cat.relationships:
            cat.ID.create_one_relationship(you.ID)
            if reaction == "already_have":
                cat.relationships(you.ID).platonic_like += randint(0,5)
                neutral = True
            elif reaction == "accept_like":
                cat.relationships(you.ID).platonic_like += randint(3,10)
                pos = True
            elif reaction == "accept_dislike":
                cat.relationships(you.ID).dislike += randint(3,8)
                neg = True
            elif reaction == "accept_neutral":
                neutral = True
            elif reaction == "accept_favourite":
                pos = True
                cat.relationships(you.ID).platonic_like += randint(10,30)

    def get_reaction_display(self, pos, neutral, neg):
        """ Display text for relationship changes """
        output = ""
        if pos:
            output = "Gained platonic like!"
        elif neutral:
            output = "Feelings unchanged."
        elif neg:
            output = "Gained dislike!"

        return output
            

    def gift_acc(self):
        """ Gives the accessory! """
        acc = self.selected_accessory.tool_tip_text
        cluster1, cluster2 = get_cluster(self.selected_cat.personality.trait)
        reaction_txt = ""
        if cluster1 and cluster2:
            cluster = choice([cluster1, cluster2])
        else:
            cluster = cluster1

        reaction = "accept_neutral"
        if acc in self.selected_cat.pelt.inventory:
            reaction = "already_have"
        elif acc in ACC_REACTION[cluster1]["like"] or (cluster2 and acc in ACC_REACTION[cluster2]["like"]):
            reaction = "accept_like"
        elif acc in ACC_REACTION[cluster1]["dislike"] or (cluster2 and acc in ACC_REACTION[cluster2]["dislike"]):
            reaction = "accept_dislike"

        if self.selected_cat.personality.trait in ACC_REACTION["favourites"]:
            if acc in ACC_REACTION["favourites"][self.selected_cat.personality.trait]:
                reaction = "accept_favourite"

        if reaction != "already_have":
            game.clan.your_cat.pelt.inventory.remove(acc)
            if acc in game.clan.your_cat.pelt.accessories:
                game.clan.your_cat.pelt.accessories.remove(acc)
            if acc == game.clan.your_cat.pelt.accessory:
                game.clan.your_cat.pelt.accessory = None
            self.selected_cat.pelt.inventory.append(acc)
            if (acc in ACC_REACTION[cluster1]["like"] or (cluster2 and acc in ACC_REACTION[cluster2]["like"])) or reaction == "accept_favourite":
                if len(self.selected_cat.pelt.accessories) <= 4:
                    self.selected_cat.pelt.accessories.append(acc)
                    self.update_selected_cat()

        if acc in ACC_REACTION_TXT["unique_gifts"].keys() and reaction in ACC_REACTION_TXT["unique_gifts"][acc].keys():
            reaction_txt = ACC_REACTION_TXT["unique_gifts"][acc][reaction]
        else:
            reaction_txt = choice(ACC_REACTION_TXT["general"][reaction] + ACC_REACTION_TXT[cluster][reaction])

        return reaction_txt, reaction, acc

    def adjust_txt(self, txt):
        process_text_dict = {}

        process_text_dict["y_c"] = (game.clan.your_cat, choice(game.clan.your_cat.pronouns))
        process_text_dict["t_c"] = (self.selected_cat, choice(self.selected_cat.pronouns))

        txt = re.sub(r"\{(.*?)\}", lambda x: pronoun_repl(x, process_text_dict, False), txt)

        txt = txt.replace("y_c", str(game.clan.your_cat.name))
        txt = txt.replace("t_c", str(self.selected_cat.name))
        txt = txt.replace("y_g", str(ACC_DISPLAY[self.selected_accessory.tool_tip_text]["default"]))
        return txt

    def update_selected_cat(self):
        """Updates the image and information on the currently selected cat"""
        for ele in self.selected_details:
            self.selected_details[ele].kill()
        self.selected_details = {}
        if self.selected_cat:

            self.selected_details["selected_image"] = pygame_gui.elements.UIImage(
                scale(pygame.Rect((565, 195), (270, 270))),
                pygame.transform.scale(
                self.selected_cat.sprite,
                (270, 270)), manager=MANAGER
            )

            info = self.selected_cat.status + "\n" + \
                self.selected_cat.genderalign + "\n" + self.selected_cat.personality.trait + "\n"

            if self.selected_cat.moons < 1:
                info += "???"
            else:
                info += self.selected_cat.skills.skill_string(short=True)

            self.selected_details["selected_info"] = pygame_gui.elements.UITextBox(
                info,
                scale(pygame.Rect((860, 225),(210, 250))),
                object_id=get_text_box_theme("#text_box_22_horizleft"),
                manager=MANAGER
            )

            name = str(self.selected_cat.name)  # get name
            if 45 <= len(name):  # check name length
                short_name = str(name)[0:9]
                name = short_name + '...'

            self.selected_details["cat_name"] = pygame_gui.elements.UITextBox(
                name,
                scale(pygame.Rect((300, 130), (1000, 80))),
                object_id=get_text_box_theme("#text_box_34_horizcenter"),
            )


    def update_selected_accessory(self):
        """Updates the image and information on the currently selected accessory"""
        for ele in self.selected_acc_details:
            self.selected_acc_details[ele].kill()

        self.selected_acc_details = {}
        if self.selected_accessory:
            cat = game.clan.your_cat
            accessory = self.selected_accessory.tool_tip_text

            dimensions = [300,300]

            x_pos = 202
            y_pos = 258

            if accessory in cat.pelt.plant_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_herbs' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.wild_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_wild' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.collars:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['collars' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.flower_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_flower' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.plant2_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_plant2' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.snake_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_snake' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.smallAnimal_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_smallAnimal' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.deadInsect_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_deadInsect' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.aliveInsect_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_aliveInsect' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.fruit_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_fruit' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.crafted_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_crafted' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.tail2_accessories:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['acc_tail2' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)
            elif accessory in cat.pelt.np_autism:
                self.selected_acc_details["selected_image"] = pygame_gui.elements.UIImage(scale(pygame.Rect((x_pos, y_pos), (dimensions))), pygame.transform.scale(sprites.sprites['np_autism' + accessory + self.cat_sprite], (dimensions)), manager=MANAGER)

            info = ""
            if self.selected_accessory.tool_tip_text in game.clan.your_cat.pelt.accessories:
                info = "\ncurrently worn"

            self.selected_acc_details["selected_info"] = pygame_gui.elements.UITextBox(
                info,
                scale(pygame.Rect((195, 105),(300, 80))),
                object_id=get_text_box_theme("#text_box_22_horizcenter_vertcenter_spacing_95"),
                manager=MANAGER
            )

            accname = ACC_DISPLAY[self.selected_accessory.tool_tip_text]["default"]
            if 13 <= len(accname):  # check name length
                short_name = str(accname)[0:9]
                accname = short_name + '...'

            self.selected_acc_details["acc name"] = pygame_gui.elements.UITextBox(
                accname,
                scale(pygame.Rect((185, 175), (330, 80))),
                object_id="#text_box_34_horizcenter", manager=MANAGER)


    def update_cat_list(self):
        """Updates the cat sprite buttons. """
        valid_cats = self.chunks(self.get_valid_cats(), 30)

        # If the number of pages becomes smaller than the number of our current page, set
        #   the current page to the last page
        if self.current_page > len(valid_cats):
            self.list_page = len(valid_cats)

        # Handle which next buttons are clickable.
        if len(valid_cats) <= 1:
            self.previous_page_button.disable()
            self.next_page_button.disable()
        elif self.current_page >= len(valid_cats):
            self.previous_page_button.enable()
            self.next_page_button.disable()
        elif self.current_page == 1 and len(valid_cats) > 1:
            self.previous_page_button.disable()
            self.next_page_button.enable()
        else:
            self.previous_page_button.enable()
            self.next_page_button.enable()
        display_cats = []
        if valid_cats:
            display_cats = valid_cats[self.current_page - 1]

        # Kill all the currently displayed cats.
        for ele in self.cat_list_buttons:
            self.cat_list_buttons[ele].kill()
        self.cat_list_buttons = {}

        pos_x = 0
        pos_y = 40
        i = 0
        for cat in display_cats:
            self.cat_list_buttons["cat" + str(i)] = UISpriteButton(
                scale(pygame.Rect((200 + pos_x, 730 + pos_y), (100, 100))),
                cat.sprite,
                cat_object=cat,
                manager=MANAGER
            )
            pos_x += 120
            if pos_x >= 1100:
                pos_x = 0
                pos_y += 120
            i += 1

    def update_accessory_list(self):
        """Updates the cat sprite buttons. """
        cat = self.the_cat
        age = cat.age
        # self.cat_sprite = str(cat.pelt.cat_sprites[cat.age])

        # setting the cat_sprite (bc this makes things much easier)
        # if cat.not_working() and age != 'newborn' and game.config['cat_sprites']['sick_sprites']:
        #     if age in ['kitten', 'adolescent']:
        #         self.cat_sprite = str(19)
        #     else:
        #         self.cat_sprite = str(18)
        if cat.pelt.paralyzed and age != 'newborn':
            if age in ['kitten', 'adolescent']:
                self.cat_sprite = str(17)
            else:
                if cat.pelt.length == 'long':
                    self.cat_sprite = str(16)
                else:
                    self.cat_sprite = str(15)
        else:
            if age == 'elder' and not game.config['fun']['all_cats_are_newborn']:
                age = 'senior'

            if game.config['fun']['all_cats_are_newborn']:
                self.cat_sprite = str(cat.pelt.cat_sprites['newborn'])
            else:
                self.cat_sprite = str(cat.pelt.cat_sprites[age])

        pos_x = 20
        pos_y = 250
        i = 0

        self.cat_list_buttons = {}
        self.accessory_buttons = {}
        self.accessories_list = []
        start_index = self.page * 30
        end_index = start_index + 30

        if cat.pelt.accessory:
            if cat.pelt.accessory not in cat.pelt.inventory:
                cat.pelt.inventory.append(cat.pelt.accessory)

        for acc in cat.pelt.accessories:
            if acc not in cat.pelt.inventory:
                cat.pelt.inventory.append(acc)

        inventory_len = 0
        new_inv = []
        if self.search_bar.get_text() in ["", "search"]:
            inventory_len = len(cat.pelt.inventory)
            new_inv = cat.pelt.inventory
        else:
            for ac in cat.pelt.inventory:
                if self.search_bar.get_text().lower() in ac.lower():
                    inventory_len+=1
                    new_inv.append(ac)
        self.max_pages = math.ceil(inventory_len/30)

        if (self.max_pages == 1 or self.max_pages == 0):
            self.previous_page_button.disable()
            self.next_page_button.disable()
        if self.page == 0:
            self.previous_page_button.disable()
        if cat.pelt.inventory:
            for a, accessory in enumerate(new_inv[start_index:min(end_index, inventory_len)], start = start_index):
                try:
                    if self.search_bar.get_text() in ["", "search"] or self.search_bar.get_text().lower() in accessory.lower():
                        self.accessory_buttons[str(i)] = UIImageButton(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), "", tool_tip_text=accessory, object_id="#blank_button")
                        if accessory in cat.pelt.plant_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_herbs' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.wild_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_wild' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.collars:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['collars' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.flower_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_flower' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.plant2_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_plant2' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.snake_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_snake' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.smallAnimal_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_smallAnimal' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.deadInsect_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_deadInsect' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.aliveInsect_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_aliveInsect' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.fruit_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_fruit' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.crafted_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_crafted' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.tail2_accessories:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['acc_tail2' + accessory + self.cat_sprite], manager=MANAGER)
                        elif accessory in cat.pelt.np_autism:
                            self.cat_list_buttons["cat" + str(i)] = pygame_gui.elements.UIImage(scale(pygame.Rect((200 + pos_x, 500 + pos_y), (100, 100))), sprites.sprites['np_autism' + accessory + self.cat_sprite], manager=MANAGER)
                        self.accessories_list.append(accessory)
                        pos_x += 120
                        if pos_x >= 1200:
                            pos_x = 0
                            pos_y += 120
                        i += 1
                except:
                    continue

    def get_valid_cats(self):
        valid_cats = []

        for cat in Cat.all_cats_list:
            if not cat.dead and not cat.outside and not cat.ID == game.clan.your_cat.ID and not cat.moons == 0:
                valid_cats.append(cat)

        return valid_cats

    def on_use(self):
        # Due to a bug in pygame, any image with buttons over it must be blited
        screen.blit(self.list_frame, (150 / 1600 * screen_x, 720 / 1400 * screen_y))
        if self.search_bar and self.stage == "choose gift":
            if self.search_bar.is_focused and self.search_bar.get_text() == "search":
                self.search_bar.set_text("")
                self.page = 0
                if self.page == 0 and (self.max_pages == 1 or self.max_pages == 0):
                    self.previous_page_button.disable()
                    self.next_page_button.disable()
                elif self.page == 0:
                    self.previous_page_button.disable()
                    self.next_page_button.enable()
                elif self.page == self.max_pages - 1:
                    self.previous_page_button.enable()
                    self.next_page_button.disable()
                else:
                    self.previous_page_button.enable()
                    self.next_page_button.enable()
            elif self.search_bar.get_text() != self.previous_search_text:
                self.page = 0
                if self.cat_list_buttons:
                    for i in self.cat_list_buttons:
                        self.cat_list_buttons[i].kill()
                    for i in self.accessory_buttons:
                        self.accessory_buttons[i].kill()

                self.update_accessory_list()

                if self.page == 0 and self.max_pages in [0, 1]:
                    self.previous_page_button.disable()
                    self.next_page_button.disable()
                elif self.page == 0:
                    self.previous_page_button.disable()
                    self.next_page_button.enable()
                elif self.page == self.max_pages - 1:
                    self.previous_page_button.enable()
                    self.next_page_button.disable()
                else:
                    self.previous_page_button.enable()
                    self.next_page_button.enable()
                self.previous_search_text = self.search_bar.get_text()

    def chunks(self, L, n):
        return [L[x: x + n] for x in range(0, len(L), n)]
